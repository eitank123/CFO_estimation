# Data card: the full systems we compare against (2026-11-17)

Blind = our system: no pilots, blind CFO/phase search, polar CA-SCL-8 + CRC-32, re-encoding check, rate-matched
to each competitor's payload and coded length. Channel for everyone: CFO up to +-0.03 (normalised to the symbol
rate), AWGN, timing known. Comparison axis: Eb/N0 per payload bit, every known symbol charged.
Sign of every gap: **+ = blind better**. Predictions: [expected_fullsys.md](expected_fullsys.md).
Published curves: [plots/DVB-RCS2/BLER/fullsys_refs.png](plots/DVB-RCS2/BLER/fullsys_refs.png).

## 1. DVB-RCS2 (ETSI EN 301 545-2, TC-LM return link)
Satellite return link: thousands of terminals send short bursts to a hub (MF-TDMA). Deployed in commercial VSAT
hubs and terminals (e.g. ST Engineering iDirect / Newtec, Gilat). Standard 2012, code inherited from DVB-RCS (2000).

| ID | Modulation | Code rate | Payload + CRC-32 | Burst (known symbols) | Es/N0 @PER 1e-3 / 1e-5 | Eb/N0 per payload bit @1e-3 |
|---|---|---|---|---|---|---|
| 3 | QPSK | 1/3 | 272 + 32 bits | 536 (80 = 15 %) | -0.27 / 0.22 dB | 2.68 dB |
| 13 | QPSK | 1/3 | 952 + 32 bits | 1616 (140 = 9 %) | -0.80 / -0.51 dB | 1.50 dB |
| 14 | QPSK | 1/2 | 1472 + 32 bits | 1616 (112 = 7 %) | 1.49 / 1.71 dB | 1.90 dB |
| 42 | pi/2-BPSK | 1/3 | 952 + 32 bits | 3236 (284 = 9 %) | -3.81 / -3.52 dB | 1.50 dB |

- **SNR region:** our test window is Es/N0 -4.5 to +2.5 dB. The standard's full family runs from -3.8 dB (ID 42)
  to +12 dB (16QAM 5/6); we test only the low-SNR end.
- **Code rates:** the lowest native rate is 1/3. Below that, DVB-RCS2 switches to spread spectrum, which has no
  published PER. The full family has 1/3, 1/2, 2/3, 3/4, 5/6.
- **Expected BLER:** the operating points are PER 1e-3 to 1e-5; the TR quotes both, at ideal sync. We measure full
  curves from about 1e-1 to 1e-5.

## 2. VDE-SAT (ITU-R M.2092-2, VHF Data Exchange, satellite link)
Maritime VHF data exchange via LEO satellites, the successor to AIS. Standard 2022/2026, IALA G1139. In trials (e.g. the
VDE payload on NorSat-2).

| Link | Modulation | Code rate | Payload + CRC-32 | Burst (known symbols) | Es/N0 design point | Eb/N0 per payload bit |
|---|---|---|---|---|---|---|
| 32 (main test) | BPSK + spreading x8 | 1/4 | 280 + 32 bits | 1641 (372 = 23 %) | -4.5 dB | 3.18 dB |
| 33 | BPSK | 1/3 | 4248 + 32 bits | 13143 (288) | -3.6 dB | 1.31 dB |
| 26 | pi/4-QPSK | 1/4 | 7 x 5456 bits | 80343 (3885) | -2.4 dB | 0.86 dB |
| 34 | pi/4-QPSK | 1/3 | 2 x 4160 bits | 13122 (642) | -0.6 dB | 1.41 dB |

- **SNR region:** Es/N0 -4.5 to -0.6 dB. Link 32 is the low-SNR, short-packet case closest to ours.
- **Code rates:** 1/4 and 1/3 on the satellite links; 1/2 and 3/4 on the terrestrial links.
- **Expected BLER:** the design target is PER 1e-2, because ARQ retransmits failures (M.2435 sec. 4.3.1). We
  measure down to 1e-4.
- **Validation curve:** M.2435 Fig. 11 (88 bits, QPSK, rate 1/4): PER 1e-2 at Es/N0 -1.5 dB.

## 3. What is similar and what is not

| Part | DVB-RCS2 | VDE-SAT | Blind (ours) |
|---|---|---|---|
| Modulation | QPSK, pi/2-BPSK | BPSK (+ spreading), pi/4-QPSK | same as theirs, rate-matched; ID 42 also on QPSK |
| Payload / CRC | CRC-32 | CRC-32 | **same payload + CRC-32** |
| FEC | 16-state duo-binary turbo, tail-biting | 8-state turbo (3GPP2 / CCSDS family) | polar, length up to 4096, NR-style puncture / shorten |
| Decoder | max-log-MAP, 8 iterations (iterative, parallel) | max-log or log-MAP, 6-8 iterations | CA-SCL list 8 (sequential) |
| Acceptance | CRC only | CRC only | CRC + re-encoding check |
| Sync | unique word + pilots, data-aided | 4 syncwords + pilot every 8 symbols, data-aided | **no known symbols:** blind search over CFO and phase, scored by the decoder |
| Known-symbol overhead | 7-15 % of the burst | 23 % of the burst | 0 % |
| Designed CFO range | 0.5 % .. 3 % of the symbol rate (+-0.005 .. +-0.03; TR 101 545-4 6.2.2, gateway-dependent); pilot aliases at +-0.04 .. 0.056 | large: LEO Doppler up to +-4 kHz + 1 ppm carrier error, no frequency pre-compensation clause in M.2092-2 (A5-2.1.2); about +-0.99/symbol on Link 32, +-0.12 on 33.6 ksym/s links; syncwords chosen for differential detection | +-0.03 |
| Error floor | turbo: possible at low PER | turbo: possible | polar + CRC list: none seen |

## 4. Where we expect to improve, and where we expect to lose

| Where | Expected | Why |
|---|---|---|
| ID 3 (short burst) | **blind +0.85 dB** | 15 % pilot overhead saved, polar strong at short K, DVB-RCS2 sync weak with 80 known symbols |
| ID 13 | **blind +0.35 dB** | 0.39 dB overhead saved; the turbo code is 0.1-0.2 dB stronger, which eats part of it |
| ID 14 shortened (4 phases) | **blind +0.24 dB** | 0.31 dB overhead saved; turbo about 0.1 dB stronger |
| ID 14 forced puncture | tie (+0.06) | puncturing at rate 1/2 costs the polar code about 0.2 dB |
| ID 42 (pi/2-BPSK) | **blind +0.39 dB** | overhead + DA sync loss at Es/N0 -3.8 dB per symbol |
| VDE Link 32 | **blind +0.55 dB** vs VDE with real sync (+0.9 vs its published design point) | 23 % known symbols = 1.12 dB saved, polar strong at K = 312; blind's own sync loss (about 0.25 dB) and the 8-state turbo's real-sync loss partly cancel |
| Code alone (genie sync both) | **loss 0.1-0.2 dB at K >= 1000**, tie at K = 304 | 16-state duo-binary turbo is about the strongest classic code at these sizes; list 8 plus CRC-32 costs the polar code a little |
| CFO near +-0.03 | about even | +-0.03 is inside DVB-RCS2's design range; its DA estimator loses only ~0.02-0.04 dB (verifier); aliases are caught by a CRC retry |
| Complexity (MACs per core) | **blind 2-3x more** (3.5-4x if the turbo uses early stop) | the blind search grid over CFO x phase dominates; the turbo is 8-12x one polar decode, which shrinks the gap from 3-7x in est4 |
| Latency / hardware | blind worse | SCL is sequential; turbo decoders parallelise over windows |
| Spectral efficiency | blind better | same payload in 7-23 % fewer symbols (VDE: also no x8 spreading) |

Uncertainty on the blind numbers is +-0.15 dB: rate matching at N = 4096 and the early-stop retune are new.
Nothing is measured yet. Smoke jobs for DVB-RCS2, VDE-SAT and the polar rate matching are running on the cluster.
