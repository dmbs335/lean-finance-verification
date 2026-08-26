# GS Quant-Style Temporal Noninterference Fixture

Run the controlled semantic audit from the repository root:

```bash
python -m tools.temporal_noninterference analyze \
  --model examples/temporal_noninterference/gs_quant_style.json \
  --out /tmp/temporal-noninterference.json
```

Verify the report by exact recomputation:

```bash
python -m tools.temporal_noninterference verify \
  --model examples/temporal_noninterference/gs_quant_style.json \
  --report /tmp/temporal-noninterference.json
```

The fixture contains one causal forward-fill engine and four deliberately unsafe
semantics representing common financial backtest failure classes:

- fallback to the final row of the complete source;
- use of observation time without release/availability time;
- bidirectional interpolation through a future endpoint;
- in-place source sorting combined with global-last fallback.

The registered mutations append extreme future rows, revise a future endpoint,
reorder equivalent data, change timestamp representation, revise already-known
past information, and change release availability.

Only mutations preserving the causal prefix at every audited decision can
constitute a temporal-noninterference counterexample. This prevents a legitimate
change in decision-time information from being mislabeled as leakage.

The benchmark is independent of `gs-quant`. A concrete adapter can map
`GenericDataSource` and backtest results into the same causal-prefix and
output-prefix contract without making that package a mandatory dependency.
