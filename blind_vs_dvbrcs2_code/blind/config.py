import numpy as np
import paths

SPS = 8
BETA = 0.25
FILTER_SPAN = 10

PREAMBLE_LENGTH = 128
MAX_LAG = [64]
CFO = [0.02 * i for i in range(-10, 11)]
TARGET_SNR = -5  # Target SNR for single-point testing
HISTOGRAM_TARGET_SNR = [2]  # SNR values to plot in the comparison histogram
IS_BPSK = False

ITERATIONS = 150000
qpsk_normalized = 1 / np.sqrt(2)
BIT_MAPPING_QPSK = {
    (0, 0): qpsk_normalized * (1 + 1j),
    (0, 1): qpsk_normalized * (1 - 1j),
    (1, 0): qpsk_normalized * (-1 + 1j),
    (1, 1): qpsk_normalized * (-1 - 1j)
}

NORMALIZED_CFO = 0.05  # CFO relative to symbol rate (e.g., 5% frequency offset)

MAX_CFO = 0.2

FINE_TUNE_HIGH_SNR = 10
FINE_TUNE_EPOCHS = 30
MAX_SNR = 10
MIN_SNR = -5

SNR = [i for i in range(MIN_SNR, MAX_SNR+1)]

NN_MAX_PHASE_DIFFERENCE = 64

LEARNING_RATE = 1e-4
EPOCHS = 95
BATCH_SIZE = 512
MSE_MULTIPLIER = 1500
SNR_WEIGHT_FACTOR = 0.5

MAX_PHASES = [64]
NN_models = [paths.model(f"best_cfo_model_L{MAX_PHASES[i]}.pth") for i in range(len(MAX_PHASES))]

SNR_SWEEP = False
CFO_SWEEP = True
TRAIN_NN = False
EVALUATE_NN = False
EVALUATE_NN_CFO = True