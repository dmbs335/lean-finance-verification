# Research-Agent Fixtures

## Bounded multi-analysis plan

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

The fixture is expected to finish with `certified-bounded` after seven controlled analysis gates pass. Exact attack remediation, bounded alpha uncertainty, portfolio selection, capacity stress, liquidation stress, matched event-study acceptance, and certificate composition are separate requirements.

The composition fixture selects the two narrow bridge receipts at cost 4. Set `maximum_composition_evidence_cost` to 3 to verify that all local analyses can remain green while the final certificate is still rejected for insufficient composition budget.

Other fail-closed controls include setting `maximum_certifiable_interval_width_bps` below 520, `minimum_adjusted_portfolio_gain` above 280, or `minimum_event_study_average_did_bps` above 850.

## Candidate review and evidence repair

Run the five-candidate gate:

```bash
python -m tools.research_agent gate-candidates \
  --batch examples/research_agent/candidates.json \
  --out /tmp/lfv-research-candidates.json
```

Expected decisions:

```text
advanceToHumanReview: 1
repairEvidence:       2
rejectCandidate:      2
```

The machine cannot deploy a strategy. A positive decision only prepares a candidate for mandatory human review. High observed alpha cannot bypass an unresolved evidence obligation, and a process-valid candidate is rejected when its impact- and capacity-adjusted lower bound is nonpositive.
