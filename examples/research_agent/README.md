# Bounded Research-Agent Fixture

Run:

```bash
python -m tools.research_agent --repository-root . run \
  --plan examples/research_agent/plan.json \
  --out /tmp/lfv-research-agent.json
```

Verify by exact recomputation:

```bash
python -m tools.research_agent --repository-root . verify \
  --plan examples/research_agent/plan.json \
  --report /tmp/lfv-research-agent.json
```

The fixture is expected to finish with `certified-bounded` after six controlled analysis gates pass. Exact attack remediation, bounded alpha uncertainty, portfolio selection, capacity stress, liquidation stress, and matched event-study acceptance are separate requirements.

Set `maximum_certifiable_interval_width_bps` below 520, `minimum_adjusted_portfolio_gain` above 280, or `minimum_event_study_average_did_bps` above 850 to exercise fail-closed rejection.
