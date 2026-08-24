# Proof-Carrying Research Agent Harness

The v3 research-agent harness connects six controlled analyses under one registered plan:

```text
fake-alpha audit
→ certifiable-alpha interval gate
→ evidence-adjusted portfolio selection
→ certifiability/capacity stress
→ shared-evidence liquidation stress
→ preregistered matched event study
→ bounded certificate
```

The plan fixes every input and numerical gate before execution. Each analysis is recomputed through its deterministic checker. The final report binds the plan and six analysis reports by canonical SHA-256 digests. A certificate is emitted only when every gate passes.

The checked-in plan requires exact recovery of injected alpha distortions; an alpha interval no wider than 600 bps with a positive lower endpoint; at least 200 units of evidence-adjusted portfolio improvement; two crowding paradox cases; one hidden-common-risk liquidation pair; an accepted event study; and average event DID of at least 800 bps.

The controlled event-study result is 850 bps across three matched pairs. Raising the agent-level threshold to 900 rejects the run even though the event-study's own preregistered 700 bps threshold passes. The nested gates make both the analysis contract and the certificate-issuance contract explicit.

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

Run the candidate gate with:

```bash
python -m tools.research_agent gate-candidates \
  --batch examples/research_agent/candidates.json \
  --out /tmp/lfv-research-candidates.json
```

Verify by exact recomputation:

```bash
python -m tools.research_agent verify-candidates \
  --batch examples/research_agent/candidates.json \
  --report /tmp/lfv-research-candidates.json
```

## Trust and scientific boundary

This is an orchestration and safety harness, not an autonomous scientist or investment adviser. It certifies that registered finite analyses executed and passed machine-checkable gates, and it prevents obvious evidence or deployability failures from reaching review.

It does not generate a novel strategy, validate real data, eliminate unobserved confounding, calibrate economic parameters, establish market causality, prove the attack language complete, or decide whether the hypothesis is scientifically important. Human approval remains mandatory and external evidence must still be authenticated by the repository's cryptographic and operational layers.
