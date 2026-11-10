# 2. Stage 1: the fast path (one decode)

Code: `small_rx.small_receive`, block "1. fast path".

## 2.1 The 4th power removes QPSK
QPSK symbols are e^{j(π/4 + kπ/2)}, so s⁴ = e^{jπ} = −1. Then

$$y_n = -r_n^4 = g^4 e^{j(2\pi\cdot 4f\,n_c + 4\theta)} + \underbrace{(\text{signal}\times\text{noise and noise}^4\text{ terms})}_{\text{zero-mean}} .$$

y is a single complex tone at frequency ν = 4f.
- **No coarse stage is needed:** for |f| ≤ 0.03, |ν| ≤ 0.12 < ½, so the tone is never aliased (in the earlier ±0.2 study, |4f| reached 0.8 and needed one).
- **FFT:** the 1024 values are zero-padded to 4096 points (4×), Y[k] = Σ_n y_n e^{−j2πkn/4096}. Only bins with |ν_k| ≤ 4·0.03 + 2/4096 are kept, and the peak is k_b = argmax|Y[k]|.
- **Parabolic refinement** on the magnitudes V₋, V₀, V₊ of bins k_b−1, k_b, k_b+1:

$$\delta = \tfrac12\,\frac{V_- - V_+}{V_- - 2V_0 + V_+}\in[-\tfrac12,\tfrac12],\qquad
f_0 = \mathrm{clip}\!\left(\frac{(k_b+\delta)/4096}{4},\,\pm0.03\right).$$

- **Cost:** 8·1024 for the 4th powers, plus the 4096-point FFT, about 2·4096·12 MACs.

## 2.2 Pre-MF correction
The chain's matched filter sits *after* the CFO, so at the true CFO the MF is slightly mismatched (the loss g(f)). The receiver de-rotates the 8-SPS samples by f₀, filters again, and puts f₀ back at symbol rate (`blind_fast.premf`):

$$r'_n = \Big[\big(r_x[m]\,e^{-j2\pi f_0 m/8}\big)\star h\Big]_{40+8n}\; e^{\,j2\pi f_0 (n+5)} .$$

r' has the same model as r, but its MF is matched up to the residual f − f₀. Every later stage works on r'.

## 2.3 Carrier phase (mod π/2)
`blind_cfo.phase4` computes the phase at 4f₀ itself, not at 4f₀ mod 1:

$$\hat\theta_0 = \tfrac14 \arg\sum_n y_n\,e^{-j2\pi\, 4 f_0\, n_c}.$$

This avoids a sign flip: n_c is a half-integer, so wrapping 4f₀ by an odd integer would negate the sum. Because of the ¼, θ is known only modulo π/2.

## 2.4 The π ambiguity: PiCode
Rotating QPSK by π negates both parts of the symbol, i.e. it **complements every coded bit**. For a polar code:
- the all-ones word is a codeword, because the last row of G_N is all ones (u = e_{N−1});
- so x ⊕ 1 = (u ⊕ e_{N−1})·G_N.

The complemented codeword therefore decodes to the **same data** with only u_{N−1} flipped. u_{N−1} is always an information bit and here holds the last CRC bit.

`blind_cfo.PiCode` accepts a list path when CRC(data) equals either the decoded CRC bits or those bits with the last one flipped. The data are correct in both cases.
- **Gain:** the phase only has to be resolved **modulo π**: 2 hypotheses (θ₀ and θ₀ + π/2) instead of 4.
- **Cost:** a wrong path passes the CRC with probability 2·2⁻¹⁶ instead of 2⁻¹⁶ (see 06).

**Validity:** this holds for any polar code with QPSK where u_{N−1} is an information bit and no shortening is used. With a distributed or masked CRC, the "complement syndrome" is a different fixed, known pattern, and the same trick applies.

## 2.5 Choosing the π/2 branch and decoding
Both branches are scored with the list-1 path metric M (03), and the smaller one wins:

$$b = \arg\min_{b\in\{0,1\}} M\big(\mathrm{LLR}(r';\,f_0,\;\hat\theta_0 + b\pi/2)\big).$$

Then one CA-SCL-8 decode runs at (f₀, θ̂₀ + bπ/2), followed by the code-aided retry and the acceptance tests of 05/06. At high SNR most packets are delivered here, which is why MACs fall with SNR.
