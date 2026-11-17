"""FINAL full-system plots (2026-11-17): blind on its final receiver (tuned F5 where adopted + per-format retrained
checkpoint NN) vs DVB-RCS2 with its own DA CFO estimate, per waveform ID. Pools every final run (fs-g*/fs-h*) per Es/N0.
Figure 1 (fs_final_id<k>.png): BLER vs Eb/N0 (known symbols charged / free), BLER vs SNR, MACs vs Eb/N0 / SNR.
Figure 2 (fs_final_capped.png): BLER vs Eb/N0 with per-packet MAC caps (packets needing more = errors), from the dumps.
MACs per core: 32-core scheduled model (provisional: NN free-information accounting fix pending)."""
import glob, json, os, sys
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT); sys.path.insert(0, "fullsys"); sys.argv = sys.argv[:1]
import tune_blind_fs as tb
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt, matplotlib.ticker
R, P = "fullsys/results/", "BLIND_IMPLEMENTATION/testing/results/plots/"
CD, CB = "#eb6834", "#1f9e6e"
IDS = {"id13": ("ID 13", "QPSK, R 1/3, 1616 sym", 140, 2.298, 1.904, ["da_fs-q13da.json"], ["fs-g13", "fs-h13"], [2.0, 5.0]),
       "id42b": ("ID 42", "pi/2-BPSK, R 1/3, 3236 sym", 284, 5.311, 4.915, ["da_fs-q42td.json"], ["fs-g42", "fs-h42"], [0.2, 0.5]),
       "id3": ("ID 3", "QPSK, R 1/3, 536 sym", 80, 2.95, 2.24, ["da_fs-q3td.json", "da_fs-q3deep.json"], ["fs-g3"], [1.0, 2.0]),
       "id14s": ("ID 14", "QPSK, R 1/2, 1616 sym", 112, 0.41, 0.09, ["da_fs-q14td.json"], ["fs-g14", "fs-h14"], [2.0, 10.0])}
CA = {}                                             # honest-accounting (--charge-all) MACs per (fmt prefix, Es/N0)
def blind_points(prefixes):
    B, parts = {}, []
    for pre in prefixes:
        for fn in glob.glob(f"{R}blind_fs_{pre}*.json"):
            part = fn.split("blind_fs_")[1][:-5]
            if part.endswith("smoke") or "_dump" in fn: continue
            ca = part.endswith("ca")
            if not ca: parts.append(part)
            for p in json.load(open(fn))["points"]:
                e = round(p["esn0"], 2)
                if ca:
                    c = CA.setdefault((prefixes[0], e), [0, 0.0]); c[0] += p["frames"]; c[1] += p["sum_c_d4a"]; continue
                r = B.setdefault(e, [0, 0, 0.0]); r[0] += p["frames"]; r[1] += p["frame_err"]; r[2] += p["sum_c_d4a"]
    for e, r in B.items():                          # MACs: honest rerun where available, else original (flagged)
        c = CA.get((prefixes[0], e)); r.append(c is not None)
        if c is not None: r[2] = c[1] / c[0] * r[0]
    return B, sorted(parts)
def da_points(files):
    out = []
    for fn in files:
        if not os.path.exists(R + fn): continue
        for p in json.load(open(R + fn))["points"]:
            out.append((p["esn0"], p["frame_err"], p["frames"], p["crit_mean"] / 1e6))
    return sorted(out)
summary = {}
for fmt, (nm, desc, known, OT, OP, das, pre, caps) in IDS.items():
    B, parts = blind_points(pre); D = da_points(das)
    be = sorted(B); bp = [B[e][1] / B[e][0] for e in be]; bm = [B[e][2] / B[e][0] / 1e6 for e in be]
    de = [d[0] for d in D]; dp = [d[1] / d[2] for d in D]; dm = [d[3] for d in D]
    summary[fmt] = dict(blind=[dict(esn0=e, frames=B[e][0], err=B[e][1], mean_macs_core=B[e][2] / B[e][0]) for e in be],
                        dvb=[dict(esn0=d[0], err=d[1], frames=d[2], mean_macs_core=d[3] * 1e6) for d in D], parts=parts)
    LD = f"DVB-RCS2 {nm}: {known} known symbols, own DA CFO estimate (+-0.03), turbo 8 it."
    LB = "BLIND final: no known symbols, polar GA CA-SCL-8, retrained checkpoint NN" + (", tuned F5" if fmt != "id3" else "")
    f, ax = plt.subplots(2, 3, figsize=(17, 9.5))
    def bl(a, xd, xb, xl, t):
        m1 = np.array(dp) > 0; m2 = np.array(bp) > 0
        a.semilogy(np.array(xd)[m1], np.array(dp)[m1], "-o", color=CD, lw=2, ms=6, label=LD)
        a.semilogy(np.array(xb)[m2], np.array(bp)[m2], "-s", color=CB, lw=2, ms=6, label=LB)
        a.set_xlabel(xl); a.set_ylabel("BLER"); a.set_ylim(1e-6, 1); a.set_title(t, fontsize=10); a.grid(True, which="both", ls=":", color="#c3c2b7")
    KEY = [(max(bm), CB), (min(bm), CB), (max(dm), CD), (min(dm), CD)]
    def mc(a, xd, xb, xl, t):
        a.plot(xd, dm, "-o", color=CD, lw=2, label=LD); a.plot(xb, bm, "-", color=CB, lw=2, label=LB); a.set_yscale("log")
        hon = np.array([B[e][3] or fmt == "id14s" for e in be])
        a.plot(np.array(xb)[hon], np.array(bm)[hon], "s", color=CB, ms=6); a.plot(np.array(xb)[~hon], np.array(bm)[~hon], "s", mfc="white", mec=CB, ms=6)
        for v, c in KEY: a.axhline(v, color=c, lw=0.7, ls="--", alpha=0.45)
        tk = sorted(set(round(v, 4) for v, _ in KEY)); a.set_yticks(tk); a.set_yticklabels([f"{v:.3g}" for v in tk], fontsize=8)
        a.yaxis.set_minor_locator(matplotlib.ticker.NullLocator()); a.set_ylim(min(tk) / 1.5, max(tk) * 1.5)
        for xs, ys, c, dy in ((xd, dm, CD, -11), (xb, bm, CB, 5)):
            for x, v in zip(xs, ys): a.annotate(f"{v:.3g}", (x, v), textcoords="offset points", xytext=(4, dy), fontsize=7, color=c)
        a.set_xlabel(xl); a.set_ylabel("MACs per core per packet [M] (mean)"); a.set_title(t, fontsize=10); a.grid(True, ls=":", color="#c3c2b7")
    T = f"{nm} ({desc})"
    bl(ax[0, 0], np.array(de) + OT, np.array(be) + OP, "Eb/N0 per payload bit [dB] (known symbols charged)", f"BLER vs Eb/N0, {T}, pilot energy charged")
    bl(ax[0, 1], np.array(de) + OP, np.array(be) + OP, "Eb/N0 per payload bit [dB] (known symbols free)", f"BLER vs Eb/N0, {T}, pilots free")
    bl(ax[0, 2], de, be, "SNR (Es/N0) [dB]", f"BLER vs SNR, {T}")
    mc(ax[1, 0], np.array(de) + OT, np.array(be) + OP, "Eb/N0 per payload bit [dB] (known symbols charged)", f"MACs vs Eb/N0, {T}")
    mc(ax[1, 1], de, be, "SNR (Es/N0) [dB]", f"MACs vs SNR, {T}")
    ax[1, 2].axis("off"); h, l = ax[0, 0].get_legend_handles_labels(); ax[1, 2].legend(h, l, loc="center", frameon=False, fontsize=9.5)
    zero = [f"{e:+.1f} dB 0/{B[e][0]}" for e in be if B[e][1] == 0]
    ax[1, 2].text(0.02, 0.1, ("Blind points with 0 errors (not plotted): " + ", ".join(zero) + "\n" if zero else "") +
                  "MACs per core: 32-core scheduled model; filled = honest accounting (--charge-all), hollow = not yet rerun;\nDVB-RCS2 at 8 turbo iterations (+ up to 3 CFO candidates).", fontsize=8.5, transform=ax[1, 2].transAxes)
    f.tight_layout(); f.savefig(f"{P}DVB-RCS2/overview/fs_final_{fmt}.png", dpi=105, bbox_inches="tight"); plt.close(f)
# capped
f, ax = plt.subplots(2, 2, figsize=(15, 10.5))
for a, (fmt, (nm, desc, known, OT, OP, das, pre, caps)) in zip(ax.flat, IDS.items()):
    parts = summary[fmt]["parts"]
    L = []
    for p in parts:
        if not os.path.isdir(f"{R}blind_fs_{p}_dump"): continue
        try: L.append(tb.load_part(p))
        except Exception as e: print("skip dump", p, str(e)[-80:])
    S = tb.Set(L); r, cd, _ = S.evaluate(); cd = cd / 1e6
    for c, col in ((None, CB), (caps[1], "#4a90d9"), (caps[0], "#7b3fb5")):
        xs, ys = [], []
        for e in sorted(set(k[1] for k in S.pt_key)):
            m = np.isin(S.pt, [i for i, k in enumerate(S.pt_key) if k[1] == e]); n = int(m.sum())
            ok = r[m] if c is None else (r[m] & (cd[m] <= c)); err = n - int(ok.sum())
            if err: xs.append(e + OP); ys.append(err / n)
        a.semilogy(xs, ys, "-s", color=col, lw=2, ms=5, label="BLIND final, no cap" if c is None else f"BLIND final, cap {c:g} M per core")
    D = da_points(das); a.semilogy([d[0] + OT for d in D if d[1]], [d[1] / d[2] for d in D if d[1]], "-o", color=CD, lw=2, ms=5, label="DVB-RCS2 (own DA CFO estimate)")
    a.set_xlabel("Eb/N0 per payload bit [dB] (known symbols charged)"); a.set_ylabel("BLER"); a.set_ylim(1e-6, 1)
    a.set_title(f"{nm} ({desc}): BLER vs Eb/N0 with and without a per-packet MAC cap", fontsize=9.5)
    a.grid(True, which="both", ls=":", color="#c3c2b7"); a.legend(fontsize=7.5, loc="lower left")
f.tight_layout(); f.savefig(f"{P}DVB-RCS2/BLER/fs_final_capped.png", dpi=105, bbox_inches="tight")
json.dump(summary, open(f"{R}fs_final_summary.json", "w"), indent=1)
for fmt, s in summary.items():
    print(fmt, [(b["esn0"], b["err"], b["frames"], round(b["mean_macs_core"] / 1e6, 3)) for b in s["blind"]])
