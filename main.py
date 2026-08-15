import config as cfg
import numpy as np
from plots import plot_mse, plot_cfo_sweep, plot_loss_curves, plot_mse_comparison
from NN_model import DenseCFOEstimator, train_cfo_model, extract_lag_summary
import torch
import channel
from Hybrid import UnifiedHybridCFOEstimator

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
    if cfg.IS_BPSK:
        return [1 if b == 1 else -1 for b in bit_array]
    return [cfg.BIT_MAPPING_QPSK[b] for b in bit_array]

def generate_bit_array():
    if cfg.IS_BPSK:
        bit_array = [int(np.random.randint(0, 2)) for _ in range(cfg.PREAMBLE_LENGTH)]
    else:
        bit_array = [tuple(np.random.randint(0, 2, 2)) for _ in range(cfg.PREAMBLE_LENGTH)]
    return map_bits(bit_array)

def apply_cfo(signal, normalized_cfo):
    n = np.arange(len(signal))
    return signal * np.exp(
        1j * 2*np.pi*normalized_cfo*n/cfg.SPS
    )

def apply_awgn(signal, snr_db, sps=cfg.SPS):
    """
    Applies AWGN using symbol SNR (Es/N0).

    Parameters
    ----------
    signal : 1D numpy array of complex samples
        Upsampled and pulse-shaped signal.
    snr_db : float
        Symbol SNR in dB (Es/N0).
    sps : int
        Samples per symbol.

    Returns
    -------
    noisy_signal : complex numpy array
        Signal with AWGN added.
    """

    snr_linear = 10 ** (snr_db / 10)

    # Average power per sample after upsampling/filtering
    sig_power = np.mean(np.abs(signal)**2)

    # Convert Es/N0 to sample-domain noise power:
    # Es = sig_power * sps
    # N0 = Es / (Es/N0)
    noise_power = sig_power * sps / snr_linear

    # Complex Gaussian noise: half power in I and half in Q
    noise_std = np.sqrt(noise_power / 2)

    noise = noise_std * (
        np.random.randn(len(signal)) +
        1j * np.random.randn(len(signal))
    )

    return signal + noise

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

def downsample(signal):
    return signal[::cfg.SPS]

def remove_filter_delay(signal):
    delay = cfg.FILTER_SPAN*cfg.SPS
    return signal[delay: delay + cfg.PREAMBLE_LENGTH*cfg.SPS]


# -------------------------------------------------------------------
# Helper to cleanly apply Channel Impairments and Rx Filter for all sweeps
# -------------------------------------------------------------------
def process_through_channel(transmitted_preamble, cfo, snr_db, rx_filter):
    # 1. Apply CFO
    preamble_cfo = apply_cfo(transmitted_preamble, cfo)
    # 2. Apply AWGN
    received_preamble = apply_awgn(preamble_cfo, snr_db)
    # 3. Rx RRC Filter
    received_preamble = np.convolve(received_preamble, rx_filter, mode='full')
    # 4. Remove filter delay
    received_preamble = remove_filter_delay(received_preamble)
    # 5. Downsample back to symbol rate
    return downsample(received_preamble)


def snr_sweep(normalized_cfo, transmitted_preamble, preamble, weights):
    errors_vs_max_lag = []
    rx_filter = channel.rrc_design(cfg.BETA, cfg.SPS, cfg.FILTER_SPAN)
    
    for i, lag in enumerate(cfg.MAX_LAG):
        errors = []
        w = weights[i]
        for snr_db in cfg.SNR:
            received_preamble = process_through_channel(transmitted_preamble, normalized_cfo, snr_db, rx_filter)
            
            # Remove phase modulation due to CFO (for correlation)
            z = received_preamble * np.conj(preamble)
        
            # Estimate CFO using Mengali & Morelli method
            R = compute_R_vector(z, lag)
            _, fT_hat = mengali_moreli_frequency_estimator(R=R, w=w)
        
            # Calculate estimation error
            error = np.abs(fT_hat - (normalized_cfo * 1.0))
            errors.append(error ** 2) 
        errors_vs_max_lag.append(errors)
        
    return errors_vs_max_lag

def CFO_sweep(transmitted_preamble, preamble, weights, snr_db=None):
    results_vs_lag = []
    rx_filter = channel.rrc_design(cfg.BETA, cfg.SPS, cfg.FILTER_SPAN)
    snr_db = cfg.TARGET_SNR if snr_db is None else snr_db
    
    for i, lag in enumerate(cfg.MAX_LAG):
        results = []
        w = weights[i]
        for cfo in cfg.CFO:
            received_preamble = process_through_channel(transmitted_preamble, cfo, snr_db, rx_filter)

            # Remove phase modulation due to CFO (for correlation)
            z = received_preamble * np.conj(preamble)
        
            # Estimate CFO using Mengali & Morelli method
            R = compute_R_vector(z, lag)
            _, fT_hat = mengali_moreli_frequency_estimator(R=R, w=w)
        
            results.append(fT_hat)
        results_vs_lag.append(results)
    
    return results_vs_lag

def snr_sweep_hybrid(normalized_cfo, transmitted_preamble, preamble, estimator):
    rx_filter = channel.rrc_design(cfg.BETA, cfg.SPS, cfg.FILTER_SPAN)
    base_errors = []

    for snr_db in cfg.SNR:
        received_preamble = process_through_channel(transmitted_preamble, normalized_cfo, snr_db, rx_filter)

        # Use the unified estimator to get the final hybrid CFO estimation
        fT_hat = estimator.estimate(received_preamble, preamble)
        
        error = np.abs(fT_hat - normalized_cfo)
        base_errors.append(error ** 2)

    return base_errors

def cfo_sweep_hybrid(transmitted_preamble, preamble, estimator, snr_db=None):
    rx_filter = channel.rrc_design(cfg.BETA, cfg.SPS, cfg.FILTER_SPAN)
    snr_db = cfg.TARGET_SNR if snr_db is None else snr_db

    results = []

    for normalized_cfo in cfg.CFO:
        received_preamble = process_through_channel(transmitted_preamble, normalized_cfo, snr_db, rx_filter)

        # Use the unified estimator to get the final physical CFO directly
        fT_hat = estimator.estimate(received_preamble, preamble)

        results.append(fT_hat)

    return results

def snr_sweep_nn(normalized_cfo, transmitted_preamble, preamble, model, max_lag):
    model.eval()
    device = next(model.parameters()).device
    rx_filter = channel.rrc_design(cfg.BETA, cfg.SPS, cfg.FILTER_SPAN)

    with torch.no_grad():
        base_errors = []

        for snr_db in cfg.SNR:
            received_preamble = process_through_channel(transmitted_preamble, normalized_cfo, snr_db, rx_filter)

            features = extract_lag_summary(received_preamble, preamble, max_lag)
            tensor_in = torch.from_numpy(features.astype(np.float32)).unsqueeze(0).to(device)

            fT_hat = model(tensor_in).item()
            fT_hat *= cfg.MAX_CFO
            
            error = np.abs(fT_hat - normalized_cfo)
            base_errors.append(error ** 2)

    return base_errors

def cfo_sweep_nn(transmitted_preamble, preamble, model, max_lag, snr_db=None):
    model.eval()
    device = next(model.parameters()).device
    rx_filter = channel.rrc_design(cfg.BETA, cfg.SPS, cfg.FILTER_SPAN)
    snr_db = cfg.TARGET_SNR if snr_db is None else snr_db

    with torch.no_grad():
        results = []

        for normalized_cfo in cfg.CFO:
            received_preamble = process_through_channel(transmitted_preamble, normalized_cfo, snr_db, rx_filter)

            features = extract_lag_summary(received_preamble, preamble, max_lag)
            tensor_in = torch.from_numpy(features.astype(np.float32)).unsqueeze(0).to(device)

            fT_hat = model(tensor_in).item()
            fT_hat *= cfg.MAX_CFO

            results.append(fT_hat)

    return results

def upscale_array(signal, sps):
    # This function is retained for fallback, but the main chain now upsamples 
    # the unified preamble + payload sequence directly in MAIN.
    upsampled = np.zeros(len(signal) * sps, dtype=complex)
    upsampled[::sps] = signal
    return upsampled


if __name__ == "__main__":
    snr_sweep_error_sum = [[0 for i in range(len(cfg.SNR))] for _ in range(len(cfg.MAX_LAG))]  # Initialize error sum for each SNR
    cfo_sweep_error_sum = [[0 for i in range(len(cfg.CFO))] for _ in range(len(cfg.MAX_LAG))]  # Initialize error sum for each CFO
    nn_snr_sweep_error_sum = [[0 for _ in range(len(cfg.SNR))] for _ in range(len(cfg.NN_models)+1)]
    nn_cfo_sweep_sum = [[0 for _ in range(len(cfg.CFO))] for _ in range(len(cfg.NN_models))]
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
                
            # 1. Generate QPSK preamble
            raw_preamble = generate_bit_array()
            preamble = np.array(raw_preamble, dtype=np.complex128)
            
            # 2. Tx Upsample & RRC Filter
            transmitted_preamble = upscale_array(preamble, cfg.SPS)
            transmitted_preamble = np.convolve(transmitted_preamble, channel.rrc_design(cfg.BETA, cfg.SPS, cfg.FILTER_SPAN), mode='full')

            # --- RUN SWEEPS ---

            if cfg.SNR_SWEEP:
                random_cfo = np.random.uniform(-cfg.MAX_CFO, cfg.MAX_CFO)
                errors_vs_max_lag = snr_sweep(random_cfo, transmitted_preamble, preamble, weights)
                snr_sweep_error_sum = [[snr_sweep_error_sum[i][j] + errors_vs_max_lag[i][j] for j in range(len(cfg.SNR))] for i in range(len(cfg.MAX_LAG))] 

            if cfg.CFO_SWEEP:
                random_snr = np.random.uniform(cfg.MIN_SNR, cfg.MAX_SNR)
                results = CFO_sweep(transmitted_preamble, preamble, weights, random_snr)
                cfo_sweep_error_sum = [[cfo_sweep_error_sum[i][j] + results[i][j] for j in range(len(cfg.CFO))] for i in range(len(cfg.MAX_LAG))] 

            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

            if cfg.EVALUATE_NN:
                for i, save_path in enumerate(cfg.NN_models):
                    max_lag = cfg.MAX_PHASES[i]

                    # 1. Load the unified estimator wrapper
                    estimator = UnifiedHybridCFOEstimator(
                        checkpoint_path="unified_hybrid_cfo_model.pth", 
                        setup_name="A"
                    )

                    random_cfo = np.random.uniform(-cfg.MAX_CFO, cfg.MAX_CFO)

                    # 2. Run the SNR sweep using the hybrid estimator
                    nn_errors_vs_max_lag = snr_sweep_hybrid(random_cfo, transmitted_preamble, preamble, estimator)  

                    nn_snr_sweep_error_sum[i] = [
                        nn_snr_sweep_error_sum[i][k] + nn_errors_vs_max_lag[k] 
                        for k in range(len(cfg.SNR))
                    ]
                    
                    model = DenseCFOEstimator(max_lag=max_lag)
                    model.load_state_dict(torch.load(save_path, map_location=device))
                    model.eval()
                    
                    nn_errors_vs_max_lag = snr_sweep_nn(random_cfo, transmitted_preamble, preamble, model, max_lag) 
                    
                    nn_snr_sweep_error_sum[i+1] = [
                        nn_snr_sweep_error_sum[i+1][k] + nn_errors_vs_max_lag[k] 
                        for k in range(len(cfg.SNR))
                    ]
                    
            if cfg.EVALUATE_NN_CFO:
                for i, save_path in enumerate(cfg.NN_models):
                    max_lag = cfg.MAX_PHASES[i]

                    # 1. Load the unified estimator wrapper
                    estimator = UnifiedHybridCFOEstimator(
                        checkpoint_path="unified_hybrid_cfo_model.pth", 
                        setup_name="A"
                    )

                    random_snr = np.random.uniform(cfg.MIN_SNR, cfg.MAX_SNR)

                    # 2. Run the CFO sweep using the hybrid estimator wrapper
                    nn_results_vs_cfo = cfo_sweep_hybrid(transmitted_preamble, preamble, estimator, random_snr)

                    nn_cfo_sweep_sum[i] = [
                        nn_cfo_sweep_sum[i][k] + nn_results_vs_cfo[k]
                        for k in range(len(cfg.CFO))
                    ]

    else:
        model, train_loss_history, val_loss_history = train_cfo_model(
            num_lags_list = cfg.MAX_PHASES,
            batch_size = cfg.BATCH_SIZE,
            base_epochs = cfg.EPOCHS,
            lr = cfg.LEARNING_RATE
        )
        plot_loss_curves(train_loss_history, val_loss_history, title="Training & Validation Loss (MAX_PHASE_DIFFERENCE = {})".format(cfg.NN_MAX_PHASE_DIFFERENCE))
        
    CRB = compute_cfo_crlb(cfg.SNR, cfg.PREAMBLE_LENGTH)

    if cfg.SNR_SWEEP:
        mse_results = [[snr_sweep_error_sum[i][j] / cfg.ITERATIONS for j in range(len(cfg.SNR))] for i in range(len(cfg.MAX_LAG))]
        plot_mse(mse_results, CRB)

    if cfg.CFO_SWEEP:
        cfo_mean_results = [[cfo_sweep_error_sum[i][j] / cfg.ITERATIONS for j in range(len(cfg.CFO))] for i in range(len(cfg.MAX_LAG))]
        plot_cfo_sweep(cfo_results=cfo_mean_results)

    if cfg.EVALUATE_NN:
        nn_mse = [
            [nn_snr_sweep_error_sum[j][k] / cfg.ITERATIONS for k in range(len(cfg.SNR))] 
            for j in range(len(cfg.NN_models)+1)
        ]
        nn_mse_results = mse_results + nn_mse
        plot_mse(nn_mse_results, CRB)
        target_snr_index = cfg.SNR.index(cfg.TARGET_SNR)
        plot_mse_comparison(
            nn_mse,
            mse_results,
            snr_values=cfg.HISTOGRAM_TARGET_SNR
        )
        
    if cfg.EVALUATE_NN_CFO:
        nn_results = [
            [nn_cfo_sweep_sum[j][k] / cfg.ITERATIONS
             for k in range(len(cfg.CFO))]
            for j in range(len(cfg.NN_models)+1)
        ]
        nn_results = cfo_mean_results + nn_results
        plot_cfo_sweep(nn_results)