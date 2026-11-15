# est5: deployed preamble / pilot systems as competitors (pilots outside the packet, energy charged), predictions 2026-11-15
Goal (user, 2026-11-15): show that blind reaches the BLER of REAL preamble / pilot-based single-carrier systems without
sending any known symbols. Same framework and back-end as est4 (expected_est4.md): 1024 data symbols carry the whole
codeword, known symbols are extra burst symbols, SNR axis = burst energy per data symbol, same CA-SCL-8 + re-encoding
check + fair metric-ordered CRC search (incl. alias / lobe hypotheses), same packets / CFO / noise. Sources: the
lit_real_*.md surveys (2026-11-15). Already in est4: DVB-RCS2 ID 13 (C1a/b), 128 preamble ML / M&M (C3; Comtech, DOCSIS
class), 64+64 pre/post (C4; Hughes class), 16+16 4th power (C2).

| New competitor | Deployed origin | Layout scaled to 1024 data symbols | Nk (dB) | Estimator chain |
|---|---|---|---|---|
| C6 VDE-SAT | ITU-R M.2092-2 (VDES satellite) | 27-symbol syncword, then 1 pilot per 27 data symbols | ~65 (0.27) | ML on the syncword + Rife-Boorstyn over all known symbols, CRC search over the +-1/27 alias lobes |
| C7 DVB-S2 style | ETSI EN 302 307 / TR 102 376 | 90-symbol PL header (SOF 26 + PLS 64) + one 36-symbol pilot block mid-burst | 126 (0.52) | M&M / L&R on the header, then joint ML header + pilot block with lobe search |
| C8 CCSDS style | CCSDS 131.2 / 130.11-G | 8 pilot blocks of 16 symbols spread over the burst (block period ~146) | 128 (0.52) | FFT (R-B) over all blocks + lobe search, per-block ML phase + linear interpolation |
| C9 ViaSat burst | US 7653150 + US 8243859 | 16-symbol midamble unique word | 16 (0.07) | 4th-power FFT over the burst, top-32 peaks each checked on the UW (pi/2 ambiguity), CRC search |
| C10 NB-IoT / LTE DMRS style | 3GPP 36.211 (NPUSCH) | 1 pilot per 7 symbols | ~171 (0.69) | R-B over the pilots (range +-0.071, no aliases at 0.03), pilot phase + interpolation |
| C11 400ZR style | OIF 400ZR | 1 pilot per 32 data symbols | 32 (0.13) | blind 4th-power coarse, R-B on the pilots, CRC search over the +-1/32 alias lobes |
| C12 Wi-Fi style | IEEE 802.11 (coarse/fine preamble) | 128-symbol preamble: 8 x 16 repeats (lag 16 coarse), lag 64 fine | 128 (0.51) | autocorrelation coarse + fine, CRC search over the +-1 fine lobes |

## Predictions (no phase noise; at the plotted, energy-charged SNR; blind numbers from 8.2a)
- C6 VDE-SAT: the best new competitor at 2/5, 1/2: 0.15-0.2 dB better than DVB-RCS2 ID 13 (lower overhead), still
  0.3-0.4 dB behind blind; at 1/10, 0.15 equal to ID 13 within +-0.1 dB, alias errors (lobe 0.59 of the peak) below 1e-4.
- C7 DVB-S2 style, C8 CCSDS style: like 128 ML / ID 13 within +-0.1 dB (same energy); C8 may show alias errors at -5 dB.
- C9 ViaSat: fails below ~0 dB like C2 (4th power), but the top-32 + UW check makes it 1-2 dB better than C2 at 1/2 and
  2/5 0.5-1 dB; BLER ~1e-1 at 0.15 -3 dB.
- C10 dense DMRS: 0.1-0.2 dB worse than ID 13 in AWGN (more overhead), the best under phase noise with tracking.
- C11 400ZR: >= 1 dB worse than ID 13 at 1/10, 0.15 (pilot energy too low for the coarse step), close at 2/5, 1/2.
- C12 Wi-Fi: worse than 128 ML; a BLER floor ~1e-3 near -5 dB from fine-lobe misses unless the CRC lobe search catches them.
- Overall: blind matches or beats every one of them in BLER (best case for them: tie at 0.15), with 0 known symbols.
