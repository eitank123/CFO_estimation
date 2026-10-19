import matplotlib.pyplot as plt
import paths
import config as cfg
import numpy as np

def plot_mse(mse_results, crb_results):
    """
    Plots MSE of CFO estimation for different lags alongside the Cramér-Rao Bound (CRB) vs SNR.

    :param mse_results: 2D array-like (shape: [num_lags, num_snr]), where each row 
                        corresponds to the MSE array across SNR values for a specific lag.
    :param crb_results: 1D array-like of theoretical CRB variance values across SNR.
    :param lags: Optional list or array of lag values (N) corresponding to each row in mse_results.
    """
    plt.figure(figsize=(10, 6))
    
    # Define a set of markers/colors for distinct visual styling per lag
    markers = ['o', 's', '^', 'd', 'v', 'p', '*', 'x']
    colors = plt.cm.viridis(np.linspace(0, 0.85, len(mse_results)))
    counter = 0
    # Plot empirical MSE for each lag N
    for i, mse_row in enumerate(mse_results):
        try:
            lag_label = f'Estimator MSE (N={cfg.MAX_LAG[i]})'
        except IndexError:
            if counter == 0:
                lag_label = f'Hybrid NN estimator'
                counter += 1
            else:
                lag_label = f'Pure NN model'
        marker = markers[i % len(markers)]
        
        plt.semilogy(
            cfg.SNR, 
            mse_row, 
            marker=marker, 
            linestyle='-', 
            color=colors[i], 
            label=lag_label
        )
    
    # Plot theoretical CRB
    plt.semilogy(
        cfg.SNR, 
        crb_results, 
        marker='None', 
        linestyle='--', 
        linewidth=2, 
        color='r', 
        label='CRB'
    )
    
    plt.title(f'CFO Estimation Performance vs. Cramér-Rao Bound (beta = {cfg.BETA})')
    plt.xlabel('SNR (dB)')
    plt.ylabel('Normalized CFO Variance / MSE')
    plt.grid(True, which='both', linestyle=':', alpha=0.6)
    plt.legend()
    plt.tight_layout()
    
    plt.savefig(paths.plot("mse.png"), dpi=300, bbox_inches="tight")
    plt.close()

def plot_cfo_sweep(cfo_results, true_cfo_values=cfg.CFO):
    """
    Plots estimated CFO vs. True Normalized CFO across different configurations/lags, 
    alongside the ideal reference line (f_hat = f_true).

    :param cfo_results: 2D or 1D array-like containing estimated CFO values. 
                        If 2D (shape: [num_lags, num_cfo]), plots a curve per lag.
    :param true_cfo_values: 1D array-like of true normalized CFO values (X-axis).
    """
    plt.figure(figsize=(10, 6))

    # Convert to 2D numpy array to handle both 1D and 2D inputs seamlessly
    results_matrix = np.atleast_2d(cfo_results)

    # Define a set of markers/colors for distinct visual styling per lag
    markers = ['o', 's', '^', 'd', 'v', 'p', '*', 'x']
    colors = plt.cm.viridis(np.linspace(0, 0.85, len(results_matrix)))
    counter = 0
    # Plot estimated CFO for each lag N (or single curve if 1D)
    for i, cfo_row in enumerate(results_matrix):
        try:
            label = f'M&M estimate (N={cfg.MAX_LAG[i]})'
        except IndexError:
            if counter == 0:
                label = f'Hybrid NN estimator'
                counter += 1
            else:
                label = f'Pure NN model'

        marker = markers[i % len(markers)]

        plt.plot(
            true_cfo_values,
            cfo_row,
            marker=marker,
            linestyle='-',
            color=colors[i],
            label=label
        )

    # Plot Ideal Reference Line (f_hat = f_true)
    plt.plot(
        true_cfo_values,
        true_cfo_values,
        linestyle='--',
        linewidth=2,
        color='k',
        label='Ideal (f_hat = f_true)'
    )

    # main.py draws a new SNR ~ U[MIN_SNR, MAX_SNR] for every iteration of the CFO sweep
    plt.title('Mean CFO estimate vs. normalized CFO (SNR ~ U[{}, {}] dB)'.format(cfg.MIN_SNR, cfg.MAX_SNR))
    plt.xlabel('Normalized CFO (f_off / f_s)')
    plt.ylabel('Estimated Normalized CFO (f_hat)')
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.legend()
    plt.tight_layout()
    
    plt.savefig(paths.plot("cfo_performance.png"), dpi=300, bbox_inches="tight")
    plt.close()

def plot_loss_curves(train_loss: list, val_loss: list, title: str = "Training & Validation Loss"):
    """
    Plots training and validation loss curves across epochs.
    
    Parameters:
        train_loss (list): Recorded training loss values per epoch.
        val_loss (list): Recorded validation loss values per epoch.
        title (str): Plot title.
    """
    epochs = range(1, len(train_loss) + 1)
    
    plt.figure(figsize=(10, 6), dpi=100)
    
    # Plot curves
    plt.plot(epochs, train_loss, label='Train Loss', color='#1f77b4', linewidth=2)
    plt.plot(epochs, val_loss, label='Validation Loss', color='#ff7f0e', linewidth=2, linestyle='--')
    
    # Enable log scale if loss values span multiple orders of magnitude
    if min(train_loss + val_loss) > 0:
        plt.yscale('log')
        plt.ylabel('Loss (Log Scale)', fontsize=12)
    else:
        plt.ylabel('Loss', fontsize=12)

    # Formatting and Styling
    plt.title(title, fontsize=14, fontweight='bold', pad=12)
    plt.xlabel('Epochs', fontsize=12)
    plt.grid(True, which="both", linestyle=":", alpha=0.6)
    plt.legend(fontsize=11, loc='upper right')
    plt.tight_layout()
    
    plt.savefig(paths.plot("loss_performance.png"), dpi=300, bbox_inches="tight")
    plt.close()


def plot_mse_comparison(nn_mse, mm_mse, snr_values=None):
    """
    Plot a comparison of NN and M&M MSE values for one or more selected SNR points.

    :param nn_mse: 1D or 2D array-like of NN MSE values. If 2D, the selected SNR
                   columns are used.
    :param mm_mse: 1D or 2D array-like of M&M MSE values. If 2D, the selected SNR
                   columns are used.
    :param snr_values: Optional SNR values to plot. Each value produces a separate figure.
    """
    nn_vals = np.asarray(nn_mse, dtype=float)
    mm_vals = np.asarray(mm_mse, dtype=float)

    if nn_vals.ndim > 2 or mm_vals.ndim > 2:
        raise ValueError("nn_mse and mm_mse must be 1D or 2D arrays")

    if snr_values is None:
        snr_values = [cfg.TARGET_SNR]
    elif np.isscalar(snr_values):
        snr_values = [snr_values]
    else:
        snr_values = list(snr_values)

    for snr_db in snr_values:
        if nn_vals.ndim == 2:
            try:
                snr_index = cfg.SNR.index(snr_db)
            except ValueError as exc:
                raise ValueError(f"SNR {snr_db} not found in cfg.SNR") from exc
            nn_plot_vals = np.ravel(nn_vals[:, snr_index])
        else:
            nn_plot_vals = np.ravel(nn_vals)

        if mm_vals.ndim == 2:
            try:
                snr_index = cfg.SNR.index(snr_db)
            except ValueError as exc:
                raise ValueError(f"SNR {snr_db} not found in cfg.SNR") from exc
            mm_plot_vals = np.ravel(mm_vals[:, snr_index])
        else:
            mm_plot_vals = np.ravel(mm_vals)

        if nn_plot_vals.size == 0 or mm_plot_vals.size == 0:
            raise ValueError("nn_mse and mm_mse must not be empty")

        n_pairs = min(nn_plot_vals.size, mm_plot_vals.size)
        nn_plot_vals = nn_plot_vals[:n_pairs]
        mm_plot_vals = mm_plot_vals[:n_pairs]

        plt.figure(figsize=(10, 6))
        width = 0.35
        positions = np.arange(n_pairs)

        plt.bar(positions - width / 2, nn_plot_vals, width=width, label='NN', color='#1f77b4')
        plt.bar(positions + width / 2, mm_plot_vals, width=width, label='M&M', color='#ff7f0e')

        labels = [f'N={cfg.MAX_PHASES[i]}' for i in range(n_pairs)]
        plt.xticks(np.arange(len(labels)), labels, rotation=25, ha='right')
        plt.xlim(-0.5, len(labels) - 0.5)
        plt.xlabel('Model / Lag')
        plt.ylabel('MSE')
        plt.title(f'MSE of NN VS M&M (SNR = {snr_db} dB)')
        plt.grid(True, axis='y', linestyle=':', alpha=0.6)
        plt.legend(handles=[
            plt.Rectangle((0, 0), 1, 1, color='#1f77b4', label='NN'),
            plt.Rectangle((0, 0), 1, 1, color='#ff7f0e', label='M&M')
        ])
        plt.tight_layout()

        plt.savefig(paths.plot(f"mse_comparison_SNR={snr_db}.png"), dpi=300, bbox_inches="tight")
        plt.close()

def plot_error_histogram(error_samples, model_names, true_cfo, snr_db, max_error=None, num_bins=300):
    """
    Plot the probability distribution of CFO estimation error with 
    symmetric bins centered around zero and outlier cutoff.

    Parameters
    ----------
    error_samples : list of array-like
        Each element contains the CFO errors (signed or absolute) for one model.
    model_names : list of str
        Names corresponding to each model.
    true_cfo : float
        True CFO used in the experiment.
    snr_db : float
        SNR used in the experiment.
    max_error : float, optional
        Threshold to trim severe outliers. If None, it defaults to the 99th percentile 
        across all models to automatically prevent huge outliers from squishing the plot.
    num_bins : int, optional
        Total number of bins (default: 60, giving 30 negative and 30 positive bins).
    """

    # 1. Determine outlier cutoff threshold if not explicitly provided
    if max_error is None:
        all_errors = np.concatenate([np.abs(np.asarray(e, dtype=float)) for e in error_samples])
        max_error = np.percentile(all_errors, 99)  # Cut off top 1% outliers dynamically

    # 2. Define explicit, symmetric bins centered around 0
    # For num_bins=60, this creates exactly 30 bins < 0 and 30 bins > 0
    bins = np.linspace(-max_error, max_error, num_bins + 1)

    plt.figure(figsize=(10, 6))

    for errors, name in zip(error_samples, model_names):
        errors = np.asarray(errors, dtype=float)

        # 3. Filter out values beyond the max_error threshold
        filtered_errors = errors[np.abs(errors) <= max_error]

        plt.hist(
            filtered_errors,
            bins=bins,
            density=True,
            alpha=0.5,
            label=name
        )

    plt.xlabel(r'CFO Error $(\hat{f}-f)$')
    plt.ylabel('Probability Density')
    plt.title(
        f'CFO Error Distribution '
        f'(CFO = {true_cfo}, SNR = {snr_db} dB)'
    )
    plt.xlim(-max_error, max_error)
    plt.grid(True, axis='y', linestyle=':', alpha=0.6)
    plt.legend()
    plt.tight_layout()

    plt.savefig(
        paths.plot(f"error_histogram_CFO={true_cfo}_SNR={snr_db}.png"),
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()