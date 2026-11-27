import math
import numpy as np
def rrc_design(beta=0.25, sps=8, span=10):

    num_taps = sps * span + 1
    taps = []

    half_width = (num_taps - 1) // 2

    for i in range(-half_width, half_width + 1):

        n = float(i)

        # beta = 0 --> sinc
        if beta == 0:
            val = (1 / math.sqrt(sps)) * np.sinc(n / sps)

        # center tap
        elif n == 0:
            val = (1.0 / math.sqrt(sps)) * (
                1.0 + beta * (4.0 / math.pi - 1.0)
            )

        # singularity at t = ±T/(4β)
        elif abs(abs(n) - sps / (4.0 * beta)) < 1e-12:

            val = (beta / math.sqrt(2.0 * sps)) * (
                (1.0 + 2.0 / math.pi)
                * math.sin(math.pi / (4.0 * beta))
                +
                (1.0 - 2.0 / math.pi)
                * math.cos(math.pi / (4.0 * beta))
            )

        else:

            angle = math.pi * n / sps

            num = (
                math.cos((1 + beta) * angle)
                +
                math.sin((1 - beta) * angle)
                / (4 * beta * n / sps)
            )

            den = 1 - (4 * beta * n / sps) ** 2

            val = (
                (4 * beta)
                / (math.pi * math.sqrt(sps))
            ) * (num / den)

        taps.append(val)

    # Normalize energy
    energy = math.sqrt(sum(x*x for x in taps))

    return [x / energy for x in taps]