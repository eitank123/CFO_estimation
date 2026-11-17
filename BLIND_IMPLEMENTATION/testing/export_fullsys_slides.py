"""Export the final full-system results (2026-11-18) into one JSON for the slide figures (slides_eq/plot_fullsys.py on
the slides branch). Reads fullsys/results: the DVB-RCS2 jointly tuned summary (fs_tuned_summary.json, plot_fs_tuned.py),
the DVB-RCS2 DA reference parts, the VDE blind parts (before tuning fs-gv32m*, final fs-gv32om*), the VDE-SAT reference
points and the VDE MAC-cap curve of the final receiver.
usage: py BLIND_IMPLEMENTATION/testing/export_fullsys_slides.py <out.json>"""
import glob, json, os, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
R = os.path.join(ROOT, "fullsys", "results")
out = {"commit": subprocess.run(["git", "-C", ROOT, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip(),
       "axis": "Eb/N0 per payload bit, known symbols charged; MACs = mean per core per packet (32-core model)"}
# DVB-RCS2
S = json.load(open(os.path.join(R, "fs_tuned_summary.json")))
OFF = {"id13": ("ID 13", "QPSK 1/3", 140, 2.298, 1.904, ["da_fs-q13da.json"]),
       "id42b": ("ID 42", "pi/2-BPSK 1/3", 284, 5.311, 4.915, ["da_fs-q42td.json"]),
       "id3": ("ID 3", "QPSK 1/3, short", 80, 2.95, 2.24, ["da_fs-q3td.json", "da_fs-q3deep.json"]),
       "id14s": ("ID 14", "QPSK 1/2", 112, 0.41, 0.09, ["da_fs-q14td.json"])}
out["dvb"] = {}
for fmt, (nm, desc, known, OT, OP, das) in OFF.items():
    D = []
    for fn in das:
        p = os.path.join(R, fn)
        if os.path.exists(p):
            D += [dict(es=q["esn0"], err=q["frame_err"], n=q["frames"], macs=q["crit_mean"]) for q in json.load(open(p))["points"]]
    D.sort(key=lambda d: d["es"])
    out["dvb"][fmt] = dict(name=nm, desc=desc, known=known, off_comp=OT, off_blind=OP, comp=D,
                           tuned=S[fmt]["tuned"], before=S[fmt]["before"])
# VDE-SAT


def pool(pat):
    B = {}
    for fn in glob.glob(os.path.join(R, f"blind_fs_{pat}*.json")):
        for q in json.load(open(fn))["points"]:
            r = B.setdefault(round(q["esn0"], 2), [0, 0, 0.0, 0.0]); r[0] += q["frames"]; r[1] += q["frame_err"]
            r[2] += q["sum_c_hd4a"]; r[3] = max(r[3], q["max_c_hd4a"])
    return [dict(es=e, n=B[e][0], err=B[e][1], macs=B[e][2] / B[e][0], max=B[e][3]) for e in sorted(B)]


vd_es = [-7.0, -6.5, -6.0, -5.5, -5.0, -4.5, -4.0]                     # VDE-SAT, own DA sync (plot_vde_final.py)
vd_p = [1.0, 119 / 150, 105 / 270, 104 / 1530, 100 / 19950, 63 / 300000, 7 / 300000]
vd_m = [.1965, .1664, .1019, .0459, .0291, .0250, .0222]
out["vde"] = dict(name="VDE-SAT Link 32", known=372, off_comp=7.68, off_blind=6.56,
                  comp=[dict(es=e, p=p, macs=m * 1e6) for e, p, m in zip(vd_es, vd_p, vd_m)],
                  before=pool("fs-gv32m"), final=pool("fs-gv32om"),
                  cap=json.load(open(os.path.join(R, "capcurve_vde32_fs-gv32om.json"))),
                  final_desc="VDE-trained NN, batch null (32 cores), final 4, win 4.0, shortlist 99.7 %/4, one phase guess")
json.dump(out, open(sys.argv[1], "w"), indent=1)
print("wrote", sys.argv[1], "commit", out["commit"])
