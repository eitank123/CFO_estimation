import config as cfg
import numpy as np
from plots import plot_mse, plot_cfo_sweep, plot_loss_curves
from NN_model import LightweightCFOEstimator, train_model, extract_lag_summary
import torch

#np.random.seed(10)

def add_frequency_offset(self, signal, freq_offset, sample_rate=8):
    if freq_offset == 0:
        return signal
    t = np.arange(len(signal)) / sample_rate
    return signal * np.exp(1j * 2 * np.pi * freq_offset * t)


def smoothing_function(correlation_lag, max_lag, window_size):
    """
    Vectorized smoothing function.

    Parameters
    ----------
    correlation_lag : int or array_like
        Correlation lag(s) m.
    max_lag : int
        Maximum correlation lag N.
    window_size : int
        Preamble length L0.

    Returns
    -------
    ndarray
        Weights w(m) for each lag.
    """
    m = np.asarray(correlation_lag, dtype=float)
    N = float(max_lag)
    L0 = float(window_size)

    numerator = 3 * ((L0 - m) * (L0 - m + 1) - N * (L0 - N))
    denominator = N * (4 * N**2 - 6 * N * L0 + 3 * L0**2 - 1)

    return numerator / denominator

def mengali_moreli_frequency_estimator(R, T=1.0, w=None):
    """
    Implements Eq. (8) from:
    Mengali & Morelli,
    'Data-Aided Frequency Estimation for Burst Digital Transmission'

    Parameters
    ----------
    R : array_like (complex)
        Correlation vector R(m), m = 0,...,M-1.
    T : float
        Symbol period (seconds).

    Returns
    -------
    f_hat : float
        Estimated frequency offset (Hz).

    fT_hat : float
        Estimated normalized frequency offset (f*T).
    """
    R = np.asarray(R)

    # Principal phase of each correlation
    theta = np.angle(R)

    # Phase increments
    dtheta = theta[1:] - theta[:-1]

    # Wrap to [-pi, pi]
    dtheta = (dtheta + np.pi) % (2*np.pi) - np.pi

    # Eq. (8)
    fT_hat = np.sum(w * dtheta) / (2 * np.pi)

    # Convert to Hz
    f_hat = fT_hat / T

    return f_hat, fT_hat


def map_bits(bit_array):
    return [cfg.BIT_MAPPING_QPSK[b] for b in bit_array]

def generate_bit_array():
    bit_array = [tuple(np.random.randint(0, 2, 2)) for _ in range(cfg.PREAMBLE_LENGTH)]
    return map_bits(bit_array)


def apply_cfo(symbols, normalized_cfo):
    """
    Applies Carrier Frequency Offset to complex symbols.
    
    :param symbols: 1D numpy array of complex symbols
    :param normalized_cfo: CFO normalized by symbol rate (f_offset / f_symbol)
    :return: CFO-impaired complex symbols
    """
    n = np.arange(len(symbols))
    cfo_phasor = np.exp(1j * 2 * np.pi * normalized_cfo * n)
    return symbols * cfo_phasor

def apply_awgn(symbols, snr_db):
    """
    Applies Additive White Gaussian Noise to complex symbols.
    
    :param symbols: 1D numpy array of complex symbols
    :param snr_db: Signal-to-Noise Ratio in dB
    :return: Noisy complex symbols
    """
    # Calculate signal power: P_sig = E[|x|^2]
    sig_power = np.mean(np.abs(symbols) ** 2)

    # Convert SNR from dB to linear scale
    snr_linear = 10 ** (snr_db / 10.0)

    # Calculate noise variance per dimension (Real and Imaginary share total variance)
    noise_power = sig_power / snr_linear
    noise_std = np.sqrt(noise_power / 2.0)
    
    # Generate complex Gaussian noise (Zero-mean, unit variance split between I and Q)
    noise = noise_std * (np.random.randn(len(symbols)) + 1j * np.random.randn(len(symbols)))
    
    return symbols + noise

def compute_cfo_crlb(snr_db_range, preamble_length):
    """
    Computes the Cramér-Rao Lower Bound (CRLB) for normalized Carrier Frequency Offset (CFO).
    
    :param snr_db_range: Array or list of SNR values in dB.
    :param preamble_length: Number of preamble symbols (N).
    :return: Array of lower bound variances (in normalized frequency squared: (f_off/f_s)^2).
    """
    snr_db = np.array(snr_db_range, dtype=np.float64)
    N = preamble_length
    
    # Convert SNR from dB to linear scale (E_s / N_0)
    snr_linear = 10.0 ** (snr_db / 10.0)
    
    # Calculate CRLB variance for normalized CFO
    crlb_variance = 6.0 / ((2.0 * np.pi) ** 2 * snr_linear * N * (N ** 2 - 1))
    
    return crlb_variance

def compute_R_vector(z, N):
    """
    Computes a vector of autocorrelation values R(m) for lags m = 1 to N.
    
    Formula: R(m) = 1 / (L_0 - m) * sum_{k=m}^{L_0 - 1} z(k) * z*(k - m)
    
    :param z: 1D numpy array of phase-removed symbols z(k) (length L_0)
    :param N: Maximum lag index (1 <= N <= len(z)//2)
    :return: 1D numpy array of complex R(m) values of length N
             (where index 0 corresponds to m=1, index N-1 to m=N)
    """
    L_0 = len(z)
    
    if N > L_0//2 or N < 1:
        raise ValueError("N must satisfy 1 <= N <= len(z)//2")

    R_vector = np.zeros(N+1, dtype=np.complex128)
    for m in range(0, N+1):
        # Element-wise product of z[m : L_0] and conjugate of z[0 : L_0 - m]
        sum_val = np.sum(z[m:L_0] * np.conj(z[0:L_0 - m]))
        R_vector[m] = sum_val / (L_0 - m)
    return R_vector

def snr_sweep(normalized_cfo, preamble, weights):
    errors_vs_max_lag = []  # Initialize error list for each max_lag
    for i, lag in enumerate(cfg.MAX_LAG):
        errors = []  # Initialize error list for each SNR
        w = weights[i]
        for snr_db in cfg.SNR:
            # 3. Apply channel impairments (CFO is applied first in the transmission channel, then AWGN)
            preamble_cfo = apply_cfo(preamble, normalized_cfo)
            received_preamble = apply_awgn(preamble_cfo, snr_db)

            # Remove phase modulation due to CFO (for correlation)
            z = received_preamble * np.conj(preamble)
        
            # 4. Estimate CFO using Mengali & Morelli method
            R = compute_R_vector(z, lag)
            f_hat, fT_hat = mengali_moreli_frequency_estimator(R=R, w=w)
        
            # 5. Calculate estimation error
            error = np.abs(fT_hat - (normalized_cfo * 1.0))  # Assuming symbol rate T=1 for simplicity
            errors.append(error ** 2)  # Accumulate squared error for MSE calculation
        errors_vs_max_lag.append(errors)
    return errors_vs_max_lag

def CFO_sweep(preamble, weights):
    """
    Performs a sweep over the SNR range to evaluate the CFO estimation performance.

    :param normalized_cfo: Normalized CFO value (f_offset / f_symbol)
    :param preamble: 1D numpy array of complex preamble symbols
    :param weights: List of weights for the estimator (from smoothing function)
    :return: List of lists containing squared errors for each SNR
    """
    
    results_vs_lag = []
    for i, lag in enumerate(cfg.MAX_LAG):
        results = []  # Initialize list for each CFO
        w = weights[i]
        for cfo in cfg.CFO:
            # Apply channel impairments (CFO and AWGN)
            preamble_cfo = apply_cfo(preamble, cfo)
            received_preamble = apply_awgn(preamble_cfo, cfg.TARGET_SNR)

            # Remove phase modulation due to CFO (for correlation)
            z = received_preamble * np.conj(preamble)
        
            # Estimate CFO using Mengali & Morelli method
            
            R = compute_R_vector(z, lag)
            f_hat, fT_hat = mengali_moreli_frequency_estimator(R=R, w=w)
        
            # Calculate estimation error
            result = fT_hat  # Assuming symbol rate T=1 for simplicity
            results.append(result)  # Accumulate squared error for MSE calculation
        results_vs_lag.append(results)
    
    return results_vs_lag

def snr_sweep_nn(normalized_cfo, preamble, model):
    errors_vs_max_lag = []

    model.eval()
    device = next(model.parameters()).device
    max_lag = cfg.NN_MAX_PHASE_DIFFERENCE

    with torch.no_grad():
        base_errors = []

        for snr_db in cfg.SNR:
            preamble_cfo = apply_cfo(preamble, normalized_cfo)
            received_preamble = apply_awgn(preamble_cfo, snr_db)

            features = extract_lag_summary(received_preamble, preamble, max_lag)
            tensor_in = torch.from_numpy(features.astype(np.float32)).unsqueeze(0).to(device)

            fT_hat = model(tensor_in).item()
            fT_hat *= cfg.MAX_CFO
            error = np.abs(fT_hat - normalized_cfo)
            base_errors.append(error ** 2)

        for _ in cfg.MAX_LAG:
            errors_vs_max_lag.append(base_errors.copy())

    return errors_vs_max_lag

if __name__ == "__main__":
    snr_sweep_error_sum = [[0 for i in range(len(cfg.SNR))] for _ in range(len(cfg.MAX_LAG))]  # Initialize error sum for each SNR
    cfo_sweep_error_sum = [[0 for i in range(len(cfg.CFO))] for _ in range(len(cfg.MAX_LAG))]  # Initialize error sum for each CFO
    nn_snr_sweep_error_sum = [[0 for i in range(len(cfg.SNR))] for _ in range(len(cfg.MAX_LAG))]  # Initialize error sum for NN SNR sweep
    training_dataset = []
    weights = []

    for lag in cfg.MAX_LAG:
        m = np.arange(1, lag + 1)
        w = smoothing_function(correlation_lag=m, max_lag=lag, window_size=cfg.PREAMBLE_LENGTH)
        weights.append(w)
    if not cfg.TRAIN_NN:
        for iter in range(cfg.ITERATIONS):
            if iter % 100 == 0:
                print(f"Iteration {iter}/{cfg.ITERATIONS}")
            # 1. Generate QPSK preamble (convert list to numpy array of complex numbers)
            raw_preamble = generate_bit_array()

            preamble = np.array(raw_preamble, dtype=np.complex128)

            # 2. Define channel impairment parameters

            if cfg.SNR_SWEEP:
                errors_vs_max_lag = snr_sweep(cfg.NORMALIZED_CFO, preamble, weights)  # Run the SNR sweep and plot results
                snr_sweep_error_sum = [[snr_sweep_error_sum[i][j] + errors_vs_max_lag[i][j] for j in range(len(cfg.SNR))] for i in range(len(cfg.MAX_LAG))]  # Accumulate errors across iterations

            if cfg.CFO_SWEEP:
                results = CFO_sweep(preamble, weights)  # Run the CFO sweep and plot results
                cfo_sweep_error_sum = [[cfo_sweep_error_sum[i][j] + results[i][j] for j in range(len(cfg.CFO))] for i in range(len(cfg.MAX_LAG))]  # Accumulate errors across iterations

            if cfg.EVALUATE_NN:
                # 1. Instantiate the model architecture
                model = LightweightCFOEstimator(max_lag=cfg.NN_MAX_PHASE_DIFFERENCE)

                # 2. Load the saved weights into the model
                save_path = cfg.NN_SAVE_PATH  # Replace with your actual path/filename if different
                model.load_state_dict(torch.load(save_path))

                # 3. Set the model to evaluation mode
                model.eval()
                nn_errors_vs_max_lag = snr_sweep_nn(cfg.NORMALIZED_CFO, preamble, model)  # Run the NN SNR sweep
                nn_snr_sweep_error_sum = [[nn_snr_sweep_error_sum[i][j] + nn_errors_vs_max_lag[i][j] for j in range(len(cfg.SNR))] for i in range(len(cfg.MAX_LAG))]  # Accumulate errors across iterations

    else:
        model, train_loss_history, val_loss_history = train_model()
        plot_loss_curves(train_loss_history, val_loss_history, title="Training & Validation Loss (MAX_PHASE_DIFFERENCE = {})".format(cfg.NN_MAX_PHASE_DIFFERENCE))
        
    CRB = compute_cfo_crlb(cfg.SNR, cfg.PREAMBLE_LENGTH)

    if cfg.SNR_SWEEP:
        # Calculate MSE for each SNR
        mse_results = [[snr_sweep_error_sum[i][j] / cfg.ITERATIONS for j in range(len(cfg.SNR))] for i in range(len(cfg.MAX_LAG))]
        plot_mse(mse_results, CRB)  # Plot MSE vs SNR

    if cfg.CFO_SWEEP:
        # Calculate MSE for each CFO
        cfo_mean_results = [[cfo_sweep_error_sum[i][j] / cfg.ITERATIONS for j in range(len(cfg.CFO))] for i in range(len(cfg.MAX_LAG))]
        plot_cfo_sweep(cfo_results=cfo_mean_results)  # Plot MSE vs CFO

    if cfg.EVALUATE_NN:
        # Calculate MSE for each SNR using the trained NN
        nn_mse_results = mse_results+[[nn_snr_sweep_error_sum[i][j] / cfg.ITERATIONS for j in range(len(cfg.SNR))] for i in range(len(cfg.MAX_LAG))]
        plot_mse(nn_mse_results, CRB)  # Plot MSE vs SNR for NN


    

