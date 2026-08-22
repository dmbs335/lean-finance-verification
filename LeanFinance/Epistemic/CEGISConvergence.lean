import LeanFinance.Epistemic.CounterexampleGuided

namespace LeanFinance.Epistemic

universe u v

/-- Finite separator problem used to state master/oracle convergence independently
    of one concrete workflow implementation. -/
structure FiniteCEGISProblem
    (Edge : Type u)
    (Candidate : Type v)
    [DecidableEq Edge] where
  allEdges : Finset Edge
  covers : Candidate → Edge → Prop
  cost : Candidate → Nat

/-- A candidate satisfies every separator constraint in one finite set. -/
def FeasibleOn
    {Edge : Type u}
    {Candidate : Type v}
    [DecidableEq Edge]
    (problem : FiniteCEGISProblem Edge Candidate)
    (edges : Finset Edge)
    (candidate : Candidate) : Prop :=
  ∀ edge,
    edge ∈ edges →
      problem.covers candidate edge

/-- Exact master result for the counterexamples discovered so far. -/
structure ExactMasterState
    {Edge : Type u}
    {Candidate : Type v}
    [DecidableEq Edge]
    (problem : FiniteCEGISProblem Edge Candidate) where
  discovered : Finset Edge
  selected : Candidate
  feasible : FeasibleOn problem discovered selected
  optimal :
    ∀ candidate,
      FeasibleOn problem discovered candidate →
        problem.cost selected ≤ problem.cost candidate

/-- A completed finite CEGIS transcript. `oracleComplete` means that the final
    candidate has no remaining counterexample in the declared finite universe.
    Distinct discovered edges are represented by a `Finset`, so repeated oracle
    answers cannot inflate the round bound. -/
structure FiniteCEGISTranscript
    {Edge : Type u}
    {Candidate : Type v}
    [DecidableEq Edge]
    (problem : FiniteCEGISProblem Edge Candidate) where
  final : ExactMasterState problem
  discoveredWithinUniverse : final.discovered ⊆ problem.allEdges
  oracleComplete : FeasibleOn problem problem.allEdges final.selected

namespace FiniteCEGISTranscript

/-- Number of distinct counterexamples learned by the transcript. -/
def distinctRoundCount
    {Edge : Type u}
    {Candidate : Type v}
    [DecidableEq Edge]
    {problem : FiniteCEGISProblem Edge Candidate}
    (transcript : FiniteCEGISTranscript problem) : Nat :=
  transcript.final.discovered.card

/-- A finite complete oracle can contribute at most one distinct refinement per
    disagreement edge. -/
theorem distinct_round_count_le_disagreement_edges
    {Edge : Type u}
    {Candidate : Type v}
    [DecidableEq Edge]
    {problem : FiniteCEGISProblem Edge Candidate}
    (transcript : FiniteCEGISTranscript problem) :
    transcript.distinctRoundCount ≤ problem.allEdges.card := by
  exact Finset.card_le_card transcript.discoveredWithinUniverse

/-- When the complete oracle returns no counterexample, the selected candidate
    satisfies every finite separator obligation. -/
theorem complete_oracle_implies_final_soundness
    {Edge : Type u}
    {Candidate : Type v}
    [DecidableEq Edge]
    {problem : FiniteCEGISProblem Edge Candidate}
    (transcript : FiniteCEGISTranscript problem) :
    FeasibleOn problem problem.allEdges transcript.final.selected :=
  transcript.oracleComplete

/-- Exact optimality on the discovered constraints plus complete-oracle
    termination implies global minimum cost. Every globally feasible candidate
    is also feasible on the discovered subset. -/
theorem exact_master_implies_global_optimality
    {Edge : Type u}
    {Candidate : Type v}
    [DecidableEq Edge]
    {problem : FiniteCEGISProblem Edge Candidate}
    (transcript : FiniteCEGISTranscript problem)
    (candidate : Candidate)
    (globallyFeasible : FeasibleOn problem problem.allEdges candidate) :
    problem.cost transcript.final.selected ≤ problem.cost candidate := by
  apply transcript.final.optimal candidate
  intro edge discovered
  exact globallyFeasible edge
    (transcript.discoveredWithinUniverse discovered)

end FiniteCEGISTranscript

end LeanFinance.Epistemic
