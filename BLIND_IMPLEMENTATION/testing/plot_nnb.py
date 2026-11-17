"""Plot of the deployable retry gate (nn_b_export.py, offline replay): per-core MAC saving per point."""
import json, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__))
R = json.load(open(os.path.join(HERE, "results", "nn_b_export.json")))
O = json.load(open(os.path.join(HERE, "results", "nn_offline.json")))["oracle"]
names = list(R)
lab = {"1/10 -5": "R = 1/10\n-5 dB", "0.15 -4": "R = 0.15\n-4 dB", "0.15 -3": "R = 0.15\n-3 dB",
       "2/5 0.5": "R = 2/5\n0.5 dB", "1/2 2": "R = 1/2\n2 dB"}
ser = [("Gate, 0.1 % point", lambda n: R[n]["B 0.001"], "#2a78b8"),
       ("Gate, 1 % point", lambda n: R[n]["B 0.01"], "#e07b28"),
       ("Perfect gate (bound)", lambda n: O[n]["B"], "#9a9a9a")]
x = np.arange(len(names)); w = 0.26
fig, ax = plt.subplots(figsize=(9, 5.2))
for k, (nm, f, c) in enumerate(ser):
    v = [f(n)["saved_pct"] for n in names]
    b = ax.bar(x + (k - 1) * w, v, w - 0.03, color=c, label=nm)
    for xi, vi, n in zip(x, v, names):
        lost = f(n)["lost"]
        ax.text(xi + (k - 1) * w, vi + 0.6, f"{vi:.1f}%" + (f"\n{lost} lost" if k < 2 else ""),
                ha="center", va="bottom", fontsize=8)
ax.set_xticks(x, [lab[n] for n in names])
ax.set_ylabel("Saving in MACs per core [%]")
ax.set_ylim(0, 50)
ax.set_title("Retry gate: MACs per core saved (offline replay, 8000 test packets per point)")
ax.grid(axis="y", alpha=0.3)
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=3, frameon=False)
fig.tight_layout()
out = os.path.join(HERE, "results", "plots", "original_study", "nn_b_gate_saving.png")
fig.savefig(out, dpi=130); print(out)
