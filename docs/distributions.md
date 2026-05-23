# Probability Distributions

All distributions used in the simulation, with type and parameters.

## Random Input Variables

| Variable | Name | Distribution | Parameters | Notes |
|---|---|---|---|---|
| IA | Inter-arrival time | Exponential | rate=2.0 orders/hr | Mean = 0.5 hr between orders |
| PCP | Page count | Discrete weighted | values=[100,200,300,400], weights=[0.3,0.4,0.2,0.1] | 200 pages most common |
| CUL | Units per order | Uniform integer | min=100, max=500 | Books per order |
| PD | Defect probability | Bernoulli (via Uniform) | p=0.05 | Sample U(0,1); fail if < PD |
| TPI | Printing time per lot | Exponential | mean=2.0 hr | Per lot, per machine |
| TPE_b | Binding time per lot | Exponential | mean=1.5 hr | |
| TPQA | QA inspection time | Uniform | min=0.5, max=1.5 hr | |
| TPE_p | Packaging time per lot | Normal | mean=0.8, std=0.1 hr | Clipped at 0 |
| TEF[0] | Printing failure interval | Exponential | mean=40.0 hr (MTBF) | Time between failures |
| TEF[1] | Binding failure interval | Exponential | mean=60.0 hr | |
| TEF[2] | QA failure interval | Exponential | mean=100.0 hr | |
| TEF[3] | Packaging failure interval | Exponential | mean=80.0 hr | |
| TDR[0] | Printing repair duration | Exponential | mean=2.0 hr | |
| TDR[1] | Binding repair duration | Exponential | mean=1.5 hr | |
| TDR[2] | QA repair duration | Exponential | mean=1.0 hr | |
| TDR[3] | Packaging repair duration | Exponential | mean=1.0 hr | |
| TMM[0] | Printing maintenance duration | Normal | mean=3.0, std=0.3 hr | |
| TMM[1] | Binding maintenance duration | Normal | mean=2.0, std=0.2 hr | |
| TMM[2] | QA maintenance duration | Normal | mean=1.0, std=0.1 hr | |
| TMM[3] | Packaging maintenance duration | Normal | mean=1.5, std=0.15 hr | |
| LT[0] | Paper replenishment lead time | Uniform | min=1.0, max=3.0 hr | |
| LT[1] | Ink replenishment lead time | Uniform | min=0.5, max=2.0 hr | |
| LT[2] | Binding material lead time | Uniform | min=1.0, max=2.0 hr | |
| LT[3] | Adhesive lead time | Uniform | min=0.5, max=1.5 hr | |
| LT[4] | Packaging material lead time | Uniform | min=1.0, max=2.5 hr | |

## PRNG Stream Names

Each variable gets its own named stream derived from the master seed via
`numpy.random.SeedSequence.spawn()`. Stream names used in code:

```
"IA", "PCP", "CUL", "PD",
"TEF_0", "TEF_1", "TEF_2", "TEF_3",
"TDR_0", "TDR_1", "TDR_2", "TDR_3",
"TMM_0", "TMM_1", "TMM_2", "TMM_3",
"TPI", "TPE_b", "TPQA", "TPE_p",
"LT_0", "LT_1", "LT_2", "LT_3", "LT_4",
"BOOK_TYPE", "PRIORITY"
```

Adding or removing any one stream does not shift the others (independent
child sequences via `SeedSequence`).
