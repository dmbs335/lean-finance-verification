# Certifiable Alpha Under Model, Attack, and Deployment Uncertainty

Identifying research-process attacks removes one source of alpha bias; it does not reveal one exact expected return. This module combines three remaining uncertainty layers:

1. a finite envelope across declared statistical/risk models;
2. maximum upward inflation from integrity distortions not detected by the selected evidence;
3. a minimum/maximum deployment-cost range.

For one evidence selection:

```text
lower = minimum model lower bound
        - maximum unresolved upward inflation
        - maximum deployment cost

upper = maximum model upper bound
        - minimum deployment cost
```

The exact solver enumerates every evidence subset and finds the minimum cost satisfying a target interval width.

## Controlled result

Without evidence, 650 bps of future-information, survivorship, and parameter-mining inflation remains possible. The deployable-alpha interval is `[-620, 550]`, width 1,170 bps.

`pitDataReceipt + searchLedger` detects every declared distortion at cost 5 and narrows the interval to `[30, 550]`, width 520 bps. The unified attestation also works but costs 6.

Crucially, the interval does not collapse to one point. After attack uncertainty is removed, the three declared models still span 150–600 bps and deployment costs span 50–120 bps. The remaining 520 bps is model and implementation uncertainty, not an unresolved integrity attack.

The numerical bounds are controlled assumptions, not estimated confidence intervals. A real application must justify each model interval, distortion bound, and cost range statistically and empirically.
