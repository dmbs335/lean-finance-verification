# Research-Agent Plan Schema Migration

The bounded research-agent plan is intentionally versioned because adding a new
analysis gate changes the meaning of the final certificate.

## v1 → v2

`lfv-proof-carrying-research-plan-v2` added:

- `analyses.certifiable_alpha_interval`;
- `gates.maximum_certifiable_interval_width_bps`;
- `gates.require_positive_certifiable_lower_bound`;
- the formal `alphaBounded` stage;
- the alpha-interval report digest.

A v1 plan cannot be silently interpreted as v2 because exact attack recovery is
not equivalent to acceptably bounded residual alpha uncertainty.

## v2 → v3

`lfv-proof-carrying-research-plan-v3` added:

- `analyses.epistemic_event_study`;
- `gates.require_event_study_acceptance`;
- `gates.minimum_event_study_average_did_bps`;
- the formal `eventStudied` stage;
- the event-study report digest.

A v2 certificate therefore does not imply that an empirical event-study
protocol was registered or passed.

## v3 → v4

`lfv-proof-carrying-research-plan-v4` adds:

- `analyses.certificate_composition`;
- `gates.require_composition_verification`;
- `gates.maximum_composition_evidence_cost`;
- the formal `pipelineComposed` stage;
- the certificate-composition report digest;
- prefix-accurate rejected-stage reporting.

A v3 certificate binds six local analysis reports by digest, but it does not
prove that the reports refer to the same dataset, decisions, result, and causal
pipeline. The v4 composition gate requires selected bridge evidence to verify
the declared global pipeline claim and keeps its evidence cost within the
registered budget.

A rejected v4 report now lists only the stage prefix that actually passed. For
example, a composition-cost failure includes `eventStudied` but omits
`pipelineComposed` and `certified`.

## Migration rule

Plans must be rewritten explicitly and recomputed under the new schema. Old
reports remain evidence for their original schema only; changing the schema ID
without adding the new analysis inputs and gates is rejected by the parser.

The current checked-in fixture is v4 and contains seven independent analysis
gates before the final `certified` stage.
