"""Is the coded QPSK packet closed under a pi/2 rotation (j s)? For each rate: rotate the symbols of random packets by j,
demap, decode noise-free (CA-SCL, PiCode) and check whether the CRC passes and the re-encoded packet equals j s.
Also the structure of the interleaver's I/Q pairs (bit index XOR of the two coded bits of a symbol).
    python blind/smoke/rot_test.py"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import blind_cfo as bc

rng = np.random.default_rng(3)
I = np.asarray(bc.INTERLEAVER)
x = I[0::2] ^ I[1::2]
print("interleaver I/Q pairs: bit-index XOR values (most common):",
      np.unique(x, return_counts=True)[0][:8], np.unique(x, return_counts=True)[1][:8], flush=True)
for rate in ("1/10", "2/5", "1/2"):
    code = bc.PiCode(bc.N_BITS, bc.CODES[rate], 16, 8)
    data = rng.integers(0, 2, (200, code.A), dtype=np.uint8)
    cw = code.encode(data)[:, I]
    s = ((1 - 2.0 * cw[:, 0::2]) + 1j * (1 - 2.0 * cw[:, 1::2])) / np.sqrt(2)
    for q, lab in ((0, "s (check)"), (1, "j s"), (2, "-s"), (3, "-j s")):
        sr = s * (1j ** q)
        z = np.zeros(len(s))
        llr = bc.llrs(sr, z, z, 0.1)                     # noise-free, the receiver's own LLR convention
        d, ok, _ = code.decode(llr, return_info=True)
        c2 = code.encode(d)[:, I]
        s2 = ((1 - 2.0 * c2[:, 0::2]) + 1j * (1 - 2.0 * c2[:, 1::2])) / np.sqrt(2)
        match = np.mean(np.abs(np.sum(s2 * np.conj(sr), 1)) / bc.N_SYM)
        print(f"R={rate} {lab}: CRC pass {ok.mean():.3f}, same data {np.mean((d == data).all(1)):.3f}, "
              f"|corr(re-encoded, rotated)| {match:.3f}", flush=True)
print("SMOKE DONE", flush=True)
