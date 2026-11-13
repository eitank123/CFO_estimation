"""Sum blind_ber_<part>.json rows per (rate, snr, rx) and print BLER (95 % CI), MACs, stages.
Usage (from the project root): py BLIND_IMPLEMENTATION/testing/agg_variants.py srch10 srch15 ...
"""
import json, collections, os, sys
from scipy.stats import beta
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "small_cfo", "blind", "results")
F = ["frames","frame_err","undetected","decodes","macs","mac_frames","crit_par_macs","macs_score","macs_fast","macs_dec","macs_par",
     "stage_1","stage_2","stage_3","stage_4","stage_5","stage_frames","crc_pass_wrong","check_caught","check_lost","n_dd","se_final","time","timed_frames",
     "crit_par_h_macs","spec_decodes","spec_pass","par_frames"]
def cp(k,n):
    lo = 0 if k==0 else beta.ppf(0.025,k,n-k+1); hi = beta.ppf(0.975,k+1,n-k) if k<n else 1
    return lo,hi
def agg(parts):
    t = collections.defaultdict(lambda: collections.Counter())
    for p in parts:
        for r in json.load(open(f"{ROOT}/blind_ber_{p}.json")):
            if "Genie" in r["rx"]: continue
            c = t[(r["rate"], r["snr"], r["rx"])]
            for f in F: c[f] += r.get(f, 0) or 0
    return t
if __name__ == "__main__":
    t = agg(sys.argv[1:])
    print(f"{'rate':5} {'snr':>5} {'rx':40} {'err/n':>12} {'BLER 95%':>22} {'totM':>7} {'coreM':>7} {'scoreM':>7} {'fastM':>6} {'decM':>6} {'dec/pk':>6} {'st1':>6} {'st2':>6} {'st3':>5} {'st4':>5} {'st5':>5} und")
    for (rate,snr,rx),c in sorted(t.items()):
        n=c["frames"]; m=c["mac_frames"] or n; k=c["frame_err"]; lo,hi=cp(k,n)
        sf=c["stage_frames"] or 1
        print(f"{rate:5} {snr:5} {rx:40} {k:5}/{n:<6} [{lo:.2e},{hi:.2e}] {c['macs']/m/1e6:7.3f} {c['crit_par_macs']/m/1e6:7.4f} {c['macs_score']/m/1e6:7.3f} {c['macs_fast']/m/1e6:6.3f} {c['macs_dec']/m/1e6:6.3f} {c['decodes']/n:6.2f} "
              + " ".join(f"{c[f'stage_{s}']/sf*100:5.1f}" for s in range(1,6)) + f" {c['undetected']}")
