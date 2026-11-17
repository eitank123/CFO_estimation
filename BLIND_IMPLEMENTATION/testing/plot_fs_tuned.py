"""DVB-RCS2 jointly tuned blind vs before tuning vs DVB-RCS2 (2026-11-18). Per waveform ID: BLER vs Eb/N0 (known
symbols charged), BLER vs SNR, MACs per core vs Eb/N0 and vs SNR. Blind parts: final runs fs-g<ID>* / fs-h<ID>* on the
fresh seeds 70xx / 71xx; "before tuning" = the parts without the jt suffix (MACs from the honest --charge-all "ca"
reruns where they exist), "jointly tuned" = the "jt" reruns (same seeds, --charge-all, the tuned --sps). Worst case per
packet as a footnote (no worst-case lines, user 2026-11-18). Output plots/DVB-RCS2/overview/fs_tuned_<fmt>.png."""
import glob, json, os
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
R, P = "fullsys/results/", "BLIND_IMPLEMENTATION/testing/results/plots/DVB-RCS2/overview/"
CD, C0, C1 = "#eb6834", "#8fcfb4", "#1f9e6e"
IDS = {"id13": ("ID 13", "QPSK, R 1/3, 1616 sym", 2.298, 1.904, ["da_fs-q13da.json"], ["fs-g13", "fs-h13"],
                '{"final": 16, "win": 4.5, "ck_keep": 0.003, "ck_min": 8}'),
       "id42b": ("ID 42", "pi/2-BPSK, R 1/3, 3236 sym", 5.311, 4.915, ["da_fs-q42td.json"], ["fs-g42", "fs-h42"],
                 '{"final": 8, "win": 4.0, "ck_keep": 0.003, "ck_min": 8}'),
       "id3": ("ID 3", "QPSK, R 1/3, 536 sym", 2.95, 2.24, ["da_fs-q3td.json", "da_fs-q3deep.json"], ["fs-g3"],
               '{"final": 8, "win": 4.5}'),
       "id14s": ("ID 14", "QPSK, R 1/2, 1616 sym", 0.41, 0.09, ["da_fs-q14td.json"], ["fs-g14", "fs-h14"],
                 '{"final": 8, "win": 4.0, "ck_keep": 0.01, "ck_min": 4}')}


def pool(prefixes, kind):
    """kind 'jt': the jointly tuned reruns; 'old': BLER from the plain parts, MACs from the 'ca' reruns if any."""
    B, CA = {}, {}
    for pre in prefixes:
        for fn in glob.glob(f"{R}blind_fs_{pre}*.json"):
            part = os.path.basename(fn)[9:-5]
            if part.endswith("smoke") or not part[len(pre):len(pre) + 1] in "mp":
                continue                                   # fs-g13... but not fs-g13x...
            jt, ca = part.endswith("jt"), part.endswith("ca")
            if (kind == "jt") != jt:
                continue
            for q in json.load(open(fn))["points"]:
                e = round(q["esn0"], 2)
                if ca:
                    c = CA.setdefault(e, [0, 0.0, 0.0]); c[0] += q["frames"]; c[1] += q["sum_c_d4a"]; c[2] = max(c[2], q["max_c_d4a"])
                    continue
                r = B.setdefault(e, [0, 0, 0.0, 0.0]); r[0] += q["frames"]; r[1] += q["frame_err"]
                r[2] += q["sum_c_d4a"]; r[3] = max(r[3], q["max_c_d4a"])
    e = sorted(B)
    m = [CA[x][1] / CA[x][0] if x in CA else B[x][2] / B[x][0] for x in e]
    mx = [CA[x][2] if x in CA else B[x][3] for x in e]
    return dict(es=np.array(e), n=[B[x][0] for x in e], err=[B[x][1] for x in e],
                p=np.array([B[x][1] / B[x][0] if B[x][1] else np.nan for x in e]), m=np.array(m) / 1e6, mx=np.array(mx) / 1e6)


def da(files):
    o = []
    for fn in files:
        if os.path.exists(R + fn):
            o += [(q["esn0"], q["frame_err"], q["frames"], q["crit_mean"] / 1e6) for q in json.load(open(R + fn))["points"]]
    o.sort()
    return dict(es=np.array([x[0] for x in o]), p=np.array([x[1] / x[2] if x[1] else np.nan for x in o]), m=np.array([x[3] for x in o]))


summary = {}
for fmt, (nm, desc, OT, OP, das, pre, sps) in IDS.items():
    b0, b1, D = pool(pre, "old"), pool(pre, "jt"), da(das)
    summary[fmt] = {k: dict(es=v["es"].tolist(), err=v["err"], n=v["n"], mean=v["m"].tolist(), max=v["mx"].tolist())
                    for k, v in (("before", b0), ("tuned", b1))}
    L = dict(D=f"DVB-RCS2 {nm}", b0="Blind, before tuning", b1="Blind, jointly tuned")
    f, ax = plt.subplots(2, 2, figsize=(15, 10))
    for a, xs, xl in ((ax[0, 0], (OT, OP), "Eb/N0 per payload bit [dB] (known symbols charged)"), (ax[0, 1], (0, 0), "SNR (Es/N0) [dB]")):
        a.semilogy(D["es"] + xs[0], D["p"], "-o", color=CD, lw=2, ms=5, label=L["D"])
        a.semilogy(b0["es"] + xs[1], b0["p"], "--s", color=C0, lw=1.5, ms=5, label=L["b0"])
        if len(b1["es"]):
            a.semilogy(b1["es"] + xs[1], b1["p"], "-D", color=C1, lw=2, ms=6, label=L["b1"])
        a.set_xlabel(xl); a.set_ylabel("BLER"); a.set_ylim(1e-6, 1); a.grid(True, which="both", ls=":", color="#c3c2b7"); a.legend(fontsize=7.5, loc="lower left")
    for a, xs, xl in ((ax[1, 0], (OT, OP), "Eb/N0 per payload bit [dB] (known symbols charged)"), (ax[1, 1], (0, 0), "SNR (Es/N0) [dB]")):
        a.semilogy(D["es"] + xs[0], D["m"], "-o", color=CD, lw=2, ms=5, label=L["D"])
        a.semilogy(b0["es"] + xs[1], b0["m"], "--s", color=C0, lw=1.5, ms=5, label=L["b0"])
        if len(b1["es"]):
            a.semilogy(b1["es"] + xs[1], b1["m"], "-D", color=C1, lw=2, ms=6, label=L["b1"])
            for x, v in zip(b1["es"] + xs[1], b1["m"]): a.annotate(f"{v:.3g}", (x, v), textcoords="offset points", xytext=(4, 4), fontsize=7, color=C1)
        for x, v in zip(D["es"] + xs[0], D["m"]): a.annotate(f"{v:.3g}", (x, v), textcoords="offset points", xytext=(4, -11), fontsize=7, color=CD)
        a.set_xlabel(xl); a.set_ylabel("MACs per core per packet [M] (mean)"); a.grid(True, which="both", ls=":", color="#c3c2b7"); a.legend(fontsize=7.5)
    T = f"{nm} ({desc})"
    ax[0, 0].set_title(f"{nm}: BLER vs Eb/N0", fontsize=10); ax[0, 1].set_title(f"{nm}: BLER vs SNR", fontsize=10)
    ax[1, 0].set_title(f"{nm}: MACs per core vs Eb/N0", fontsize=10); ax[1, 1].set_title(f"{nm}: MACs per core vs SNR", fontsize=10)
    wc = lambda b: ", ".join(f"{e:+.1f} dB {m:.2g} M" for e, m in zip(b["es"], b["mx"]))
    f.text(0.01, -0.045, f"{T}. DVB-RCS2: own data-aided CFO estimate, turbo max-log 8 it. Blind tuned: {sps}. Eb/N0 with known symbols charged.\nWorst case per packet (max MACs per core over packets), jointly tuned: {wc(b1)}\nbefore tuning: {wc(b0)}",
           fontsize=7.5)
    f.tight_layout(); f.savefig(f"{P}fs_tuned_{fmt}.png", dpi=105, bbox_inches="tight"); plt.close(f)
json.dump(summary, open(f"{R}fs_tuned_summary.json", "w"), indent=1)
for fmt, s in summary.items():
    for k in ("before", "tuned"):
        print(fmt, k, [(e, er, n, round(m, 3)) for e, er, n, m in zip(s[k]["es"], s[k]["err"], s[k]["n"], s[k]["mean"])])
