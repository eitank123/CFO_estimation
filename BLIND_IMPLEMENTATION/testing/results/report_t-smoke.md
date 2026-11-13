# Stage 3 dump analysis: t-smoke

## SNR -5 dB: 600 packets, 0 not decoded right (BLER 0.00e+00), 4 by the fast path

**Where the MACs go (mean per packet)**

| part | MACs | share |
|---|---|---|
| fast path | 0.783 M | 19% |
| CA-SCL decodes (search + retries) | 0.579 M | 14% |
| rest (search metrics, refinement scoring, checks) | 2.808 M | 67% |
| total | 4.170 M | per core 0.308 M |

**Failure types** (packets not decoded right)

| type | packets |
|---|---|
| Stage 2: true CFO region not among the Stage 3 candidates | 0 |
| sync / list: true region reached but no CA-SCL-8 decode of it is right | 0 |
| selection: true packet in a final list but another path chosen | 0 |
| order / budget: a right decode exists among the top 6 but was not reached | 0 |

**Stage 3 hypotheses** 3684 in 614 candidates; accepted right 3295, accepted wrong 0

**A / C: ranking inside a candidate** (decodes stop at the first acceptance)

| ranking | budget T | CA-SCL decodes | accepted right | accepted wrong | extra MACs (corr.) |
|---|---|---|---|---|---|
| path metric (baseline) | 1 | 614 | 594 | 0 | 0 |
| path metric (baseline) | 2 | 634 | 594 | 0 | 0 |
| path metric (baseline) | 3 | 654 | 595 | 0 | 0 |
| path metric (baseline) | 6 | 711 | 595 | 0 | 0 |
| SC-codeword correlation | 1 | 614 | 594 | 0 | 22.63 M |
| SC-codeword correlation | 2 | 634 | 594 | 0 | 22.63 M |
| SC-codeword correlation | 3 | 654 | 594 | 0 | 22.63 M |
| SC-codeword correlation | 6 | 712 | 595 | 0 | 22.63 M |
| metric, correlation as tie-break (|dM| < 1) | 1 | 614 | 594 | 0 | 22.63 M |
| metric, correlation as tie-break (|dM| < 1) | 2 | 634 | 594 | 0 | 22.63 M |
| metric, correlation as tie-break (|dM| < 1) | 3 | 654 | 595 | 0 | 22.63 M |
| metric, correlation as tie-break (|dM| < 1) | 6 | 711 | 595 | 0 | 22.63 M |
| joint z(metric) - z(correlation) | 1 | 614 | 594 | 0 | 22.63 M |
| joint z(metric) - z(correlation) | 2 | 634 | 594 | 0 | 22.63 M |
| joint z(metric) - z(correlation) | 3 | 654 | 594 | 0 | 22.63 M |
| joint z(metric) - z(correlation) | 6 | 712 | 595 | 0 | 22.63 M |

**B: screening** (skip hypotheses with rho_sc < t x sqrt(s / (1 + s)), metric order, T = 2)

| t | decodes | accepted right | accepted wrong | right hypotheses screened out |
|---|---|---|---|---|
| 0.0 | 634 | 594 | 0 | 0 of 3295 |
| 0.2 | 634 | 594 | 0 | 0 of 3295 |
| 0.3 | 634 | 594 | 0 | 0 of 3295 |
| 0.4 | 634 | 594 | 0 | 0 of 3295 |
| 0.5 | 634 | 594 | 0 | 0 of 3295 |

Predictive power (AUC, right-and-accepted vs other hypotheses): SC-codeword correlation 0.989, path metric 0.994.

**F: list re-ranking potential** hypotheses whose CA-SCL list holds the true packet but chose another path: 0 (of which CRC-passing chosen path: 0); hypotheses with the true packet in the list: 3295.

**J:** no wrong accepted decode among 3295 accepted (upper bound 9.1e-04); nothing for a second check to catch.

## SNR -3 dB: 600 packets, 0 not decoded right (BLER 0.00e+00), 23 by the fast path

**Where the MACs go (mean per packet)**

| part | MACs | share |
|---|---|---|
| fast path | 0.782 M | 24% |
| CA-SCL decodes (search + retries) | 0.559 M | 17% |
| rest (search metrics, refinement scoring, checks) | 1.863 M | 58% |
| total | 3.204 M | per core 0.274 M |

**Failure types** (packets not decoded right)

| type | packets |
|---|---|
| Stage 2: true CFO region not among the Stage 3 candidates | 0 |
| sync / list: true region reached but no CA-SCL-8 decode of it is right | 0 |
| selection: true packet in a final list but another path chosen | 0 |
| order / budget: a right decode exists among the top 6 but was not reached | 0 |

**Stage 3 hypotheses** 3522 in 587 candidates; accepted right 3302, accepted wrong 0

**A / C: ranking inside a candidate** (decodes stop at the first acceptance)

| ranking | budget T | CA-SCL decodes | accepted right | accepted wrong | extra MACs (corr.) |
|---|---|---|---|---|---|
| path metric (baseline) | 1 | 587 | 575 | 0 | 0 |
| path metric (baseline) | 2 | 599 | 575 | 0 | 0 |
| path metric (baseline) | 3 | 611 | 575 | 0 | 0 |
| path metric (baseline) | 6 | 647 | 575 | 0 | 0 |
| SC-codeword correlation | 1 | 587 | 575 | 0 | 21.64 M |
| SC-codeword correlation | 2 | 599 | 575 | 0 | 21.64 M |
| SC-codeword correlation | 3 | 611 | 575 | 0 | 21.64 M |
| SC-codeword correlation | 6 | 647 | 575 | 0 | 21.64 M |
| metric, correlation as tie-break (|dM| < 1) | 1 | 587 | 575 | 0 | 21.64 M |
| metric, correlation as tie-break (|dM| < 1) | 2 | 599 | 575 | 0 | 21.64 M |
| metric, correlation as tie-break (|dM| < 1) | 3 | 611 | 575 | 0 | 21.64 M |
| metric, correlation as tie-break (|dM| < 1) | 6 | 647 | 575 | 0 | 21.64 M |
| joint z(metric) - z(correlation) | 1 | 587 | 575 | 0 | 21.64 M |
| joint z(metric) - z(correlation) | 2 | 599 | 575 | 0 | 21.64 M |
| joint z(metric) - z(correlation) | 3 | 611 | 575 | 0 | 21.64 M |
| joint z(metric) - z(correlation) | 6 | 647 | 575 | 0 | 21.64 M |

**B: screening** (skip hypotheses with rho_sc < t x sqrt(s / (1 + s)), metric order, T = 2)

| t | decodes | accepted right | accepted wrong | right hypotheses screened out |
|---|---|---|---|---|
| 0.0 | 599 | 575 | 0 | 0 of 3302 |
| 0.2 | 599 | 575 | 0 | 0 of 3302 |
| 0.3 | 599 | 575 | 0 | 0 of 3302 |
| 0.4 | 599 | 575 | 0 | 0 of 3302 |
| 0.5 | 599 | 575 | 0 | 0 of 3302 |

Predictive power (AUC, right-and-accepted vs other hypotheses): SC-codeword correlation 0.992, path metric 0.995.

**F: list re-ranking potential** hypotheses whose CA-SCL list holds the true packet but chose another path: 0 (of which CRC-passing chosen path: 0); hypotheses with the true packet in the list: 3302.

**J:** no wrong accepted decode among 3302 accepted (upper bound 9.1e-04); nothing for a second check to catch.
