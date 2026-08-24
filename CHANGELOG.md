# Changelog

## v0.2.0-research — Finance Frontier Consolidation

### Formal semantics

- Added the research-agent `eventStudied` stage and bound the preregistered event-study report into the final bounded certificate.
- Separated synthetic distortion-free benchmark ground truth from real economic alpha.
- Formalized the decomposition:

  ```text
  observed alpha
  = economic alpha
  + research-process attack bias
  + risk-model bias
  + sampling noise
  ```

- Proved that complete attack-bias removal still leaves model and sampling error.
- Distinguished epistemic death, capacity death, and ecological decay.
- Added capacity-extinction witnesses and proved that capacity death need not imply epistemic death.
- Added a candidate-level machine policy with only `advanceToHumanReview`, `repairEvidence`, and `rejectCandidate` outcomes.
- Made low-return-correlation dependency overlap explicit in the epistemic-liquidation formal layer.

### Executable research tools

- Upgraded the canonical research-agent plan/report schema to v3 with six registered analyses and nested event-study gates.
- Added exact candidate-level evidence-repair synthesis to `tools/research_agent` rather than maintaining a parallel agent package.
- Added deployable lower-bound gating after residual uncertainty, market impact, and capacity haircuts.
- Enriched the canonical certifiability-crowding report with alpha-death classification.
- Enriched the canonical epistemic-liquidation report with dependency domains, overlap scores, latent crowding, and realized common-risk attribution.
- Kept fake-alpha recovery, alpha-interval synthesis, portfolio selection, crowding, liquidation, event-study, and research-agent outputs deterministic and exactly recomputable.

### Documentation and curriculum

- Rewrote the root README around the integrated evidence → alpha → portfolio → market dynamics → event study → research-agent path.
- Expanded the formal assurance document to distinguish kernel theorems, exact finite computations, external verification, and empirical assumptions.
- Clarified that a collapsed synthetic fake-alpha interval is not exact identification of real expected alpha.
- Documented the difference between latent epistemic crowding and realized synchronized liquidation.
- Documented the separate meanings of epistemic, capacity, and ecological alpha death.
- Aligned the learning-app event-study and research-agent prerequisite graph with the v3 stage order.

### CI

- Added the epistemic event-study suite to the main Lean CI.
- Added consolidated research-candidate, alpha-death, and dependency-overlap regressions.
- Preserved all canonical/generated artifact reproducibility checks and the complete pinned Lean build.

### Superseded parallel work

The stale parallel branches behind PRs #51–#55 are superseded by the single consolidation PR. Their unique contributions were reimplemented in the existing canonical packages; their duplicated Python/Lean packages are not part of the supported architecture.

### Research boundary

This release candidate does not establish a universal empirical market law. The next high-value milestone is a lawful strict point-in-time study with authenticated original vintages, followed by a real methodology-shock dataset testing whether evidence-dependency overlap predicts flows and tail co-movement beyond holdings, factor, and liquidity overlap.
