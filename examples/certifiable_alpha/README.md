# Certifiable-Alpha Uncertainty Fixture

Run the exact evidence search from the repository root:

```bash
python -m tools.certifiable_alpha_interval analyze \
  --model examples/certifiable_alpha/uncertainty.json \
  --out /tmp/certifiable-alpha-interval.json
```

The expected minimum-cost evidence set is:

```text
pitDataReceipt
searchLedger
```

It removes all 650 bps of declared attack inflation and narrows the deployable
alpha interval from `[-620, 550]` to `[30, 550]`. The remaining 520 bps is not a
missed attack in this fixture; it comes from the declared model envelope and
deployment-cost range.

The fixture is controlled. Its interval endpoints, attack maxima, and costs are
inputs, not estimates from market data.
