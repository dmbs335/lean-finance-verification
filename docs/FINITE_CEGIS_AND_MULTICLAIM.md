# Finite CEGIS Convergence and Multi-Claim Evidence

## Finite convergence certificate

`FiniteCEGISProblem` separates the complete finite disagreement-edge universe, candidate coverage relation, and cost function. `ExactMasterState` certifies feasibility and minimum cost on the constraints discovered so far. `FiniteCEGISTranscript` adds two final obligations:

- discovered constraints are contained in the complete edge universe;
- the complete oracle has no remaining counterexample for the selected candidate.

The formal layer proves:

- the number of distinct refinement constraints is bounded by the number of finite disagreement edges;
- complete-oracle termination implies global feasibility;
- exact master optimality on the discovered subset implies global minimum cost, because every globally feasible candidate is also feasible on that subset.

This is the general finite convergence result underlying the concrete workflow transcripts. It does not claim termination for an infinite or incompletely enumerated attack language.

## Multi-claim composition

A real research certificate carries several integrity claims. `VerifiesAllClaims` requires one evidence selection to verify each claim. The formal layer proves that the union of individually sufficient evidence selections is always sufficient and that verifying every claim separately verifies their conjunction.

Sufficiency does not imply optimality. In the checked-in fixture:

- `hiddenReceipt` verifies `noHidden` at cost 2;
- `futureReceipt` verifies `noFuture` at cost 2;
- their union costs 4;
- one `unifiedAttestation` verifies both claims at cost 3.

`tools/multiclaim_synth` constructs claim-labelled separator edges, enumerates every channel subset, computes every claim-specific optimum and the global optimum, and reports evidence-synergy savings. The result is exact over the finite world, claim, and channel language.
