import numpy as np
import paths
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader

import config as cfg

# =====================================================================

# Feature Extraction

# =====================================================================

def generate_qpsk_preamble(preamble_len: int) -> np.ndarray:
    """Generate a random unit-power QPSK preamble."""
    qpsk_map = {
    (0, 0): (1.0 + 1.0j) / np.sqrt(2),
    (0, 1): (-1.0 + 1.0j) / np.sqrt(2),
    (1, 1): (-1.0 - 1.0j) / np.sqrt(2),
    (1, 0): (1.0 - 1.0j) / np.sqrt(2),
    }

    bits = [
        tuple(np.random.randint(0, 2, 2))
        for _ in range(preamble_len)
    ]

    return np.array(
        [qpsk_map[b] for b in bits],
        dtype=np.complex128
    )

def extract_lag_summary(
    received_preamble: np.ndarray,
    preamble: np.ndarray,
    max_lag: int
    ) -> np.ndarray:
    """
    Extract CFO-related statistics from lag correlations.

    For each lag m:

        z[n] = r[n] * conj(s[n])

        C_m = mean( z[n] * conj(z[n-m]) )

    For an ideal CFO-only signal:

        C_m ~= exp(j * 2*pi*f0*m)

    Features per lag:

        0: Re(C_m)
        1: Im(C_m)
        2: |C_m|
        3: angle(C_m)

    Output:
        (max_lag, 4)
    """

    L0 = len(received_preamble)

    if max_lag >= L0:
        raise ValueError(
            f"max_lag ({max_lag}) must be smaller than "
            f"preamble length ({L0})."
        )

    # Remove known QPSK modulation.
    z = received_preamble * np.conj(preamble)

    lag_features = np.zeros(
        (max_lag, 4),
        dtype=np.float32
    )

    for m in range(1, max_lag + 1):

        # C_m = average of z[n] * conj(z[n-m])
        c_mean = (
            np.sum(
                z[m:L0] *
                np.conj(z[0:L0 - m])
            )
            / (L0 - m)
        )

        c_real = np.real(c_mean)
        c_imag = np.imag(c_mean)
        magnitude = np.abs(c_mean)
        phase = np.angle(c_mean)

        lag_features[m - 1, 0] = c_real
        lag_features[m - 1, 1] = c_imag
        lag_features[m - 1, 2] = magnitude
        lag_features[m - 1, 3] = phase

    return lag_features

# =====================================================================

# 1. Dynamic Training Dataset (Supports Curriculum Learning)

# =====================================================================

class DynamicCFODataset(Dataset):
    """
    Unified dataset where the SNR range can be dynamically updated
    during training for curriculum learning.
    """

    def __init__(
        self,
        min_snr: float = cfg.MIN_SNR,
        max_snr: float = cfg.MAX_SNR,
        iterations: int = cfg.ITERATIONS,
        preamble_len: int = cfg.PREAMBLE_LENGTH,
        max_lag: int = 16
    ):
        super().__init__()

        if max_lag >= preamble_len:
            raise ValueError(
                f"max_lag ({max_lag}) must be smaller than "
                f"preamble_len ({preamble_len})."
            )

        self.min_snr = min_snr
        self.max_snr = max_snr
        self.iterations = iterations
        self.preamble_len = preamble_len
        self.max_lag = max_lag

        self.n_indices = np.arange(
            preamble_len,
            dtype=np.float64
        )

    def update_snr_range(
        self,
        min_snr: float,
        max_snr: float
    ):
        """Update the SNR range dynamically."""
        self.min_snr = min_snr
        self.max_snr = max_snr

    def sample_snr(self) -> float:
        """Sample a continuous SNR from the current curriculum region."""
        return np.random.uniform(
            self.min_snr,
            self.max_snr
        )

    def __len__(self):
        return self.iterations

    def __getitem__(self, idx):

        # -------------------------------------------------------------
        # CFO
        # -------------------------------------------------------------

        normalized_cfo = np.random.uniform(
            -cfg.MAX_CFO,
            cfg.MAX_CFO
        )

        # -------------------------------------------------------------
        # SNR
        # -------------------------------------------------------------

        snr_db = self.sample_snr()

        snr_linear = 10.0 ** (snr_db / 10.0)

        # Unit signal power.
        #
        # Complex noise power:
        #
        #       E[|n|^2] = 1 / SNR
        #
        # Therefore each real/imaginary component has variance:
        #
        #       1 / (2*SNR)
        #
        noise_std = np.sqrt(
            1.0 / (2.0 * snr_linear)
        )

        # -------------------------------------------------------------
        # QPSK preamble
        # -------------------------------------------------------------

        preamble = generate_qpsk_preamble(
            self.preamble_len
        )

        # -------------------------------------------------------------
        # CFO
        # -------------------------------------------------------------

        cfo_phasor = np.exp(
            1j *
            2.0 *
            np.pi *
            normalized_cfo *
            self.n_indices
        )

        preamble_cfo = preamble * cfo_phasor

        # -------------------------------------------------------------
        # AWGN
        # -------------------------------------------------------------

        noise = noise_std * (
            np.random.randn(self.preamble_len)
            +
            1j * np.random.randn(self.preamble_len)
        )

        received_preamble = preamble_cfo + noise

        # -------------------------------------------------------------
        # Features
        # -------------------------------------------------------------

        X = extract_lag_summary(
            received_preamble,
            preamble,
            self.max_lag
        )

        # Normalize physical CFO to [-1, 1].
        y = normalized_cfo / cfg.MAX_CFO

        return (
            torch.from_numpy(X),
            torch.tensor(
                [y],
                dtype=torch.float32
            ),
            torch.tensor(
                snr_db,
                dtype=torch.float32
            )
        )

# =====================================================================

# 2. Fixed Validation Dataset

# =====================================================================

class FixedSNRDataset(Dataset):
    """
    Fixed validation dataset for stable evaluation metrics.
    """

    def __init__(
        self,
        snr_db: float,
        size: int = 1000,
        preamble_len: int = cfg.PREAMBLE_LENGTH,
        max_lag: int = 16
    ):

        if max_lag >= preamble_len:
            raise ValueError(
                f"max_lag ({max_lag}) must be smaller than "
                f"preamble_len ({preamble_len})."
            )

        self.size = size
        self.data = []

        n_indices = np.arange(
            preamble_len,
            dtype=np.float64
        )

        snr_linear = 10.0 ** (snr_db / 10.0)

        noise_std = np.sqrt(
            1.0 / (2.0 * snr_linear)
        )

        for _ in range(size):

            # ---------------------------------------------------------
            # CFO
            # ---------------------------------------------------------

            normalized_cfo = np.random.uniform(
                -cfg.MAX_CFO,
                cfg.MAX_CFO
            )

            # ---------------------------------------------------------
            # QPSK
            # ---------------------------------------------------------

            preamble = generate_qpsk_preamble(
                preamble_len
            )

            # ---------------------------------------------------------
            # CFO rotation
            # ---------------------------------------------------------

            cfo_phasor = np.exp(
                1j *
                2.0 *
                np.pi *
                normalized_cfo *
                n_indices
            )

            preamble_cfo = (
                preamble *
                cfo_phasor
            )

            # ---------------------------------------------------------
            # AWGN
            # ---------------------------------------------------------

            noise = noise_std * (
                np.random.randn(preamble_len)
                +
                1j * np.random.randn(preamble_len)
            )

            received = (
                preamble_cfo +
                noise
            )

            # ---------------------------------------------------------
            # Features
            # ---------------------------------------------------------

            X = extract_lag_summary(
                received,
                preamble,
                max_lag
            )

            # Normalized target.
            y = normalized_cfo / cfg.MAX_CFO

            self.data.append(
                (
                    torch.from_numpy(X),
                    torch.tensor(
                        [y],
                        dtype=torch.float32
                    ),
                    torch.tensor(
                        snr_db,
                        dtype=torch.float32
                    )
                )
            )

    def __len__(self):
        return self.size

    def __getitem__(self, idx):
        return self.data[idx]

# =====================================================================

# 3. Dense CFO Estimator (MLP)

# =====================================================================

class DenseCFOEstimator(nn.Module):
    """
    Lightweight MLP designed for lag-correlation CFO features.

    Input:
        [Batch, max_lag, 4]

    Features:
        Re(C_m)
        Im(C_m)
        |C_m|
        angle(C_m)

    Architecture:

        4*L -> 128 -> 64 -> 32 -> 1

    No BatchNorm:
        absolute correlation magnitude contains useful SNR/reliability
        information.

    No Dropout:
        training data is continuously randomized, so classical finite
        dataset overfitting is not the primary concern.
    """

    def __init__(
        self,
        max_lag: int,
        in_channels: int = 4
    ):
        super().__init__()

        input_dim = max_lag * in_channels

        self.net = nn.Sequential(

            nn.Flatten(start_dim=1),

            nn.Linear(
                input_dim,
                128
            ),
            nn.GELU(),

            nn.Linear(
                128,
                64
            ),
            nn.GELU(),

            nn.Linear(
                64,
                32
            ),
            nn.GELU(),

            nn.Linear(
                32,
                1
            )
        )

    def forward(self, x):
        return self.net(x)

# =====================================================================

# 4. CRB Calculation

# =====================================================================

def _compute_crb(
    snr_db: float,
    preamble_len: int
    ) -> float:
    """
    Theoretical CFO CRB for normalized CFO:
    
        f0 = Delta_f / Fs

    under a known unit-power signal in complex AWGN.

    CRB(f0) =
        3 /
        [2*pi^2*SNR*L*(L^2-1)]

    This is a local/unbiased-estimator bound.
    At low SNR and with bounded CFO priors, the CRB should therefore
    be interpreted carefully.
    """

    snr_linear = 10.0 ** (
        snr_db / 10.0
    )

    denominator = (
        2.0 *
        np.pi ** 2 *
        snr_linear *
        preamble_len *
        (preamble_len ** 2 - 1.0)
    )

    return 3.0 / denominator

# =====================================================================

# 5. Helper: Evaluate Model

# =====================================================================

def _evaluate_model(
    model,
    val_loaders,
    val_snrs,
    device,
    lag
    ):
    """
    Evaluate one model at one lag.

    Returns:
        mse_per_snr

    All MSE values are converted back to physical CFO units.
    """

    model.eval()

    mse_per_snr = {}

    with torch.no_grad():

        for snr in val_snrs:

            squared_error = 0.0

            for X_val, y_val, _ in val_loaders[snr]:

                X_val = X_val.to(
                    device,
                    non_blocking=True
                )

                y_val = y_val.to(
                    device,
                    non_blocking=True
                )

                # Use only the requested number of lags.
                X_val_lag = X_val[:, :lag, :]

                preds = model(
                    X_val_lag
                )

                batch_mse = F.mse_loss(
                    preds,
                    y_val,
                    reduction="sum"
                )

                squared_error += (
                    batch_mse.item()
                )

            # MSE in normalized CFO.
            normalized_mse = (
                squared_error /
                len(val_loaders[snr].dataset)
            )

            # Convert back to physical CFO.
            physical_mse = (
                normalized_mse *
                (cfg.MAX_CFO ** 2)
            )

            mse_per_snr[snr] = physical_mse

    return mse_per_snr

# =====================================================================

# 6. Detailed Evaluation

# =====================================================================

def _evaluate_model_detailed(
    model,
    val_loaders,
    val_snrs,
    device,
    lag
    ):
    """
    Detailed validation.

    Returns:

        {
            snr: {
                "mse": ...,
                "bias": ...,
                "variance": ...,
                "crb": ...,
                "mse_crb_ratio": ...
            }
        }
    """

    model.eval()

    results = {}

    with torch.no_grad():

        for snr in val_snrs:

            all_errors = []

            for X_val, y_val, _ in val_loaders[snr]:

                X_val = X_val.to(
                    device,
                    non_blocking=True
                )

                y_val = y_val.to(
                    device,
                    non_blocking=True
                )

                X_val_lag = X_val[:, :lag, :]

                predictions = model(
                    X_val_lag
                )

                # Normalized CFO -> physical CFO.
                pred_cfo = (
                    predictions *
                    cfg.MAX_CFO
                )

                true_cfo = (
                    y_val *
                    cfg.MAX_CFO
                )

                errors = (
                    pred_cfo -
                    true_cfo
                )

                all_errors.append(
                    errors.detach().cpu()
                )

            errors = torch.cat(
                all_errors,
                dim=0
            ).numpy().flatten()

            mse = float(
                np.mean(errors ** 2)
            )

            bias = float(
                np.mean(errors)
            )

            variance = float(
                np.var(errors)
            )

            crb = _compute_crb(
                snr,
                cfg.PREAMBLE_LENGTH
            )

            mse_crb_ratio = (
                mse / crb
                if crb > 0
                else np.inf
            )

            results[snr] = {
                "mse": mse,
                "bias": bias,
                "variance": variance,
                "crb": crb,
                "mse_crb_ratio": mse_crb_ratio
            }

    return results

# =====================================================================

# 7. Training with Reverse Curriculum Learning (Modified)

# =====================================================================

def train_cfo_model(
    num_lags_list: list,
    batch_size: int,
    base_epochs: int,
    lr: float
    ):

    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    print(f"Training device: {device}")

    max_lag = max(num_lags_list)

    if max_lag >= cfg.PREAMBLE_LENGTH:
        raise ValueError(
            f"Maximum lag ({max_lag}) must be "
            f"smaller than PREAMBLE_LENGTH "
            f"({cfg.PREAMBLE_LENGTH})."
        )

    # -------------------------------------------------------------
    # Validation SNR points
    # -------------------------------------------------------------

    val_snrs = [-10, -8, -6, -4, -2]

    # -------------------------------------------------------------
    # Validation datasets
    # -------------------------------------------------------------

    print("Generating fixed validation datasets...")

    val_size = int(cfg.ITERATIONS * 0.2)
    val_loaders = {}

    for snr in val_snrs:
        val_loaders[snr] = DataLoader(
            FixedSNRDataset(
                snr_db=snr,
                size=val_size,
                max_lag=max_lag
            ),
            batch_size=500,
            shuffle=False,
            pin_memory=(device.type == "cuda")
        )

    # -------------------------------------------------------------
    # Models
    # -------------------------------------------------------------

    models = nn.ModuleDict({
        str(lag): DenseCFOEstimator(max_lag=lag, in_channels=4)
        for lag in num_lags_list
    }).to(device)

    # -------------------------------------------------------------
    # ONE persistent optimizer
    # -------------------------------------------------------------

    optimizer = optim.AdamW(
        models.parameters(),
        lr=lr,
        weight_decay=1e-5
    )

    # -------------------------------------------------------------
    # Curriculum (Modified)
    # -------------------------------------------------------------

    # -------------------------------------------------------------
    # Curriculum (Modified)
    # -------------------------------------------------------------

    curriculum_stages = [
        ("Phase 1: High-SNR Initialization", -2.0, 5.0, base_epochs),
        ("Phase 2: Upper-Mid-SNR Initialization", -6.0, -2.0, base_epochs),
        ("Phase 3: Low Adaptation", -10.0, -6.0, base_epochs),
        ("Phase 4: Overall Transition", -10.0, -2.0, base_epochs),
    ]

    # -------------------------------------------------------------
    # Checkpoint tracking
    # -------------------------------------------------------------

    best_full_range_mses = {str(lag): float("inf") for lag in num_lags_list}
    best_low_snr_mses = {str(lag): float("inf") for lag in num_lags_list}

    full_model_paths = {str(lag): paths.model(f"best_cfo_model_L{lag}.pth") for lag in num_lags_list}
    low_model_paths = {str(lag): paths.model(f"best_cfo_model_low_L{lag}.pth") for lag in num_lags_list}

    # -------------------------------------------------------------
    # Curriculum Execution
    # -------------------------------------------------------------

    def get_infinite_batches(loader):
        while True:
            for batch in loader:
                yield batch

    for phase_idx, (phase_name, min_snr, max_snr, stage_epochs) in enumerate(curriculum_stages):

        print("\n" + "=" * 75)
        print(f"{phase_name} | SNR Range: [{min_snr}, {max_snr}] dB | Epochs: {stage_epochs}")
        print("=" * 75)

        # ---------------------------------------------------------
        # Progressively decay the starting LR for each new stage
        # ---------------------------------------------------------
        
        stage_decay = 0.5  # Multiplier to reduce LR per stage. Tune between 0.4 and 0.8.
        stage_lr = lr * (stage_decay ** phase_idx)
        
        for param_group in optimizer.param_groups:
            param_group["lr"] = stage_lr

        scheduler = optim.lr_scheduler.CosineAnnealingLR(
            optimizer,
            T_max=stage_epochs,
            eta_min=stage_lr * 2e-4
        )

        # ---------------------------------------------------------
        # Dynamic datasets (Main and Anchor)
        # ---------------------------------------------------------
        
        train_dataset = DynamicCFODataset(
            min_snr=min_snr,
            max_snr=max_snr,
            iterations=cfg.ITERATIONS,
            preamble_len=cfg.PREAMBLE_LENGTH,
            max_lag=max_lag
        )

        # Anchor dataset covers everything from the current minimum SNR up to 20.0 dB.
        anchor_dataset = DynamicCFODataset(
            min_snr=min_snr,
            max_snr=20.0,
            iterations=cfg.ITERATIONS,
            preamble_len=cfg.PREAMBLE_LENGTH,
            max_lag=max_lag
        )

        num_workers = min(8, max(0, cfg.ITERATIONS // max(batch_size, 1)))

        train_loader = DataLoader(
            train_dataset,
            batch_size=batch_size,
            shuffle=True,
            num_workers=num_workers,
            pin_memory=(device.type == "cuda"),
            persistent_workers=(num_workers > 0)
        )

        anchor_loader = DataLoader(
            anchor_dataset,
            batch_size=max(16, batch_size // 4), # Smaller batch for the anchor
            shuffle=True,
            num_workers=num_workers,
            pin_memory=(device.type == "cuda"),
            persistent_workers=(num_workers > 0)
        )
        
        anchor_iter = iter(get_infinite_batches(anchor_loader))

        # ---------------------------------------------------------
        # Stage training
        # ---------------------------------------------------------

        for epoch in range(1, stage_epochs + 1):

            models.train()
            epoch_loss = 0.0

            # -----------------------------------------------------
            # Training batches
            # -----------------------------------------------------

            for X_batch, y_batch, snr_db_batch in train_loader:

                X_batch = X_batch.to(device, non_blocking=True)
                y_batch = y_batch.to(device, non_blocking=True)
                snr_db_batch = snr_db_batch.to(device, non_blocking=True)
                
                # Fetch anchor batch (now unpacking snr_db as well)
                X_anchor, y_anchor, snr_db_anchor = next(anchor_iter)
                X_anchor = X_anchor.to(device, non_blocking=True)
                y_anchor = y_anchor.to(device, non_blocking=True)
                snr_db_anchor = snr_db_anchor.to(device, non_blocking=True)

                # -------------------------------------------------
                # Compute Log-Scaled SNR Weights
                # log10(1 + linear_snr) compresses the dynamic range 
                # so high-SNR doesn't starve low-SNR gradients.
                # -------------------------------------------------
                snr_linear_main = 10.0 ** (snr_db_batch / 10.0)
                weight_main = torch.log10(1.0 + snr_linear_main)

                snr_linear_anchor = 10.0 ** (snr_db_anchor / 10.0)
                weight_anchor = torch.log10(1.0 + snr_linear_anchor)

                optimizer.zero_grad(set_to_none=True)
                total_loss = 0.0

                for str_l, model in models.items():

                    lag = int(str_l)

                    # Main curriculum loss (element-wise MSE multiplied by weight)
                    X_lag = X_batch[:, :lag, :]
                    predictions = model(X_lag)
                    
                    sq_err_main = (predictions - y_batch) ** 2
                    main_loss = (sq_err_main * weight_main.unsqueeze(1)).mean()
                    
                    # Anchor loss (element-wise MSE multiplied by weight)
                    X_anchor_lag = X_anchor[:, :lag, :]
                    anchor_predictions = model(X_anchor_lag)
                    
                    sq_err_anchor = (anchor_predictions - y_anchor) ** 2
                    anchor_loss = (sq_err_anchor * weight_anchor.unsqueeze(1)).mean()

                    # Combine losses (Anchor weight = 0.25)
                    loss = main_loss + 0.25 * anchor_loss
                    total_loss = total_loss + loss

                total_loss.backward()

                torch.nn.utils.clip_grad_norm_(
                    models.parameters(),
                    max_norm=5.0
                )

                optimizer.step()
                epoch_loss += total_loss.item()

            scheduler.step()
            current_lr = optimizer.param_groups[0]["lr"]

            # ---------------------------------------------------------
            # Validation
            # ---------------------------------------------------------

            should_validate = (epoch % 5 == 0 or epoch == stage_epochs)

            if not should_validate:
                continue

            print(f"\n--- {phase_name} | Epoch {epoch}/{stage_epochs} ---")
            
            train_loss = epoch_loss / len(train_loader)
            print(f"Train Combined MSE: {train_loss:.3e} | LR: {current_lr:.3e}")

            for str_l, model in models.items():

                lag = int(str_l)
                detailed = _evaluate_model_detailed(
                    model, val_loaders, val_snrs, device, lag
                )

                avg_full_mse = np.mean([detailed[s]["mse"] for s in val_snrs])
                low_snr_keys = [s for s in val_snrs if s <= 0]
                avg_low_mse = np.mean([detailed[s]["mse"] for s in low_snr_keys])

                avg_ratio = np.mean([
                    detailed[s]["mse_crb_ratio"]
                    for s in val_snrs
                    if np.isfinite(detailed[s]["mse_crb_ratio"])
                ])

                marker_full = ""
                if avg_full_mse < best_full_range_mses[str_l]:
                    best_full_range_mses[str_l] = avg_full_mse
                    torch.save(model.state_dict(), full_model_paths[str_l])
                    marker_full = " [NEW BEST FULL]"

                marker_low = ""
                if avg_low_mse < best_low_snr_mses[str_l]:
                    best_low_snr_mses[str_l] = avg_low_mse
                    torch.save(model.state_dict(), low_model_paths[str_l])
                    marker_low = " [NEW BEST LOW]"

                print(
                    f"\nLag {str_l:<3} | "
                    f"Avg Full MSE: {avg_full_mse:.3e} | "
                    f"Avg Low MSE: {avg_low_mse:.3e} | "
                    f"Avg MSE/CRB: {avg_ratio:.3f}"
                    f"{marker_full}{marker_low}"
                )

                for snr in val_snrs:
                    r = detailed[snr]
                    print(
                        f"    {snr:>4} dB | "
                        f"MSE: {r['mse']:.3e} | "
                        f"Bias: {r['bias']:+.3e} | "
                        f"Var: {r['variance']:.3e} | "
                        f"CRB: {r['crb']:.3e} | "
                        f"MSE/CRB: {r['mse_crb_ratio']:.2f}"
                    )

    # =================================================================
    # Final Report
    # =================================================================

    print("\n" + "=" * 75)
    print("TRAINING COMPLETE")
    print("=" * 75)

    print("\nBest Full-Range Models:")
    for lag in num_lags_list:
        print(f"Lag {lag:<3} | MSE = {best_full_range_mses[str(lag)]:.4e} | File = {full_model_paths[str(lag)]}")

    print("\nBest Low-SNR Models:")
    for lag in num_lags_list:
        print(f"Lag {lag:<3} | MSE = {best_low_snr_mses[str(lag)]:.4e} | File = {low_model_paths[str(lag)]}")

    print("\n" + "=" * 75)
    print("FINAL BEST-MODEL VALIDATION")
    print("=" * 75)

    for str_l in models.keys():
        lag = int(str_l)
        model = models[str_l]
        checkpoint = low_model_paths[str_l]

        try:
            model.load_state_dict(torch.load(checkpoint, map_location=device))
        except FileNotFoundError:
            print(f"Warning: checkpoint not found for Lag {lag}: {checkpoint}")
            continue

        detailed = _evaluate_model_detailed(model, val_loaders, val_snrs, device, lag)

        print("\n" + "-" * 100)
        print(f"Lag {lag} | Best Low-SNR Model")
        print("-" * 100)
        print(f"{'SNR':>7} | {'MSE':>13} | {'Bias':>13} | {'Variance':>13} | {'CRB':>13} | {'MSE/CRB':>10}")
        print("-" * 100)

        for snr in sorted(val_snrs):
            r = detailed[snr]
            print(
                f"{snr:>7.1f} | "
                f"{r['mse']:>13.4e} | "
                f"{r['bias']:>+13.4e} | "
                f"{r['variance']:>13.4e} | "
                f"{r['crb']:>13.4e} | "
                f"{r['mse_crb_ratio']:>10.3f}"
            )

    # =================================================================
    # Save Final Stage Weights
    # =================================================================

    final_model_paths = {str(lag): paths.model(f"final_cfo_model_L{lag}.pth") for lag in num_lags_list}

    for str_l, model in models.items():
        torch.save(model.state_dict(), final_model_paths[str_l])
        print(f"Saved final stage model for Lag {str_l} to {final_model_paths[str_l]}")

    # =================================================================
    # Final Report
    # =================================================================

    print("\n" + "=" * 75)
    print("TRAINING COMPLETE")
    print("=" * 75)