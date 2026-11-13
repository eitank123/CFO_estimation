# 1. Signal model and conventions

## Transmitter
- **Data:** A data bits with A = 205 / 307 / 819 / 1024 for R = 1/10, 0.15, 2/5, 1/2 (R = 0.15 is the main low-SNR rate; R = 1/10 is kept as a second low-SNR rate). CRC-16 is appended, so the encoder takes K = A + 16 information bits.
- **Polar code:** N = 2048. The information set is chosen by the polarization-weight (PW) reliability order, and the frozen bits are 0.
  - In u, the CRC bits follow the data in the same order (`polar.PolarCode`).
  - Codeword: x = u·G_N, with G_N = F^{⊗11} and F = [[1,0],[1,1]].
- **Interleaver:** a fixed random permutation of the 2048 coded bits (seed 12345).
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
