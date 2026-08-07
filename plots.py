import matplotlib.pyplot as plt
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

    # Plot empirical MSE for each lag N
    for i, mse_row in enumerate(mse_results):
        try:
            lag_label = f'Estimator MSE (N={cfg.MAX_LAG[i]})'
        except IndexError:
            lag_label = f'NN estimator (N={cfg.MAX_PHASES[i-len(cfg.MAX_LAG)]})'
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
    
    plt.title('CFO Estimation Performance vs. Cramér-Rao Bound')
    plt.xlabel('SNR (dB)')
    plt.ylabel('Normalized CFO Variance / MSE')
    plt.grid(True, which='both', linestyle=':', alpha=0.6)
    plt.legend()
    plt.tight_layout()
    
    plt.savefig("mse.png", dpi=300, bbox_inches="tight")
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

    # Plot estimated CFO for each lag N (or single curve if 1D)
    for i, cfo_row in enumerate(results_matrix):
        try:
            label = f'Estimated CFO (N={cfg.MAX_LAG[i]})'
        except IndexError:
            label = f'NN estimator (N={cfg.MAX_PHASES[i-len(cfg.MAX_LAG)]})'
            
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

    plt.title('CFO Estimation Performance vs. Normalized CFO (SNR = {} dB)'.format(cfg.TARGET_SNR))
    plt.xlabel('Normalized CFO (f_off / f_s)')
    plt.ylabel('Estimated Normalized CFO (f_hat)')
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.legend()
    plt.tight_layout()
    
    plt.savefig("cfo_performance.png", dpi=300, bbox_inches="tight")
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
    
    plt.savefig("loss_performance.png", dpi=300, bbox_inches="tight")
    plt.close()