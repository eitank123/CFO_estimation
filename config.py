import numpy as np
PREAMBLE_LENGTH = 128
SNR = [i for i in range(-5, 10)]
MAX_LAG = [8, 16, 32, 64]
CFO = [0.02 * i for i in range(-10, 11)]
TARGET_SNR = -6  # Target SNR for single-point testing

ITERATIONS = 500

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

NN_MAX_PHASE_DIFFERENCE = 32

NN_SAVE_PATH = f"cfo_estimator_N={NN_MAX_PHASE_DIFFERENCE}.pth"  # Path to save the trained neural network model
lr = 1.5e-3
EPOCHS = 300
BATCH_SIZE = 256
MSE_MULTIPLIER = 1500

SNR_SWEEP = True
CFO_SWEEP = False
TRAIN_NN = False
EVALUATE_NN = True