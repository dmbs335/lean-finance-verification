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

## Migration rule

Plans must be rewritten explicitly and recomputed under the new schema. Old
reports remain evidence for their original schema only; changing the schema ID
without adding the new analysis inputs and gates is rejected by the parser.

The current checked-in fixture is v3 and contains six independent analysis
gates before the final `certified` stage.
