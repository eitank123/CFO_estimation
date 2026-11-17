"""
Baseline identity of the blind-receiver format hooks (fullsys/blind_fmt.py, small_rx nopi / bpsk_sq / ck_useful /
stage_acc, polar fz_mask, bc.FMT, bf.premf): the CURRENT receiver without a format context must equal the git HEAD
receiver bit for bit (decoded data, CRC passes, CFO estimates, every st counter incl. the MAC counts).

    py fullsys/selftest_blind_fs.py --extract     # LOCAL, git only (no receiver code): HEAD sources -> fullsys/_head/
    python fullsys/selftest_blind_fs.py           # cluster job fs-blbase: both probes, compare

The probes run in two subprocesses with BLIND_STUDY=small_cfo: HEAD (sys.path = fullsys/_head first: polar, blind_cfo,
blind_fast, blind_vp, small_rx, blind_ber, fastscl as committed) and current. Each runs small_rx.small_receive on fixed
seeds: R = 1/10 testing_s11g at +1 dB (fast path) and -3 dB (search, spec11), R = 1/2 base2_qfix_fzs at 3 dB and
1.5 dB (search, joint list, F5 fz_stop), a few packets each. The current probe then enters and leaves a BlindFormat
context (id13, its caches built) and repeats the first point: the globals must be restored (same result).
"""

import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HEAD_DIR = os.path.join(ROOT, "fullsys", "_head")
FILES = ("polar.py", "blind_cfo.py", "blind_fast.py", "blind_vp.py", "small_rx.py", "blind_ber.py", "fastscl.py")
POINTS = (("1/10", "testing_s11g", 1.0, 3), ("1/10", "testing_s11g", -3.0, 2), ("1/2", "base2_qfix_fzs", 3.0, 3),
          ("1/2", "base2_qfix_fzs", 1.5, 2))


def extract():
    """git show HEAD:<file> -> fullsys/_head/<file> (no code executed)."""
    os.makedirs(HEAD_DIR, exist_ok=True)
    rev = subprocess.run(["git", "-C", ROOT, "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout
    for f in FILES:
        src = subprocess.run(["git", "-C", ROOT, "show", f"HEAD:{f}"], capture_output=True, text=True,
                             check=True).stdout
        with open(os.path.join(HEAD_DIR, f), "w", newline="\n") as fh:
            fh.write(src)
    with open(os.path.join(HEAD_DIR, "HEAD_REV"), "w", newline="\n") as fh:
        fh.write(rev)
    print(f"extracted {len(FILES)} files of HEAD {rev.strip()} -> {HEAD_DIR}")


def _point(pt, idx):
    import numpy as np
    import blind_ber as bb
    import blind_cfo as bc
    import small_rx
    from polar import PolarCode
    tr = sys.modules["bl_testing_run"]
    rate, key, snr, B = pt
    base, flags = tr.VARIANTS[key]
    A = bc.CODES[rate]
    rng = np.random.default_rng(1234 + idx)
    code = PolarCode(bc.N_BITS, A, 16, 8)
    pi = bc.PiCode(bc.N_BITS, A, 16, 8)
    data, cw, r, rx, f, th = bc.frames(B, code, snr, rng)
    spec = {"sps": {**bb.RX[tr.BASE[base]]["sps"], **flags, "rate": rate, "truth": data, "truth_f": f,
                    "truth_th": th}}
    st = dict(decodes=0, metric_evals=0)
    out, ok, ff, f0 = small_rx.small_receive(r, rx, snr, pi, 1.0 / (2.0 * 10 ** (snr / 10)), st, spec)
    return dict(out=out.tolist(), ok=ok.tolist(), f_fin=[repr(float(x)) for x in ff], f0=[repr(float(x)) for x in f0],
                st={k: repr(v) for k, v in sorted(st.items()) if not isinstance(v, list)})


def probe(which):
    """One side: import the modules (HEAD shadowing first on sys.path), run POINTS, print JSON."""
    import importlib.util
    if which == "head":
        sys.path.insert(0, HEAD_DIR)
    sys.path.insert(1 if which == "head" else 0, ROOT)
    import polar, blind_cfo, blind_fast, blind_vp, small_rx, blind_ber, fastscl   # noqa: E401,F401
    for m in (polar, blind_cfo, blind_fast, blind_vp, small_rx, blind_ber, fastscl):
        want = HEAD_DIR if which == "head" else ROOT
        assert os.path.dirname(os.path.abspath(m.__file__)) == want, (which, m.__name__, m.__file__)
    sp = importlib.util.spec_from_file_location("bl_testing_run", os.path.join(ROOT, "BLIND_IMPLEMENTATION", "testing",
                                                                                "run.py"))
    tr = importlib.util.module_from_spec(sp)
    sys.modules["bl_testing_run"] = tr
    sp.loader.exec_module(tr)
    res = {f"{i}": _point(pt, i) for i, pt in enumerate(POINTS)}
    if which == "cur":                                  # a format context in and out, then the first point again
        from fullsys.blind_fmt import BlindFormat
        import blind_cfo as bc
        F = BlindFormat("id13", 952, 2952, "qpsk")
        with F:
            blind_fast.fast_sc(952)
            blind_fast.grid(2)
            assert bc.N_BITS == 4096 and bc.FMT is F
        assert bc.FMT is None and bc.N_BITS == 2048 and bc.N_SYM == 1024
        res["restore"] = _point(POINTS[0], 0)
    print("PROBE_JSON " + json.dumps(res))


def compare():
    t0 = time.time()
    assert os.path.exists(os.path.join(HEAD_DIR, "small_rx.py")), "run --extract locally first (and push fullsys/_head)"
    env = {**os.environ, "BLIND_STUDY": "small_cfo", "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1",
           "OPENBLAS_NUM_THREADS": "1"}
    out = {}
    for w in ("head", "cur"):
        p = subprocess.run([sys.executable, os.path.abspath(__file__), "--probe", w], capture_output=True, text=True,
                           env=env, cwd=ROOT)
        line = [x for x in p.stdout.splitlines() if x.startswith("PROBE_JSON ")]
        if p.returncode or not line:
            print(p.stdout[-3000:], p.stderr[-3000:])
            sys.exit(f"FAILED: probe {w} (exit {p.returncode})")
        out[w] = json.loads(line[0][len("PROBE_JSON "):])
    fails = 0
    for i, pt in enumerate(POINTS):
        h, c = out["head"][str(i)], out["cur"][str(i)]
        same = h == c
        diff = [k for k in h if h[k] != c.get(k)]
        stdiff = [k for k in set(h["st"]) | set(c["st"]) if h["st"].get(k) != c["st"].get(k)]
        print(f"  {'ok  ' if same else 'FAIL'} {pt}: passed {sum(h['ok'])}/{pt[3]}, macs {h['st'].get('macs')}, "
              f"crit_par_d4a {h['st'].get('crit_par_d4a_macs')}" + ("" if same else f" | differ: {diff} {stdiff[:12]}"))
        fails += not same
    same = out["cur"]["restore"] == out["cur"]["0"]
    print(f"  {'ok  ' if same else 'FAIL'} BlindFormat context entered / left: point 0 repeated identically")
    fails += not same
    print(f"{'PASS' if not fails else f'FAILED ({fails})'} in {time.time() - t0:.1f} s (HEAD "
          f"{open(os.path.join(HEAD_DIR, 'HEAD_REV')).read().strip()})")
    return 1 if fails else 0


if __name__ == "__main__":
    if "--extract" in sys.argv:
        extract()
    elif "--probe" in sys.argv:
        probe(sys.argv[sys.argv.index("--probe") + 1])
    else:
        sys.exit(compare())
