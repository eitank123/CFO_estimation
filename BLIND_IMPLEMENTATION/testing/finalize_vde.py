"""Finalize the VDE deliverables for the chosen final receiver (2026-11-18).
usage: py BLIND_IMPLEMENTATION/testing/finalize_vde.py onephase|tuned
Redraws the VDE plots for that receiver (overview, MACs vs SNR, MAC-cap BLER and MACs) and fills the placeholders of
testing/results/summary_fullsys_2026-11-18.md. The scratchpad plot scripts are passed by path (SCRATCH env var)."""
import json, os, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
choice = sys.argv[1]
pre = {"onephase": "fs-gv32om", "tuned": "fs-gv32km"}[choice]
SCR = os.environ["SCRATCH"]
env = {**os.environ, "VDE_FINAL": pre}
for cmd in (["py", "BLIND_IMPLEMENTATION/testing/plot_vde_final.py", pre], ["py", os.path.join(SCR, "macsnr.py")],
            ["py", os.path.join(SCR, "vdecap2.py")], ["py", os.path.join(SCR, "vdecapmac.py")]):
    r = subprocess.run(cmd, env=env, capture_output=True, text=True)
    print(" ".join(cmd[1:])[-60:], "rc", r.returncode, (r.stderr or "")[-200:])
R = "fullsys/results/blind_fs_"
m = {pt: json.load(open(R + pre + pt[1:] + ".json"))["points"][0] for pt in ("m50", "m46")}
mac = [m[p]["sum_c_hd4a"] / m[p]["frames"] / 1e6 for p in ("m50", "m46")]
cap = json.load(open(f"fullsys/results/capcurve_vde32_{pre}.json"))
worst = max(v["max"] for v in cap["None"].values())
lab = ("jointly tuned + one phase guess" if choice == "onephase" else "jointly tuned")
sent = {"onephase": "jointly tuned (batch null on 32 cores, final 4, win 4.0, shortlist 99.7 %/4) plus ONE phase guess "
                    "instead of two: same BLER (paired fresh packets), mean MACs per core 5.88 -> 2.05 M at -6.6 dB and "
                    f"0.42 -> 0.21 M at -4.6 dB (-50 ... -65 %), worst case 8.4 -> {worst:.1f} M.",
        "tuned": "jointly tuned (batch null on 32 cores, final 4, win 4.0, shortlist 99.7 %/4): same BLER (paired fresh "
                 "packets), mean MACs per core 5.88 -> 2.20 M at -6.6 dB and 0.42 -> 0.31 M at -4.6 dB (-26 ... -63 %), "
                 f"worst case 8.4 -> {worst:.1f} M."}[choice]
p = "BLIND_IMPLEMENTATION/testing/results/summary_fullsys_2026-11-18.md"
s = open(p, encoding="utf-8").read()
s = s.replace("VDE_FINAL_MACS", f"{min(mac):.2f}-{max(mac):.2f}").replace("VDE_FINAL_RATIO", f"~{sum(mac) / 2 / 0.028:.0f}x")
s = s.replace("VDE_FINAL_SENTENCE", sent).replace("VDE_FINAL_WORST", f"{worst:.1f}")
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("summary filled for", lab, "| MACs at -5.0 / -4.6 dB:", [round(x, 3) for x in mac], "| worst", round(worst, 2))
