# 1. Signal model and conventions

## Transmitter
- **Data:** A data bits with A = 205 / 307 / 819 / 1024 for R = 1/10, 0.15, 2/5, 1/2 (R = 0.15 is the main low-SNR rate; R = 1/10 is kept as a second low-SNR rate). CRC-16 is appended, so the encoder takes K = A + 16 information bits.
- **Polar code:** N = 2048. The information set is chosen by the polarization-weight (PW) reliability order, and the frozen bits are 0.
  - In u, the CRC bits follow the data in the same order (`polar.PolarCode`).
  - Codeword: x = u·G_N, with G_N = F^{⊗11} and F = [[1,0],[1,1]].
- **Interleaver:** a fixed random permutation of the 2048 coded bits (seed 12345). **It is a required part of the
  blind system, not an option** (see "Why the bit interleaver is required" below).
- **QPSK mapping:** bits (2n, 2n+1) map to the symbol

$$s_n = \frac{(1-2c_{2n}) + j(1-2c_{2n+1})}{\sqrt2},\qquad n=0,\dots,1023 .$$

- **Pulse shaping:** upsampled by SPS = 8, root-raised-cosine with β = 0.25 and a span of 10 symbols, normalised to unit energy (Σh² = 1).

## Channel (full Tx/Rx chain, `txrx_chain.py`, `blind_cfo.transmit_full`)
The CFO is applied per 8-SPS sample, **before** the matched filter:

$$r_x[m] = e^{j(2\pi f m/8+\varphi)}\,(s\star h)[m] + w[m],\qquad
w[m]\sim\mathcal{CN}\!\left(0,\;\frac{E_s}{\mathrm{SNR}}\right),\quad E_s=\frac1{1024}\sum_m |(s\star h)[m]|^2 .$$

- **Matched filter:** the same RRC, with the filter delay of 10·8/2 = 40 samples removed, then downsampled. The symbol-rate output is

$$r_n = g(f)\,s_n\,e^{j(2\pi f (n+5)+\varphi)} + w_n,\qquad w_n\sim\mathcal{CN}(0,1/\mathrm{SNR}) .$$

- **SNR:** the matched-filter output SNR equals E_s/N_0 exactly (unit-energy RRC).
- **CFO loss:** g(f) = Σ_k h_k² cos(2πfk/8) ≤ 1 is the MF's CFO loss. It is removed by the pre-MF correction (stage 1).

## Why the bit interleaver is required (found 2026-11-17)
The receiver tests the carrier phase only modulo π/2 by search and resolves π with PiCode. This works only if the
**four QPSK rotations of a codeword are distinguishable by the decoder**. Without a bit interleaver they are not:
- A Gray-QPSK symbol carries two adjacent code bits (x_2m, x_2m+1). Rotating it by π/2 maps them to
  (x_2m+1 ⊕ 1, x_2m).
- For a polar code that is the index translation i → i ⊕ 1 (an automorphism of the code) plus the word "ones at
  the even positions", which is itself a codeword (u = e_{N-2}, an information bit).
- So **a π/2-rotated codeword is another codeword**. The two π/2 phase branches give *identical* path metrics, the
  receiver cannot tell them apart, and it picks branch 0 whenever they tie. Every packet whose true phase lies in the
  other π/2 half fails (or, worse, passes the CRC with the wrong data if the CRC cannot tell).

A fixed pseudo-random permutation of the coded bits before QPSK mapping (seed 12345 here) splits the pairs, so a
rotation no longer maps codewords to codewords. The decoder's metric then identifies the right branch. A GF(2) rank
check confirms it: for the rate-matched ID 13 code, rank([G; rotated G]) is 984 = K without the interleaver (the
rotated code equals the code) and 1967 with it.

How it was found: on the full-system formats (fullsys/blind_fmt.py) the 5G NR sub-block interleaver of the rate
matching keeps bit pairs together and the extra random interleaver had been left out. Blind then failed 37 % of the
packets at every SNR, with p_m_br0 == p_m_br1 in 199 of 200 packets and 72 of 73 failures in one π/2 half of the true
phase, while the same code with genie sync (true phase given) was fine. The fix restores the random channel
interleaver over the E sent bits (same on Tx and Rx). The earlier dead end "OLD receiver without the bit
interleaver" ([DEAD_ENDS.md](DEAD_ENDS.md)) is the same effect at the native format. A receiver that instead uses
the symmetry (PiCode4, one decode for all 4 rotations) works only when the interleaver is absent and has its own
undetected-error problem ([testing/results/expected_eq.md](testing/results/expected_eq.md)).

## Conventions used everywhere
- **f:** CFO in **cycles per symbol**, |f| ≤ MAX_CFO = 0.03. It is uniform per packet, and the phase φ is uniform.
- **Centred time index:** n_c = n − 511.5. The receivers refer the carrier phase to the packet centre, θ = φ + 2πf(511.5 + 5), so that

$$r_n = g\,s_n\,e^{j(2\pi f n_c + \theta)} + w_n .$$

- **LLR of a de-rotated symbol** y_n = r_n·e^{−j(2πf̂·n_c + θ̂)}, using the true SNR (σ² = 1/(2·SNR) per real dimension):

$$L_{2n} = \frac{\sqrt2\,\Re\, y_n}{\sigma^2},\qquad L_{2n+1} = \frac{\sqrt2\,\Im\, y_n}{\sigma^2}\qquad(\text{positive}\Rightarrow\text{bit }0),$$

  then de-interleaved (`blind_cfo.llrs`).
- **Search step:** STEP = 1.5·10⁻⁴ · 512/1024 = **7.5·10⁻⁵**. This is the CFO error that still decodes reliably.
  - The phase error at the packet edge is 2π·7.5·10⁻⁵·512 ≈ 0.24 rad.
  - The receiver's grid steps are multiples of STEP.
