"""Two-pass replay (2026-11-17, VDE MAC cuts): receiver A on every packet; only the packets A rejects ("no packet":
CRC / re-encoding check failed, known at the receiver) are re-received from scratch by receiver B (e.g. A = no NN,
B = the VDE-trained checkpoint NN). Exact offline from two PAIRED runs with --dump (same seed / --calib / frames /
batch): both receivers are deterministic per packet, so B's per-packet result and cost are the ones B would give in the
second pass. A packet A accepts wrongly stays wrong (undetected; B never sees it). Cost per packet = A + (B if A
rejected), per core in the profile's standard model (c_hd4a at 0.15, c_d4a at 2/5, 1/2).

usage: py fullsys/two_pass_replay.py --a fs-cv32am54 fs-cv32am50 ... --b fs-ztv32k0m54 ... [--model c_hd4a] --name X
writes fullsys/results/twopass_<name>.json; prints per Es/N0: n, errors and mean / max MACs per core of A, B, A->B."""
import argparse, glob, json, os
import numpy as np

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")


def load(parts, model):
    """{(esn0, chunk tag, pk): (passed, right, cost, f)} over the parts' dump folders."""
    D = {}
    for part in parts:
        fs = sorted(glob.glob(os.path.join(R, f"blind_fs_{part}_dump", "pk_*.npz")))
        assert fs, f"no dump for {part}"
        for fn in fs:
            z = np.load(fn)
            tag = os.path.basename(fn)[3:-4]
            for i in range(len(z["pk"])):
                D[(tag, int(z["pk"][i]))] = (bool(z["passed"][i]), bool(z["right"][i]), float(z[model][i]),
                                             float(z["f"][i]), float(z["esn0"]))
    return D


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", nargs="+", required=True)
    ap.add_argument("--b", nargs="+", required=True)
    ap.add_argument("--model", default="c_hd4a")
    ap.add_argument("--name", required=True)
    o = ap.parse_args()
    A, B = load(o.a, o.model), load(o.b, o.model)
    keys = sorted(set(A) & set(B))
    assert keys, "no common packets (not paired?)"
    bad = sum(abs(A[k][3] - B[k][3]) > 1e-6 for k in keys)
    assert bad == 0, f"{bad} packets with different true CFO: runs are not paired"
    out = {}
    for e in sorted(set(A[k][4] for k in keys)):
        ks = [k for k in keys if A[k][4] == e]
        a = np.array([A[k][:3] for k in ks]); b = np.array([B[k][:3] for k in ks])
        rej = a[:, 0] == 0                                     # A said "no packet"
        r2 = np.where(rej, b[:, 1], a[:, 1]).astype(bool)
        c2 = a[:, 2] + np.where(rej, b[:, 2], 0.0)
        row = dict(esn0=e, n=len(ks), A_rej=int(rej.sum()),
                   err_A=int((a[:, 1] == 0).sum()), err_B=int((b[:, 1] == 0).sum()), err_2p=int((~r2).sum()),
                   mean_A=float(a[:, 2].mean()), mean_B=float(b[:, 2].mean()), mean_2p=float(c2.mean()),
                   max_A=float(a[:, 2].max()), max_B=float(b[:, 2].max()), max_2p=float(c2.max()))
        out[str(e)] = row
        print(f"Es/N0 {e:+.1f}: n {row['n']}, A rejects {row['A_rej']}; errors A {row['err_A']} / B {row['err_B']} / "
              f"A->B {row['err_2p']}; mean MACs/core A {row['mean_A']/1e6:.3f} / B {row['mean_B']/1e6:.3f} / "
              f"A->B {row['mean_2p']/1e6:.3f} M; max {row['max_A']/1e6:.2f} / {row['max_B']/1e6:.2f} / {row['max_2p']/1e6:.2f} M")
    json.dump(dict(a=o.a, b=o.b, model=o.model, points=out), open(os.path.join(R, f"twopass_{o.name}.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
