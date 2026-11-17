"""
Few-pilot ("Vernier comb") CFO acquisition + code-aided search, and the operation (real-MAC) counts of every receiver.

A handful of known symbols (15-24 of the 1024, 1.5-2.3 % overhead) in 1-4 short blocks. Their likelihood over the CFO
grid is the "frequency ruler": a contiguous block gives one wide lobe, blocks at a spacing D give lobes every 1/D
(teeth of a comb), nested spacings (D, 4D, ...) resolve which tooth like a Vernier. The ruler only has to bring the
true cell to the top few of the search order; the code-aided metric (Fast-SSC, frozen bits) picks the right tooth and
the re-encoding check + CRC confirm it. The pilots also give the carrier phase (mod 2 pi): no 4th-power phase, no pi
ambiguity (plain CA-SCL instead of PiCode: half the false CRC passes).

    python blind_vp.py ranks --part a        # E4: rank of the true cell / pilot-ML outage per pattern and SNR
Receivers are registered in blind_ber.py (kind "vp").

MAC model (real multiply-accumulates; a comparison or add counts as one): complex multiply 4, FFT of n points
2 n log2 n, CA-SCL L = 8 decode L N log2 N = 180,224 (polar_ber_experiment), LLRs of a hypothesis 6,144 (de-rotation
1024 complex multiplies + scaling), Fast-SSC metric: 2n per inner node of size n (f + g) and n (2n for REP / SPC) per
leaf node, 4th-power phase of a cell 4,096, re-encoding check ~20,000.
"""
import argparse
import json
import multiprocessing as mp
import os

import numpy as np

import blind_cfo as bc
import blind_fast as bf

# ----------------------------------------------------------------------------------------------- patterns
def _blocks(starts, L):
    return tuple(int(s + j) for s in starts for j in range(L))


PATTERNS = {
    "C16": _blocks([0], 16),                       # contiguous short preamble
    "C24": _blocks([0], 24),
    "V2x8 D32": _blocks([0, 32], 8),               # two blocks: lobes every 1/32
    "V2x8 D64": _blocks([0, 64], 8),
    "N3x5": _blocks([0, 20, 80], 5),               # nested comb, spacing x4 (15 symbols)
    "N4x4": _blocks([0, 12, 48, 192], 4),          # nested comb, 16 symbols
    "N3x8": _blocks([0, 32, 128], 8),              # nested comb, 24 symbols
    "N4x6": _blocks([0, 24, 96, 384], 6),
    "R3x8": _blocks([0, 571, 1016], 8),            # long-span pattern with the lowest peak sidelobe (still ~1)
}

# ----------------------------------------------------------------------------------------------- MAC model
MAC = dict(cmul=4, decode=8 * bc.N_BITS * int(np.log2(bc.N_BITS)), llr=6144, phase4=4096, reencode=20000)


def fft_macs(n):
    return 2 * n * int(np.log2(n))


def metric_macs(A, hard=False):
    """Real ops of one Fast-SSC metric evaluation (from the node plan of the code)."""
    def walk(q, n):
        if q[0] == "N":
            return 2 * n + walk(q[1], n // 2) + walk(q[2], n // 2)
        return 2 * n if q[0] in ("REP", "SPC") else n
    return walk(bf.fast_sc(A).plan, bc.N_BITS)


SPECTRAL_MACS = 3 * fft_macs(bc.NFFT_S) + 2 * bc.NFFT_S      # PSD-template estimator (8 SPS)
CYCLIC_MACS = 3 * fft_macs(bc.NFFT_S) + 4 * bc.NFFT_S        # band-edge cyclic statistic
S4_MACS = 2 * 4 * bc.N_SYM + fft_macs(bc.NFFT4)              # r^4 + FFT
NEWTON_MACS = 4 * 3 * 4 * bc.N_SYM + 4 * 8 * bc.N_SYM        # 4 iterations x 3 sums + the exponentials
PREMF_MACS = 4 * (bc.N_SYM + bc.SPAN) * bc.SPS + 2 * (bc.SPAN * bc.SPS + 1) * bc.N_SYM   # de-rotation + 2nd MF


# ----------------------------------------------------------------------------------------------- pilot likelihood
def pilot_A(z, pos, F):
    """A(F) = sum_k z_k exp(-j 2 pi F nc_k); z (B, K) = r s* at the pilots, F (B, H) or (H,). Returns (B, H)."""
    nc = np.asarray(pos, float) - bc.CENTRE
    if F.ndim == 1:
        return z @ np.exp(-2j * np.pi * np.outer(nc, F))
    return np.einsum("bk,bhk->bh", z, np.exp(-2j * np.pi * F[:, :, None] * nc[None, None]))


def pilot_loglik(A, snr):
    """Non-coherent log-likelihood log I0(2 |A| / N0) of a CFO hypothesis from the pilots (Es = 1, N0 = 1 / snr)."""
    from scipy.special import i0e
    x = 2 * np.abs(A) * 10 ** (snr / 10)
    return np.log(i0e(x)) + x


# ----------------------------------------------------------------------------------------------- receiver
VP_DEFAULT = dict(pattern="N4x4", blind_terms=False, z0=4.0, rounds=(16, 16, 32, 64, 128, 256, 512, 1024, 2048),
                  T=2, final=3, verify=True, premf=True, step=None, rate=None, s0=True, phase="pilot")


def vp_receive(r, rx, snr, code, sigma2, st, spec, sym):
    """Few-pilot receiver. sym (B, N_SYM) transmitted symbols (only the pilot positions are used). Returns decoded
    data (B, A), CRC passed (B,), final CFO (B,), the top-ranked cell's CFO (B,)."""
    p = {**VP_DEFAULT, **spec.get("vp", {})}
    pos = np.array(PATTERNS[p["pattern"]])
    K = len(pos)
    k = p["step"] or bf.grid_step(p["rate"], snr)
    g = bf.grid(k)["f"]
    G = len(g)
    B = len(r)
    fast = bf.fast_sc(code.A)
    m_eval = metric_macs(code.A) + MAC["llr"]
    macs = np.zeros(B)
    out = np.zeros((B, code.A), np.uint8)
    have = np.zeros(B, bool)
    passed = np.zeros(B, bool)
    f_fin = np.full(B, np.nan)
    snr_lin = 10 ** (snr / 10)
    sig_th = 1 / np.sqrt(2 * K * snr_lin)                     # pilot phase std at the right CFO
    if p["phase"] == "pilot":                                  # pilot phase, sub-offsets when it is noisy
        sub = (-1.2 * sig_th, 0.0, 1.2 * sig_th) if sig_th > 0.12 else (0.0,)
    else:                                                      # 4th-power phase, its pi/2 branch from the pilots
        sub = (-np.pi / 12, 0.0, np.pi / 12) if snr < -4 else (0.0,)
    use4 = p["phase"] != "pilot"

    def decode(fr, fh, th):
        d, ok, _ = code.decode(bc.llrs(r[fr], fh, th, sigma2), return_info=True)
        st["decodes"] += len(fr)
        np.add.at(macs, fr, MAC["decode"] + MAC["llr"])
        if p["verify"] and ok.any():
            j = np.where(ok)[0]
            np.add.at(macs, fr[j], MAC["reencode"])
            ok[j] = bf.reencode_rho(code, r[fr[j]], d[j], fh[j]) > bf.rho_min(snr)
            st["rejected"] = st.get("rejected", 0) + int(len(j) - ok[j].sum())
        first = ~have[fr]
        out[fr[first]], have[fr[first]], f_fin[fr[first]] = d[first], True, fh[first]
        w = fr[ok]
        out[w], passed[w], f_fin[w] = d[ok], True, fh[ok]
        return ok

    def score(fr, fh, th):
        M = np.empty(len(fr), np.float32)
        for a in range(0, len(fr), 2048):
            sl = slice(a, a + 2048)
            M[sl] = fast.metric(bc.llrs(r[fr[sl]], fh[sl], th[sl], sigma2))
        st["metric_evals"] += len(fr)
        np.add.at(macs, fr, m_eval)
        return M

    # pilot ruler on the post-MF samples, then (optionally) the pre-MF correction by its ML cell and the ruler again
    zp = r[:, pos] * np.conj(sym[:, pos])
    A = pilot_A(zp, pos, g)
    macs += MAC["cmul"] * K * G + MAC["cmul"] * K
    if p["premf"]:
        f_c = g[np.abs(A).argmax(1)]
        r = bf.premf(r, rx, f_c)
        zp = r[:, pos] * np.conj(sym[:, pos])
        A = pilot_A(zp, pos, g)
        macs += PREMF_MACS + MAC["cmul"] * K * G
    y4 = -(r ** 4)
    macs += 2 * MAC["cmul"] * bc.N_SYM
    post = pilot_loglik(A, snr)
    if p["blind_terms"]:                                       # + the blind statistics (spectral prior, cyclic, 4th)
        S4, fs, C = bf.features2(r, rx, k)
        post = post + bf.posterior2(S4, fs, C, snr, k)
        macs += SPECTRAL_MACS + CYCLIC_MACS + S4_MACS
    order = np.argsort(-post, 1)
    macs += G * int(np.log2(G))
    f_top = g[order[:, 0]]
    th_all = np.angle(A)                                       # pilot phase at every cell (centre reference)
    if p["s0"]:                                                # stage 0: the top cell, refined on the pilots, decoded
        fr = np.arange(B)
        f0 = _pilot_refine(zp, pos, f_top)
        th0 = np.angle(pilot_A(zp, pos, f0[:, None]))[:, 0]
        macs += 3 * MAC["cmul"] * K * 3
        decode(fr, f0, th0)
    nF = p["final"]
    bestM = np.full((B, nF), np.inf, np.float32)
    bestC = np.zeros((B, nF), int)
    stats = np.zeros((B, 0), np.float32)
    tried = [set() for _ in range(B)]
    roffs = np.arange(-(k // 2), k // 2 + 1)
    ptr = 0
    for Kr in p["rounds"]:
        idx = np.where(~passed)[0]
        if not len(idx) or ptr >= G:
            break
        cells = order[idx, ptr:ptr + Kr]
        ptr += cells.shape[1]
        nK = cells.shape[1]
        fr = np.repeat(idx, nK)
        c = cells.ravel()
        th = np.take_along_axis(th_all[idx], cells, 1).ravel()
        if use4:
            th = _snap4(y4[fr], g[c], th, k, c)
            np.add.at(macs, fr, MAC["phase4"])
        Ms = [score(fr, g[c], th + s) for s in sub]
        M = np.min(Ms, 0).reshape(len(idx), nK)
        new = np.stack(Ms, 1).reshape(len(idx), nK * len(sub))
        full = np.zeros((B, stats.shape[1] + new.shape[1]), np.float32)
        full[:, :stats.shape[1]] = stats
        full[idx, stats.shape[1]:] = new
        stats = full
        v = stats[idx]
        med = np.median(v, 1)
        mad = 1.4826 * np.median(np.abs(v - med[:, None]), 1) + 1e-6
        z = (med[:, None] - M) / mad[:, None]
        allM = np.concatenate([bestM[idx], M], 1)
        allC = np.concatenate([bestC[idx], cells], 1)
        o = np.argsort(allM, 1)[:, :nF]
        bestM[idx], bestC[idx] = np.take_along_axis(allM, o, 1), np.take_along_axis(allC, o, 1)
        cand = []
        top = np.argsort(-z, 1)[:, :2]
        for j, kk in zip(*np.where(np.take_along_axis(z, top, 1) > p["z0"])):
            cc = cells[j, top[j, kk]]
            if cc not in tried[idx[j]]:
                tried[idx[j]].add(cc)
                cand.append((idx[j], g[cc]))
        if cand:
            _vp_refine(cand, roffs, sub, p["T"], zp, pos, score, decode, passed, macs, K, r if use4 else None)
    cand = []
    for i in np.where(~passed)[0]:
        for m, cc in zip(bestM[i], bestC[i]):
            if np.isfinite(m) and cc not in tried[i]:
                tried[i].add(cc)
                cand.append((i, g[cc]))
    if cand:
        _vp_refine(cand, roffs, sub, p["T"], zp, pos, score, decode, passed, macs, K, r if use4 else None)
    st["macs"] = st.get("macs", 0.0) + float(macs.sum())
    return out, passed, f_fin, f_top


def _pilot_refine(zp, pos, f, iters=2):
    """A few Newton-like steps on |A(f)|^2 from the pilots alone (3-point parabola, step 1/4 of a grid cell)."""
    h = bc.STEP
    for _ in range(iters):
        F = f[:, None] + np.array([-h, 0.0, h])[None]
        P = np.abs(pilot_A(zp, pos, F)) ** 2
        den = P[:, 0] - 2 * P[:, 1] + P[:, 2]
        f = f + np.clip(0.5 * h * (P[:, 0] - P[:, 2]) / np.where(den < 0, den, -1e-30), -2 * h, 2 * h)
    return f


def _snap4(y4, f, th_p, k, cells):
    """4th-power phase at the cells (mod pi/2), on the pi/2 branch nearest the pilot phase th_p."""
    th4 = np.angle(np.einsum("hn,hn->h", y4, bf._rot2(k, cells, 4))) / 4
    return th4 + np.round((th_p - th4) / (np.pi / 2)) * (np.pi / 2)


def _vp_refine(cand, roffs, sub, T, zp, pos, score, decode, passed, macs, K, r=None):
    """Candidate cells: CFO offsets roffs x STEP, the pilot phase at each (4th-power phase on the pilot's pi/2 branch
    when r is given), x phase sub-offsets; CA-SCL on the best T."""
    fr = np.array([c[0] for c in cand])
    F = np.array([c[1] for c in cand])[:, None] + roffs[None] * bc.STEP
    TH = np.angle(pilot_A(zp[fr], pos, F))
    np.add.at(macs, fr, MAC["cmul"] * K * F.shape[1])
    if r is not None:
        T4 = bc.phase4(r[fr], F)
        TH = T4 + np.round((TH - T4) / (np.pi / 2)) * (np.pi / 2)
        np.add.at(macs, fr, MAC["phase4"] * F.shape[1])
    F = np.repeat(F, len(sub), 1)
    TH = (TH[:, :, None] + np.array(sub)[None, None]).reshape(len(fr), -1)
    H = F.shape[1]
    M = score(np.repeat(fr, H), F.ravel(), TH.ravel()).reshape(len(fr), H)
    o = np.argsort(M, 1)
    act = np.ones(len(fr), bool)
    for t in range(T):
        j = np.where(act & ~passed[fr])[0]
        if not len(j):
            break
        ok = decode(fr[j], F[j, o[j, t]], TH[j, o[j, t]])
        act[j[ok]] = False


# ----------------------------------------------------------------------------------------------- E4: ranks
E4_SNRS = (-6.0, -5.0, -4.0, -3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0)
RANK_K = (1, 3, 10, 30, 100, 300, 1000)


def _e4_work(task):
    snr, seed, n = task
    from polar import PolarCode
    code = PolarCode(bc.N_BITS, 205, 16, 8)
    rng = np.random.default_rng(seed)
    g = bf.grid(4)["f"]
    gf = bf.grid(1)["f"]                                          # 1-step grid for the pilot-only ML estimate
    out = {}
    for _ in range(n // 50):
        data, cw, r, rx, f, th = bc.frames(50, code, snr, rng)
        sym = ((1 - 2.0 * cw[:, 0::2]) + 1j * (1 - 2.0 * cw[:, 1::2])) / np.sqrt(2)
        S4, fs, C = bf.features2(r, rx, 4)
        blind = bf.posterior2(S4, fs, C, snr, 4)
        true = np.abs(g[None] - f[:, None]).argmin(1)
        rows = np.arange(len(f))
        for name, pos in PATTERNS.items():
            pos = np.array(pos)
            zp = r[:, pos] * np.conj(sym[:, pos])
            L = pilot_loglik(pilot_A(zp, pos, g), snr)
            for tag, sc in ((name, L), (name + " + blind", L + blind)):
                o = out.setdefault(tag, {"rank": [], "se": 0.0, "out": 0, "n": 0})
                o["rank"] += list((sc > sc[rows, true][:, None]).sum(1).astype(int))
            # pilot-only ML estimate (1-step grid + parabola): outage of the pilots alone
            Af = np.abs(pilot_A(zp, pos, gf))
            fml = _pilot_refine(zp, pos, gf[Af.argmax(1)])
            o = out[name]
            o["se"] += float(np.sum((fml - f) ** 2))
            o["out"] += int(np.sum(np.abs(fml - f) > bc.TOL))
            o["n"] += len(f)
    return snr, out


def run_e4(part, workers, n, chunks):
    tasks = [(s, 8800 + 31 * i + int(10 * s + 100), n) for s in E4_SNRS for i in range(chunks)]
    acc = {}
    with mp.Pool(workers) as pool:
        for i, (snr, out) in enumerate(pool.imap_unordered(_e4_work, tasks), 1):
            a = acc.setdefault(snr, {})
            for k, v in out.items():
                b = a.setdefault(k, {"rank": [], "se": 0.0, "out": 0, "n": 0})
                b["rank"] += v["rank"]
                b["se"] += v["se"]
                b["out"] += v["out"]
                b["n"] += v["n"]
            with open(bc.path("logs", f"vp_e4_{part}.progress"), "a") as fh:
                fh.write(f"{i} {len(tasks)} 0\n")
    res = []
    for snr in sorted(acc):
        for k, v in acc[snr].items():
            rk = np.array(v["rank"])
            row = {"snr": snr, "pattern": k, "K": len(PATTERNS[k.replace(" + blind", "")]), "frames": len(rk),
                   "rank_mean": float(rk.mean()), "rank_median": float(np.median(rk)),
                   "P_rank_ge": {str(K): float(np.mean(rk >= K)) for K in RANK_K}}
            if v["n"]:
                row.update(ml_rmse=float(np.sqrt(v["se"] / v["n"])), ml_outage=v["out"] / v["n"])
            res.append(row)
        print(f"{snr:5.1f} dB " + " | ".join(f"{r['pattern']}: {r['rank_mean']:.1f}" for r in res if r["snr"] == snr),
              flush=True)
    json.dump(res, open(bc.path("results", f"vp_e4_{part}.json"), "w"), indent=1)
    print("EVAL DONE", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["ranks"])
    ap.add_argument("--part", default="a")
    ap.add_argument("--frames", type=int, default=2000, help="per chunk")
    ap.add_argument("--chunks", type=int, default=4)
    ap.add_argument("--workers", type=int, default=16)
    a = ap.parse_args()
    run_e4(a.part, a.workers, a.frames, a.chunks)


# ----------------------------------------------------------------------------------------------- MAC-light features
# The PSD-template and band-edge cyclic statistics need the band |nu| <= |f| + (1 + beta) / 2 <= 0.83 only: decimating
# the 8-SPS pre-MF samples by 4 (24-tap FIR, passband 0.85, stopband 1.15 cycles/symbol) to 2 SPS and an FFT of 4096
# instead of 16384 gives the same estimates for ~1/4 of the operations.
DEC = 4
NFFT_L = bc.NFFT_S // DEC
_lpf = None
_tl = None


def decimate(rx):
    global _lpf
    from scipy.signal import firwin, lfilter
    if _lpf is None:
        _lpf = firwin(32, 1.0 / bc.SPS * 2, window=("kaiser", 7.0))        # cutoff 1.0 cycle/symbol (Nyquist 4)
    return lfilter(_lpf, 1.0, rx, axis=1)[:, ::DEC]


LITE_MACS = 2 * 32 * (bc.N_SYM + 2 * bc.SPAN) * bc.SPS // DEC + 3 * fft_macs(NFFT_L) + 2 * NFFT_L   # one statistic
DECIM_MACS = 2 * 32 * (bc.N_SYM + 2 * bc.SPAN) * bc.SPS // DEC        # the 2-SPS decimation (shared by the statistics)
NFFT_SM = 2048                                                         # small spectral estimate: bins of 1/1024
SMALL_SPEC_MACS = 3 * fft_macs(NFFT_SM) + 2 * NFFT_SM
PREMF_FAIR_MACS = MAC["cmul"] * (bc.N_SYM + 2 * bc.SPAN) * bc.SPS     # de-rotation only: its MF replaces the chain's
_tsm = None


def spectral_small(x):
    """PSD-template CFO estimate from the 2-SPS decimated samples x with a 2048-point FFT (bins 1/1024 cycle/symbol,
    parabolic interpolation): ~1e-3 accuracy, enough for the fast path (4th-power ambiguity +-1/8, pre-MF centre)."""
    global _tsm
    from txrx_chain import rrc
    import config as cfg
    if _tsm is None:
        decimate(np.zeros((1, 8), complex))
        H8 = np.fft.fft(rrc(cfg.BETA), bc.NFFT_S) * np.fft.fft(_lpf, bc.NFFT_S)       # bins 1/2048
        jj = (np.fft.fftfreq(NFFT_SM) * NFFT_SM).astype(int)                        # bins 1/1024
        _tsm = np.conj(np.fft.fft(np.abs(H8[(2 * jj) % bc.NFFT_S]) ** 2))
    X = np.fft.fft(x[:, :NFFT_SM], NFFT_SM, axis=1)
    C = np.fft.ifft(np.fft.fft(np.abs(X) ** 2, axis=1) * _tsm[None], axis=1).real
    kk = np.fft.fftfreq(NFFT_SM) * NFFT_SM
    sps_l = bc.SPS / DEC
    i = np.where(np.abs(kk) / NFFT_SM * sps_l > bc.MAX_CFO + 0.01, -np.inf, C).argmax(1)
    rows = np.arange(len(C))
    c0, cm, cp = C[rows, i], C[rows, (i - 1) % NFFT_SM], C[rows, (i + 1) % NFFT_SM]
    den = cm - 2 * c0 + cp
    return (kk[i] + np.clip(0.5 * (cm - cp) / np.where(den < 0, den, -1e-30), -0.5, 0.5)) / NFFT_SM * sps_l


def features_lite(r, rx, k, curves=False):
    """S4, spectral estimate, cyclic statistic on bf.grid(k), from 2-SPS decimated samples [, and the full PSD-template
    and cyclic curves over NFFT_L bins (for the NN posterior)]."""
    global _tl
    from txrx_chain import rrc
    import config as cfg
    x = decimate(rx)
    if _tl is None:
        decimate(rx[:1, :1])
        # the RRC times the decimation filter (its band-edge attenuation and delay phase), bin spacing 1/2048
        H8 = np.fft.fft(rrc(cfg.BETA), bc.NFFT_S) * np.fft.fft(_lpf, bc.NFFT_S)
        H = np.concatenate([H8[:NFFT_L // 2], H8[-NFFT_L // 2:]])           # |nu| < 1
        half = NFFT_L // 4                                                  # 1/2 cycle/symbol in bins
        W = np.roll(H, -half) * np.conj(np.roll(H, half))
        _tl = (np.conj(np.fft.fft(np.abs(H) ** 2)), np.conj(np.fft.fft(W)), half)
    T, Wf, half = _tl
    X = np.fft.fft(x, NFFT_L, axis=1)
    Cp = np.fft.ifft(np.fft.fft(np.abs(X) ** 2, axis=1) * T[None], axis=1).real
    kk = np.fft.fftfreq(NFFT_L) * NFFT_L
    sps_l = bc.SPS / DEC
    i = np.where(np.abs(kk) / NFFT_L * sps_l > bc.MAX_CFO + 0.01, -np.inf, Cp).argmax(1)
    rows = np.arange(len(Cp))
    c0, cm, cp = Cp[rows, i], Cp[rows, (i - 1) % NFFT_L], Cp[rows, (i + 1) % NFFT_L]
    den = cm - 2 * c0 + cp
    fs = (kk[i] + np.clip(0.5 * (cm - cp) / np.where(den < 0, den, -1e-30), -0.5, 0.5)) / NFFT_L * sps_l
    P = np.roll(X, -half, axis=1) * np.conj(np.roll(X, half, axis=1))
    Cc = np.fft.ifft(np.fft.fft(P, axis=1) * Wf[None], axis=1)
    g = bf.grid(k)["f"]
    C = Cc[:, np.round(g / sps_l * NFFT_L).astype(int) % NFFT_L].real
    step = k * bc.STEP
    Y = np.abs(np.fft.fft(-(r ** 4), bc.NFFT4)) ** 2
    Y /= Y.mean(1, keepdims=True)
    nu = (4 * g) % 1.0
    w = int(np.ceil(4 * step * bc.NFFT4)) + 1
    b0 = np.floor((nu - 2 * step) * bc.NFFT4).astype(int)
    S4 = Y[:, (b0[:, None] + np.arange(w)[None]) % bc.NFFT4].max(2)
    if curves:
        return S4, fs, C, Cp, Cc.real, Y
    return S4, fs, C


def s4_grid(r, k):
    """4th-power periodogram on bf.grid(k) (max over the FFT bins of each cell), normalised by its mean."""
    g = bf.grid(k)["f"]
    step = k * bc.STEP
    Y = np.abs(np.fft.fft(-(r ** 4), bc.NFFT4)) ** 2
    Y /= Y.mean(1, keepdims=True)
    nu = (4 * g) % 1.0
    w = int(np.ceil(4 * step * bc.NFFT4)) + 1
    b0 = np.floor((nu - 2 * step) * bc.NFFT4).astype(int)
    return Y[:, (b0[:, None] + np.arange(w)[None]) % bc.NFFT4].max(2)
