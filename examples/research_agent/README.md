# Bounded Research-Agent Fixture

Run the registered controlled plan from the repository root:

```bash
python -m tools.research_agent \
  --repository-root . \
  run \
  --plan examples/research_agent/plan.json \
  --out /tmp/lfv-research-agent.json
```

Verify a previously emitted report by exact recomputation:

```bash
python -m tools.research_agent \
  --repository-root . \
  verify \
  --plan examples/research_agent/plan.json \
  --report /tmp/lfv-research-agent.json
```

The fixture is expected to finish with `certified-bounded`. That status means
all four finite, controlled analysis gates passed and their canonical digests
were bound to the registered plan. It does not certify a real trading strategy,
real market data, or causal market calibration.

Increase `minimum_adjusted_portfolio_gain` above the controlled gain of 280 to
exercise fail-closed behavior: the agent emits a diagnostic `rejected` report
and no certificate.
