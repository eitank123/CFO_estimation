import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader, TensorDataset
import config as cfg

# =====================================================================
# 0. Signal Helpers and CFO Feature Extraction
# =====================================================================

def generate_qpsk_preamble(preamble_len: int) -> np.ndarray:
    bits = np.random.choice([-1.0, 1.0], size=(preamble_len, 2))
    return (bits[:, 0] + 1j * bits[:, 1]) / np.sqrt(2.0)


def apply_cfo(symbols: np.ndarray, normalized_cfo: float) -> np.ndarray:
    n = np.arange(len(symbols))
    return symbols * np.exp(1j * 2.0 * np.pi * normalized_cfo * n)


def apply_awgn(symbols: np.ndarray, snr_db: float) -> np.ndarray:
    sig_power = np.mean(np.abs(symbols) ** 2)
    snr_linear = 10.0 ** (snr_db / 10.0)
    noise_power = sig_power / snr_linear
    noise_std = np.sqrt(noise_power / 2.0)
    noise = noise_std * (np.random.randn(len(symbols)) + 1j * np.random.randn(len(symbols)))
    return symbols + noise


def sample_training_snr() -> float:
    u = np.random.beta(0.9, 2.0)
    return cfg.MIN_SNR + u * (cfg.MAX_SNR - cfg.MIN_SNR)


def normalize_target(cfo):
    if np.isscalar(cfo):
        return float(cfo) / cfg.MAX_CFO
    cfo_arr = np.asarray(cfo, dtype=np.float32)
    normalized = cfo_arr / cfg.MAX_CFO
    if normalized.size == 1:
        return float(normalized)
    return normalized


def denormalize_target(normalized_cfo: float) -> float:
    return float(normalized_cfo) * cfg.MAX_CFO


def extract_lag_summary(
    received_preamble: np.ndarray,
    reference_preamble: np.ndarray,
    max_lag: int
) -> np.ndarray:
    z = received_preamble * np.conj(reference_preamble)
    lag_features = np.zeros((max_lag, 6), dtype=np.float32)

    for lag_idx, lag in enumerate(range(1, max_lag + 1)):
        c = z[lag:] * np.conj(z[:-lag])
        c_mean = np.mean(c)

        lag_features[lag_idx, 0] = np.real(c_mean)
        lag_features[lag_idx, 1] = np.imag(c_mean)
        lag_features[lag_idx, 2] = np.var(np.real(c), ddof=0)
        lag_features[lag_idx, 3] = np.var(np.imag(c), ddof=0)
        lag_features[lag_idx, 4] = lag / max_lag
        lag_features[lag_idx, 5] = 1.0 / lag

    return lag_features


def preprocess_cfo_preamble(
    received_preamble: np.ndarray,
    reference_preamble: np.ndarray,
    max_lag: int = cfg.NN_MAX_PHASE_DIFFERENCE
) -> torch.Tensor:
    features = extract_lag_summary(received_preamble, reference_preamble, max_lag)
    return torch.from_numpy(features).unsqueeze(0)


def estimate_cfo(model: nn.Module, received_preamble: np.ndarray, reference_preamble: np.ndarray) -> float:
    device = next(model.parameters()).device
    model.eval()
    features = preprocess_cfo_preamble(received_preamble, reference_preamble)
    with torch.no_grad():
        output = model(features.to(device))
    return denormalize_target(output.cpu().item())

# =====================================================================
# 1. Dataset Generation
# =====================================================================

def training_dataset_generator(
    iterations: int = cfg.ITERATIONS,
    preamble_len: int = cfg.PREAMBLE_LENGTH,
    max_lag: int = cfg.NN_MAX_PHASE_DIFFERENCE
):
    X = np.zeros((iterations, max_lag, 6), dtype=np.float32)
    y = np.zeros((iterations, 1), dtype=np.float32)

    for i in range(iterations):
        if i > 0 and i % 10000 == 0:
            print(f"Generating validation data {i}/{iterations}")

        normalized_cfo = np.random.uniform(-cfg.MAX_CFO, cfg.MAX_CFO)
        snr_db = sample_training_snr()
        preamble = generate_qpsk_preamble(preamble_len)
        received_preamble = apply_awgn(apply_cfo(preamble, normalized_cfo), snr_db)

        X[i] = extract_lag_summary(received_preamble, preamble, max_lag)
        y[i, 0] = float(normalized_cfo) / cfg.MAX_CFO

    return torch.from_numpy(X), torch.from_numpy(y)


class OnTheFlyCFODataset(Dataset):
    def __init__(
        self,
        iterations: int = cfg.ITERATIONS,
        preamble_len: int = cfg.PREAMBLE_LENGTH,
        max_lag: int = cfg.NN_MAX_PHASE_DIFFERENCE
    ):
        super().__init__()
        self.iterations = iterations
        self.preamble_len = preamble_len
        self.max_lag = max_lag
        self.n_indices = np.arange(preamble_len)

    def __len__(self):
        return self.iterations

    def __getitem__(self, idx):
        normalized_cfo = np.random.uniform(-cfg.MAX_CFO, cfg.MAX_CFO)
        snr_db = sample_training_snr()
        preamble = generate_qpsk_preamble(self.preamble_len)

        cfo_phasor = np.exp(1j * 2.0 * np.pi * normalized_cfo * self.n_indices)
        preamble_cfo = preamble * cfo_phasor

        snr_linear = 10.0 ** (snr_db / 10.0)
        noise_std = np.sqrt(1.0 / (2.0 * snr_linear))
        noise = noise_std * (np.random.randn(self.preamble_len) + 1j * np.random.randn(self.preamble_len))
        received_preamble = preamble_cfo + noise

        X = extract_lag_summary(received_preamble, preamble, self.max_lag)
        y = float(normalized_cfo) / cfg.MAX_CFO
        return torch.from_numpy(X), torch.tensor([y], dtype=torch.float32)

# =====================================================================
# 2. Neural Network Architecture
# =====================================================================

class ResidualLagBlock(nn.Module):
    def __init__(self, hidden_dim: int):
        super().__init__()
        self.fc1 = nn.Linear(hidden_dim, hidden_dim, bias=False)
        self.ln1 = nn.LayerNorm(hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim, bias=False)
        self.gn2 = nn.GroupNorm(4, hidden_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        residual = x
        x = self.fc1(x)
        x = self.ln1(x)
        x = F.gelu(x)
        x = self.fc2(x)
        x = x.permute(0, 2, 1)
        x = self.gn2(x)
        x = x.permute(0, 2, 1)
        return F.gelu(x + residual)


class LightweightCFOEstimator(nn.Module):
    def __init__(self, max_lag: int, hidden_dim: int = 64):
        super().__init__()
        
        # The input size directly scales with max_lag.
        # This gives the network more parameters to learn from when max_lag is higher.
        input_features = max_lag * 6
        
        self.network = nn.Sequential(
            nn.Flatten(),
            
            # Layer 1: Globally mixes all lag features simultaneously.
            # No pooling bottlenecks. It explicitly maps out the phase trajectory.
            nn.Linear(input_features, hidden_dim),
            nn.GELU(),
            
            # Layer 2: Distills the cross-lag dependencies.
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.GELU(),
            
            # Layer 3: Final CFO Regression.
            nn.Linear(hidden_dim // 2, 1)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x shape entering: (Batch, max_lag, 6)
        # Flatten makes it: (Batch, max_lag * 6)
        return self.network(x)

# =====================================================================
# 3. Training Routine
# =====================================================================

def train_cfo_model(
    train_dataset: Dataset,
    val_dataset: Dataset,
    num_lags: int,
    batch_size: int,
    epochs: int,
    lr: float,
    save_path: str
):
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=8,
        pin_memory=torch.cuda.is_available()
    )
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Training on device: {device}")

    model = LightweightCFOEstimator(max_lag=num_lags).to(device)
    criterion = nn.MSELoss()
    optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=5e-7)

    best_val_loss = float('inf')
    train_loss_history = []
    val_loss_history = []

    for epoch in range(1, epochs + 1):
        model.train()
        running_train_loss = 0.0

        for X_batch, y_batch in train_loader:
            X_batch = X_batch.to(device)
            y_batch = y_batch.to(device)

            optimizer.zero_grad()
            predictions = model(X_batch)
            loss = criterion(predictions, y_batch)
            loss.backward()
            optimizer.step()

            running_train_loss += loss.item() * X_batch.size(0)

        train_loss = running_train_loss / len(train_loader.dataset)

        model.eval()
        running_val_loss = 0.0
    
        with torch.no_grad():
            for X_batch, y_batch in val_loader:
                X_batch = X_batch.to(device)
                y_batch = y_batch.to(device)
                predictions = model(X_batch)
                loss = criterion(predictions, y_batch)
                running_val_loss += loss.item() * X_batch.size(0)

        val_loss = running_val_loss / len(val_loader.dataset)
        train_loss_history.append(train_loss / cfg.BATCH_SIZE)
        val_loss_history.append(val_loss / cfg.BATCH_SIZE)

        scheduler.step()

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(model.state_dict(), save_path)
            saved_flag = "*"
        else:
            saved_flag = ""

        if epoch % 5 == 0 or epoch == 1:
            physical_train_mse = train_loss * (cfg.MAX_CFO ** 2)
            physical_val_mse = val_loss * (cfg.MAX_CFO ** 2)
            physical_best_mse = best_val_loss * (cfg.MAX_CFO ** 2)
            current_lr = optimizer.param_groups[0]['lr']
            print(
                f"Epoch [{epoch:02d}/{epochs:02d}] | "
                f"Train MSE: {physical_train_mse:.5e} | "
                f"Val MSE: {physical_val_mse:.5e} | "
                f"Best MSE: {physical_best_mse:.5e} | "
                f"LR: {current_lr:.1e} {saved_flag}"
            )

    print(f"\nTraining complete. Best model saved to '{save_path}' with Val MSE: {best_val_loss * (cfg.MAX_CFO ** 2):.5e}")
    return model, train_loss_history, val_loss_history

# =====================================================================
# 4. Training Wrapper
# =====================================================================

def train_model(
    preamble_len: int = cfg.PREAMBLE_LENGTH,
    num_lags: int = cfg.NN_MAX_PHASE_DIFFERENCE,
    batch_size: int = cfg.BATCH_SIZE,
    epochs: int = cfg.EPOCHS,
    lr: float = cfg.lr
):
    train_samples = int(cfg.ITERATIONS * 0.8)
    val_samples = max(1, cfg.ITERATIONS - train_samples)

    train_dataset = OnTheFlyCFODataset(
        iterations=train_samples,
        preamble_len=preamble_len,
        max_lag=num_lags
    )

    X_val, y_val = training_dataset_generator(
        iterations=val_samples,
        preamble_len=preamble_len,
        max_lag=num_lags
    )
    val_dataset = TensorDataset(X_val, y_val)

    trained_model, train_loss_history, val_loss_history = train_cfo_model(
        train_dataset=train_dataset,
        val_dataset=val_dataset,
        num_lags=num_lags,
        batch_size=batch_size,
        epochs=epochs,
        lr=lr,
        save_path=cfg.NN_SAVE_PATH
    )

    return trained_model, train_loss_history, val_loss_history
