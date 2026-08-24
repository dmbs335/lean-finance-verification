# Proof-Carrying Research Agent Harness

The v4 research-agent harness connects seven controlled analyses under one registered plan:

```text
fake-alpha audit
→ certifiable-alpha interval gate
→ evidence-adjusted portfolio selection
→ certifiability/capacity stress
→ shared-evidence liquidation stress
→ preregistered matched event study
→ certificate composition
→ bounded certificate
```

The plan fixes every input and numerical gate before execution. Each analysis is recomputed through its deterministic checker. The final report binds the plan and seven analysis reports by canonical SHA-256 digests. A certificate is emitted only when every local gate passes **and** the selected bridge evidence verifies the declared global pipeline claim.

The checked-in plan requires exact recovery of injected alpha distortions; an alpha interval no wider than 600 bps with a positive lower endpoint; at least 200 units of evidence-adjusted portfolio improvement; two crowding paradox cases; one hidden-common-risk liquidation pair; an accepted event study with average DID of at least 800 bps; and a composition architecture no more expensive than 4 units.

The controlled composition analysis selects:

```text
dataDecisionBindingReceipt
decisionResultBindingReceipt
```

at cost 4. Local dataset, decision, and result certificates are valid in every controlled world, but their pass/fail summary does not verify the global claim. The bridge receipts bind the exact dataset to the decision and the exact decision to the result. Lowering the agent's composition-cost budget to 3 rejects the run even though all six local analyses remain green.

## Prefix-accurate failure stages

The agent computes every analysis for diagnostics, but `completed_stages` records only the ordered prefix that passed. A failed event-study gate does not report `eventStudied`; a failed composition gate includes `eventStudied` but omits `pipelineComposed` and `certified`.

This prevents a diagnostic execution from being misreported as a completed proof stage.

## Candidate decision policy

The same canonical package contains a second, candidate-level fail-closed policy. Its machine decisions are deliberately limited to:

```text
advanceToHumanReview
repairEvidence
rejectCandidate
```

Autonomous deployment is absent from both the Lean state space and the executable report.

For each candidate the gate computes:

```text
certifiable lower bound
= attack-cleaned alpha - residual uncertainty

deployable lower bound
= certifiable lower bound
  - market impact
  - capacity haircut
```

A candidate advances only when every declared integrity obligation is separated by selected evidence and the deployable lower bound is positive. Advancement means mandatory human review, not investment approval.

When an integrity obligation is unresolved, the gate enumerates the declared channel language and returns the exact minimum-cost repair. If no declared channel can separate the remaining obligation, the candidate is rejected with the unresolved witness.

The controlled candidate batch demonstrates all three paths:

- `certifiableMomentum` advances to human review with a 25 bps deployable lower bound;
- `futureLeakCandidate` receives a one-channel `dataAccessReceipt` repair despite 120 bps of observed alpha;
- `parameterAndCostCandidate` receives the exact `evaluationContract + searchLedger` repair at cost 4;
- `overcrowdedCandidate` is integrity-valid but rejected at a -3 bps deployable lower bound;
- `unobservableCandidate` is rejected because its required hardware receipt is outside the declared channel language.

Run the registered plan with:

```bash
python -m tools.research_agent --repository-root . run \
  --plan examples/research_agent/plan.json \
  --out /tmp/lfv-research-agent.json
```

Run the candidate gate with:

```bash
python -m tools.research_agent gate-candidates \
  --batch examples/research_agent/candidates.json \
  --out /tmp/lfv-research-candidates.json
```

## Trust and scientific boundary

This is an orchestration and safety harness, not an autonomous scientist or investment adviser. It certifies that registered finite analyses executed, passed machine-checkable gates, and were composed through the declared binding language.

It does not generate a novel strategy, validate real data, eliminate unobserved confounding, calibrate economic parameters, establish market causality, prove the attack or composition language complete, or establish that binding digests were measured at the correct causal boundary. Human approval remains mandatory and external evidence must still be authenticated by the repository's cryptographic and operational layers.
