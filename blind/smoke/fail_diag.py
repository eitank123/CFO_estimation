"""Why do the packets fail? Runs a receiver on many packets and classifies every failure:
    false pass      CRC passed at a wrong CFO (undetected error)
    genie fails     the packet fails even at the true CFO (pre-MF genie): noise, nothing to gain from the CFO
    not reached     the true cell was never scored (search order / budget)
    z <= z0         scored, but its z-test statistic was below z0 (the list-1 metric missed it)
    crowded out     z > z0, but 2 other cells of its round had a higher z (only the top 2 are decoded)
    decoded, lost   the true cell (or its neighbour) was decoded (refined) but the CRC failed
and prints, per class, the posterior rank of the true cell and its z / metric rank.
    python blind/smoke/fail_diag.py --points 1/10:-5:60000 --rx "Pilots N3x8 + v3 eco7, default grid + CRC" """
import argparse
import json
import os
import sys
from multiprocessing import Pool

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import blind_cfo as bc
import blind_fast as bf
import blind_ber as bb
from polar import PolarCode


def run(job):
    rate, snr, nm, n, seed = job
    code = PolarCode(bc.N_BITS, bc.CODES[rate], 16, 8)
    pi_code = bc.PiCode(bc.N_BITS, bc.CODES[rate], 16, 8)
    sigma2 = 1.0 / (2.0 * 10 ** (snr / 10))
    rng = np.random.default_rng(seed)
    spec = {**bb.RX[nm]}
    spec["sps"] = {**spec["sps"], "rate": rate}
    rows = []
    for _ in range(n // 100):
        data, cw, r, rx, f, th = bc.frames(100, code, snr, rng)
        B = len(f)
        st = dict(decodes=0, metric_evals=0, truth=f,
                  diag={"prank": np.full(B, -1), "z": np.full(B, np.nan), "rnd": np.full(B, -1),
                        "zrank": np.full(B, -1), "Mrank": np.full(B, -1), "tried": np.zeros(B, bool),
                        "tried_nb": np.zeros(B, bool), "rho": np.full(B, np.nan),
                        "stage": np.full(B, -1), "ca": np.zeros(B, bool)})
        sym = ((1 - 2.0 * cw[:, 0::2]) + 1j * (1 - 2.0 * cw[:, 1::2])) / np.sqrt(2)
        args = (r, rx, snr, pi_code, sigma2, st, spec) + ((sym,) if spec["sps"].get("pilots") else ())
        dec, ok, ff, _ = bf.sps3_receive(*args)
        bad = (dec != data).any(1)
        if not bad.any():
            continue
        w = np.where(bad)[0]
        rc = bf.premf(r[w], rx[w], f[w])
        gd, gok, _ = code.decode(bc.llrs(rc, f[w], th[w], sigma2), return_info=True)
        g_bad = (gd != data[w]).any(1)
        D = st["diag"]
        rel = {}
        for i in w[ok[w]]:                                  # false passes: how does the decoded packet relate to the truth?
            def syms(d):
                c = pi_code.encode(d[None])[0][bc.INTERLEAVER]
                return ((1 - 2.0 * c[0::2]) + 1j * (1 - 2.0 * c[1::2])) / np.sqrt(2)
            sd, stru = syms(dec[i]), syms(data[i])
            q = np.round(np.angle(sd / stru) / (np.pi / 2)).astype(int) % 4     # decoded = truth x j^q, per symbol
            seg = q.reshape(8, -1)
            rc = bf.premf(r[i:i + 1], rx[i:i + 1], np.array([ff[i]]))[0]
            rho_at = lambda s, fh: float(np.abs(np.sum(rc * np.conj(s) * np.exp(-2j * np.pi * fh * bc.NC)))
                                          / np.sqrt(bc.N_SYM * np.sum(np.abs(rc) ** 2)))
            rel[i] = dict(bit_err=int((dec[i] != data[i]).sum()),
                          q_frac=[float(np.mean(q == k)) for k in range(4)],
                          q_seg=[int(np.bincount(s_, minlength=4).argmax()) for s_ in seg],
                          rho_dec=rho_at(sd, ff[i]), rho_true_at_fh=rho_at(stru, ff[i]),
                          # decoded vs the truth rotated by the residual CFO (a pi/2 "staircase" would give ~0.9)
                          c_stair=float(np.abs(np.sum(np.conj(sd) * stru * np.exp(2j * np.pi * (f[i] - ff[i]) * bc.NC)))
                                        / bc.N_SYM))
        for j, i in enumerate(w):
            rows.append(dict(passed=bool(ok[i]), ferr=float(abs(ff[i] - f[i])) if np.isfinite(ff[i]) else None,
                             genie_bad=bool(g_bad[j]), prank=int(D["prank"][i]), z=float(D["z"][i]),
                             rnd=int(D["rnd"][i]), zrank=int(D["zrank"][i]), Mrank=int(D["Mrank"][i]),
                             tried=bool(D["tried"][i]), tried_nb=bool(D["tried_nb"][i]),
                             rho=float(D["rho"][i]), stage=int(D["stage"][i]), ca=bool(D["ca"][i]),
                             rel=rel.get(i)))
    return rate, snr, nm, n, rows


def classify(x, z0=4.0):
    if x["passed"]:
        return "false pass"
    if x["genie_bad"]:
        return "genie fails"
    if x["tried"] or x["tried_nb"]:
        return "decoded, lost"
    if not np.isfinite(x["z"]):
        return "not reached"
    if x["z"] <= z0:
        return "z <= z0"
    return "crowded out"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--points", nargs="+", required=True)          # rate:snr:packets
    ap.add_argument("--rx", nargs="+", required=True)
    ap.add_argument("--chunks", type=int, default=16)
    ap.add_argument("--out", default="fail_diag")
    a = ap.parse_args()
    jobs = []
    for pt in a.points:
        rate, snr, n = pt.split(":")
        for nm in a.rx:
            for c in range(a.chunks):
                jobs.append((rate, float(snr), nm, int(n) // a.chunks, 7700 + c))
    agg = {}
    with Pool(16) as pool:
        for rate, snr, nm, n, rows in pool.imap_unordered(run, jobs):
            e = agg.setdefault((rate, snr, nm), {"n": 0, "rows": []})
            e["n"] += n
            e["rows"] += rows
    out = []
    for (rate, snr, nm), e in sorted(agg.items()):
        rows, n = e["rows"], e["n"]
        print(f"R={rate} {snr:+.1f} dB {nm}: {len(rows)} failures / {n} packets (BLER {len(rows) / n:.2e})", flush=True)
        cls = {}
        for x in rows:
            cls.setdefault(classify(x), []).append(x)
        for c in ("false pass", "genie fails", "not reached", "z <= z0", "crowded out", "decoded, lost"):
            xs = cls.get(c, [])
            if not xs:
                continue
            pr = np.array([x["prank"] for x in xs])
            zz = np.array([x["z"] for x in xs])
            line = f"    {c:14s} {len(xs):4d} ({len(xs) / len(rows):5.1%})  posterior rank median {np.median(pr):.0f}"
            if np.isfinite(zz).any():
                line += (f", z median {np.nanmedian(zz):.2f}, z rank median "
                         f"{np.median([x['zrank'] for x in xs if x['zrank'] >= 0] or [-1]):.0f}, metric rank median "
                         f"{np.median([x['Mrank'] for x in xs if x['Mrank'] >= 0] or [-1]):.0f}")
            if c == "false pass":
                line += f", |f error| median {np.median([x['ferr'] for x in xs]):.2e}"
                for x in xs:
                    line += (f"\n        f error {x['ferr']:.5f} rho {x['rho']:.3f} (min {bf.rho_min(snr):.3f}) stage "
                             f"{x['stage']} code-aided {x['ca']} posterior rank {x['prank']} | {x['rel']}")
            print(line, flush=True)
        out.append({"rate": rate, "snr": snr, "rx": nm, "packets": n, "failures": rows})
    json.dump(out, open(bc.path("results", f"{a.out}.json"), "w"), indent=1)
    print("SMOKE DONE", flush=True)
