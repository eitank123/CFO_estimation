# Stage 3 dump analysis: t-dump10

## SNR -5 dB: 100000 packets, 16 not decoded right (BLER 1.60e-04), 1370 by the fast path

**Where the MACs go (mean per packet)**

| part | MACs | share |
|---|---|---|
| fast path | 0.782 M | 19% |
| CA-SCL decodes (search + retries) | 0.622 M | 15% |
| rest (search metrics, refinement scoring, checks) | 2.753 M | 66% |
| total | 4.157 M | per core 0.313 M |

**Failure types** (packets not decoded right)

| type | packets |
|---|---|
| Stage 2: true CFO region not among the Stage 3 candidates | 14 |
| sync / list: true region reached but no CA-SCL-8 decode of it is right | 1 |
| selection: true packet in a final list but another path chosen | 0 |
| order / budget: a right decode exists among the top 6 but was not reached | 1 |

**Stage 3 hypotheses** 644880 in 107480 candidates; accepted right 552883, accepted wrong 8

**A / C: ranking inside a candidate** (decodes stop at the first acceptance)

| ranking | budget T | CA-SCL decodes | accepted right | accepted wrong | extra MACs (corr.) |
|---|---|---|---|---|---|
| path metric (baseline) | 1 | 107480 | 98090 | 0 | 0 |
| path metric (baseline) | 2 | 116870 | 98224 | 0 | 0 |
| path metric (baseline) | 3 | 126126 | 98277 | 0 | 0 |
| path metric (baseline) | 6 | 153688 | 98319 | 0 | 0 |
| SC-codeword correlation | 1 | 107480 | 98010 | 0 | 3962.14 M |
| SC-codeword correlation | 2 | 116950 | 98196 | 0 | 3962.14 M |
| SC-codeword correlation | 3 | 126234 | 98263 | 0 | 3962.14 M |
| SC-codeword correlation | 6 | 153813 | 98319 | 0 | 3962.14 M |
| metric, correlation as tie-break (|dM| < 1) | 1 | 107480 | 98090 | 0 | 3962.14 M |
| metric, correlation as tie-break (|dM| < 1) | 2 | 116870 | 98222 | 0 | 3962.14 M |
| metric, correlation as tie-break (|dM| < 1) | 3 | 126128 | 98276 | 0 | 3962.14 M |
| metric, correlation as tie-break (|dM| < 1) | 6 | 153694 | 98319 | 0 | 3962.14 M |
| joint z(metric) - z(correlation) | 1 | 107480 | 98066 | 0 | 3962.14 M |
| joint z(metric) - z(correlation) | 2 | 116894 | 98219 | 0 | 3962.14 M |
| joint z(metric) - z(correlation) | 3 | 126155 | 98266 | 0 | 3962.14 M |
| joint z(metric) - z(correlation) | 6 | 153726 | 98319 | 0 | 3962.14 M |

**B: screening** (skip hypotheses with rho_sc < t x sqrt(s / (1 + s)), metric order, T = 2)

| t | decodes | accepted right | accepted wrong | right hypotheses screened out |
|---|---|---|---|---|
| 0.0 | 116870 | 98224 | 0 | 0 of 552883 |
| 0.2 | 116870 | 98224 | 0 | 0 of 552883 |
| 0.3 | 116870 | 98224 | 0 | 0 of 552883 |
| 0.4 | 116870 | 98224 | 0 | 0 of 552883 |
| 0.5 | 116870 | 98224 | 0 | 0 of 552883 |

Predictive power (AUC, right-and-accepted vs other hypotheses): SC-codeword correlation 0.981, path metric 0.985.

**F: list re-ranking potential** hypotheses whose CA-SCL list holds the true packet but chose another path: 0 (of which CRC-passing chosen path: 0); hypotheses with the true packet in the list: 552888.

**J: half-packet consistency on accepted decodes** (wrong accepted vs right)

| statistic | right: 0.1 % quantile | wrong: max |
|---|---|---|
| rho | 0.403 | 0.440 |
| min(|C1|, |C2|) | 0.203 | 0.208 |
| |phase(C1 C2*)| | -1.090 | -0.006 |

## SNR -4.5 dB: 50000 packets, 0 not decoded right (BLER 0.00e+00), 793 by the fast path

**Where the MACs go (mean per packet)**

| part | MACs | share |
|---|---|---|
| fast path | 0.781 M | 23% |
| CA-SCL decodes (search + retries) | 0.572 M | 17% |
| rest (search metrics, refinement scoring, checks) | 2.062 M | 60% |
| total | 3.415 M | per core 0.276 M |

**Failure types** (packets not decoded right)

| type | packets |
|---|---|
| Stage 2: true CFO region not among the Stage 3 candidates | 0 |
| sync / list: true region reached but no CA-SCL-8 decode of it is right | 0 |
| selection: true packet in a final list but another path chosen | 0 |
| order / budget: a right decode exists among the top 6 but was not reached | 0 |

**Stage 3 hypotheses** 302334 in 50389 candidates; accepted right 282450, accepted wrong 1

**A / C: ranking inside a candidate** (decodes stop at the first acceptance)

| ranking | budget T | CA-SCL decodes | accepted right | accepted wrong | extra MACs (corr.) |
|---|---|---|---|---|---|
| path metric (baseline) | 1 | 50389 | 49084 | 0 | 0 |
| path metric (baseline) | 2 | 51694 | 49109 | 0 | 0 |
| path metric (baseline) | 3 | 52974 | 49120 | 0 | 0 |
| path metric (baseline) | 6 | 56766 | 49129 | 0 | 0 |
| SC-codeword correlation | 1 | 50389 | 49064 | 0 | 1857.54 M |
| SC-codeword correlation | 2 | 51714 | 49106 | 0 | 1857.54 M |
| SC-codeword correlation | 3 | 52997 | 49117 | 0 | 1857.54 M |
| SC-codeword correlation | 6 | 56796 | 49129 | 0 | 1857.54 M |
| metric, correlation as tie-break (|dM| < 1) | 1 | 50389 | 49084 | 0 | 1857.54 M |
| metric, correlation as tie-break (|dM| < 1) | 2 | 51694 | 49109 | 0 | 1857.54 M |
| metric, correlation as tie-break (|dM| < 1) | 3 | 52974 | 49119 | 0 | 1857.54 M |
| metric, correlation as tie-break (|dM| < 1) | 6 | 56767 | 49129 | 0 | 1857.54 M |
| joint z(metric) - z(correlation) | 1 | 50389 | 49080 | 0 | 1857.54 M |
| joint z(metric) - z(correlation) | 2 | 51698 | 49109 | 0 | 1857.54 M |
| joint z(metric) - z(correlation) | 3 | 52978 | 49117 | 0 | 1857.54 M |
| joint z(metric) - z(correlation) | 6 | 56776 | 49129 | 0 | 1857.54 M |

**B: screening** (skip hypotheses with rho_sc < t x sqrt(s / (1 + s)), metric order, T = 2)

| t | decodes | accepted right | accepted wrong | right hypotheses screened out |
|---|---|---|---|---|
| 0.0 | 51694 | 49109 | 0 | 0 of 282450 |
| 0.2 | 51694 | 49109 | 0 | 0 of 282450 |
| 0.3 | 51694 | 49109 | 0 | 0 of 282450 |
| 0.4 | 51694 | 49109 | 0 | 0 of 282450 |
| 0.5 | 51694 | 49109 | 0 | 0 of 282450 |

Predictive power (AUC, right-and-accepted vs other hypotheses): SC-codeword correlation 0.988, path metric 0.989.

**F: list re-ranking potential** hypotheses whose CA-SCL list holds the true packet but chose another path: 0 (of which CRC-passing chosen path: 0); hypotheses with the true packet in the list: 282456.

**J: half-packet consistency on accepted decodes** (wrong accepted vs right)

| statistic | right: 0.1 % quantile | wrong: max |
|---|---|---|
| rho | 0.406 | 0.432 |
| min(|C1|, |C2|) | 0.214 | 0.207 |
| |phase(C1 C2*)| | -1.172 | -0.131 |
