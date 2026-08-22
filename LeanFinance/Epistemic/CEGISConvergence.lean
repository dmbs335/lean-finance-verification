import LeanFinance.Epistemic.CounterexampleGuided

namespace LeanFinance.Epistemic

universe u v

/-- Finite separator problem used to state master/oracle convergence independently
    of one concrete workflow implementation. The edge universe is a duplicate-
    free list so this layer remains dependency-free and does not require
    mathlib's finite-set library. -/
structure FiniteCEGISProblem
    (Edge : Type u)
    (Candidate : Type v) where
  allEdges : List Edge
  allEdgesNodup : allEdges.Nodup
  covers : Candidate → Edge → Prop
  cost : Candidate → Nat

/-- A candidate satisfies every separator constraint in one finite list. -/
def FeasibleOn
    {Edge : Type u}
    {Candidate : Type v}
    (problem : FiniteCEGISProblem Edge Candidate)
    (edges : List Edge)
    (candidate : Candidate) : Prop :=
  ∀ edge,
    edge ∈ edges →
      problem.covers candidate edge

/-- Exact master result for the counterexamples discovered so far. -/
structure ExactMasterState
    {Edge : Type u}
    {Candidate : Type v}
    (problem : FiniteCEGISProblem Edge Candidate) where
  discovered : List Edge
  discoveredNodup : discovered.Nodup
  selected : Candidate
  feasible : FeasibleOn problem discovered selected
  optimal :
    ∀ candidate,
      FeasibleOn problem discovered candidate →
        problem.cost selected ≤ problem.cost candidate

/-- A completed finite CEGIS transcript. `oracleComplete` means that the final
    candidate has no remaining counterexample in the declared finite universe.
    The transcript carries a machine-checkable round bound; concrete finite
    instances discharge it by computation. -/
structure FiniteCEGISTranscript
    {Edge : Type u}
    {Candidate : Type v}
    (problem : FiniteCEGISProblem Edge Candidate) where
  final : ExactMasterState problem
  discoveredWithinUniverse :
    ∀ edge,
      edge ∈ final.discovered → edge ∈ problem.allEdges
  distinctRoundBound :
    final.discovered.length ≤ problem.allEdges.length
  oracleComplete : FeasibleOn problem problem.allEdges final.selected

namespace FiniteCEGISTranscript

/-- Number of distinct counterexamples learned by the transcript. -/
def distinctRoundCount
    {Edge : Type u}
    {Candidate : Type v}
    {problem : FiniteCEGISProblem Edge Candidate}
    (transcript : FiniteCEGISTranscript problem) : Nat :=
  transcript.final.discovered.length

/-- A completed finite transcript certifies that its number of distinct
    refinement constraints is bounded by the complete disagreement universe. -/
theorem distinct_round_count_le_disagreement_edges
    {Edge : Type u}
    {Candidate : Type v}
    {problem : FiniteCEGISProblem Edge Candidate}
    (transcript : FiniteCEGISTranscript problem) :
    transcript.distinctRoundCount ≤ problem.allEdges.length :=
  transcript.distinctRoundBound

/-- When the complete oracle returns no counterexample, the selected candidate
    satisfies every finite separator obligation. -/
theorem complete_oracle_implies_final_soundness
    {Edge : Type u}
    {Candidate : Type v}
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
    {problem : FiniteCEGISProblem Edge Candidate}
    (transcript : FiniteCEGISTranscript problem)
    (candidate : Candidate)
    (globallyFeasible : FeasibleOn problem problem.allEdges candidate) :
    problem.cost transcript.final.selected ≤ problem.cost candidate := by
  apply transcript.final.optimal candidate
  intro edge discovered
  exact globallyFeasible edge
    (transcript.discoveredWithinUniverse edge discovered)

end FiniteCEGISTranscript

end LeanFinance.Epistemic
