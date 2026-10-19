import os
import paths
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F

from torch.utils.data import Dataset, DataLoader


# =====================================================================
# Configuration
# =====================================================================

class cfg:
    MIN_SNR = -10.0
    MAX_SNR = 10.0

    PREAMBLE_LENGTH = 128
    MAX_CFO = 0.2
    MAX_LAG = 64

    NUM_TRAIN = 25000
    NUM_VAL = 5000
    NUM_TEST_PER_SNR = 2000

    BATCH_SIZE = 256
    EPOCHS = 50

    SEED = 42
    NUM_WORKERS = 8

    # Curriculum
    CURRICULUM_STAGES = [
        (-5.0, 0.0),    # Stage 1: Low/mid SNR
        (0.0, 5.0),     # Stage 2: Mid SNR
        (5.0, 10.0),    # Stage 3: High SNR
        (-5.0, 10.0)    # Stage 4: Fine-tune across full region
    ]


# =====================================================================
# Reproducibility
# =====================================================================

def set_seed(seed):
    np.random.seed(seed)
    torch.manual_seed(seed)

    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


# =====================================================================
# Phase 1 Expert
# =====================================================================

class DenseCFOEstimator(nn.Module):

    def __init__(self, max_lag: int, in_channels: int = 4):
        super().__init__()

        input_dim = max_lag * in_channels

        self.net = nn.Sequential(
            nn.Flatten(start_dim=1),

            nn.Linear(input_dim, 128),
            nn.GELU(),

            nn.Linear(128, 64),
            nn.GELU(),

            nn.Linear(64, 32),
            nn.GELU(),

            nn.Linear(32, 1)
        )

    def forward(self, x):
        return self.net(x)


# =====================================================================
# EXACT EXPERT FEATURE EXTRACTION
# =====================================================================

def extract_lag_summary(
    received_preamble,
    preamble,
    max_lag
):
    """
    Extract the exact four features used by the Phase-1 expert.

    For every lag m:

        z[n] = r[n] * conj(s[n])

        C_m = mean(
            z[n] * conj(z[n-m])
        )

    Features:

        0 -> Re(C_m)
        1 -> Im(C_m)
        2 -> |C_m|
        3 -> angle(C_m)

    Output shape:

        (max_lag, 4)
    """

    L0 = len(received_preamble)

    if max_lag >= L0:
        raise ValueError(
            f"max_lag ({max_lag}) must be smaller than "
            f"preamble length ({L0})"
        )

    # Remove known QPSK modulation
    z = received_preamble * np.conj(preamble)

    lag_features = np.zeros(
        (max_lag, 4),
        dtype=np.float32
    )

    for m in range(1, max_lag + 1):

        c_mean = (
            np.sum(
                z[m:L0] *
                np.conj(z[:L0 - m])
            )
            / (L0 - m)
        )

        lag_features[m - 1, 0] = np.real(c_mean)
        lag_features[m - 1, 1] = np.imag(c_mean)
        lag_features[m - 1, 2] = np.abs(c_mean)
        lag_features[m - 1, 3] = np.angle(c_mean)

    return lag_features


# =====================================================================
# Mengali-Morelli CFO Estimator
# =====================================================================

def mm_cfo_estimate(
    received_preamble,
    preamble,
    max_lag_mm
):

    L = len(received_preamble)
    M = max_lag_mm

    # Remove known QPSK symbols
    z = received_preamble * np.conj(preamble)

    # -------------------------------------------------------------
    # Autocorrelation
    # -------------------------------------------------------------

    R = np.zeros(
        M + 1,
        dtype=np.complex128
    )

    for m in range(1, M + 1):

        R[m] = (
            np.sum(
                z[m:L] *
                np.conj(z[:L - m])
            )
            / (L - m)
        )

    # -------------------------------------------------------------
    # Phase differences
    # -------------------------------------------------------------

    delta_phi = np.zeros(M)

    delta_phi[0] = np.angle(R[1])

    if M > 1:

        delta_phi[1:] = np.angle(
            R[2:] *
            np.conj(R[1:M])
        )

    # -------------------------------------------------------------
    # M&M weights
    # -------------------------------------------------------------

    m = np.arange(
        1,
        M + 1
    )

    denominator = (
        M *
        (
            4 * M**2
            - 6 * M * L
            + 3 * L**2
            - 1
        )
    )

    weights = (
        3 *
        (
            (L - m) * (L - m + 1)
            - M * (L - M)
        )
        / denominator
    )

    # -------------------------------------------------------------
    # CFO estimate
    # -------------------------------------------------------------

    physical_cfo = (
        np.sum(
            weights * delta_phi
        )
        / (2 * np.pi)
    )

    # Normalize to NN target convention
    normalized_cfo = (
        physical_cfo /
        cfg.MAX_CFO
    )

    return normalized_cfo


# =====================================================================
# CRB
# =====================================================================

def calculate_crb(
    snr_db,
    L
):

    snr_linear = 10.0 ** (
        snr_db / 10.0
    )

    return (
        3.0 /
        (
            2.0 *
            np.pi**2 *
            snr_linear *
            L *
            (L**2 - 1)
        )
    )


# =====================================================================
# Dataset
# =====================================================================

class FusionDataset(Dataset):

    def __init__(
        self,
        num_samples,
        expert_state,
        snr_range=None,
        fixed_snr=None,
        seed=42
    ):

        self.num_samples = num_samples

        self.snr_range = (
            snr_range
            if snr_range is not None
            else (
                cfg.MIN_SNR,
                cfg.MAX_SNR
            )
        )

        self.fixed_snr = fixed_snr
        self.seed = seed

        self.worker_expert = None

        self.expert_state = expert_state

        self.n_indices = np.arange(
            cfg.PREAMBLE_LENGTH,
            dtype=np.float64
        )

    def __len__(self):
        return self.num_samples

    # -------------------------------------------------------------
    # Create expert once per worker
    # -------------------------------------------------------------

    def _get_expert(self):

        if self.worker_expert is None:

            self.worker_expert = DenseCFOEstimator(
                cfg.MAX_LAG,
                4
            )

            self.worker_expert.load_state_dict(
                self.expert_state
            )

            self.worker_expert.eval()

            for p in self.worker_expert.parameters():
                p.requires_grad = False

        return self.worker_expert

    # -------------------------------------------------------------
    # Generate one sample
    # -------------------------------------------------------------

    def __getitem__(self, idx):

        expert = self._get_expert()

        # ---------------------------------------------------------
        # Random generator
        # ---------------------------------------------------------

        rng = np.random.default_rng()

        # ---------------------------------------------------------
        # Target CFO
        # ---------------------------------------------------------

        normalized_cfo = rng.uniform(
            -1.0,
            1.0
        )

        # ---------------------------------------------------------
        # SNR
        # ---------------------------------------------------------

        if self.fixed_snr is not None:

            snr_db = self.fixed_snr

        else:

            snr_db = rng.uniform(
                self.snr_range[0],
                self.snr_range[1]
            )

        snr_linear = (
            10.0 **
            (snr_db / 10.0)
        )

        noise_std = np.sqrt(
            1.0 /
            (2.0 * snr_linear)
        )

        # ---------------------------------------------------------
        # QPSK preamble
        # ---------------------------------------------------------

        bits = rng.integers(
            0,
            2,
            size=(
                cfg.PREAMBLE_LENGTH,
                2
            )
        )

        real_part = np.where(
            bits[:, 1] == 0,
            1.0,
            -1.0
        )

        imag_part = np.where(
            bits[:, 0] == 0,
            1.0,
            -1.0
        )

        preamble = (
            real_part +
            1j * imag_part
        ) / np.sqrt(2)

        # ---------------------------------------------------------
        # Apply CFO
        # ---------------------------------------------------------

        physical_cfo = (
            normalized_cfo *
            cfg.MAX_CFO
        )

        cfo_phasor = np.exp(
            1j *
            2 *
            np.pi *
            physical_cfo *
            self.n_indices
        )

        # ---------------------------------------------------------
        # AWGN
        # ---------------------------------------------------------

        noise = (
            noise_std *
            (
                rng.standard_normal(
                    cfg.PREAMBLE_LENGTH
                )
                +
                1j *
                rng.standard_normal(
                    cfg.PREAMBLE_LENGTH
                )
            )
        )

        received = (
            preamble *
            cfo_phasor
            +
            noise
        )

        # ---------------------------------------------------------
        # EXACT expert features
        # ---------------------------------------------------------

        lag_summary = extract_lag_summary(
            received,
            preamble,
            cfg.MAX_LAG
        )

        # ---------------------------------------------------------
        # Phase-1 Expert
        # ---------------------------------------------------------

        with torch.no_grad():

            x = (
                torch
                .from_numpy(lag_summary)
                .float()
                .unsqueeze(0)
            )

            nn_est = expert(x).item()

        # ---------------------------------------------------------
        # M&M
        # ---------------------------------------------------------

        mm_est = mm_cfo_estimate(
            received,
            preamble,
            cfg.MAX_LAG
        )

        # ---------------------------------------------------------
        # ONLY MODEL A FEATURES
        # ---------------------------------------------------------

        features_A = np.array(
            [
                nn_est,
                mm_est
            ],
            dtype=np.float32
        )

        # ---------------------------------------------------------
        # Return
        # ---------------------------------------------------------

        return (
            torch.from_numpy(features_A),

            torch.tensor(
                [normalized_cfo],
                dtype=torch.float32
            ),

            torch.tensor(
                [snr_db],
                dtype=torch.float32
            )
        )


# =====================================================================
# Fusion Network A
# =====================================================================

class FusionNetwork(nn.Module):

    """
    Fusion Model A

    Input:
        [NN_estimate, MM_estimate]

    Output:
        w * NN + (1-w) * MM
    """

    def __init__(
        self,
        in_features=2
    ):

        super().__init__()

        self.net = nn.Sequential(

            nn.LayerNorm(
                in_features
            ),

            nn.Linear(
                in_features,
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
                16
            ),

            nn.GELU()
        )

        self.out_layer = nn.Linear(
            16,
            1
        )

    def forward(
        self,
        x,
        nn_est,
        mm_est
    ):

        out = self.out_layer(
            self.net(x)
        )

        w = torch.sigmoid(out)

        estimate = (
            w * nn_est
            +
            (1.0 - w) * mm_est
        )

        return estimate, w


# =====================================================================
# DataLoader
# =====================================================================

def make_loader(
    num_samples,
    expert_state,
    device,
    snr_range=None,
    fixed_snr=None,
    seed=42,
    shuffle=False
):

    dataset = FusionDataset(
        num_samples=num_samples,
        expert_state=expert_state,
        snr_range=snr_range,
        fixed_snr=fixed_snr,
        seed=seed
    )

    return DataLoader(
        dataset,

        batch_size=cfg.BATCH_SIZE,

        shuffle=shuffle,

        num_workers=cfg.NUM_WORKERS,

        pin_memory=(
            device.type == "cuda"
        ),

        persistent_workers=(
            cfg.NUM_WORKERS > 0
        ),

        prefetch_factor=2,

        drop_last=False
    )


# =====================================================================
# SNR Binning
# =====================================================================

def map_snr_to_bin(snr_db):

    snr_rounded = (
        torch.round(
            snr_db / 2.0
        ) * 2.0
    )

    return torch.clamp(
        snr_rounded,
        -10.0,
        10.0
    )


def get_bin_index(snr_rounded):

    return (
        (snr_rounded + 10.0) /
        2.0
    ).long()


# =====================================================================
# Expert Baseline
# =====================================================================

def compute_nn_baseline_tensor(
    calib_loader,
    device,
    max_cfo
):

    snr_range = [
        -10, -8, -6, -4, -2,
        0, 2, 4, 6, 8, 10
    ]

    sum_sq_err = {
        s: 0.0
        for s in snr_range
    }

    sample_counts = {
        s: 0
        for s in snr_range
    }

    with torch.no_grad():

        for (
            features,
            y_true,
            snr_db
        ) in calib_loader:

            features = features.to(
                device,
                non_blocking=True
            )

            y_true = y_true.to(
                device,
                non_blocking=True
            )

            snr_db = snr_db.to(
                device,
                non_blocking=True
            )

            nn_est = features[:, 0:1]

            fT_nn = (
                nn_est *
                max_cfo
            )

            fT_true = (
                y_true *
                max_cfo
            )

            sq_err = (
                fT_nn -
                fT_true
            ) ** 2

            s_bins = map_snr_to_bin(
                snr_db
            )

            for target_snr in snr_range:

                mask = (
                    s_bins ==
                    target_snr
                )

                if mask.any():

                    sum_sq_err[target_snr] += (
                        sq_err[mask]
                        .sum()
                        .item()
                    )

                    sample_counts[target_snr] += (
                        mask.sum()
                        .item()
                    )

    print(
        "\n--- Expert Calibration ---"
    )

    print(
        f"{'SNR':<8} | "
        f"{'Samples':<10} | "
        f"{'NN MSE':<14}"
    )

    print("-" * 40)

    available_mses = [
        sum_sq_err[s] /
        sample_counts[s]
        for s in snr_range
        if sample_counts[s] > 0
    ]

    fallback_mse = (
        sum(available_mses) /
        len(available_mses)
        if available_mses
        else 1.0
    )

    vals = []

    for s in snr_range:

        count = sample_counts[s]

        if count == 0:

            mse_val = fallback_mse

            print(
                f"{s:<8} | "
                f"{count:<10} | "
                f"{mse_val:<14.4e} "
                f"(fallback)"
            )

        else:

            mse_val = (
                sum_sq_err[s] /
                count
            )

            print(
                f"{s:<8} | "
                f"{count:<10} | "
                f"{mse_val:<14.4e}"
            )

        vals.append(mse_val)

    print()

    return torch.tensor(
        vals,
        dtype=torch.float32,
        device=device
    )


# =====================================================================
# Relative Loss
# =====================================================================

def relative_to_nn_mse_loss(
    y_pred,
    y_true,
    snr_db_batch,
    max_cfo,
    baseline_vals
):

    fT_hat = (
        y_pred *
        max_cfo
    )

    fT_true = (
        y_true *
        max_cfo
    )

    snr_rounded = map_snr_to_bin(
        snr_db_batch
    )

    indices = get_bin_index(
        snr_rounded
    )

    base_mse = baseline_vals[
        indices
    ].unsqueeze(1)

    squared_error = (
        fT_hat -
        fT_true
    ) ** 2

    relative_loss = (
        squared_error /
        torch.clamp(
            base_mse,
            min=1e-12
        )
    )

    return torch.mean(
        relative_loss
    )


# =====================================================================
# Train Fusion A
# =====================================================================

def train_fusion_model(
    model,
    train_loader,
    val_loader,
    device,
    epochs,
    baseline_vals=None
):

    if baseline_vals is None:

        baseline_vals = (
            compute_nn_baseline_tensor(
                val_loader,
                device,
                cfg.MAX_CFO
            )
        )

    optimizer = optim.AdamW(
        model.parameters(),
        lr=3e-4,
        weight_decay=1e-5
    )

    scheduler = optim.lr_scheduler.CosineAnnealingLR(
        optimizer,
        T_max=epochs,
        eta_min=1e-7
    )

    best_loss = float("inf")
    best_weights = None

    for epoch in range(epochs):

        # =========================================================
        # Training
        # =========================================================

        model.train()

        train_mse = 0.0
        train_rel = 0.0

        for (
            features,
            y_true,
            snr_db
        ) in train_loader:

            features = features.to(
                device,
                non_blocking=True
            )

            y_true = y_true.to(
                device,
                non_blocking=True
            )

            snr_db = snr_db.to(
                device,
                non_blocking=True
            )

            nn_est = features[:, 0:1]
            mm_est = features[:, 1:2]

            optimizer.zero_grad(
                set_to_none=True
            )

            estimate, weights = model(
                features,
                nn_est,
                mm_est
            )

            loss = relative_to_nn_mse_loss(
                estimate,
                y_true,
                snr_db,
                cfg.MAX_CFO,
                baseline_vals
            )

            loss.backward()

            optimizer.step()

            with torch.no_grad():

                physical_mse = F.mse_loss(
                    estimate * cfg.MAX_CFO,
                    y_true * cfg.MAX_CFO
                )

            train_mse += (
                physical_mse.item()
            )

            train_rel += (
                loss.item()
            )

        n_train = len(
            train_loader
        )

        train_mse /= n_train
        train_rel /= n_train

        # =========================================================
        # Validation
        # =========================================================

        model.eval()

        val_mse = 0.0
        val_rel = 0.0

        val_nn_mse = 0.0
        val_mm_mse = 0.0

        with torch.no_grad():

            for (
                features,
                y_true,
                snr_db
            ) in val_loader:

                features = features.to(
                    device,
                    non_blocking=True
                )

                y_true = y_true.to(
                    device,
                    non_blocking=True
                )

                snr_db = snr_db.to(
                    device,
                    non_blocking=True
                )

                nn_est = features[:, 0:1]
                mm_est = features[:, 1:2]

                estimate, weights = model(
                    features,
                    nn_est,
                    mm_est
                )

                physical_mse = F.mse_loss(
                    estimate * cfg.MAX_CFO,
                    y_true * cfg.MAX_CFO
                )

                nn_mse = F.mse_loss(
                    nn_est * cfg.MAX_CFO,
                    y_true * cfg.MAX_CFO
                )

                mm_mse = F.mse_loss(
                    mm_est * cfg.MAX_CFO,
                    y_true * cfg.MAX_CFO
                )

                rel_loss = relative_to_nn_mse_loss(
                    estimate,
                    y_true,
                    snr_db,
                    cfg.MAX_CFO,
                    baseline_vals
                )

                val_mse += (
                    physical_mse.item()
                )

                val_rel += (
                    rel_loss.item()
                )

                val_nn_mse += (
                    nn_mse.item()
                )

                val_mm_mse += (
                    mm_mse.item()
                )

        n_val = len(
            val_loader
        )

        val_mse /= n_val
        val_rel /= n_val
        val_nn_mse /= n_val
        val_mm_mse /= n_val

        # =========================================================
        # Logging
        # =========================================================

        if (
            (epoch + 1) % 5 == 0
            or epoch == 0
        ):

            lr = (
                optimizer
                .param_groups[0]["lr"]
            )

            print(
                f"Epoch {epoch+1:02d}/{epochs} | "
                f"Train MSE: {train_mse:.4e} | "
                f"Val MSE: {val_mse:.4e} | "
                f"NN MSE: {val_nn_mse:.4e} | "
                f"M&M MSE: {val_mm_mse:.4e} | "
                f"Rel: {val_rel:.4e} | "
                f"LR: {lr:.3e}"
            )

        # =========================================================
        # Save best
        # =========================================================

        if val_mse < best_loss:

            best_loss = val_mse

            best_weights = {
                k: v.detach()
                .cpu()
                .clone()
                for k, v in
                model.state_dict().items()
            }

        scheduler.step()

    if best_weights is not None:

        model.load_state_dict(
            best_weights
        )

    return model


# =====================================================================
# Expert Diagnostic
# =====================================================================

@torch.no_grad()
def evaluate_expert_per_snr(
    expert_state,
    device
):

    print(
        "\n"
        + "=" * 70
    )

    print(
        "PHASE-1 EXPERT DIAGNOSTIC"
    )

    print(
        "=" * 70
    )

    snr_grid = np.arange(
        -4,
        11,
        2
    )

    expert = DenseCFOEstimator(
        cfg.MAX_LAG,
        4
    ).to(device)

    expert.load_state_dict(
        expert_state
    )

    expert.eval()

    for snr_db in snr_grid:

        loader = make_loader(
            cfg.NUM_TEST_PER_SNR,
            expert_state,
            device,
            fixed_snr=float(snr_db),
            seed=cfg.SEED + 5000,
            shuffle=False
        )

        mse_sum = 0.0
        total = 0

        for (
            features,
            y_true,
            snr
        ) in loader:

            features = features.to(
                device
            )

            y_true = y_true.to(
                device
            )

            # IMPORTANT:
            # The dataset's first feature is the expert output.
            nn_est = features[:, 0:1]

            mse_sum += F.mse_loss(
                nn_est * cfg.MAX_CFO,
                y_true * cfg.MAX_CFO,
                reduction="sum"
            ).item()

            total += y_true.shape[0]

        mse = (
            mse_sum /
            total
        )

        crb = calculate_crb(
            snr_db,
            cfg.PREAMBLE_LENGTH
        )

        print(
            f"SNR={snr_db:>4} dB | "
            f"Expert MSE={mse:.4e} | "
            f"CRB={crb:.4e}"
        )

    print(
        "=" * 70
    )


# =====================================================================
# Fusion Evaluation
# =====================================================================

@torch.no_grad()
def evaluate_fusion_per_snr(
    model,
    expert_state,
    device
):

    print(
        "\n"
        + "=" * 100
    )

    print(
        "FUSION A PER-SNR EVALUATION"
    )

    print(
        "=" * 100
    )

    print(
        f"{'SNR':<7} | "
        f"{'Fusion MSE':<14} | "
        f"{'NN MSE':<14} | "
        f"{'M&M MSE':<14} | "
        f"{'Avg W':<10} | "
        f"{'CRB':<14}"
    )

    print("-" * 100)

    snr_grid = np.arange(
        -4,
        11,
        2
    )

    model.eval()

    for snr_db in snr_grid:

        test_loader = make_loader(
            cfg.NUM_TEST_PER_SNR,
            expert_state,
            device,
            fixed_snr=float(snr_db),
            seed=cfg.SEED + 999,
            shuffle=False
        )

        fusion_sq = 0.0
        nn_sq = 0.0
        mm_sq = 0.0

        weight_sum = 0.0

        total = 0

        for (
            features,
            y_true,
            snr
        ) in test_loader:

            features = features.to(
                device,
                non_blocking=True
            )

            y_true = y_true.to(
                device,
                non_blocking=True
            )

            nn_est = features[:, 0:1]
            mm_est = features[:, 1:2]

            estimate, weights = model(
                features,
                nn_est,
                mm_est
            )

            fusion_sq += F.mse_loss(
                estimate * cfg.MAX_CFO,
                y_true * cfg.MAX_CFO,
                reduction="sum"
            ).item()

            nn_sq += F.mse_loss(
                nn_est * cfg.MAX_CFO,
                y_true * cfg.MAX_CFO,
                reduction="sum"
            ).item()

            mm_sq += F.mse_loss(
                mm_est * cfg.MAX_CFO,
                y_true * cfg.MAX_CFO,
                reduction="sum"
            ).item()

            weight_sum += (
                weights.sum().item()
            )

            total += (
                y_true.shape[0]
            )

        fusion_mse = (
            fusion_sq /
            total
        )

        nn_mse = (
            nn_sq /
            total
        )

        mm_mse = (
            mm_sq /
            total
        )

        avg_weight = (
            weight_sum /
            total
        )

        crb = calculate_crb(
            snr_db,
            cfg.PREAMBLE_LENGTH
        )

        print(
            f"{snr_db:<7} | "
            f"{fusion_mse:<14.4e} | "
            f"{nn_mse:<14.4e} | "
            f"{mm_mse:<14.4e} | "
            f"{avg_weight:<10.4f} | "
            f"{crb:<14.4e}"
        )


# =====================================================================
# Unified Inference Wrapper
# =====================================================================

class UnifiedHybridCFOEstimator:

    """
    Final estimator.

    IMPORTANT:
        This version only contains Fusion Model A.

    Input:
        received_preamble
        preamble

    Output:
        physical CFO
    """

    def __init__(
        self,
        checkpoint_path=paths.model("unified_hybrid_cfo_model.pth"),
        device=None
    ):

        self.device = (
            device
            if device is not None
            else torch.device(
                "cuda"
                if torch.cuda.is_available()
                else "cpu"
            )
        )

        if not os.path.exists(
            checkpoint_path
        ):

            raise FileNotFoundError(
                f"Checkpoint not found: "
                f"{checkpoint_path}"
            )

        ckpt = torch.load(
            checkpoint_path,
            map_location=self.device,
            weights_only=False
        )

        self.max_lag = (
            ckpt["config"]["max_lag"]
        )

        self.max_cfo = (
            ckpt["config"]["max_cfo"]
        )

        # -------------------------------------------------------------
        # Load Phase-1 expert
        # -------------------------------------------------------------

        self.expert = DenseCFOEstimator(
            self.max_lag,
            4
        ).to(self.device)

        self.expert.load_state_dict(
            ckpt["phase1_state"]
        )

        self.expert.eval()

        # -------------------------------------------------------------
        # Load ONLY Fusion A
        # -------------------------------------------------------------

        self.fusion_model = FusionNetwork(
            in_features=2
        ).to(self.device)

        self.fusion_model.load_state_dict(
            ckpt["phase2_state"]
        )

        self.fusion_model.eval()

    def estimate(
        self,
        received_preamble,
        preamble
    ):

        # -------------------------------------------------------------
        # 1. Exact expert features
        # -------------------------------------------------------------

        lag_summary = extract_lag_summary(
            received_preamble,
            preamble,
            self.max_lag
        )

        # -------------------------------------------------------------
        # 2. Phase-1 expert
        # -------------------------------------------------------------

        with torch.no_grad():

            x_nn = (
                torch
                .from_numpy(lag_summary)
                .float()
                .unsqueeze(0)
                .to(self.device)
            )

            nn_est = (
                self.expert(x_nn)
                .item()
            )

        # -------------------------------------------------------------
        # 3. M&M
        # -------------------------------------------------------------

        mm_est = mm_cfo_estimate(
            received_preamble,
            preamble,
            self.max_lag
        )

        # -------------------------------------------------------------
        # 4. ONLY Model-A features
        # -------------------------------------------------------------

        features = torch.tensor(
            [[
                nn_est,
                mm_est
            ]],
            dtype=torch.float32,
            device=self.device
        )

        nn_t = features[:, 0:1]
        mm_t = features[:, 1:2]

        # -------------------------------------------------------------
        # 5. Fusion
        # -------------------------------------------------------------

        with torch.no_grad():

            estimate, weight = (
                self.fusion_model(
                    features,
                    nn_t,
                    mm_t
                )
            )

        # -------------------------------------------------------------
        # 6. Convert normalized CFO -> physical CFO
        # -------------------------------------------------------------

        physical_cfo = (
            estimate.item() *
            self.max_cfo
        )

        return physical_cfo


# =====================================================================
# Main Experiment
# =====================================================================

def run_experiment():

    set_seed(
        cfg.SEED
    )

    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    print(
        f"Using device: {device}"
    )

    # ================================================================
    # Load Phase-1 Expert
    # ================================================================

    pretrained_path = (
        paths.model("best_cfo_model_crb_L64.pth")
    )

    if not os.path.exists(
        pretrained_path
    ):

        raise FileNotFoundError(
            f"\nPhase-1 expert checkpoint "
            f"not found:\n"
            f"  {pretrained_path}\n\n"
            f"Do NOT create a dummy expert. "
            f"The Hybrid model must use the "
            f"actual pretrained expert."
        )

    print(
        "\n--- Loading Phase-1 Expert ---"
    )

    expert_nn = DenseCFOEstimator(
        cfg.MAX_LAG,
        4
    )

    expert_nn.load_state_dict(
        torch.load(
            pretrained_path,
            map_location="cpu",
            weights_only=True
        )
    )

    expert_nn.eval()

    for p in expert_nn.parameters():
        p.requires_grad = False

    expert_state = {
        k: v.cpu().clone()
        for k, v in
        expert_nn.state_dict().items()
    }

    del expert_nn

    print(
        f"Expert checkpoint: "
        f"{pretrained_path}"
    )

    print(
        f"MAX_LAG: "
        f"{cfg.MAX_LAG}"
    )

    print(
        f"Input shape: "
        f"({cfg.MAX_LAG}, 4)"
    )

    # ================================================================
    # IMPORTANT DIAGNOSTIC
    # ================================================================

    evaluate_expert_per_snr(
        expert_state,
        device
    )

    # ================================================================
    # Generate Curriculum Loaders
    # ================================================================

    print(
        "\n--- Generating Curriculum Data ---"
    )

    curriculum_loaders = []

    for stage_idx, snr_range in enumerate(
        cfg.CURRICULUM_STAGES
    ):

        print(
            f"Stage {stage_idx + 1}: "
            f"{snr_range} dB"
        )

        train_loader = make_loader(
            cfg.NUM_TRAIN,
            expert_state,
            device,
            snr_range=snr_range,
            seed=cfg.SEED + stage_idx,
            shuffle=True
        )

        val_loader = make_loader(
            cfg.NUM_VAL,
            expert_state,
            device,
            snr_range=snr_range,
            seed=cfg.SEED + 1000000 + stage_idx,
            shuffle=False
        )

        curriculum_loaders.append(
            (
                snr_range,
                train_loader,
                val_loader
            )
        )

    # ================================================================
    # Fusion Model A ONLY
    # ================================================================

    print(
        "\n"
        + "=" * 70
    )

    print(
        "TRAINING FUSION MODEL A ONLY"
    )

    print(
        "Input = [NN_estimate, MM_estimate]"
    )

    print(
        "=" * 70
    )

    model = FusionNetwork(
        in_features=2
    ).to(device)

    # ================================================================
    # Curriculum Training
    # ================================================================

    for stage_idx, (
        snr_range,
        train_loader,
        val_loader
    ) in enumerate(
        curriculum_loaders
    ):

        print(
            "\n"
            + "-" * 70
        )

        print(
            f"CURRICULUM STAGE "
            f"{stage_idx + 1}/"
            f"{len(cfg.CURRICULUM_STAGES)}"
        )

        print(
            f"SNR range: "
            f"{snr_range} dB"
        )

        print(
            "-" * 70
        )

        model = train_fusion_model(
            model=model,
            train_loader=train_loader,
            val_loader=val_loader,
            device=device,
            epochs=cfg.EPOCHS
        )

    # ================================================================
    # Final Evaluation
    # ================================================================

    evaluate_fusion_per_snr(
        model,
        expert_state,
        device
    )

    # ================================================================
    # Save Unified Checkpoint
    # ================================================================

    unified_checkpoint = {

        "phase1_state":
            expert_state,

        "phase2_state":
            model.state_dict(),

        "config": {
            "max_lag":
                cfg.MAX_LAG,

            "max_cfo":
                cfg.MAX_CFO,

            "preamble_length":
                cfg.PREAMBLE_LENGTH
        }
    }

    output_path = (
        paths.model("unified_hybrid_cfo_model.pth")
    )

    torch.save(
        unified_checkpoint,
        output_path
    )

    print(
        "\n"
        + "=" * 70
    )

    print(
        "CHECKPOINT SAVED"
    )

    print(
        output_path
    )

    print(
        "=" * 70
    )

    # ================================================================
    # End-to-End Test
    # ================================================================

    print(
        "\n--- Testing End-to-End Inference ---"
    )

    estimator = (
        UnifiedHybridCFOEstimator(
            checkpoint_path=output_path,
            device=device
        )
    )

    # Generate test preamble
    rng = np.random.default_rng(
        cfg.SEED
    )

    dummy_preamble = (
        rng.choice(
            [1, -1],
            cfg.PREAMBLE_LENGTH
        )
        +
        1j *
        rng.choice(
            [1, -1],
            cfg.PREAMBLE_LENGTH
        )
    ) / np.sqrt(2)

    # True normalized CFO = 0.25
    # Physical CFO = 0.25 * MAX_CFO
    true_normalized_cfo = 0.25

    dummy_received = (dummy_preamble *np.exp(1j *2 *np.pi *(true_normalized_cfo *cfg.MAX_CFO) *np.arange(cfg.PREAMBLE_LENGTH)))

    estimated_cfo = estimator.estimate(dummy_received,dummy_preamble)
    true_physical_cfo = (true_normalized_cfo *cfg.MAX_CFO)

    print(f"True CFO: " f"{true_physical_cfo:.6f}")

    print(f"Estimated CFO: "f"{estimated_cfo:.6f}")


# =====================================================================
# Entry Point
# =====================================================================

if __name__ == "__main__":

    torch.set_num_threads(1)

    run_experiment()