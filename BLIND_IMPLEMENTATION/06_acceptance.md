# 6. Acceptance: CRC-16, PiCode and the re-encoding check

Code: `blind_cfo.PiCode.decode`, `blind_fast.reencode_rho`, `blind_fast.rho_min`, `small_rx.decode`.

## 6.1 Why CRC-16 alone is not enough
- **One decode:** a list decoder outputs up to 8 paths. A wrong path passes CRC-16 with probability 2⁻¹⁶, and with PiCode's two accepted patterns 2·2⁻¹⁶ ≈ 3·10⁻⁵.
- **A search:** the blind receiver decodes many hypotheses per packet, so the chance that **some** wrong hypothesis passes adds up.
  - Measured: at R = 1/10 −5 dB, about 5·10⁻⁴ of the packets had a wrong first CRC pass.
  - On noise-only input: 8–25 % of packets produce a CRC pass.

## 6.2 The re-encoding check
A wrong CRC pass is a valid codeword **unrelated** to the received samples. So the receiver re-encodes the decoded data, maps it to symbols s̃, and correlates with r' at the hypothesis CFO. This is phase-free, so PiCode's complement counts too:

$$\rho = \frac{\big|\sum_n r'_n\,\tilde s_n^{*}\,e^{-j2\pi \hat f n_c}\big|}{\sqrt{N\sum_n |r'_n|^2}},\qquad N = 1024 .$$

**Right packet:** Σ r' s̃* ≈ N·g·e^{jθ}, and Σ|r'|² ≈ N(1 + 1/SNR), so

$$\rho_{\text{right}} \approx \sqrt{\frac{\mathrm{SNR}}{1+\mathrm{SNR}}}\qquad(0.49 \text{ at } -5\text{ dB}).$$

**Unrelated codeword:** the sum is a sum of N random-phase terms, so ρ is about Rayleigh with scale 1/√(2N):

$$P(\rho > t) \approx e^{-N t^2}\qquad(t = 0.12:\; e^{-14.7} = 4\cdot10^{-7}).$$

**Threshold.** With s the SNR estimate, linear:

$$\rho > \max\!\Big(0.12,\;\tfrac12\sqrt{\tfrac{s}{1+s}},\;\mathrm{RHO\_N}(\mathrm{SNR})\sqrt{\tfrac{s}{1+s}}\Big),$$

- RHO_N is a per-rate table that tightens the threshold to a fraction of the expected right-packet value (R = 1/10: 0.775 at −5 dB down to 0.553 at 0 dB; R = 0.15: 0.873 at −4.5 dB down to 0.655 at +1 dB; R = 2/5: 0.928 to 0.883; R = 1/2: 0.934 to 0.903). Each table is calibrated per code from the false passes of wrong-CFO hypotheses (R = 0.15: runs `fp15a/b`).
- The 128-pilot comparison receivers (est3) use the same threshold, so the comparison is fair.
- Option `re_margin`: the threshold uses SNR + margin. Then an SNR estimate that is too low cannot lower it; a margin of 1 dB fixes the −1 dB SNR-error case.

**Measured effect:**
- 86–100 % of wrong CRC passes are removed;
- at most 4 of about 6,400 correct passes were rejected, and the search recovered all of them, so the BLER cost is about zero;
- noise-only false alarms drop from 8–25 % to **0 in 9,600**;
- the cost is 20,000 MACs per check.

## 6.3 Final decision
A hypothesis is **accepted** only if all of these hold:
- CRC(data) matches either pattern (PiCode);
- ρ is above the threshold;
- for the pilot variant only, the pilot coherence check passes.

The first accepted hypothesis ends the search. If no hypothesis is accepted, the packet is a block error (the first decode's output is delivered and counted as wrong).
