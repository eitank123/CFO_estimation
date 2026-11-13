# 4. Stage 2: the search over CFO × phase hypotheses

Code: `small_rx.small_receive`, block "2. search". It runs only for packets the fast path did not deliver.

## 4.1 The grid of cells
Cells are spaced k·STEP apart over the whole range (`blind_fast.grid`):

$$f_c = -0.03 + c\,k\,\mathrm{STEP},\qquad c = 0,\dots,C-1 .$$

| Rate | k | Spacing | Cells C |
|---|---|---|---|
| 1/10 | 4 (fixed, `kstep`) | 3·10⁻⁴ | **201** |
| 2/5 | 2 | 1.5·10⁻⁴ | 401 |
| 1/2 | 2 (SNR < 4 dB), 4 (SNR ≥ 4 dB) | | 401 / 201 |

**Why k = 4 is safe at R = 1/10:** the worst-case residual inside a cell is half a spacing. That gives a phase drift at the packet edge of 2π·1.5·10⁻⁴·512 ≈ 0.48 rad, still inside the low-rate code's metric basin. The cell is refined later, in 05.

**Phase of a cell.** Each cell reads its own 4th-power phase from the FFT that already exists, at the bin b_c nearest to 4f_c:

$$\theta_c = \tfrac14\arg\big(Y[b_c]\,e^{\,j2\pi\nu_c\cdot 511.5}\big).$$

The phase hypotheses are θ_c + q·π/4:
- **below −1 dB:** q = 0, 1, 2, 3. That covers the π/2 branch and the half-steps between, because the 4th-power phase is noisy there;
- **from −1 dB up:** q ∈ {0, 2}, i.e. θ_c and θ_c + π/2.

**Known issue (R = 0.15):** R = 0.15 uses the R = 1/10 settings, including this switch. Its BLER rises from 0 in
780k packets at −2 dB to 1.6·10⁻⁴ at −1 dB, exactly where the phases drop from 4 to 2; in 10 of 11 analysed
failures the true CFO region never reached the candidates. A version with 4 phases at every SNR fixed it in a
paired test (same 400k packets at −1 dB: 0 errors vs 72 with the switch).

Each (cell, phase) pair is one **hypothesis**.

## 4.2 Robust z-score
At a checkpoint, each live cell keeps its best phase, with partial metric M_c. The cells are compared by a robust z:

$$z_c = \frac{\mathrm{median}(M) - M_c}{1.4826\;\mathrm{MAD}(M)}\qquad(\text{higher} = \text{better}).$$

Median and MAD are not moved by the one good cell, so the right cell stands out as a large z, typically z > 6–10. Cells with z ≤ τ are dropped, but the k_min = 16 best are always kept.

## 4.3 Checkpoint schedule per rate
- **R = 1/10, coarse start.**
  1. Only every **2nd** cell (stride 2) is decoded up to c = ½, and the z-test runs there (τ = −0.5).
  2. The neighbours of each surviving cell **join** at that point, with every phase, and pay for their own decode up to ½. The true cell is never more than one cell away from a survivor.
  3. At c = ½ each cell also keeps only its **best 2 phases** (`phase_keep`).
  4. A second z-test runs at c = ¾, then the decode completes to c = 1.
- **R = 2/5 and 1/2, checkpoint NN** (`small_ck_nn.py`).
  - At c = ¼ (R = 2/5) or 3/16 (R = 1/2), every cell has been decoded that far. A small network then outputs log P(cell) from per-cell features:
    - the 4th-power periodogram of the packet and of its two halves;
    - the halves' phase agreement;
    - the distance to f₀;
    - the lag-4 autocorrelation estimate;
    - the z-trajectories of the partial metrics (total and rate-0 part);
    - the phase contrast;
    - SNR and grid step.
  - Architecture: 2 convolutions along the cell axis (width 3, 12 channels), FiLM-modulated by SNR, plus a skip connection from the z-feature, then a log-softmax over the cells.
  - Only the cells within cumulative probability 1 − 10⁻³ continue (at least 8). The usual z-tests follow at the later checkpoints (R = 2/5: ⅜, ½, ¾; R = 1/2: ¼, ½), with τ = −1 and k_min = 16.

**Early win (all rates).** At any checkpoint, a cell with z > **6** is refined and decoded at once (05). If it is accepted, the other cells are never finished.

## 4.4 Thirty-two decoder cores: batches, passes, joint comparison
A real receiver has a fixed number of decoder cores (here 32), not one per cell.
- **R = 1/10, batches of 32.**
  - **Ordering:** the cells are cut into contiguous blocks of 32. The blocks are ordered by a prior, the 4th-power periodogram on the grid, normalised by its mean:

$$\mathrm{LP}_c = w_4(\mathrm{SNR})\; \max_{\text{bins of cell }c}\frac{|Y[k]|^2}{\overline{|Y|^2}},$$

    with w₄ = 0.1 at −5 dB, ⅓ at −2 dB and 1 at 1 dB. Each block is ranked by the log-sum-exp of its cells.
  - **Rounds** are cumulative: round r covers blocks 1..r. A block is decoded up to the first checkpoint; if its best z there is below **5**, the round stops and the next block is added. Cells already paid for are never charged again, and the last round sees every cell, so **no cell is lost for good**.
- **R = 2/5 and 1/2, fixed 32 cores in passes.** All stored path metrics of every pass are compared jointly; nothing is decoded twice. At R = 2/5, **best-first 32** comes first: the prior's best 32 cells go through the whole pipeline, and the full grid follows only if none of them is accepted.

## 4.5 Candidates
After the last checkpoint, the cells are taken in z order: the ones with z > z₀ = **4**, at most 4, then the 32 best by final path metric. Each candidate goes to stage 3 (05), and the search stops at the first accepted decode.
