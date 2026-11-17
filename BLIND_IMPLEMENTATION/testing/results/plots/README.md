# Plots

| Folder | What is in it | Made by |
|---|---|---|
| `DVB-RCS2/overview/` | One figure per waveform ID (13, 42, 3, 14): BLER vs Eb/N0 (known symbols charged / free), BLER vs SNR, MACs vs Eb/N0 and vs SNR; blind final receiver vs DVB-RCS2 with its own DA CFO estimate | `testing/plot_fs_final.py` |
| `DVB-RCS2/BLER/` | BLER with and without a per-packet MAC cap (`fs_final_capped`, `fs_bler_capped`), DVB-RCS2 reference validation (`fullsys_refs`), ID 14 code-only | `plot_fs_final.py`, `plot_fullsys_refs.py` |
| `DVB-RCS2/MACs/` | BLER vs mean MACs, BLER vs max MACs, BLER vs MAC budget, BLER/MACs vs MAC cap | scratchpad scripts (2026-11-17) |
| `DVB-RCS2/tuning/` | Evidence for the chosen thresholds: F5 early-stop sweep (`fs_tuning_f5`, incl. VDE), checkpoint NN off / old / retrained (`fs_nn_compare`) | `plot_tuning_f5.py`; see `results/tuning_fullsys.md` |
| `DVB-RCS2/superseded/` | Earlier versions (before the final receiver / honest MAC accounting); kept for history | - |
| `VDE-SAT/overview/` | VDE-SAT Link 32 vs blind (no NN / before tuning / jointly tuned): BLER and MACs vs Eb/N0 and vs SNR | `testing/plot_vde_final.py` (arg: the tuned part prefix, default `fs-gv32km`) |
| `VDE-SAT/MACs/` | MACs vs SNR (mean, worst case); jointly tuned receiver regular vs MAC cap 2 / 1 / 0.5 M: BLER (`fs_vde_tuned_capped`) and MACs (`fs_vde_tuned_macs_capped`); older cap plot `fs_vde_capped` (receiver before tuning) | scratchpad scripts (2026-11-17/18), data `fullsys/results/capcurve_vde32*.json` |
| `VDE-SAT/tuning/` | MAC-cut comparison on calibration packets (`fs_vde_mac_cuts`) | scratchpad script; record `results/tuning_fullsys.md` |
| `VDE-SAT/superseded/` | First VDE results | - |
| `original_study/` | The original blind study (R = 1/10, 0.15, 2/5, 1/2; 1024-symbol packets): BLER / MACs curves, presentation figures, thresholds, cap, fast path | the other `testing/plot_*.py` scripts |
