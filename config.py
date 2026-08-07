import numpy as np
PREAMBLE_LENGTH = 128
MAX_LAG = [8, 16, 32, 64]
CFO = [0.02 * i for i in range(-10, 11)]
TARGET_SNR = -6  # Target SNR for single-point testing

SPS = 8
BETA = 0.25
FILTER_SPAN = 10
ITERATIONS =1500

qpsk_normalized = 1 / np.sqrt(2)
BIT_MAPPING_QPSK = {
    (0, 0): qpsk_normalized * (1 + 1j),
    (0, 1): qpsk_normalized * (1 - 1j),
    (1, 0): qpsk_normalized * (-1 + 1j),
    (1, 1): qpsk_normalized * (-1 - 1j)
}

NORMALIZED_CFO = 0.05  # CFO relative to symbol rate (e.g., 5% frequency offset)

MAX_CFO = 0.2
MAX_SNR = 10
MIN_SNR = -5

SNR = [i for i in range(MIN_SNR, MAX_SNR+1)]


NN_MAX_PHASE_DIFFERENCE = 8

NN_SAVE_PATH = f"cfo_estimator_N={NN_MAX_PHASE_DIFFERENCE}_2FEATURES_removePLATEAU.pth"  # Path to save the trained neural network model
lr = 1e-3
EPOCHS = 400
BATCH_SIZE = 512
MSE_MULTIPLIER = 1500
SNR_WEIGHT_FACTOR = 1.01

MAX_PHASES = [8, 16, 32]
NN_models = [f"cfo_estimator_N={i}_2FEATURES_removePLATEAU.pth" for i in MAX_PHASES]

SNR_SWEEP = True
CFO_SWEEP = False
TRAIN_NN = False
EVALUATE_NN = False
EVALUATE_NN_CFO = False