"""
E6: CFO basin of the code-aided metric with per-segment phase tracking (MAC reduction idea 7 for v3).

v3 scores a grid cell with ONE carrier phase for the whole packet (the 4th-power phase at the cell's CFO). A CFO
error d leaves a phase ramp 2 pi d nc across the packet, so the metric only recognises the right cell for |d| up to the
basin; the grid step is set from it (blind_fast.grid_step). If the phase is estimated per segment of the packet (4th
power on each of S segments, the pi/2 branch of each chosen next to the previous segment), a CFO error leaves only the
ramp inside one segment, so the basin could widen ~S x and the grid be coarser (fewer cells for the same rank).
Alternatively the cell's CFO is snapped to the local maximum of the 4th-power periodogram inside the cell.

Per packet and method: metric at the true CFO + d STEP (d = 0 .. 16) and at 64 far "wrong" CFOs (the null); robust
z = (median_null - M) / MAD_null; reported P(z > z0) for z0 = 4 (v3's decode threshold) vs d.

    python blind_basin.py --part a        # -> blind/results/basin_e6_a.json
"""
import argparse
import json
import multiprocessing as mp

import numpy as np

import blind_cfo as bc
import blind_fast as bf

OFFS = (0, 1, 2, 3, 4, 6, 8, 10, 12, 16)
METHODS = ("global (v3)", "2 segments", "4 segments", "8 segments", "snap to 4th-power peak")
POINTS = (("1/10", -5.0), ("1/10", -4.0), ("1/10", -3.0), ("1/10", -2.0), ("1/3", 0.5), ("1/2", 2.0))


def _llr(y, sigma2):
    l2 = np.empty((len(y), bc.N_BITS), np.float32)
    l2[:, 0::2] = y.real
    l2[:, 1::2] = y.imag
    l2 *= np.sqrt(2) / sigma2
    out = np.empty_like(l2)
    out[:, bc.INTERLEAVER] = l2
    return out


def phases(r, fh, S):
    """Per-segment 4th-power phase (B, N) at CFO fh: segment phases mod pi/2, unwrapped segment to segment."""
    y4 = -(r * np.exp(-2j * np.pi * fh[:, None] * bc.NC[None])) ** 4
    seg = np.array_split(np.arange(bc.N_SYM), S)
    th = np.stack([np.angle(y4[:, s].sum(1)) / 4 for s in seg], 1)          # (B, S), mod pi/2
    for j in range(1, S):
        th[:, j] += np.round((th[:, j - 1] - th[:, j]) / (np.pi / 2)) * (np.pi / 2)
    full = np.empty((len(r), bc.N_SYM))
    for j, s in enumerate(seg):
        full[:, s] = th[:, j:j + 1]
    return full


def snap(r, fh, k):
    """CFO of the 4th-power periodogram maximum within +-k/2 STEP of fh (5-point search + parabola)."""
    d = np.linspace(-k / 2, k / 2, 5) * bc.STEP
    y4 = -(r ** 4)
    P = np.abs(np.einsum("bn,bdn->bd", y4, np.exp(-2j * np.pi * 4 * (fh[:, None, None] + d[None, :, None])
                                                     * bc.NC[None, None]))) ** 2
    i = np.clip(P.argmax(1), 1, 3)
    rows = np.arange(len(r))
    c0, cm, cp = P[rows, i], P[rows, i - 1], P[rows, i + 1]
    den = cm - 2 * c0 + cp
    step = d[1] - d[0]
    return fh + d[i] + np.clip(0.5 * (cm - cp) / np.where(den < 0, den, -1e-30), -0.5, 0.5) * step


def score(r, fh, method, sigma2, metric, k):
    """Best metric over the 4 phase offsets q pi/4 (v3's phase search)."""
    if method.startswith("snap"):
        fh = snap(r, fh, k)
    S = 1 if method.startswith(("global", "snap")) else int(method.split()[0])
    th = phases(r, fh, S)
    y = r * np.exp(-1j * (2 * np.pi * fh[:, None] * bc.NC[None] + th))
    return np.min([metric(_llr(y * np.exp(-1j * q * np.pi / 4), sigma2)) for q in range(4)], 0)


def _work(task):
    rate, snr, seed, n = task
    code = bc.PiCode(bc.N_BITS, bc.CODES[rate], 16, 8)
    metric = bf.fast_sc(code.A).metric
    sigma2 = 1.0 / (2.0 * 10 ** (snr / 10))
    k = bf.grid_step(rate, snr)
    rng = np.random.default_rng(seed)
    out = {m: {d: [] for d in OFFS} for m in METHODS}
    for _ in range(n // 50):
        _, _, r, rx, f, _ = bc.frames(50, code, snr, rng)
        r = bf.premf(r, rx, f)                                  # the pre-MF correction at the right CFO (as v3 near it)
        for m in METHODS:
            null = np.stack([score(r, f + s * rng.uniform(0.01, 0.05, len(f)), m, sigma2, metric, k)
                             for s in rng.choice([-1, 1], 64)], 1)
            med = np.median(null, 1)
            mad = 1.4826 * np.median(np.abs(null - med[:, None]), 1) + 1e-6
            for d in OFFS:
                sgn = rng.choice([-1, 1], len(f))
                z = (med - score(r, f + sgn * d * bc.STEP, m, sigma2, metric, k)) / mad
                out[m][d] += list(z)
    return rate, snr, out


def main(a):
    pts = [(p.split(":")[0], float(p.split(":")[1])) for p in a.points] if a.points else POINTS
    tasks = [(rate, snr, 9100 + 17 * i + int(10 * snr + 100), a.frames) for rate, snr in pts for i in range(a.chunks)]
    acc = {}
    with mp.Pool(a.workers) as pool:
        for i, (rate, snr, out) in enumerate(pool.imap_unordered(_work, tasks), 1):
            t = acc.setdefault((rate, snr), {m: {d: [] for d in OFFS} for m in METHODS})
            for m in METHODS:
                for d in OFFS:
                    t[m][d] += out[m][d]
            with open(bc.path("logs", f"basin_e6_{a.part}.progress"), "a") as fh:
                fh.write(f"{i} {len(tasks)} 0\n")
    res = []
    for (rate, snr), t in sorted(acc.items()):
        for m in METHODS:
            z = {d: np.array(v) for d, v in t[m].items()}
            res.append({"rate": rate, "snr": snr, "method": m, "frames": len(z[0]), "grid_step": bf.grid_step(rate, snr),
                        "P_z_gt_4": {str(d): float(np.mean(z[d] > 4)) for d in OFFS},
                        "z_median": {str(d): float(np.median(z[d])) for d in OFFS}})
            print(f"{rate} {snr:5.1f} dB {m:24s} " + " ".join(f"{d}:{res[-1]['P_z_gt_4'][str(d)]:.3f}" for d in OFFS),
                  flush=True)
    json.dump(res, open(bc.path("results", f"basin_e6_{a.part}.json"), "w"), indent=1)
    print("EVAL DONE", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", default="a")
    ap.add_argument("--frames", type=int, default=500)
    ap.add_argument("--chunks", type=int, default=4)
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--points", nargs="+", default=None, help='"rate:snr" items (default POINTS)')
    main(ap.parse_args())
