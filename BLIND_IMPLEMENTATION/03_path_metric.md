# 3. The decoder as a CFO detector: the Fast-SSC path metric

Code: `blind_fast.FastSC` (`metric`, `metric_nodes`, `metric_cw`).

## 3.1 Path metric of a successive-cancellation path
Given channel LLRs L (2048 values) at a hypothesis (f̂, θ̂), the list-1 SC decoder walks the polar tree and takes, for every bit u_i, its LLR λ_i and a decision û_i:
- for a **frozen** bit, û_i = 0;
- for an information bit, the hard decision.

The LLR-based path metric (Balatsoukas-Stimming et al. 2015) accumulates

$$M = \sum_{i=0}^{N-1} \ln\!\big(1+e^{-(1-2\hat u_i)\lambda_i}\big) \;\approx\; -\ln P(\hat u \mid \mathbf r) .$$

- **Information bits:** the penalty is ln(1 + e^{−|λ_i|}), which is small.
- **Frozen bits:** the penalty is ln(1 + e^{−λ_i}). It is large whenever the channel "votes" for a 1 where the code says 0.

## 3.2 Fast-SSC: the same metric at node level
The tree is cut at special nodes (`FastSC._plan`), with LLR vector a of length n at each node:

| Node | Content | Penalty added to M | Decision |
|---|---|---|---|
| Rate-0 | all frozen | Σ_i ln(1 + e^{−a_i}) | all 0 |
| Rate-1 | all information | Σ_i ln(1 + e^{−\|a_i\|}) | hard decisions |
| REP | only the last bit is information | min(Σ ln(1+e^{−a_i}), Σ ln(1+e^{+a_i})) | all equal |
| SPC | only the first bit is frozen | Σ ln(1+e^{−\|a_i\|}) + \|a_min\| if the parity is odd | hard, least reliable bit flipped |

Internal nodes split a = [x, y] into the left child, with f(x, y) = sign(xy)·min(|x|, |y|) (min-sum), and the right child, with g = y + (1 − 2β_left)·x.

## 3.3 Why it separates right from wrong CFO
- **At the right (f, θ):** the LLRs are noisy versions of a codeword. Frozen-bit LLRs λ_i are mostly positive and large, so their penalties are small.
- **At a CFO error Δf:** the symbols rotate by 2πΔf·n_c across the packet. Once the rotation is large, the LLRs no longer belong to any codeword, and the frozen-bit LLRs become random with zero mean. Each frozen bit then costs about ln 2 or more on average.
- **Size of the gap:** with N − K frozen bits, M grows by roughly (N − K)·ln 2. That is **1271 nats at R = 1/10** and 708 nats at R = 2/5, against a noise spread of a few tens of nats.
- **The frozen bits are "implicit pilots"** in the code. At R = 1/10, 1827 of the 2048 bits are frozen, which is why the blind receiver works at −5 dB.

## 3.4 Partial metrics (checkpoints)
`metric_nodes` returns each leaf's penalty in decoding order, with rate-0 nodes split into 64-bit chunks. The cumulative sum up to the leaf that ends at codeword fraction c is the **partial path metric** M(c).
- **Why early checkpoints help:** the left (early) part of a polar code holds most frozen bits. At R = 1/10 the first half is mostly frozen and carries most of the CFO information.
- **Cost of the first half:** only **36 %** of a full metric pass (Fast-SSC tree cost, `small_rx.cost_share`), so stopping at c = ½ is cheap.

## 3.5 Cost
One full metric pass costs 2n per internal node (f and g), n per rate-0 / rate-1 leaf, and 2n per REP / SPC leaf (`blind_vp.metric_macs`). The LLR computation and de-rotation add 4·1024 + 6144 MACs per hypothesis.
