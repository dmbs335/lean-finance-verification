# Epistemic-Crowding Event-Study Fixture

Run the preregistered controlled analysis from the repository root:

```bash
python -m tools.epistemic_event_study analyze \
  --plan examples/epistemic_event_study/vendor_shock.json \
  --out /tmp/epistemic-event-study.json
```

Verify a saved report by exact recomputation:

```bash
python -m tools.epistemic_event_study verify \
  --plan examples/epistemic_event_study/vendor_shock.json \
  --report /tmp/epistemic-event-study.json
```

The fixture is expected to emit `accepted-controlled`, with aggregate event DID
`2550 / 3 = 850` bps after the registration, matching, and pretrend gates pass.
The inputs are synthetic and do not establish a causal real-market effect.
