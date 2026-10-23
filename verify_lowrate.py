"""Consistency and theory checks of the low-rate study (lowrate/results/polar_results_ebn0_chain.npy).

    py verify_lowrate.py            -> prints PASS / WARN / FAIL lines and writes lowrate/verification.txt

Checks:
  1. NN + CRC search vs NN alone, same frames (common random numbers): the search starts from the NN decision and
     only replaces frames whose CRC failed, so its BLER may not be higher (beyond 3 sigma) at any point.
  2. CRB source vs theory: BLER of an estimator with Gaussian error N(0, CRB) predicted from the measured
     BLER-vs-|CFO error| curve (results/polar_results_error_chain.npy, R = 1/10 at -5 and -4 dB).
  3. Every BLER curve falls with SNR (no rise beyond 3 sigma).
  4. Points copied from the main results (R = 1/10, 1/4, 1/2 Genie / NN / M&M) are unchanged.
  5. Required SNR (BLER < 1e-2): Genie <= CRB bound <= NN, M&M; NN + CRC search within 0.2 dB of the Genie.
"""
import os

import numpy as np

os.environ.setdefault("CFO_STUDY", "lowrate")
import paths  # noqa: E402
import polar_ber_experiment as p  # noqa: E402

lines = []


def report(status, msg):
    lines.append(f"{status:5s} {msg}")
    print(lines[-1], flush=True)


def sigma(b, n):
    return np.sqrt(max(b * (1 - b), 1 / n) / n)


res = list(np.load(paths.result("polar_results_ebn0_chain.npy"), allow_pickle=True))
get = {(r["code"], round(r["esn0"], 2), r["src"]): r for r in res}

# 1. search <= NN
worse, n_pts = [], 0
for (code, s, src), r in get.items():
    if src != p.SEARCH or (code, s, "SNR-aware NN") not in get:
        continue
    nn = get[(code, s, "SNR-aware NN")]
    n_pts += 1
    if r["bler"] > nn["bler"] + 3 * np.hypot(sigma(r["bler"], r["frames"]), sigma(nn["bler"], nn["frames"])):
        worse.append((code, s, r["bler"], nn["bler"]))
report("PASS" if not worse else "FAIL", f"NN + CRC search BLER <= NN BLER at all {n_pts} common points" +
       (f": violations {worse[:5]}" if worse else ""))

# 2. CRB source vs prediction from the BLER-vs-error curve
main_err = list(np.load(os.path.join(paths.ROOT, "results", "polar_results_error_chain.npy"), allow_pickle=True))
for s in (-5.0, -4.0):
    pts = sorted((r["src"], r["bler"]) for r in main_err if r["code"] == "R=0.1" and abs(r["esn0"] - s) < 0.02)
    e, b = np.array(pts).T
    z = np.random.default_rng(0).standard_normal(400000) * p.crb_std(s)
    pred = np.mean(np.interp(np.abs(z), e, b))           # BLER(|e|) linear between the measured error points
    m = get.get(("R=0.1", s, p.CRB_SRC))
    if m is None:
        report("WARN", f"CRB source at R=0.1, {s:g} dB not simulated")
        continue
    sd = sigma(m["bler"], m["frames"])
    ok = abs(m["bler"] - pred) < max(3 * sd, 0.15 * pred)
    report("PASS" if ok else "WARN", f"CRB source R=0.1, {s:g} dB: measured BLER {m['bler']:.3f} vs predicted "
           f"{pred:.3f} from the BLER-vs-CFO-error curve (sqrt CRB = {p.crb_std(s):.2e})")

# 3. monotone in SNR
rises = []
for code in {k[0] for k in get}:
    for src in p.SOURCES:
        x, y, n = p.bler_curve(res, code, src)
        for i in range(1, len(x)):
            if y[i] > y[i - 1] + 3 * np.hypot(sigma(y[i], n[i]), sigma(y[i - 1], n[i - 1])):
                rises.append((code, src[:12], x[i - 1], x[i], y[i - 1], y[i]))
report("PASS" if not rises else "WARN", f"BLER falls with SNR on every curve (3 sigma)" +
       (f"; rises: {rises[:6]}" if rises else ""))

# 4. copied points unchanged
main_res = {(r["code"], round(r["esn0"], 2), r["src"]): r
            for r in np.load(os.path.join(paths.ROOT, "results", "polar_results_ebn0_chain.npy"), allow_pickle=True)}
diff = [k for k, r in main_res.items() if k in get and (get[k]["bler"] != r["bler"] or get[k]["frames"] != r["frames"])]
report("PASS" if not diff else "FAIL", f"{len([k for k in main_res if k in get])} points copied from the main results "
       f"unchanged" + (f"; differ: {diff[:5]}" if diff else ""))

# 5. required-SNR ordering
bad = []
for code in sorted({k[0] for k in get}, key=p.rate):
    req = {}
    for src in p.SOURCES:
        x, y, _ = p.bler_curve(res, code, src)
        if len(x):
            req[src] = p.required_snr(x, y)
    g, c, s_ = req.get(p.GENIE), req.get(p.CRB_SRC), req.get(p.SEARCH)
    for est in ("SNR-aware NN", "M&M"):
        if c is not None and req.get(est) is not None and req[est] < c - 0.25:
            bad.append(f"{code}: {est} {req[est]:.2f} < CRB {c:.2f}")
    if g is not None and c is not None and c < g - 0.25:
        bad.append(f"{code}: CRB {c:.2f} < Genie {g:.2f}")
    if g is not None and s_ is not None and abs(s_ - g) > 0.2:
        bad.append(f"{code}: search {s_:.2f} vs Genie {g:.2f}")
report("PASS" if not bad else "WARN", "required SNR: Genie <= CRB bound <= NN, M&M; search within 0.2 dB of Genie"
       + (f"; {bad}" if bad else ""))

with open(os.path.join(paths.BASE, "verification.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")
print(f"{sum(l.startswith('PASS') for l in lines)} PASS, {sum(l.startswith('WARN') for l in lines)} WARN, "
      f"{sum(l.startswith('FAIL') for l in lines)} FAIL -> {os.path.join(paths.BASE, 'verification.txt')}")
