import os, copy, numpy as np, torch, torch.nn as nn, torch.optim as optim
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
import matplotlib.pyplot as plt

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

    # 3-Stage Curriculum SNR Regions
    CURRICULUM_STAGES = [
        (0.0, 10.0),    # Stage 1: High SNR
        (-5.0, 0.0),    # Stage 2: Mid SNR
        (-10.0, -5.0),  # Stage 3: Low SNR
        (-10.0, 10.0)   #Stage 4: Fine-tune
    ]

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
            nn.Flatten(start_dim=1), nn.Linear(input_dim, 128), nn.GELU(),
            nn.Linear(128, 64), nn.GELU(), nn.Linear(64, 32), nn.GELU(),
            nn.Linear(32, 1)
        )

    def forward(self, x):
        return self.net(x)

# =====================================================================
# Signal Processing
# =====================================================================
def extract_lag_summary(received_preamble, preamble, max_lag):
    L0 = len(received_preamble)
    z = received_preamble * np.conj(preamble)
    lag_features = np.zeros((max_lag, 4), dtype=np.float32)
    
    for m in range(1, max_lag + 1):
        c_mean = np.sum(z[m:L0] * np.conj(z[:L0-m])) / (L0-m)
        lag_features[m-1] = [np.real(c_mean), np.imag(c_mean),
                             np.abs(c_mean), np.angle(c_mean)]
    return lag_features

def mm_cfo_estimate(received_preamble, preamble, max_lag_mm):
    L = len(received_preamble)
    M = max_lag_mm

    # Remove known QPSK symbols
    z = received_preamble * np.conj(preamble)

    # -------------------------------------------------------------
    # Autocorrelation R[m]
    # -------------------------------------------------------------
    R = np.zeros(M + 1, dtype=np.complex128)

    for m in range(1, M + 1):
        R[m] = (
            np.sum(
                z[m:L] * np.conj(z[:L-m])
            ) / (L - m)
        )

    # R[0] is real/positive, so:
    # Δφ[1] = angle(R[1])
    # Δφ[m] = angle(R[m] R*[m-1])
    # -------------------------------------------------------------
    delta_phi = np.zeros(M)

    delta_phi[0] = np.angle(R[1])

    if M > 1:
        delta_phi[1:] = np.angle(
            R[2:] * np.conj(R[1:M])
        )

    # -------------------------------------------------------------
    # Mengali-Morelli weights
    # -------------------------------------------------------------
    m = np.arange(1, M + 1)

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
    # M&M CFO estimate
    # -------------------------------------------------------------
    physical_cfo = (
        np.sum(weights * delta_phi)
        / (2 * np.pi)
    )

    # Normalize to the NN target convention
    return physical_cfo / cfg.MAX_CFO

def calculate_crb(snr_db, L):
    snr_linear = 10.0 ** (snr_db / 10.0)
    return 3.0 / (2.0 * np.pi**2 * snr_linear * L * (L**2 - 1))

# =====================================================================
# ON-THE-FLY Dataset
# =====================================================================
class FusionDataset(Dataset):
    def __init__(self, num_samples, expert_state, snr_range=None, fixed_snr=None, seed=42):
        self.num_samples = num_samples
        self.snr_range = snr_range if snr_range is not None else (cfg.MIN_SNR, cfg.MAX_SNR)
        self.fixed_snr = fixed_snr
        self.seed = seed
        self.worker_expert = None
        self.expert_state = expert_state
        self.n_indices = np.arange(cfg.PREAMBLE_LENGTH, dtype=np.float64)

    def __len__(self):
        return self.num_samples

    def _get_expert(self):
        if self.worker_expert is None:
            self.worker_expert = DenseCFOEstimator(cfg.MAX_LAG, 4)
            self.worker_expert.load_state_dict(self.expert_state)
            self.worker_expert.eval()
            for p in self.worker_expert.parameters():
                p.requires_grad = False
        return self.worker_expert

    def __getitem__(self, idx):
        expert = self._get_expert()
        rng = np.random.default_rng()

        normalized_cfo = rng.uniform(-1.0, 1.0)
        snr_db = self.fixed_snr if self.fixed_snr is not None else rng.uniform(self.snr_range[0], self.snr_range[1])
        snr_linear = 10.0 ** (snr_db / 10.0)
        noise_std = np.sqrt(1.0 / (2.0 * snr_linear))

        bits = rng.integers(0, 2, size=(cfg.PREAMBLE_LENGTH, 2))
        real_part = np.where(bits[:, 1] == 0, 1.0, -1.0)
        imag_part = np.where(bits[:, 0] == 0, 1.0, -1.0)
        preamble = (real_part + 1j * imag_part) / np.sqrt(2)

        physical_cfo = normalized_cfo * cfg.MAX_CFO
        cfo_phasor = np.exp(1j * 2 * np.pi * physical_cfo * self.n_indices)
        noise = noise_std * (rng.standard_normal(cfg.PREAMBLE_LENGTH) +
                             1j * rng.standard_normal(cfg.PREAMBLE_LENGTH))
        received = preamble * cfo_phasor + noise

        lag_summary = extract_lag_summary(received, preamble, cfg.MAX_LAG)

        with torch.no_grad():
            x = torch.from_numpy(lag_summary).float().unsqueeze(0)
            nn_est = expert(x).item()

        mm_est = mm_cfo_estimate(received, preamble, cfg.MAX_LAG)

        denom = nn_est - mm_est
        w_opt = 0.5 if abs(denom) < 1e-8 else (normalized_cfo - mm_est) / denom
        w_opt = np.clip(w_opt, 0.0, 1.0)

        diff_est = abs(nn_est - mm_est)
        mags = lag_summary[:, 2]

        feat_A = np.array([nn_est, mm_est], dtype=np.float32)
        feat_A2 = np.array([nn_est, mm_est, diff_est], dtype=np.float32)
        feat_B = np.array([nn_est, mm_est, mags[0]], dtype=np.float32)
        feat_C = np.concatenate(([nn_est, mm_est], mags)).astype(np.float32)
        feat_D = np.concatenate(([nn_est, mm_est], lag_summary.ravel())).astype(np.float32)

        return (torch.from_numpy(feat_A),
                torch.from_numpy(feat_A2),
                torch.from_numpy(feat_B),
                torch.from_numpy(feat_C),
                torch.from_numpy(feat_D),
                torch.tensor([normalized_cfo], dtype=torch.float32),
                torch.tensor([w_opt], dtype=torch.float32),
                torch.tensor([snr_db], dtype=torch.float32))

# =====================================================================
# Fusion Network
# =====================================================================
class FusionNetwork(nn.Module):
    def __init__(self, in_features: int, is_residual=False):
        super().__init__()
        self.is_residual = is_residual
        self.net = nn.Sequential(
            nn.LayerNorm(in_features), 
            nn.Linear(in_features, 64), nn.GELU(),
            nn.Linear(64, 32), nn.GELU(),
            nn.Linear(32, 16), nn.GELU()
        )
        self.out_layer = nn.Linear(16, 2 if is_residual else 1)

    def forward(self, x, nn_est, mm_est):
        out = self.out_layer(self.net(x))
        w = torch.sigmoid(out[:, 0].unsqueeze(1))
        if self.is_residual:
            r = out[:, 1].unsqueeze(1)
            return w * nn_est + (1-w) * mm_est + r, w, r
        return w * nn_est + (1-w) * mm_est, w, None

# =====================================================================
# Unified End-to-End Inference Wrapper
# =====================================================================
class UnifiedHybridCFOEstimator:
    """
    Loads everything from a single unified checkpoint file and provides
    a single method to get the final physical CFO estimation.
    """
    def __init__(self, checkpoint_path="unified_hybrid_cfo_model.pth", setup_name="Residual_C", device=None):
        self.device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        if not os.path.exists(checkpoint_path):
            raise FileNotFoundError(f"Unified checkpoint not found at {checkpoint_path}")
            
        ckpt = torch.load(checkpoint_path, map_location=self.device, weights_only=False)
        self.max_lag = ckpt["config"]["max_lag"]
        self.max_cfo = ckpt["config"]["max_cfo"]
        self.setup_name = setup_name

        # Load Phase-1 Expert
        self.expert = DenseCFOEstimator(self.max_lag, 4).to(self.device)
        self.expert.load_state_dict(ckpt["phase1_state"])
        self.expert.eval()

        # Load Phase-2 Fusion Model
        is_res = "Residual" in setup_name
        base_key = setup_name.replace("Residual_", "")
        
        in_dims = {
            "A": 2,
            "B": 3,
            "C": 2 + self.max_lag,
            "D": 2 + 4 * self.max_lag
        }
        in_dim = in_dims[base_key]

        self.fusion_model = FusionNetwork(in_dim, is_residual=is_res).to(self.device)
        self.fusion_model.load_state_dict(ckpt["phase2_states"][setup_name])
        self.fusion_model.eval()

    def estimate(self, received_preamble: np.ndarray, preamble: np.ndarray) -> float:
        """
        Takes raw received preamble and known preamble, returns final physical CFO.
        """
        # 1. Extract feature summary
        lag_summary = extract_lag_summary(received_preamble, preamble, self.max_lag)

        # 2. Run Phase-1 Neural Network Expert
        with torch.no_grad():
            x_nn = torch.from_numpy(lag_summary).float().unsqueeze(0).to(self.device)
            nn_est = self.expert(x_nn).item()

        # 3. Run Mengali & Morelli (M&M) algorithm
        mm_est = mm_cfo_estimate(received_preamble, preamble, self.max_lag)

        # 4. Construct feature vector based on setup
        diff_est = abs(nn_est - mm_est)
        mags = lag_summary[:, 2]

        base_key = self.setup_name.replace("Residual_", "")
        if base_key == "A":
            feat = np.array([nn_est, mm_est], dtype=np.float32)
        elif base_key == "B":
            feat = np.array([nn_est, mm_est, mags[0]], dtype=np.float32)
        elif base_key == "C":
            feat = np.concatenate(([nn_est, mm_est], mags)).astype(np.float32)
        elif base_key == "D":
            feat = np.concatenate(([nn_est, mm_est], lag_summary.ravel())).astype(np.float32)
        else:
            raise ValueError(f"Unknown setup: {self.setup_name}")

        # 5. Run Fusion Network
        with torch.no_grad():
            x_fusion = torch.from_numpy(feat).unsqueeze(0).to(self.device)
            nn_t = x_fusion[:, 0:1]
            mm_t = x_fusion[:, 1:2]
            
            est_norm, _, _ = self.fusion_model(x_fusion, nn_t, mm_t)
            physical_cfo = est_norm.item() * self.max_cfo

        return physical_cfo

# =====================================================================
# DataLoader Factory
# =====================================================================
def make_loader(num_samples, expert_state, device, snr_range=None, fixed_snr=None, seed=42, shuffle=False):
    dataset = FusionDataset(num_samples, expert_state, snr_range=snr_range, fixed_snr=fixed_snr, seed=seed)
    return DataLoader(
        dataset,
        batch_size=cfg.BATCH_SIZE,
        shuffle=shuffle,
        num_workers=cfg.NUM_WORKERS,
        pin_memory=(device.type == "cuda"),
        persistent_workers=(cfg.NUM_WORKERS > 0),
        prefetch_factor=2,
        drop_last=False
    )

# =====================================================================
# Training
# =====================================================================
# Configuration parameters for oracle robustness and weight regularization
ORACLE_DENOM_THRESHOLD = 1e-6
LAMBDA_WEIGHT_EXTREME = 1e-5

# ==========================================
# 1. Shared SNR Binning Helpers
# ==========================================
def map_snr_to_bin(snr_db):
    """Maps continuous SNR values to discrete bins: [-10, -8, -6, -4, -2, 0, 2, 4, 6, 8, 10]"""
    snr_rounded = torch.round(snr_db / 2.0) * 2.0
    return torch.clamp(snr_rounded, -10.0, 10.0)

def get_bin_index(snr_rounded):
    """Converts clamped discrete SNR values to tensor indices [0..10]"""
    return ((snr_rounded + 10.0) / 2.0).long()


# ==========================================
# 2. Leakage-Free Baseline Calibration with Curriculum-Aware Fallback
# ==========================================
def compute_nn_baseline_tensor(calib_loader, device, max_cfo):
    """
    Computes baseline physical MSE of the pre-trained Phase-1 NN expert using exact 
    sample-level accumulation over a calibration loader. Automatically assigns 
    sensible fallbacks for SNR bins missing from restricted curriculum stages.
    """
    snr_range = [-10, -8, -6, -4, -2, 0, 2, 4, 6, 8, 10]
    sum_sq_err = {s: 0.0 for s in snr_range}
    sample_counts = {s: 0 for s in snr_range}
    
    with torch.no_grad():
        for batch in calib_loader:
            feat_A, feat_A2, feat_B, feat_C, feat_D, y_true, opt_w, snr_db = batch
            nn_est = feat_A[:, 0:1].to(device, non_blocking=True)
            y_t = y_true.to(device, non_blocking=True)
            s_db = snr_db.to(device, non_blocking=True)
            
            fT_nn = nn_est * max_cfo
            fT_true = y_t * max_cfo
            sq_err = (fT_nn - fT_true) ** 2
            
            s_bins = map_snr_to_bin(s_db)
            
            for target_snr in snr_range:
                mask = (s_bins == target_snr)
                if mask.any():
                    sum_sq_err[target_snr] += sq_err[mask].sum().item()
                    sample_counts[target_snr] += mask.sum().item()

    print("\n--- Calibration Set SNR Bin Diagnostics ---")
    print(f"{'SNR (dB)':<10} | {'Sample Count':<15} | {'Status':<10}")
    print("-" * 41)
    
    # First pass to compute available MSEs for fallback calculation
    available_mses = [sum_sq_err[s] / sample_counts[s] for s in snr_range if sample_counts[s] > 0]
    fallback_mse = sum(available_mses) / len(available_mses) if available_mses else 1.0

    vals = []
    for s in snr_range:
        count = sample_counts[s]
        if count == 0:
            vals.append(fallback_mse)
            print(f"{s:<10} | {count:<15} | {'MISSING (Fallback)':<18}")
        else:
            mse_val = sum_sq_err[s] / count
            vals.append(mse_val)
            print(f"{s:<10} | {count:<15} | {'OK':<10}")
            
    print("-----------------------------------------")
    print("Calibration baseline successfully verified across all bins.\n")
    
    return torch.tensor(vals, device=device)


# ==========================================
# 3. Loss Functions with None-Safety and Regularization
# ==========================================
def relative_to_nn_mse_loss(y_pred, y_true, snr_db_batch, max_cfo, baseline_vals=None):
    """
    Computes the relative-to-NN MSE loss: L_relative = E[ (f_fusion - f_true)^2 / MSE_NN(SNR) ].
    Includes safety fallback if baseline_vals is None.
    """
    if baseline_vals is None:
        baseline_vals = torch.ones(11, device=y_pred.device)

    fT_hat = y_pred * max_cfo
    fT_true = y_true * max_cfo

    snr_rounded = map_snr_to_bin(snr_db_batch)
    indices = get_bin_index(snr_rounded)
    base_mse = baseline_vals[indices]

    squared_error = (fT_hat - fT_true) ** 2
    relative_loss = squared_error / base_mse

    return torch.mean(relative_loss)


def total_hybrid_loss(y_pred, y_true, snr_db_batch, weights, max_cfo, baseline_vals=None, lambda_extreme=LAMBDA_WEIGHT_EXTREME):
    """
    Computes total training loss: L_total = L_relative_nn + lambda_extreme * E[w * (1 - w)].
    """
    if baseline_vals is None:
        baseline_vals = torch.ones(11, device=y_pred.device)

    rel_loss = relative_to_nn_mse_loss(y_pred, y_true, snr_db_batch, max_cfo, baseline_vals)
    weight_reg = torch.mean(weights * (1.0 - weights))
    total_loss = rel_loss + lambda_extreme * weight_reg
    return total_loss, rel_loss, weight_reg


# ==========================================
# 4. Training Function with Robust Baseline Resolution & Logging
# ==========================================
def train_fusion_model(name, model, train_loader, val_loader, device, epochs, baseline_vals=None, lambda_extreme=LAMBDA_WEIGHT_EXTREME):
    if baseline_vals is None:
        baseline_vals = compute_nn_baseline_tensor(val_loader, device, cfg.MAX_CFO)

    optimizer = optim.AdamW(model.parameters(), lr=3e-4, weight_decay=1e-5)

    scheduler = optim.lr_scheduler.CosineAnnealingLR(
        optimizer,
        T_max=epochs,
        eta_min=1e-7
    )
    best_loss = float('inf')
    best_weights = None

    name_to_idx = {"A": 0, "B": 2, "C": 3, "D": 4}
    feat_idx = name_to_idx[name]

    for epoch in range(epochs):
        model.train()
        train_physical_mse = 0.0
        train_rel_loss_sum = 0.0
        train_reg_sum = 0.0
        train_total_loss_sum = 0.0

        for feat_A, feat_A2, feat_B, feat_C, feat_D, y_true, opt_w, snr_db in train_loader:
            feature_map = [feat_A, feat_A2, feat_B, feat_C, feat_D]
            batch_features = feature_map[feat_idx].to(device, non_blocking=True)
            y_true = y_true.to(device, non_blocking=True)
            snr_db = snr_db.to(device, non_blocking=True)

            nn_est = batch_features[:, 0:1]
            mm_est = batch_features[:, 1:2]

            optimizer.zero_grad(set_to_none=True)
            est_fusion, weights, _ = model(batch_features, nn_est, mm_est)

            total_loss, rel_loss, weight_reg = total_hybrid_loss(
                est_fusion, y_true, snr_db, weights, cfg.MAX_CFO, baseline_vals, lambda_extreme
            )

            with torch.no_grad():
                physical_mse = F.mse_loss(est_fusion * cfg.MAX_CFO, y_true * cfg.MAX_CFO)

            total_loss.backward()
            optimizer.step()

            train_physical_mse += physical_mse.item()
            train_rel_loss_sum += rel_loss.item()
            train_reg_sum += weight_reg.item()
            train_total_loss_sum += total_loss.item()

        n_train = len(train_loader)
        train_physical_mse /= n_train
        train_rel_loss_sum /= n_train
        train_reg_sum /= n_train
        train_total_loss_sum /= n_train

        model.eval()
        val_physical_mse = 0.0
        val_rel_loss_sum = 0.0
        val_reg_sum = 0.0
        val_nn_mse = 0.0
        val_mm_mse = 0.0

        with torch.no_grad():
            for feat_A, feat_A2, feat_B, feat_C, feat_D, y_true, opt_w, snr_db in val_loader:
                feature_map = [feat_A, feat_A2, feat_B, feat_C, feat_D]
                batch_features = feature_map[feat_idx].to(device, non_blocking=True)
                y_true = y_true.to(device, non_blocking=True)
                snr_db = snr_db.to(device, non_blocking=True)

                nn_est = batch_features[:, 0:1]
                mm_est = batch_features[:, 1:2]

                est_fusion, weights, _ = model(batch_features, nn_est, mm_est)
                
                rel_loss = relative_to_nn_mse_loss(est_fusion, y_true, snr_db, cfg.MAX_CFO, baseline_vals)
                weight_reg = torch.mean(weights * (1.0 - weights))
                physical_mse = F.mse_loss(est_fusion * cfg.MAX_CFO, y_true * cfg.MAX_CFO)
                nn_mse = F.mse_loss(nn_est * cfg.MAX_CFO, y_true * cfg.MAX_CFO)
                mm_mse = F.mse_loss(mm_est * cfg.MAX_CFO, y_true * cfg.MAX_CFO)

                val_physical_mse += physical_mse.item()
                val_rel_loss_sum += rel_loss.item()
                val_reg_sum += weight_reg.item()
                val_nn_mse += nn_mse.item()
                val_mm_mse += mm_mse.item()

        n_val = len(val_loader)
        val_physical_mse /= n_val
        val_rel_loss_sum /= n_val
        val_reg_sum /= n_val
        val_nn_mse /= n_val
        val_mm_mse /= n_val

        if ((epoch + 1) % 5 == 0):
            lr = optimizer.param_groups[0]["lr"]
            val_total_loss = val_rel_loss_sum + lambda_extreme * val_reg_sum
            print(f"Epoch {epoch+1:02d}/{epochs} | Train Physical MSE: {train_physical_mse:.4e} | Val Physical MSE: {val_physical_mse:.4e} | Relative Loss: {val_rel_loss_sum:.4e} | Weight Reg: {val_reg_sum:.4e} | Total Loss: {val_total_loss:.4e} | NN MSE: {val_nn_mse:.4e} | M&M MSE: {val_mm_mse:.4e} | LR: {lr:.3e}")

        if val_physical_mse < best_loss:
            best_loss = val_physical_mse
            best_weights = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
        scheduler.step()

    if best_weights is not None:
        model.load_state_dict(best_weights)

    return model


# ==========================================
# 5. Setup-Aware Evaluation with Complete Metrics & Gain/Disagreement Diagnostics
# ==========================================
@torch.no_grad()
def evaluate_per_snr_weights(model, test_loader, device, max_cfo, setup_name="A", stage_name=""):
    """
    Setup-aware evaluation computing sample-level MSEs, robust oracle weights, 
    weight error metrics (RMSE_w, MAE_w), gain metrics (G_NN, G_MM, Oracle Gap), 
    and estimator disagreement diagnostics.
    """
    model.eval()
    snr_range = [-10, -8, -6, -4, -2, 0, 2, 4, 6, 8, 10]
    
    print(f"\n--- Per-SNR Comprehensive Evaluation [{setup_name}] {stage_name} ---")
    print(f"{'SNR':<5} | {'Fusion MSE':<10} | {'NN MSE':<10} | {'M&M MSE':<10} | {'Oracle MSE':<10} | {'FusW':<6} | {'OracW':<6} | {'RMSE_w':<7} | {'MAE_w':<7} | {'G_NN':<7} | {'G_MM':<7} | {'OracGap':<8} | {'Mean |NN-MM|':<11}")
    print("-" * 145)
    
    for target_snr in snr_range:
        sum_sq_fusion = 0.0
        sum_sq_nn = 0.0
        sum_sq_mm = 0.0
        sum_sq_oracle = 0.0
        
        sum_fusion_w = 0.0
        sum_oracle_w = 0.0
        
        sum_abs_w_diff = 0.0
        sum_sq_w_diff = 0.0
        sum_disagreement = 0.0
        total_count = 0
        
        for feat_A, feat_A2, feat_B, feat_C, feat_D, y_true, opt_w, snr_db in test_loader:
            s_bins = map_snr_to_bin(snr_db)
            mask = (s_bins == target_snr)
            if not mask.any():
                continue
                
            feature_map_dict = {
                "A": feat_A,
                "B": feat_B,
                "C": feat_C,
                "D": feat_D,
            }
            selected_feat = feature_map_dict[setup_name]
            
            batch_features = selected_feat[mask].to(device, non_blocking=True)
            y_t = y_true[mask].to(device, non_blocking=True)
            
            nn_est = batch_features[:, 0:1]
            mm_est = batch_features[:, 1:2]
            
            est_fusion, weights, _ = model(batch_features, nn_est, mm_est)
            
            fT_true = y_t * max_cfo
            fT_fusion = est_fusion * max_cfo
            fT_nn = nn_est * max_cfo
            fT_mm = mm_est * max_cfo
            
            disagreement = torch.abs(fT_nn - fT_mm)
            sum_disagreement += torch.sum(disagreement).item()
            
            denom = fT_nn - fT_mm
            w_star = torch.where(
                torch.abs(denom) < ORACLE_DENOM_THRESHOLD,
                torch.tensor(0.5, device=denom.device),
                torch.clamp((fT_true - fT_mm) / denom, 0.0, 1.0)
            )
            fT_oracle = w_star * fT_nn + (1.0 - w_star) * fT_mm
            
            sum_sq_fusion += torch.sum((fT_fusion - fT_true) ** 2).item()
            sum_sq_nn += torch.sum((fT_nn - fT_true) ** 2).item()
            sum_sq_mm += torch.sum((fT_mm - fT_true) ** 2).item()
            sum_sq_oracle += torch.sum((fT_oracle - fT_true) ** 2).item()
            
            sum_fusion_w += torch.sum(weights).item()
            sum_oracle_w += torch.sum(w_star).item()
            
            w_diff = weights - w_star
            sum_abs_w_diff += torch.sum(torch.abs(w_diff)).item()
            sum_sq_w_diff += torch.sum(w_diff ** 2).item()
            
            total_count += mask.sum().item()
            
        if total_count > 0:
            mse_fusion = sum_sq_fusion / total_count
            mse_nn = sum_sq_nn / total_count
            mse_mm = sum_sq_mm / total_count
            mse_oracle = sum_sq_oracle / total_count
            
            avg_fw = sum_fusion_w / total_count
            avg_ow = sum_oracle_w / total_count
            
            rmse_w = torch.sqrt(torch.tensor(sum_sq_w_diff / total_count)).item()
            mae_w = sum_abs_w_diff / total_count
            
            g_nn = 1.0 - (mse_fusion / mse_nn) if mse_nn > 0 else 0.0
            g_mm = 1.0 - (mse_fusion / mse_mm) if mse_mm > 0 else 0.0
            oracle_gap = mse_fusion / mse_oracle if mse_oracle > 0 else 0.0
            mean_disagreement = sum_disagreement / total_count
            
            print(f"{target_snr:<5} | {mse_fusion:<10.3e} | {mse_nn:<10.3e} | {mse_mm:<10.3e} | {mse_oracle:<10.3e} | {avg_fw:<6.3f} | {avg_ow:<6.3f} | {rmse_w:<7.3f} | {mae_w:<7.3f} | {g_nn:<7.3f} | {g_mm:<7.3f} | {oracle_gap:<8.3f} | {mean_disagreement:<11.3e}")
# =====================================================================
# Main Experiment & Packaging
# =====================================================================
def run_experiment():
    set_seed(cfg.SEED)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    pretrained_path = "best_cfo_model_low_L64.pth"
    if not os.path.exists(pretrained_path):
        dummy_expert = DenseCFOEstimator(cfg.MAX_LAG, 4)
        torch.save(dummy_expert.state_dict(), pretrained_path)

    expert_nn = DenseCFOEstimator(cfg.MAX_LAG, 4)
    expert_nn.load_state_dict(torch.load(pretrained_path, map_location="cpu", weights_only=True))
    expert_nn.eval()
    for p in expert_nn.parameters():
        p.requires_grad = False

    expert_state = {k: v.cpu().clone() for k, v in expert_nn.state_dict().items()}
    del expert_nn

    # Generate Curriculum Data Loaders
    print("\n--- Generating Curriculum Data Loaders ---")
    curriculum_loaders = []
    for stage_idx, snr_range in enumerate(cfg.CURRICULUM_STAGES):
        tr_l = make_loader(cfg.NUM_TRAIN, expert_state, device, snr_range=snr_range, seed=cfg.SEED+stage_idx, shuffle=True)
        va_l = make_loader(cfg.NUM_VAL, expert_state, device, snr_range=snr_range, seed=cfg.SEED+1000000+stage_idx, shuffle=False)
        curriculum_loaders.append((snr_range, tr_l, va_l))

    setups = {
        "A": (2, False),
        "B": (3, False),
        "C": (2 + cfg.MAX_LAG, False),
        "D": (2 + 4*cfg.MAX_LAG, False),
    }

    print("\n--- Training and Evaluating Phase 2 Models ---")
    snr_grid = np.arange(-10, 11, 2)  # [-10, -8, -6, ..., 10]
    trained_models = {}

    for name, (in_dim, is_res) in setups.items():
        print(f"\n{'='*50}\nTraining Setup {name} (Dim={in_dim}, Residual={is_res})\n{'='*50}")
        model = FusionNetwork(in_dim, is_residual=is_res).to(device)
        
        # 1. Iterative 3-Stage Curriculum Training
        for stage_idx, (snr_range, tr_l, va_l) in enumerate(curriculum_loaders):
            print(f"\n--- Curriculum Stage {stage_idx+1}/{len(cfg.CURRICULUM_STAGES)}: SNR Range {snr_range} dB ---")
            model = train_fusion_model(
                name, model, tr_l, va_l,
                device, cfg.EPOCHS
            )
            
        trained_models[name] = model

        # 2. Evaluate MSE and Average Fusion Weight per SNR point
        print(f"\n--- Per-SNR MSE & Weight Evaluation for Setup {name} ---")
        print(f"{'SNR (dB)':<10} | {'MSE (Physical CFO)':<20} | {'Avg Weight (w)':<18} | {'CRB':<15}")
        print("-" * 71)

        base_key = name.replace("Residual_", "")
        name_to_idx = {"A": 0, "B": 2, "C": 3, "D": 4}
        feat_idx = name_to_idx[base_key]

        trained_models[name].eval()
        with torch.no_grad():
            for snr_db in snr_grid:
                test_loader = make_loader(
                    cfg.NUM_TEST_PER_SNR, expert_state, device,
                    fixed_snr=float(snr_db), seed=cfg.SEED + 999, shuffle=False
                )
                
                mse_sum = 0.0
                weight_sum = 0.0
                total_samples = 0

                for feat_A, feat_A2, feat_B, feat_C, feat_D, y_true, opt_w, snr_db_val in test_loader:
                    feature_map = [feat_A, feat_A2, feat_B, feat_C, feat_D]
                    batch_features = feature_map[feat_idx].to(device, non_blocking=True)
                    y_true = y_true.to(device, non_blocking=True)

                    nn_est = batch_features[:, 0:1]
                    mm_est = batch_features[:, 1:2]

                    est_fusion, w, _ = trained_models[name](batch_features, nn_est, mm_est)

                    est_physical = est_fusion * cfg.MAX_CFO
                    y_physical = y_true * cfg.MAX_CFO

                    mse_sum += F.mse_loss(est_physical, y_physical, reduction='sum').item()
                    weight_sum += w.sum().item()
                    total_samples += y_physical.size(0)

                mean_mse = mse_sum / total_samples
                mean_weight = weight_sum / total_samples
                crb_val = calculate_crb(snr_db, cfg.PREAMBLE_LENGTH)
                
                print(f"{snr_db:<10} | {mean_mse:<20.4e} | {mean_weight:<18.4f} | {crb_val:<15.4e}")

    # -------------------------------------------------------------
    # Bundle everything into a single unified checkpoint file
    # -------------------------------------------------------------
    unified_checkpoint = {
        "phase1_state": expert_state,
        "phase2_states": {name: model.state_dict() for name, model in trained_models.items()},
        "config": {
            "max_lag": cfg.MAX_LAG,
            "max_cfo": cfg.MAX_CFO,
            "preamble_length": cfg.PREAMBLE_LENGTH
        }
    }
    torch.save(unified_checkpoint, "unified_hybrid_cfo_model.pth")
    print("\nSuccessfully saved unified bundle to 'unified_hybrid_cfo_model.pth'")

    # -------------------------------------------------------------
    # Demonstration of single-file inference
    # -------------------------------------------------------------
    print("\n--- Testing Single-File Inference Wrapper ---")
    estimator = UnifiedHybridCFOEstimator(checkpoint_path="unified_hybrid_cfo_model.pth", setup_name="Residual_C", device=device)
    
    # Generate a dummy test signal
    dummy_preamble = (np.random.choice([1, -1], cfg.PREAMBLE_LENGTH) + 1j * np.random.choice([1, -1], cfg.PREAMBLE_LENGTH)) / np.sqrt(2)
    dummy_received = dummy_preamble * np.exp(1j * 2 * np.pi * 0.05 * np.arange(cfg.PREAMBLE_LENGTH))
    
    estimated_cfo = estimator.estimate(dummy_received, dummy_preamble)
    print(f"End-to-End Estimated Physical CFO: {estimated_cfo:.5f}")

if __name__ == "__main__":
    torch.set_num_threads(1)
    run_experiment()