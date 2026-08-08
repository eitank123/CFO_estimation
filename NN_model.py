import numpy as np
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
    """
    Generate a random QPSK preamble.

    Returns:
        Complex numpy array of shape (preamble_len,)
    """

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

        C_m = E[z[n] * conj(z[n-m])]

    where:

        z[n] = received[n] * conj(preamble[n])

    For an ideal CFO-only channel:

        angle(C_m) ~= 2*pi*f_CFO*m

    Output shape:
        (max_lag, 3)

    Features:
        0: cos(correlation phase)
        1: sin(correlation phase)
        2: correlation magnitude

    Using sin/cos instead of raw phase avoids the discontinuity
    between +pi and -pi.
    """

    L0 = len(received_preamble)

    # Remove the known QPSK symbols.
    #
    # If:
    #   r[n] = s[n] * exp(j*2*pi*f*n) + w[n]
    #
    # then:
    #   r[n] * conj(s[n])
    #
    # approximately removes the known modulation.
    z = received_preamble * np.conj(preamble)

    lag_features = np.zeros(
        (max_lag, 3),
        dtype=np.float32
    )

    for m in range(1, max_lag + 1):

        c_mean = (
            np.sum(
                z[m:L0]
                * np.conj(z[0:L0 - m])
            )
            / (L0 - m)
        )

        phase = np.angle(c_mean)
        magnitude = np.abs(c_mean)

        # -------------------------------------------------------------
        # Phase represented continuously through sin/cos.
        # -------------------------------------------------------------

        lag_features[m - 1, 0] = np.cos(phase)
        lag_features[m - 1, 1] = np.sin(phase)

        # -------------------------------------------------------------
        # Magnitude contains useful confidence/SNR information.
        #
        # log1p compresses the dynamic range and prevents large
        # correlation values from dominating the network.
        # -------------------------------------------------------------

        lag_features[m - 1, 2] = np.log1p(magnitude)

    return lag_features


# =====================================================================
# 1. Low-SNR ONLY Dataset
# =====================================================================

class LowSnrBiasedCFODataset(Dataset):
    """
    Low-SNR-only training dataset.

    Every training sample is drawn uniformly from -10 dB to 0 dB.

    No high-SNR samples are used during training.

    No SNR weighting is applied.
    """

    def __init__(
        self,
        iterations: int = cfg.ITERATIONS,
        preamble_len: int = cfg.PREAMBLE_LENGTH,
        max_lag: int = 16
    ):
        super().__init__()

        self.iterations = iterations
        self.preamble_len = preamble_len
        self.max_lag = max_lag

        self.n_indices = np.arange(
            preamble_len,
            dtype=np.float64
        )

    def sample_snr(self) -> float:
        """
        Uniform training distribution over low SNR.
        """

        return np.random.uniform(
            -10.0,
            0.0
        )

    def __len__(self):
        return self.iterations

    def __getitem__(self, idx):

        # =============================================================
        # Random CFO
        # =============================================================

        normalized_cfo = np.random.uniform(
            -cfg.MAX_CFO,
            cfg.MAX_CFO
        )

        # =============================================================
        # Random low SNR
        # =============================================================

        snr_db = self.sample_snr()

        # =============================================================
        # Generate QPSK preamble
        # =============================================================

        preamble = generate_qpsk_preamble(
            self.preamble_len
        )

        # =============================================================
        # Apply CFO
        # =============================================================

        cfo_phasor = np.exp(
            1j
            * 2.0
            * np.pi
            * normalized_cfo
            * self.n_indices
        )

        preamble_cfo = (
            preamble
            * cfo_phasor
        )

        # =============================================================
        # AWGN
        # =============================================================

        snr_linear = 10.0 ** (
            snr_db / 10.0
        )

        # QPSK symbols have unit average power.
        #
        # Complex AWGN:
        #
        # E[|n|^2] = 1 / SNR
        #
        # Therefore each real component has variance:
        #
        # 1 / (2*SNR)
        #

        noise_std = np.sqrt(
            1.0
            / (2.0 * snr_linear)
        )

        noise = noise_std * (
            np.random.randn(
                self.preamble_len
            )
            +
            1j * np.random.randn(
                self.preamble_len
            )
        )

        received_preamble = (
            preamble_cfo
            + noise
        )

        # =============================================================
        # Feature extraction
        # =============================================================

        X = extract_lag_summary(
            received_preamble,
            preamble,
            self.max_lag
        )

        # =============================================================
        # Normalized target
        #
        # Target is approximately [-1, 1].
        # =============================================================

        y = (
            normalized_cfo
            / cfg.MAX_CFO
        )

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
    Fixed validation dataset for one particular SNR.

    The dataset is generated once and then reused at every epoch,
    making validation comparisons consistent.
    """

    def __init__(
        self,
        snr_db: float,
        size: int = 1000,
        preamble_len: int = cfg.PREAMBLE_LENGTH,
        max_lag: int = 16
    ):

        self.size = size
        self.data = []

        n_indices = np.arange(
            preamble_len,
            dtype=np.float64
        )

        snr_linear = 10.0 ** (
            snr_db / 10.0
        )

        noise_std = np.sqrt(
            1.0
            / (2.0 * snr_linear)
        )

        for _ in range(size):

            # =========================================================
            # Random CFO
            # =========================================================

            normalized_cfo = np.random.uniform(
                -cfg.MAX_CFO,
                cfg.MAX_CFO
            )

            # =========================================================
            # Random QPSK preamble
            # =========================================================

            preamble = generate_qpsk_preamble(
                preamble_len
            )

            # =========================================================
            # Apply CFO
            # =========================================================

            cfo_phasor = np.exp(
                1j
                * 2.0
                * np.pi
                * normalized_cfo
                * n_indices
            )

            preamble_cfo = (
                preamble
                * cfo_phasor
            )

            # =========================================================
            # AWGN
            # =========================================================

            noise = noise_std * (
                np.random.randn(
                    preamble_len
                )
                +
                1j * np.random.randn(
                    preamble_len
                )
            )

            received = (
                preamble_cfo
                + noise
            )

            # =========================================================
            # Feature extraction
            # =========================================================

            X = extract_lag_summary(
                received,
                preamble,
                max_lag
            )

            # =========================================================
            # Normalized target
            # =========================================================

            y = (
                normalized_cfo
                / cfg.MAX_CFO
            )

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
# 3. Lightweight CFO Estimator
# =====================================================================

class LightweightCFOEstimator(nn.Module):
    """
    Lightweight CNN operating on lag-correlation features.

    Input shape:
        (Batch, Sequence, Channels)

    where:

        Sequence = number of lags
        Channels = 3

    Channels:
        0 = cos(correlation phase)
        1 = sin(correlation phase)
        2 = log correlation magnitude

    Internally the tensor is converted to:

        (Batch, Channels, Sequence)

    before Conv1d processing.
    """

    def __init__(
        self,
        in_channels: int = 3
    ):
        super().__init__()

        # =============================================================
        # Convolutional feature extractor
        #
        # No max-pooling:
        #
        # Lag position is physically meaningful.
        #
        # We therefore preserve the lag resolution.
        # =============================================================

        self.feature_extractor = nn.Sequential(

            # ---------------------------------------------------------
            # Block 1
            # ---------------------------------------------------------

            nn.Conv1d(
                in_channels,
                32,
                kernel_size=3,
                padding=1
            ),

            nn.GELU(),

            # ---------------------------------------------------------
            # Block 2
            # ---------------------------------------------------------

            nn.Conv1d(
                32,
                64,
                kernel_size=3,
                padding=1
            ),

            nn.GELU(),

            # ---------------------------------------------------------
            # Block 3
            # ---------------------------------------------------------

            nn.Conv1d(
                64,
                64,
                kernel_size=3,
                padding=1
            ),

            nn.GELU()
        )

        # =============================================================
        # Preserve some lag-position information.
        #
        # AdaptiveAvgPool1d(4):
        #
        # L=8  -> 4 bins
        # L=16 -> 4 bins
        # L=32 -> 4 bins
        #
        # Unlike global pooling to one value, this does not completely
        # destroy the relationship with lag position.
        # =============================================================

        self.pool = nn.AdaptiveAvgPool1d(4)

        # =============================================================
        # Regression head
        # =============================================================

        self.regressor = nn.Sequential(

            nn.Flatten(),

            nn.Linear(
                64 * 4,
                64
            ),

            nn.GELU(),

            nn.Linear(
                64,
                1
            )
        )

    def forward(self, x):
        """
        Input:
            x shape = (Batch, Sequence, Channels)

        Example:
            (512, 16, 3)

        Convert to:
            (512, 3, 16)
        """

        x = x.permute(
            0,
            2,
            1
        )

        features = self.feature_extractor(x)

        features = self.pool(features)

        cfo_estimate = self.regressor(
            features
        )

        return cfo_estimate


# =====================================================================
# 4. SNR Weighting
# =====================================================================

def snr_weight(snr_db):
    """
    Kept for compatibility with the rest of the project.

    IMPORTANT:
        This experiment does NOT use SNR weighting.

    Every training sample in [-10, 0] dB contributes equally.
    """

    weight = 10.0 ** (
        -snr_db / 20.0
    )

    weight = torch.clamp(
        weight,
        min=0.5,
        max=3.0
    )

    return weight


# =====================================================================
# 5. Training
# =====================================================================

def train_cfo_model(
    train_dataset: LowSnrBiasedCFODataset,
    num_lags_list: list,
    batch_size: int,
    epochs: int,
    lr: float
):

    # =================================================================
    # Device
    # =================================================================

    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    print(
        f"Training device: {device}"
    )

    print(
        "Training SNR range: [-10, 0] dB"
    )

    print(
        "Training distribution: UNIFORM"
    )

    print(
        "SNR weighting: DISABLED"
    )

    print(
        "Loss: MSE"
    )

    print(
        "Features: cos(phase), sin(phase), log(magnitude)"
    )

    # =================================================================
    # DataLoader
    # =================================================================

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=8,
        pin_memory=True,
        persistent_workers=True
    )

    # =================================================================
    # Validation SNRs
    # =================================================================

    val_snrs = [
        -10,
        -8,
        -6,
        -4,
        -2,
        0,
        5,
        10,
        20
    ]

    # =================================================================
    # Maximum lag
    # =================================================================

    max_lag = max(
        num_lags_list
    )

    # =================================================================
    # Validation datasets
    # =================================================================

    val_loaders = {
        snr: DataLoader(
            FixedSNRDataset(
                snr_db=snr,
                size=int(
                    cfg.ITERATIONS
                    * 0.2
                ),
                max_lag=max_lag
            ),
            batch_size=500,
            shuffle=False
        )
        for snr in val_snrs
    }

    # =================================================================
    # Models
    # =================================================================

    models = nn.ModuleDict({
        str(lag): LightweightCFOEstimator(
            in_channels=3
        )
        for lag in num_lags_list
    }).to(device)

    # =================================================================
    # Optimizer
    # =================================================================

    optimizer = optim.AdamW(
        models.parameters(),
        lr=lr,
        weight_decay=1e-4
    )

    # =================================================================
    # Learning-rate scheduler
    # =================================================================

    scheduler = optim.lr_scheduler.CosineAnnealingLR(
        optimizer,
        T_max=epochs,
        eta_min=1e-7
    )

    # =================================================================
    # Loss history
    # =================================================================

    train_loss_history_dict = {
        str(lag): []
        for lag in num_lags_list
    }

    val_loss_history_dict = {
        str(lag): []
        for lag in num_lags_list
    }

    # =================================================================
    # Best validation MSE
    # =================================================================

    best_low_snr_mses = {
        str(lag): float("inf")
        for lag in num_lags_list
    }

    # =================================================================
    # Training loop
    # =================================================================

    for epoch in range(
        1,
        epochs + 1
    ):

        models.train()

        # -------------------------------------------------------------
        # Accumulate individual model losses
        # -------------------------------------------------------------

        epoch_train_loss = {
            str(lag): 0.0
            for lag in num_lags_list
        }

        num_train_batches = 0

        # =============================================================
        # Training batches
        # =============================================================

        for (
            X_batch,
            y_batch,
            snr_batch
        ) in train_loader:

            X_batch = X_batch.to(
                device,
                non_blocking=True
            )

            y_batch = y_batch.to(
                device,
                non_blocking=True
            )

            # ---------------------------------------------------------
            # Clear gradients
            # ---------------------------------------------------------

            optimizer.zero_grad(
                set_to_none=True
            )

            total_loss = 0.0

            # =========================================================
            # Train each lag model
            # =========================================================

            for str_l, model in models.items():

                lag = int(str_l)

                # -----------------------------------------------------
                # X shape:
                #
                #   (Batch, max_lag, 3)
                #
                # Keep only requested lags.
                # -----------------------------------------------------

                X_lag = X_batch[
                    :,
                    :lag,
                    :
                ]

                predictions = model(
                    X_lag
                )

                # -----------------------------------------------------
                # Ordinary MSE
                #
                # This is intentional:
                #
                # The evaluation metric is physical CFO MSE.
                # -----------------------------------------------------

                loss = F.mse_loss(
                    predictions,
                    y_batch
                )

                total_loss = (
                    total_loss
                    + loss
                )

                epoch_train_loss[
                    str_l
                ] += loss.item()

            # ---------------------------------------------------------
            # Backpropagate the combined loss.
            # ---------------------------------------------------------

            total_loss.backward()

            optimizer.step()

            num_train_batches += 1

        # =============================================================
        # Store average training loss
        # =============================================================

        for str_l in train_loss_history_dict:

            avg_train_loss = (
                epoch_train_loss[str_l]
                / num_train_batches
            )

            train_loss_history_dict[
                str_l
            ].append(
                avg_train_loss
            )

        # =============================================================
        # Scheduler
        # =============================================================

        scheduler.step()

        # =============================================================
        # Validation
        # =============================================================

        if (
            epoch % 5 == 0
            or epoch == epochs
        ):

            models.eval()

            print(
                f"\n--- Epoch {epoch}/{epochs} "
                f"Validation (Physical MSE) ---"
            )

            with torch.no_grad():

                for str_l, model in models.items():

                    lag = int(str_l)

                    mse_per_snr = {}

                    low_snr_accum = 0.0

                    # =================================================
                    # Evaluate each SNR separately
                    # =================================================

                    for snr in val_snrs:

                        squared_error = 0.0

                        for (
                            X_val,
                            y_val,
                            _
                        ) in val_loaders[snr]:

                            X_val = X_val.to(
                                device,
                                non_blocking=True
                            )

                            y_val = y_val.to(
                                device,
                                non_blocking=True
                            )

                            X_val_lag = X_val[
                                :,
                                :lag,
                                :
                            ]

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

                        # =================================================
                        # Normalized MSE
                        # =================================================

                        normalized_mse = (
                            squared_error
                            /
                            len(
                                val_loaders[
                                    snr
                                ].dataset
                            )
                        )

                        # =================================================
                        # Convert normalized CFO MSE into physical MSE
                        #
                        # y = f / MAX_CFO
                        #
                        # Therefore:
                        #
                        # MSE_f =
                        # MSE_y * MAX_CFO^2
                        # =================================================

                        physical_mse = (
                            normalized_mse
                            *
                            (
                                cfg.MAX_CFO
                                ** 2
                            )
                        )

                        mse_per_snr[
                            snr
                        ] = physical_mse

                        # -------------------------------------------------
                        # Main metric:
                        # average only over training SNR region
                        # -------------------------------------------------

                        if snr <= 0:

                            low_snr_accum += (
                                physical_mse
                            )

                    # =================================================
                    # Average low-SNR validation MSE
                    # =================================================

                    num_low_snr = sum(
                        1
                        for snr in val_snrs
                        if snr <= 0
                    )

                    avg_low_snr_mse = (
                        low_snr_accum
                        /
                        num_low_snr
                    )

                    # =================================================
                    # Store validation history
                    # =================================================

                    val_loss_history_dict[
                        str_l
                    ].append(
                        avg_low_snr_mse
                    )

                    # =================================================
                    # Save best model
                    # =================================================

                    marker = ""

                    if (
                        avg_low_snr_mse
                        <
                        best_low_snr_mses[
                            str_l
                        ]
                    ):

                        best_low_snr_mses[
                            str_l
                        ] = (
                            avg_low_snr_mse
                        )

                        torch.save(
                            model.state_dict(),
                            f"best_low_snr_L{str_l}.pth"
                        )

                        marker = " [NEW BEST]"

                    # =================================================
                    # Print
                    # =================================================

                    print(
                        f"Lag {str_l:<2} | "
                        f"Avg Low-SNR MSE: "
                        f"{avg_low_snr_mse:.2e}"
                        f"{marker}"
                    )

                    print(
                        f"       | "
                        f"-10dB: "
                        f"{mse_per_snr[-10]:.2e} | "
                        f"-8dB:  "
                        f"{mse_per_snr[-8]:.2e} | "
                        f"-6dB:  "
                        f"{mse_per_snr[-6]:.2e} | "
                        f"-4dB:  "
                        f"{mse_per_snr[-4]:.2e} | "
                        f"-2dB:  "
                        f"{mse_per_snr[-2]:.2e} | "
                        f"0dB:   "
                        f"{mse_per_snr[0]:.2e} | "
                        f"20dB:  "
                        f"{mse_per_snr[20]:.2e}"
                    )

            # =========================================================
            # Current learning rate
            # =========================================================

            current_lr = (
                optimizer.param_groups[0]["lr"]
            )

            print(
                f"       | LR: "
                f"{current_lr:.3e}"
            )

    # =================================================================
    # Save final models
    # =================================================================

    for str_l, model in models.items():

        torch.save(
            model.state_dict(),
            f"last_model_L{str_l}.pth"
        )

    # =================================================================
    # Return
    # =================================================================

    return (
        models,
        train_loss_history_dict,
        val_loss_history_dict
    )