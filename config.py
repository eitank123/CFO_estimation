import numpy as np

SPS = 8
BETA = 0.25
FILTER_SPAN = 10

PREAMBLE_LENGTH = 128
MAX_LAG = [2, 4, 8, 16, 32]
CFO = [0.02 * i for i in range(-10, 11)]
TARGET_SNR = -6  # Target SNR for single-point testing
HISTOGRAM_TARGET_SNR = [-10, -6, -2]  # SNR values to plot in the comparison histogram

ITERATIONS = 10000
qpsk_normalized = 1 / np.sqrt(2)
BIT_MAPPING_QPSK = {
    (0, 0): qpsk_normalized * (1 + 1j),
    (0, 1): qpsk_normalized * (1 - 1j),
    (1, 0): qpsk_normalized * (-1 + 1j),
    (1, 1): qpsk_normalized * (-1 - 1j)
}

NORMALIZED_CFO = 0.05  # CFO relative to symbol rate (e.g., 5% frequency offset)

MAX_CFO = 0.2
MAX_SNR = 0
MIN_SNR = -10

SNR = [i for i in range(MIN_SNR, MAX_SNR+1)]


NN_MAX_PHASE_DIFFERENCE = 64

NN_SAVE_PATH = f"cfo_estimator_N={NN_MAX_PHASE_DIFFERENCE}_2FEATURES_removePLATEAU.pth"  # Path to save the trained neural network model
lr = 0.5e-3
EPOCHS = 75
BATCH_SIZE = 128
MSE_MULTIPLIER = 1500
SNR_WEIGHT_FACTOR = 0.5

MAX_PHASES = [2, 4, 8, 16, 32]
NN_models = [f"best_low_snr_L{i}.pth" for i in MAX_PHASES]

SNR_SWEEP = True
CFO_SWEEP = False
TRAIN_NN = False
EVALUATE_NN = True
EVALUATE_NN_CFO = False