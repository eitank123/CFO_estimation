"""Aggregate the results used by the slides from a checkout of full-chain-cfo (c90c5b7).

Usage: python slides_eq/aggregate_results.py <full-chain-cfo checkout> <out.json>
Blind: merged blind_ber.json counts and blind_ber_* parts (MACs, per-core histograms ph_/pg_);
pilot reference: est3 bler_*.json, MACs from est3/plots.pilot_macs (4 decodes at once).
The cap rows (cap_snr.json, presentation arm) are added to slides_eq/data/results_c90c5b7.json separately.
"""
import sys, os, json, glob
import numpy as np
W = sys.argv[1]; sys.path.insert(0, W); sys.path.insert(0, os.path.join(W, "est3")); os.chdir(W)
import importlib.util
spec = importlib.util.spec_from_file_location("e3plots", os.path.join(W, "est3", "plots.py"))
P = importlib.util.module_from_spec(spec); spec.loader.exec_module(P)
RATES = ("1/10", "2/5", "1/2")
out = {}
rows = P.bler_rows()
print(sorted(set(r["src"] for r in rows)))
for rate in RATES:
    o = out[rate] = {}
    o["blind_bler"] = P.blind_bler(rate)
    # merged blind counts from blind_ber.json: frames, errors
    bj = json.load(open(P.BLIND_JSON))
    o["blind_cnt"] = sorted((x["snr"], x["frame_err"], x["frames"], x.get("undetected", 0)) for x in bj if x["rate"] == rate and x["rx"] == P.BLIND_RX[rate])
    for src in ("ML direct PM+all", "ML direct"):
        o[src] = sorted((r["snr"], r["frame_err"], r["frames"], r["extra_decodes_per_frame"], r["metric_evals"] / r["frames"],
                         (r["metric_rounds"] / r["frames"]) if r.get("metric_rounds") else None) for r in rows if r["rate"] == rate and r["src"] == src)
        mac = []
        for s, e, n, x, me, mr in o[src]:
            t, c = P.pilot_macs(rate, src, x, m_evals=me if "PM" in src else 0.0, m_rounds=mr if "PM" in src else None)
            mac.append((s, t, c))
        o[src + " macs"] = mac
    bl, hist = {}, {}
    for r in P.blind_parts(rate, "crit_par_macs"):
        a = bl.setdefault(r["snr"], [0.0, 0.0, 0.0])
        a[0] += r["mac_frames"]; a[1] += r["macs"]; a[2] += r["crit_par_macs"]
        if any(k.startswith("ph_") for k in r):
            h = hist.setdefault(r["snr"], [0, np.zeros(100), np.zeros(100), 0])
            h[0] += r["frames"]; h[3] += r["frame_err"]
            for b in range(100):
                h[1][b] += r.get(f"ph_{b:02d}", 0); h[2][b] += r.get(f"pg_{b:02d}", 0)
    o["blind_macs"] = sorted((s, v[1] / v[0], v[2] / v[0], v[0]) for s, v in bl.items())
    o["hist"] = {str(s): dict(n=v[0], err=v[3], ph=v[1].tolist(), pg=v[2].tolist(), crit_mean=bl[s][2] / bl[s][0]) for s, v in hist.items()}
json.dump(out, open(sys.argv[2], "w"))
for rate in RATES:
    print(rate, "blind", out[rate]["blind_cnt"])
    print("  ML PM+all", [(a, b, c) for a, b, c, *_ in out[rate]["ML direct PM+all"]])
    print("  macs blind", [(s, round(t/1e6, 2), round(c/1e6, 3), int(n)) for s, t, c, n in out[rate]["blind_macs"]])
    print("  macs ML PM+all", [(s, round(t/1e6, 2), round(c/1e6, 3)) for s, t, c in out[rate]["ML direct PM+all macs"]])
    print("  hist snrs", {k: (v["n"], sum(v["ph"])) for k, v in out[rate]["hist"].items()})
