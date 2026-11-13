# Stage 3 dump analysis: t-dump15a, t-dump15b@-1

## SNR -4 dB: 50000 packets, 199 not decoded right (BLER 3.98e-03), 826 by the fast path

**Where the MACs go (mean per packet)**

| part | MACs | share |
|---|---|---|
| fast path | 0.787 M | 11% |
| CA-SCL decodes (search + retries) | 1.865 M | 25% |
| rest (search metrics, refinement scoring, checks) | 4.668 M | 64% |
| total | 7.320 M | per core 0.644 M |

**Failure types** (packets not decoded right)

| type | packets |
|---|---|
| Stage 2: true CFO region not among the Stage 3 candidates | 117 |
| sync / list: true region reached but no CA-SCL-8 decode of it is right | 65 |
| selection: true packet in a final list but another path chosen | 0 |
| order / budget: a right decode exists among the top 6 but was not reached | 17 |

**Stage 3 hypotheses** 815376 in 135896 candidates; accepted right 256449, accepted wrong 3

**A / C: ranking inside a candidate** (decodes stop at the first acceptance)

| ranking | budget T | CA-SCL decodes | accepted right | accepted wrong | extra MACs (corr.) |
|---|---|---|---|---|---|
| path metric (baseline) | 1 | 135896 | 48122 | 0 | 0 |
| path metric (baseline) | 2 | 223670 | 48396 | 0 | 0 |
| path metric (baseline) | 3 | 311170 | 48513 | 0 | 0 |
| path metric (baseline) | 6 | 573166 | 48654 | 0 | 0 |
| SC-codeword correlation | 1 | 135896 | 47998 | 0 | 5009.67 M |
| SC-codeword correlation | 2 | 223794 | 48347 | 0 | 5009.67 M |
| SC-codeword correlation | 3 | 311343 | 48485 | 0 | 5009.67 M |
| SC-codeword correlation | 6 | 573381 | 48654 | 0 | 5009.67 M |
| metric, correlation as tie-break (|dM| < 1) | 1 | 135896 | 48124 | 0 | 5009.67 M |
| metric, correlation as tie-break (|dM| < 1) | 2 | 223668 | 48396 | 0 | 5009.67 M |
| metric, correlation as tie-break (|dM| < 1) | 3 | 311168 | 48514 | 0 | 5009.67 M |
| metric, correlation as tie-break (|dM| < 1) | 6 | 573157 | 48654 | 0 | 5009.67 M |
| joint z(metric) - z(correlation) | 1 | 135896 | 48087 | 0 | 5009.67 M |
| joint z(metric) - z(correlation) | 2 | 223705 | 48385 | 0 | 5009.67 M |
| joint z(metric) - z(correlation) | 3 | 311216 | 48503 | 0 | 5009.67 M |
| joint z(metric) - z(correlation) | 6 | 573228 | 48654 | 0 | 5009.67 M |

**B: screening** (skip hypotheses with rho_sc < t x sqrt(s / (1 + s)), metric order, T = 2)

| t | decodes | accepted right | accepted wrong | right hypotheses screened out |
|---|---|---|---|---|
| 0.0 | 223670 | 48396 | 0 | 0 of 256449 |
| 0.2 | 223670 | 48396 | 0 | 0 of 256449 |
| 0.3 | 223670 | 48396 | 0 | 0 of 256449 |
| 0.4 | 223670 | 48396 | 0 | 0 of 256449 |
| 0.5 | 223670 | 48396 | 0 | 0 of 256449 |

Predictive power (AUC, right-and-accepted vs other hypotheses): SC-codeword correlation 0.985, path metric 0.990.

**F: list re-ranking potential** hypotheses whose CA-SCL list holds the true packet but chose another path: 0 (of which CRC-passing chosen path: 0); hypotheses with the true packet in the list: 256456.

**J: half-packet consistency on accepted decodes** (wrong accepted vs right)

| statistic | right: 0.1 % quantile | wrong: max |
|---|---|---|
| rho | 0.470 | 0.515 |
| min(|C1|, |C2|) | 0.228 | 0.252 |
| |phase(C1 C2*)| | -0.887 | -0.236 |

## SNR -3 dB: 60000 packets, 6 not decoded right (BLER 1.00e-04), 1881 by the fast path

**Where the MACs go (mean per packet)**

| part | MACs | share |
|---|---|---|
| fast path | 0.783 M | 24% |
| CA-SCL decodes (search + retries) | 0.585 M | 18% |
| rest (search metrics, refinement scoring, checks) | 1.939 M | 59% |
| total | 3.307 M | per core 0.283 M |

**Failure types** (packets not decoded right)

| type | packets |
|---|---|
| Stage 2: true CFO region not among the Stage 3 candidates | 6 |
| sync / list: true region reached but no CA-SCL-8 decode of it is right | 0 |
| selection: true packet in a final list but another path chosen | 0 |
| order / budget: a right decode exists among the top 6 but was not reached | 0 |

**Stage 3 hypotheses** 366354 in 61059 candidates; accepted right 329697, accepted wrong 2

**A / C: ranking inside a candidate** (decodes stop at the first acceptance)

| ranking | budget T | CA-SCL decodes | accepted right | accepted wrong | extra MACs (corr.) |
|---|---|---|---|---|---|
| path metric (baseline) | 1 | 61059 | 57919 | 0 | 0 |
| path metric (baseline) | 2 | 64199 | 57954 | 0 | 0 |
| path metric (baseline) | 3 | 67304 | 57964 | 0 | 0 |
| path metric (baseline) | 6 | 76574 | 57974 | 0 | 0 |
| SC-codeword correlation | 1 | 61059 | 57898 | 0 | 2250.88 M |
| SC-codeword correlation | 2 | 64220 | 57946 | 0 | 2250.88 M |
| SC-codeword correlation | 3 | 67333 | 57959 | 0 | 2250.88 M |
| SC-codeword correlation | 6 | 76616 | 57974 | 0 | 2250.88 M |
| metric, correlation as tie-break (|dM| < 1) | 1 | 61059 | 57919 | 0 | 2250.88 M |
| metric, correlation as tie-break (|dM| < 1) | 2 | 64199 | 57954 | 0 | 2250.88 M |
| metric, correlation as tie-break (|dM| < 1) | 3 | 67304 | 57963 | 0 | 2250.88 M |
| metric, correlation as tie-break (|dM| < 1) | 6 | 76576 | 57974 | 0 | 2250.88 M |
| joint z(metric) - z(correlation) | 1 | 61059 | 57915 | 0 | 2250.88 M |
| joint z(metric) - z(correlation) | 2 | 64203 | 57952 | 0 | 2250.88 M |
| joint z(metric) - z(correlation) | 3 | 67310 | 57962 | 0 | 2250.88 M |
| joint z(metric) - z(correlation) | 6 | 76587 | 57974 | 0 | 2250.88 M |

**B: screening** (skip hypotheses with rho_sc < t x sqrt(s / (1 + s)), metric order, T = 2)

| t | decodes | accepted right | accepted wrong | right hypotheses screened out |
|---|---|---|---|---|
| 0.0 | 64199 | 57954 | 0 | 0 of 329697 |
| 0.2 | 64199 | 57954 | 0 | 0 of 329697 |
| 0.3 | 64199 | 57954 | 0 | 0 of 329697 |
| 0.4 | 64199 | 57954 | 0 | 0 of 329697 |
| 0.5 | 64199 | 57954 | 0 | 0 of 329697 |

Predictive power (AUC, right-and-accepted vs other hypotheses): SC-codeword correlation 0.994, path metric 0.997.

**F: list re-ranking potential** hypotheses whose CA-SCL list holds the true packet but chose another path: 0 (of which CRC-passing chosen path: 0); hypotheses with the true packet in the list: 329698.

**J: half-packet consistency on accepted decodes** (wrong accepted vs right)

| statistic | right: 0.1 % quantile | wrong: max |
|---|---|---|
| rho | 0.480 | 0.479 |
| min(|C1|, |C2|) | 0.250 | 0.257 |
| |phase(C1 C2*)| | -1.054 | -0.290 |

## SNR -1 dB: 100000 packets, 11 not decoded right (BLER 1.10e-04), 16889 by the fast path

**Where the MACs go (mean per packet)**

| part | MACs | share |
|---|---|---|
| fast path | 0.750 M | 32% |
| CA-SCL decodes (search + retries) | 0.568 M | 24% |
| rest (search metrics, refinement scoring, checks) | 1.031 M | 44% |
| total | 2.349 M | per core 0.237 M |

**Failure types** (packets not decoded right)

| type | packets |
|---|---|
| Stage 2: true CFO region not among the Stage 3 candidates | 10 |
| sync / list: true region reached but no CA-SCL-8 decode of it is right | 1 |
| selection: true packet in a final list but another path chosen | 0 |
| order / budget: a right decode exists among the top 6 but was not reached | 0 |

**Stage 3 hypotheses** 462170 in 92424 candidates; accepted right 286007, accepted wrong 0

**A / C: ranking inside a candidate** (decodes stop at the first acceptance)

| ranking | budget T | CA-SCL decodes | accepted right | accepted wrong | extra MACs (corr.) |
|---|---|---|---|---|---|
| path metric (baseline) | 1 | 92424 | 82162 | 0 | 0 |
| path metric (baseline) | 2 | 102686 | 82204 | 0 | 0 |
| path metric (baseline) | 3 | 112906 | 82220 | 0 | 0 |
| path metric (baseline) | 6 | 133354 | 82230 | 0 | 0 |
| SC-codeword correlation | 1 | 92424 | 82157 | 0 | 2839.57 M |
| SC-codeword correlation | 2 | 102691 | 82197 | 0 | 2839.57 M |
| SC-codeword correlation | 3 | 112918 | 82218 | 0 | 2839.57 M |
| SC-codeword correlation | 6 | 133372 | 82230 | 0 | 2839.57 M |
| metric, correlation as tie-break (|dM| < 1) | 1 | 92424 | 82161 | 0 | 2839.57 M |
| metric, correlation as tie-break (|dM| < 1) | 2 | 102687 | 82205 | 0 | 2839.57 M |
| metric, correlation as tie-break (|dM| < 1) | 3 | 112906 | 82221 | 0 | 2839.57 M |
| metric, correlation as tie-break (|dM| < 1) | 6 | 133354 | 82230 | 0 | 2839.57 M |
| joint z(metric) - z(correlation) | 1 | 92424 | 82165 | 0 | 2839.57 M |
| joint z(metric) - z(correlation) | 2 | 102683 | 82198 | 0 | 2839.57 M |
| joint z(metric) - z(correlation) | 3 | 112909 | 82221 | 0 | 2839.57 M |
| joint z(metric) - z(correlation) | 6 | 133357 | 82230 | 0 | 2839.57 M |

**B: screening** (skip hypotheses with rho_sc < t x sqrt(s / (1 + s)), metric order, T = 2)

| t | decodes | accepted right | accepted wrong | right hypotheses screened out |
|---|---|---|---|---|
| 0.0 | 102686 | 82204 | 0 | 0 of 286007 |
| 0.2 | 102686 | 82204 | 0 | 0 of 286007 |
| 0.3 | 102686 | 82204 | 0 | 0 of 286007 |
| 0.4 | 102686 | 82204 | 0 | 0 of 286007 |
| 0.5 | 102686 | 82204 | 0 | 0 of 286007 |

Predictive power (AUC, right-and-accepted vs other hypotheses): SC-codeword correlation 0.998, path metric 0.998.

**F: list re-ranking potential** hypotheses whose CA-SCL list holds the true packet but chose another path: 0 (of which CRC-passing chosen path: 0); hypotheses with the true packet in the list: 286037.

**J:** no wrong accepted decode among 286007 accepted (upper bound 1.0e-05); nothing for a second check to catch.
