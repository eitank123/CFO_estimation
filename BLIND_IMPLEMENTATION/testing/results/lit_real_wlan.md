# Literature survey: CFO estimation in REAL Wi-Fi and short-range single-carrier systems (2026-11-15)

Scope: IEEE 802.11ad/ay single-carrier (60 GHz), 802.11b DSSS/CCK, a paragraph on OFDM Wi-Fi, Bluetooth (BR, LE 1M/2M,
LE Coded), IEEE 802.15.4 O-QPSK, 802.15.4z HRP UWB, LoRa, Sigfox, mioty. Compared with our setting: 1024 QPSK symbols,
polar N = 2048 + CRC-16, Es/N0 -5 ... +3 dB, |f| <= 0.03 cycles/symbol, no pilots. New material only; the DVB-RCS2,
polar-sync and blind-CFO surveys (lit_dvbrcs2.md, lit_polar_sync.md, lit_blind_cfo.md) are not repeated.
One entry per source is in "Reference entries" at the end, for merging into REFERENCES.md.

**Access limits, said plainly.** The IEEE 802.11 / 802.15.4 and Bluetooth Core texts are paywalled or PDF-only and could not
be read. Every PDF I fetched (core.ac.uk, ieee802.org, Berkeley, TUM) came back as undecodable binary or HTTP 403, and IEEE
Xplore gave no abstract. Standard numbers below come from vendor documentation (MathWorks, Keysight, Nordic,
rfwireless-world) and patents, with the read depth listed per source. Everything marked [derived] is my arithmetic, not a
quoted number. No simulation was run.

## 1. Ranked takeaways

1. **No deployed short-range system does what we do. All of them are data-aided (preamble) and work at a much
   higher SNR per symbol or with a much smaller normalised CFO.** 802.11ad SC tolerates +-20 ppm per device at 60 GHz, which
   is +-2.42 MHz relative over a 1.76 Gchip/s chip rate, i.e. **|f| <= 1.4e-3 cycles/chip [derived]**: 22x smaller than our
   0.03. Its STF alone is 17 x Ga128 = 2176 chips (rfwireless-world; MathWorks), more than twice our whole 1024-symbol burst.
   Its lowest SC MCS (MCS1, pi/2-BPSK) has a -68 dBm sensitivity, about **+3.5 dB per chip [derived, NF = 10 dB assumed]**,
   above our whole SNR range. The systems that do work far below 0 dB per chip (LoRa SF12 at -20 dB, BLE Coded near 0 dB,
   802.15.4 DSSS) spread each symbol over 8 to 4096 chips and detect it non-coherently or differentially. At the symbol level
   they run at about +9 to +16 dB, where a few preamble symbols are enough. **Verdict: no real WLAN / short-range system is a
   tighter competitor than the ones we already simulate (128-preamble ML, 64 + 64 joint ML, DVB-RCS2 ID 13).**
2. **The deployed estimator family is "repeated-sequence autocorrelation, coarse then fine".** 802.11ad uses a lag-128
   autocorrelation on the Golay STF; its unambiguous range is +-1/(2*128) cycles/chip = +-6.875 MHz = **114.58 ppm at 60 GHz
   [derived]**. That matches the 114.58 ppm SC tolerance reported by Liu et al. (TCSI 2015, snippet only), so the lag is
   confirmed indirectly. 802.11b correlates consecutive Barker symbols, then hands over to a phase-tracking loop. These are
   Schmidl-Cox / Moose / Fitz-type estimators. They are **worse than the ML-128 we already have**, on the same known energy
   (see 3).
3. **If the user wants a "what real Wi-Fi does" competitor, build "Wi-Fi-style STF + LTF on 128 extra known symbols":
   8 x 16-symbol repetitions, a lag-16 coarse estimate (unambiguous |f| < 1/32 = 0.03125, which just covers our 0.03), then
   2 x 64 symbols with a lag-64 fine estimate (range +-0.0078).** Expected numbers (Gaussian approximation, [derived], not
   simulated): at Es/N0 = -5 dB the coarse std is about 2.7e-3 cycles/symbol, so about 0.4 % of packets miss the fine
   window (about 4.7e-4 at -4 dB). The fine std is about 8.9e-4, which is 1.9x the 128-symbol CRB std (4.8e-4) or 5.3 dB
   in variance. **So it should be clearly worse than our 128-preamble ML.** It should floor at a BLER of about 1e-3 to 5e-3
   near -5 ... -4 dB at R = 1/10 and 0.15, unless a CRC search over the +-1 fine lobes is added (as in our 64 + 64
   receiver). Its value is only as a "deployed-practice" reference line. It cannot beat blind or ML-128.
4. **For a low-SNR, wide-CFO burst, the deployed state of the art uses a bank of frequency hypotheses tested by
   correlation.** We already do this in software, and in a stronger form. A BLE Long Range sync patent (US 2018/0270091)
   covers +-200 kHz (150 kHz Tx + 50 kHz Rx) at 1 Msym/s, i.e. **+-0.2 cycles/symbol [derived]**. It uses an FFT of the
   preamble correlation with 15.625 kHz bins and sums 4 to 6 bins over 27 offset combinations. It also alternates
   half-bin-shifted FFTs, because a half-bin offset loses about 3 dB. This is our Stage 1 / Stage 2 CFO-cell grid, but
   applied to a known preamble, not to the decoder metric. **We already use it** (4th-power FFT plus the CFO-cell grid).
   The half-bin straddle loss they report (3 dB) is the same effect our peak-picked fast path handles.
5. **LoRa sync is the closest published analysis of a deployed "integer + fractional" CFO split, and it reports a 1-2 dB
   sync loss at PER 1e-3** (Xhonneux et al., IEEE IoT-J; Tapparel & Burg, Asilomar 2024). LoRa estimates the fractional CFO
   from the phase between consecutive identical upchirps (5 bins around the peak, summed over preamble pairs) and the
   integer CFO from (s_up + s_down)/2. The range is |df| < B/4 = **0.25 cycles/chip [derived]**. The structural idea
   (fractional part from a phase difference, integer part by a discrete search) is our Stage 1 + Stage 2. They did not
   compare with a CRB. **Not applicable** as a competitor: chirp spread spectrum, uncoded or Hamming-coded, 8 upchirps of
   2^SF chips.

**OFDM Wi-Fi context (one paragraph).** 802.11a/g/n/ac/ax estimate the CFO data-aided. The coarse estimate is an L-STF
autocorrelation at lag 16 samples (0.8 us). MathWorks `wlanCoarseCFOEstimate` gives its maximum as 625 kHz, twice the
312.5 kHz subcarrier spacing. The fine estimate is an L-LTF autocorrelation at lag 64 (3.2 us), with a maximum of
156.25 kHz, half the spacing. Both cite Moose 1994 / Schmidl-Cox-type estimators. With the 802.11 tolerance of +-20 ppm
(5 GHz; +-25 ppm at 2.4 GHz, standard text not read), the relative offset is about +-232 kHz at 5.8 GHz. That is
0.0116 cycles/sample at 20 MS/s, or 0.74 of a subcarrier spacing [derived]. Pilot subcarriers then track the residual
phase. The two-stage lag-16 / lag-64 structure is what takeaway 3 transplants to single carrier.

## 2. Per-source table

CFO is normalised to the symbol (or chip) rate as |df / Rs| [derived] unless quoted. "Comparable?" is against our setting:
+-0.03 cycles/symbol, -5 ... +3 dB Es/N0, 1024-symbol coded QPSK burst, no pilots.

| # | Source (year) | Link | Rel. | Algorithm (DA / blind, overhead, coarse / fine) | Designed CFO -> normalised [derived] | Operating SNR | Reported performance / complexity | Comparable? |
|---|---|---|---|---|---|---|---|---|
| 1 | MathWorks, "802.11ad PER SC PHY simulation with TGay channel" (doc page, current) | [link](https://www.mathworks.com/help/wlan/ug/802-11ad-packet-error-rate-single-carrier-phy-simulation-with-tgay-channel.html) | medium | `dmgCFOEstimate(stf)` on the DMG STF (data-aided, single estimate), then correction | 20 ppm x 60 GHz = 1.2 MHz -> 6.8e-4 cycles/chip at 1.76 Gchip/s | MCS 9, 4096-byte PSDU, SNR 6-8.5 dB | PER 1 at 6 dB, 0.09 at 7.5 dB, 0.03 at 8.5 dB (only 100 packets per point, the page says "too small for meaningful results") | No: 25x smaller CFO, +6 dB, long PSDU |
| 2 | rfwireless-world, "WLAN 802.11ad physical layer" (tutorial) | [link](https://www.rfwireless-world.com/tutorials/wlan-802-11ad-physical-layer) | medium | SC STF = {16 x Ga128, -Ga128} (2176 chips), CEF = {Gu512, Gv512, -Gb128} (1152 chips) | n/a | SC 385-4620 Mb/s | structure only | Preamble overhead larger than our burst |
| 3 | rfwireless-world, "802.11ad RF PHY layer testing" | [link](https://www.rfwireless-world.com/articles/wlan-ieee-802-11ad-rf-phy-layer-testing) | medium | Tx centre-frequency and symbol-clock tolerance +-20 ppm; sensitivity table | +-20 ppm per device -> +-40 ppm relative -> 2.42 MHz -> **1.4e-3 cycles/chip** | MCS0 -78 dBm, MCS1 -68 dBm ... MCS12 -53 dBm -> about -6.5 / +3.5 / +18.5 dB per chip [derived, kTB over 1.76 GHz + NF 10 dB assumed] | EVM limits -6 ... -21 dB. The page's "+-3024 Hz" example is inconsistent with 20 ppm at 60 GHz (that is 1.2 MHz); treat it as a page error | MCS1 is above our SNR range |
| 4 | Liu, Wei, Huang, Chan, Jou, "All-digital synchronization for SC/OFDM mode of IEEE 802.15.3c and IEEE 802.11ad", IEEE TCSI 2015 | [doi](https://doi.org/10.1109/TCSI.2014.2361035) | medium | Joint preamble detection, boundary detection and CFO from the Golay STF (DA). Accumulated correlations reduce CFO noise | max tolerable CFO 114.58 ppm (SC), 171.87 ppm (OFDM) = lag-128 autocorrelation range at 1.76 / 2.64 GS/s [derived match] | not read | ASIC. Gate count and MSE not read (abstract not available; snippet only) | Estimator class only |
| 5 | MathWorks `wlanCoarseCFOEstimate` / `wlanFineCFOEstimate` reference pages | [coarse](https://www.mathworks.com/help/wlan/ref/wlancoarsecfoestimate.html), [fine](https://www.mathworks.com/help/wlan/ref/wlanfinecfoestimate.html) | low | OFDM Wi-Fi: L-STF autocorrelation (coarse), L-LTF autocorrelation (fine). Cites Moose 1994 and Li 2001 | coarse max 625 kHz (2 x subcarrier spacing), fine max 156.25 kHz (half the spacing), at 20 MHz -> 0.031 / 0.0078 cycles/sample | n/a | none | Same lags as the "Wi-Fi-style" competitor of takeaway 3 |
| 6 | 802.11b DSSS patents (US 8798210, US 7742548, US 9231648; search snippets) | [9231648](https://patents.google.com/patent/US9231648) | low | Long preamble 128 Barker-spread symbols (short: 56). Coarse CFO by correlating Barker outputs of consecutive symbols, residual limited to about +-5 ppm, then a phase-tracking loop | +-25 ppm per device, 50 ppm / about 120 kHz total -> 0.12 cycles per 1 Msym/s symbol, 0.011 cycles/chip | DBPSK 1 Mb/s, about 11 chips / symbol spreading gain | none read | No: differential, uncoded, high-SNR per symbol |
| 7 | Sharpe, Tong, Shin, Lee, "Synchronization for low-energy long-range communications", US 2018/0270091 | [link](https://ipiq.io/patents/5237399) | **high (method)** | BLE Coded preamble (10 x '00111100', 80 us) detected with an FFT of the correlation. 15.625 kHz bins; sums of 4 (or 6) bins over 27 combinations cover all offsets; alternate half-bin FFTs | +-200 kHz (150 Tx + 50 Rx) at 1 Msym/s -> **0.2 cycles/symbol** | "around 0 dB" | Half-bin offset costs about 3 dB. No detection numbers | Same idea as our CFO-cell grid; data-aided, GFSK |
| 8 | Keysight 89600 ICFT help + Nordic DevZone (quoting Core Spec Vol 6 Part A 3.1.2) | [Keysight](https://helpfiles.keysight.com/csg/89600B/Webhelp/Subsystems/bluetoothdemod/content/bluetooth_resultstbldata_icft.htm), [Nordic](https://devzone.nordicsemi.com/f/nordic-q-a/14478/nrf52832-frequency-tolerance-bluetooth) | medium | ICFT measured over the preamble | LE: +-150 kHz incl. drift; drift < 50 kHz, < 400 Hz/us; BR/EDR Tx +-75 kHz -> LE 1M 0.15, LE 2M 0.075, BR 0.075 cycles/symbol | n/a | n/a | CFO 2.5-5x ours relative to the symbol rate, but GFSK discriminator detection |
| 9 | MathWorks, "Bluetooth packet structure" | [link](https://www.mathworks.com/help/bluetooth/gs/bluetooth-packet-structure.html) | low | LE Coded: uncoded 80-symbol preamble, FEC block 1 (access address, CI, TERM1) always S = 8 | n/a | n/a | n/a | n/a |
| 10 | Zhang, Shi, Han, Li, Wang, Rabie, Kharel, "Implementation-friendly and energy-efficient symbol-by-symbol detection for IEEE 802.15.4 O-QPSK receivers", IEEE Access 8, 2020 | [doi](https://doi.org/10.1109/ACCESS.2020.3020183) | low | Residual CFO estimated from the preamble, then non-coherent detection | 802.15.4: +-40 ppm per device (patent snippets) -> about +-196 kHz at 2.45 GHz -> 0.098 cycles/chip (2 Mchip/s), 3.1 cycles per 16-ary symbol | 32-chip DSSS | **4 preamble symbols** are enough for CFO. Runtime 0.17x, +2.2 dB at PER 1e-3 vs the conventional detector | No: DSSS, non-coherent |
| 11 | 802.15.4 2450 MHz PHY: Nordic packet docs; IEEE 802.15.4b draft (unreadable PDF) | [Nordic](https://docs.nordicsemi.com/r/bundle/ps_nrf54lv10a/page/radio.html-ieee802154_packet), [draft](https://www.ieee802.org/15/pub/05/15-05-0101-01-004b-4b-phy-clause-draft.pdf) | low | SHR: 4 zero octets (8 symbols, 128 us) + SFD 0xA7, 160 us | see 10 | sensitivity at PER < 1 %, 20-octet PSDU | n/a | n/a |
| 12 | Xhonneux, Afisiadis, Bol, Louveaux, "A low-complexity LoRa synchronization algorithm robust to sampling time offsets", IEEE IoT-J (arXiv 1912.11344) | [link](https://arxiv.org/abs/1912.11344) | medium | Fractional CFO from the phase between consecutive upchirps (5 bins, N_C pairs); integer CFO from (s_up + s_down)/2; iterative with STO | +-20 ppm at 868 MHz = +-0.14 B (BW 125 kHz); range +-B/4 -> 0.14 / 0.25 cycles/chip | SF8, 1e5 trials; -9 dB = SER 1e-4 for an ideal receiver | <= 0.5 dB loss at PER 1e-2, about 1-2 dB at PER 1e-3 vs perfect sync; "very low" overhead, no numbers | Structure only |
| 13 | Tapparel, Burg, "LoRa fine synchronization with two-pass time and frequency offset estimation", Asilomar 2024 (arXiv 2502.08485) | [link](https://arxiv.org/abs/2502.08485) | low | Two-pass: fractional CFO, fractional STO, SFO compensated in the preamble, integer CFO / STO | [-B/4, B/4]; 40 ppm simulated (SF7-10), 32 ppm (SF12) | about -28 ... +5 dB per chip | SF12: without SFO compensation the SER floors at 46 %; preamble compensation gains 6 dB at SER 1e-3, within 1 dB of no-SFO. No CRB, no complexity numbers | No |
| 14 | Semtech SX1276/8 datasheet (Scribd copy) + Mobilefish LoRa tutorial | [Scribd](https://www.scribd.com/document/694010185/DS-SX1276-7-8-9-W-APP-V7), [Mobilefish](https://www.mobilefish.com/download/lora/lora_part16.pdf) | low | Chip limits | max Tx-Rx offset +-25 % of BW -> 0.25 cycles/chip | SNR limit -7.5 dB (SF7) ... -20 dB (SF12) per chip -> +13.6 ... +16.1 dB per LoRa symbol [derived] | n/a | No |
| 15 | CEA-Leti, "A TCXO-less 100 Hz-minimum-bandwidth transceiver for UNB sub-GHz IoT" (HAL cea-02195029; blocked, snippet only) | [link](https://hal.archives-ouvertes.fr/cea-02195029) | low | Sigfox-type UNB, DBPSK, non-coherent | tolerates CFO and drift of +-75 Hz at 100 b/s -> 0.75 cycles/symbol | n/a | n/a | No: the base station FFT-scans the band; 1-symbol differential |
| 16 | Wikipedia, "Mioty" | [link](https://en.wikipedia.org/wiki/Mioty) | low | Telegram splitting: about 15 ms bursts on 2 kHz carriers, pilots in each burst, convolutional FEC tolerates about 50 % burst loss | not given | not given | no CFO numbers; ETSI TS 103 357 not readable | No |
| 17 | Keysight 89600 HRP UWB "Frequency error compensation"; MathWorks "Recovery of IEEE 802.15.4z UWB signals" | [Keysight](https://helpfiles.keysight.com/csg/89600B/Webhelp/Subsystems/hrpuwb/content/hrpuwb_dlg_adv_initfreqerrcomp.htm), [MathWorks](https://it.mathworks.com/help/comm/ug/uwb-signal-recovery.html) | low | Analyzer: lock range about +-1 MHz, estimated on SYNC or the whole frame. MathWorks: coarse FFT compensator (1 kHz resolution) then a carrier synchroniser; 2.73 MHz coarse offset in its capture | +-1 MHz / 499.2 MHz -> 2e-3 cycles/chip | n/a | none | No: impulse radio, ranging |

Not found or not readable: the 802.11ay EDMG SC CFO and guard-interval tracking performance (only patents saying "CFO
estimated from the reference signal" turned up); any Intel / Qualcomm 60 GHz chip paper with CFO numbers; Bluetooth
Coded receiver CFO accuracy; Lanzisera & Pister 2007 (802.15.4 sensitivity limits, PDF undecodable); the ETSI mioty spec;
the Sigfox base-station algorithm.

## 3. Per-component verdict (vs these real systems)

| Our component | Real-system state of the art | Verdict |
|---|---|---|
| Coarse CFO (4th-power FFT fast path, Stage 1) | Data-aided repeated-preamble autocorrelation (802.11ad lag 128, Wi-Fi lag 16), FFT of the preamble correlation (BLE LR), up/down-chirp peaks (LoRa) | **We already use** the FFT form, blind. Theirs need a known preamble, so not applicable without pilots |
| CFO hypothesis grid (Stage 2 cells x phases) | Banks of frequency hypotheses / half-bin-shifted FFTs (BLE LR patent; US 11930461, title only) | **We already use it**, with a stronger score (decoder metric instead of preamble correlation) |
| Fine CFO / phase (Stage 3, code-aided retry) | Wi-Fi LTF / 802.11ad CEF fine estimate, then pilot or GI-Golay phase tracking (the 802.11ad GI = Ga64 per 512-chip block is not verified in a readable source) | **Not applicable**: needs known symbols. Our code-aided refinement is the blind counterpart |
| Acceptance (CRC + rho) | CRC / FCS only, after a preamble-detection threshold | **We are ahead**: the re-encoding check has no counterpart there |
| Complexity | Hardwired correlators; per-packet cost is tiny because the SNR per symbol is high | Not comparable: none of them decodes per hypothesis |

## 4. Competitor recommendation

- **Do not add** any of these as a main competitor. Each is either a weaker estimator on the same known energy (Wi-Fi /
  802.11ad autocorrelation vs our ML-128) or a different modulation regime (GFSK, DSSS, CSS, UNB) that cannot run at
  -5 dB per QPSK symbol with |f| up to 0.03.
- **Optional "deployed-practice" line** (only if the presentation needs a real-standard reference): "Wi-Fi-style
  STF/LTF", 128 extra known symbols, energy charged (+0.51 dB as in 8.2a):
  - coarse: lag-16 autocorrelation over 8 x 16 symbols, f_c = angle(sum r[n+16] r*[n]) / (2 pi 16);
  - fine: Moose on 2 x 64 symbols, lag 64, range +-0.0078; optionally a CRC search over the +-1 fine lobes as in our
    64 + 64 receiver.
  - Expected [derived, Gaussian, not simulated]: fine std about 1.9x the CRB std; 0.05-0.4 % coarse outliers at
    -4 ... -5 dB. So it should be worse than ML-128 everywhere, with a floor of about 1e-3 to 5e-3 near -5 dB at R = 1/10 and
    0.15 without a lobe search. Test: the est4 back-end, R = 0.15 at -4 / -3 / -2.5 dB and R = 1/2 at +1.5 / +2.5 dB,
    480k packets per point.
  - Derivation used: lag-D autocorrelation over L known symbols, var(f) ~ (1/SNR + 1/(2 SNR^2)) / ((2 pi D)^2 (L - D)).
    CRB for N = 128 known symbols: var = 6 / ((2 pi)^2 SNR N (N^2 - 1)). At SNR = -5 dB the CRB std is 4.8e-4 cycles/symbol.
- Comparability caveat: deployed standards were designed for CFO 5-25x smaller relative to the symbol rate (802.11ad,
  OFDM Wi-Fi) or for 10-20 dB more SNR per symbol (BLE, 15.4, LoRa, Sigfox). Their tolerance numbers are not a test of our
  regime.

## Reference entries

### MathWorks, "802.11ad Packet Error Rate Single Carrier PHY Simulation with TGay Channel", WLAN Toolbox documentation (accessed 2026-11-15)
- Link: https://www.mathworks.com/help/wlan/ug/802-11ad-packet-error-rate-single-carrier-phy-simulation-with-tgay-channel.html   - Type: app note (vendor example)   - Read depth: full
#### What it does
Applies CFO = 20 ppm x 60 GHz = 1.2 MHz (6.8e-4 cycles/chip at 1.76 Gchip/s [derived]), estimates it once from the DMG STF
with `dmgCFOEstimate`, corrects, decodes MCS 9 with 4096-byte PSDUs. PER 1 / 0.5 / 0.38 / 0.09 / 0.07 / 0.03 at 6 / 6.5 /
7 / 7.5 / 8 / 8.5 dB (100 packets max per point).
#### What we took / could take
Confirms that deployed 802.11ad SC CFO estimation is a one-shot data-aided STF estimate at a small normalised CFO. No
competitor needed from it.
#### Used in
-

### rfwireless-world, "WLAN 802.11ad Physical Layer Overview" (tutorial, accessed 2026-11-15)
- Link: https://www.rfwireless-world.com/tutorials/wlan-802-11ad-physical-layer   - Type: app note (tutorial)   - Read depth: full
#### What it does
SC STF = {16 x Ga128, -Ga128} (2176 chips); CEF = {Gu512, Gv512, -Gb128}; SC PHY 385-4620 Mb/s.
#### What we took / could take
Preamble overhead (about 3300 chips) exceeds our whole 1024-symbol burst, so the 802.11ad preamble is not a fair
transplant. Used for the comparability argument only.
#### Used in
-

### rfwireless-world, "WLAN IEEE 802.11ad RF PHY Layer Testing" (accessed 2026-11-15)
- Link: https://www.rfwireless-world.com/articles/wlan-ieee-802-11ad-rf-phy-layer-testing   - Type: app note (tutorial)   - Read depth: full
#### What it does
Tx centre frequency and symbol clock tolerance +-20 ppm; sensitivity MCS0 -78, MCS1 -68 ... MCS12 -53 dBm; EVM -6 ...
-21 dB. Relative CFO +-40 ppm at 60.48 GHz = +-2.42 MHz = 1.4e-3 cycles/chip [derived]. Per-chip SNR at sensitivity
about -6.5 dB (MCS0) and +3.5 dB (MCS1) [derived, NF 10 dB assumed]. The page's "+-3024 Hz" example looks wrong.
#### What we took / could take
Normalised CFO and SNR for the comparability verdict (802.11ad SC: 22x smaller CFO; its lowest SC MCS sits above our SNR
range).
#### Used in
-

### W.-C. Liu, T.-C. Wei, Y.-S. Huang, C.-D. Chan, S.-J. Jou, "All-Digital Synchronization for SC/OFDM Mode of IEEE 802.15.3c and IEEE 802.11ad", IEEE Trans. Circuits Syst. I, 2015
- Link: https://doi.org/10.1109/TCSI.2014.2361035   - Type: paper   - Read depth: snippet (metadata via Semantic Scholar; abstract not available)
#### What it does
Joint Golay preamble detection, boundary detection and CFO estimation ASIC. Reported max tolerable CFO 114.58 ppm (SC) and
171.87 ppm (OFDM), which equals the +-1/(2*128) range of a lag-128 autocorrelation at 1.76 / 2.64 GS/s and 60 GHz
[derived match].
#### What we took / could take
Confirms that the deployed 60 GHz CFO estimator is a lag-128 repeated-Golay autocorrelation. Not used further.
#### Used in
-

### MathWorks, `wlanCoarseCFOEstimate` and `wlanFineCFOEstimate` reference pages (accessed 2026-11-15)
- Link: https://www.mathworks.com/help/wlan/ref/wlancoarsecfoestimate.html ; https://www.mathworks.com/help/wlan/ref/wlanfinecfoestimate.html   - Type: app note (vendor reference)   - Read depth: full
#### What it does
OFDM Wi-Fi CFO estimation: L-STF autocorrelation, max 625 kHz (2 x subcarrier spacing); L-LTF autocorrelation, max
156.25 kHz (half the spacing). Cites Moose 1994 and Li 2001. At 20 MS/s that is 0.031 / 0.0078 cycles/sample [derived].
#### What we took / could take
Template for the optional "Wi-Fi-style STF/LTF" single-carrier competitor (lag 16 coarse, lag 64 fine, 128 known symbols).
#### Used in
-

### 802.11b DSSS CFO patents: US 8798210, US 7742548, US 9231648 (search snippets)
- Link: https://patents.google.com/patent/US9231648   - Type: patent   - Read depth: snippet
#### What it does
802.11b long preamble 128 Barker-spread symbols (short 56). +-25 ppm per device, 50 ppm / about 120 kHz total; coarse CFO
from the correlation of consecutive Barker outputs, residual target +-5 ppm, then a phase-tracking loop. 0.12 cycles per
1 Msym/s symbol [derived].
#### What we took / could take
Not used: differential DSSS at high SNR per symbol; no relevance to a coded QPSK burst at -5 dB.
#### Used in
-

### J. C. Sharpe, F. Tong, M.-C. Shin, J. Lee, "Synchronization for low-energy long-range communications", US 2018/0270091 A1, 2018
- Link: https://ipiq.io/patents/5237399   - Type: patent   - Read depth: full (web text)
#### What it does
BLE Coded (Long Range) preamble detection over +-200 kHz (150 kHz Tx + 50 kHz Rx; 0.2 cycles/symbol at 1 Msym/s
[derived]) at about 0 dB SNR. FFT of the preamble correlation with 15.625 kHz bins; sums of 4 (or 6) bins over 27
combinations; alternating half-bin-shifted FFTs because a half-bin offset costs about 3 dB. No detection numbers.
#### What we took / could take
Confirms that the frequency-hypothesis bank (our Stage 1 / Stage 2 CFO-cell grid) is deployed practice. The 3 dB half-bin
loss supports our peak-picked / interpolated fast path. Nothing new to adopt.
#### Used in
-

### Keysight 89600 VSA help, "ICFT (Bluetooth)"; Nordic DevZone thread "nRF52832 frequency tolerance Bluetooth" (quoting Bluetooth Core Spec Vol 6 Part A 3.1.2)
- Link: https://helpfiles.keysight.com/csg/89600B/Webhelp/Subsystems/bluetoothdemod/content/bluetooth_resultstbldata_icft.htm ; https://devzone.nordicsemi.com/f/nordic-q-a/14478/nrf52832-frequency-tolerance-bluetooth   - Type: app note / forum   - Read depth: snippet
#### What it does
LE: centre frequency within +-150 kHz including drift; drift < 50 kHz per packet, < 400 Hz/us; BR/EDR Tx +-75 kHz.
ICFT is measured over the preamble. Normalised: LE 1M 0.15, LE 2M 0.075, BR 0.075 cycles/symbol [derived].
#### What we took / could take
Comparability only (GFSK with discriminator detection, not coherent QPSK).
#### Used in
-

### MathWorks, "Bluetooth Packet Structure", Bluetooth Toolbox documentation (accessed 2026-11-15)
- Link: https://www.mathworks.com/help/bluetooth/gs/bluetooth-packet-structure.html   - Type: app note (vendor reference)   - Read depth: snippet
#### What it does
LE Coded: uncoded 80-symbol preamble ('00111100' x 10); FEC block 1 (access address, CI, TERM1) S = 8; CI selects S = 2 or
S = 8 for FEC block 2.
#### What we took / could take
Not used: structure reference only.
#### Used in
-

### G. Zhang, C. Shi, C. Han, X. Li, D. Wang, K. Rabie, R. Kharel, "Implementation-Friendly and Energy-Efficient Symbol-by-Symbol Detection Scheme for IEEE 802.15.4 O-QPSK Receivers", IEEE Access, vol. 8, pp. 158402-158415, 2020
- Link: https://doi.org/10.1109/ACCESS.2020.3020183   - Type: paper   - Read depth: abstract
#### What it does
Residual CFO estimated from the preamble, then non-coherent detection. 4 preamble symbols are enough for accurate CFO;
0.17x the running time and 2.2 dB gain at PER 1e-3 vs the conventional detector, (32, 4) DSSS. 802.15.4 +-40 ppm per device
(patent snippets) -> 0.098 cycles/chip, 3.1 cycles per 16-ary symbol [derived].
#### What we took / could take
Not used: DSSS non-coherent detection at high SNR per symbol.
#### Used in
-

### Nordic Semiconductor, nRF54L radio documentation, "IEEE 802.15.4 packet"; IEEE 802.15.4b PHY clause draft 15-05-0101-01
- Link: https://docs.nordicsemi.com/r/bundle/ps_nrf54lv10a/page/radio.html-ieee802154_packet ; https://www.ieee802.org/15/pub/05/15-05-0101-01-004b-4b-phy-clause-draft.pdf   - Type: app note / standard draft   - Read depth: snippet (draft PDF not decodable)
#### What it does
2.4 GHz SHR = 4 zero octets (8 symbols, 128 us) + SFD 0xA7 (160 us total). Sensitivity defined at PER < 1 % with a
20-octet PSDU.
#### What we took / could take
Not used: structure reference only.
#### Used in
-

### M. Xhonneux, O. Afisiadis, D. Bol, J. Louveaux, "A Low-Complexity LoRa Synchronization Algorithm Robust to Sampling Time Offsets", IEEE Internet of Things Journal (arXiv 1912.11344, v2 2021)
- Link: https://arxiv.org/abs/1912.11344   - Type: paper   - Read depth: full (first 100k characters of the HTML)
#### What it does
Fractional CFO from the phase between consecutive upchirps (5 bins around the peak, N_C pairs); integer CFO =
(s_up + s_down)/2; iterative STO. Range |df| <= B/4 (0.25 cycles/chip); 20 ppm at 868 MHz / 125 kHz = 0.14 B. SF8, 1e5
trials: <= 0.5 dB loss at PER 1e-2, about 1-2 dB at PER 1e-3 vs perfect sync. No CRB, no complexity numbers.
#### What we took / could take
Same integer + fractional split as our Stage 1 + Stage 2; confirmation only.
#### Used in
-

### J. Tapparel, A. Burg, "LoRa Fine Synchronization with Two-Pass Time and Frequency Offset Estimation", 58th Asilomar Conf., 2024, pp. 1802-1806 (arXiv 2502.08485)
- Link: https://arxiv.org/abs/2502.08485   - Type: paper   - Read depth: full (HTML)
#### What it does
Two-pass sync with SFO compensated in the preamble; CFO range [-B/4, B/4]; 40 ppm (SF7-10) and 32 ppm (SF12) simulated.
SF12: without SFO compensation the SER floors at 46 %; preamble compensation gives 6 dB at SER 1e-3, within 1 dB of no SFO.
#### What we took / could take
Not used: our timing is ideal and the burst is short (SFO negligible). Relevant only if a clock-offset study is added.
#### Used in
-

### Semtech SX1276/77/78/79 datasheet (Scribd copy, rev. 7); Mobilefish LoRa tutorial part 16
- Link: https://www.scribd.com/document/694010185/DS-SX1276-7-8-9-W-APP-V7 ; https://www.mobilefish.com/download/lora/lora_part16.pdf   - Type: datasheet / tutorial   - Read depth: snippet
#### What it does
LoRa demodulator SNR limit -7.5 dB (SF7) ... -20 dB (SF12) per chip, i.e. +13.6 ... +16.1 dB per LoRa symbol [derived].
Max tolerated Tx-Rx offset +-25 % of BW (0.25 cycles/chip).
#### What we took / could take
Comparability only.
#### Used in
-

### CEA-Leti, "A TCXO-less 100Hz-minimum-bandwidth transceiver for ultra-narrow-band sub-GHz IoT cellular networks" (HAL cea-02195029)
- Link: https://hal.archives-ouvertes.fr/cea-02195029   - Type: paper   - Read depth: snippet (page blocked by bot protection)
#### What it does
UNB (Sigfox-type) DBPSK transceiver tolerating CFO and drift of +-75 Hz at 100 b/s (0.75 cycles/symbol [derived]).
#### What we took / could take
Not used: one-symbol differential detection; the base station scans the band by FFT.
#### Used in
-

### Wikipedia, "Mioty" (accessed 2026-11-15)
- Link: https://en.wikipedia.org/wiki/Mioty   - Type: encyclopedia   - Read depth: full
#### What it does
Telegram splitting (ETSI TS 103 357): about 15 ms bursts on 2 kHz carriers, pilots in each burst, convolutional FEC tolerating
about 50 % burst loss. No CFO numbers.
#### What we took / could take
Not used: no CFO details; the ETSI spec could not be read.
#### Used in
-

### Keysight 89600 VSA help, "Frequency Error Compensation (802.15.4 HRP UWB)"; MathWorks, "Recovery of IEEE 802.15.4z UWB Signals"
- Link: https://helpfiles.keysight.com/csg/89600B/Webhelp/Subsystems/hrpuwb/content/hrpuwb_dlg_adv_initfreqerrcomp.htm ; https://it.mathworks.com/help/comm/ug/uwb-signal-recovery.html   - Type: app note   - Read depth: snippet (Keysight) / full (MathWorks)
#### What it does
Analyzer lock range about +-1 MHz (2e-3 cycles/chip at 499.2 MHz [derived]), estimated on SYNC or the whole frame.
MathWorks: coarse FFT compensator (1 kHz resolution, 2.73 MHz found), then a PAM carrier synchroniser.
#### What we took / could take
Not used: impulse-radio ranging PHY.
#### Used in
-
