import LeanFinance.Epistemic.CEGISConvergence

namespace LeanFinance.Epistemic.CEGISConvergenceExample

inductive Edge where
  | hidden
  | future
  | mutation
  deriving Repr, DecidableEq

inductive Candidate where
  | none
  | hiddenOnly
  | hiddenFuture
  | complete
  deriving Repr, DecidableEq

def allEdges : List Edge :=
  [.hidden, .future, .mutation]

def covers : Candidate → Edge → Prop
  | .none, _ => False
  | .hiddenOnly, .hidden => True
  | .hiddenOnly, _ => False
  | .hiddenFuture, .hidden => True
  | .hiddenFuture, .future => True
  | .hiddenFuture, .mutation => False
  | .complete, _ => True

def cost : Candidate → Nat
  | .none => 0
  | .hiddenOnly => 2
  | .hiddenFuture => 4
  | .complete => 7

def problem : FiniteCEGISProblem Edge Candidate :=
  {
    allEdges := allEdges
    allEdgesNodup := by decide
    covers := covers
    cost := cost
  }

def finalMaster : ExactMasterState problem :=
  {
    discovered := allEdges
    discoveredNodup := by decide
    selected := .complete
    feasible := by
      intro edge member
      cases edge <;> simp [problem, covers]
    optimal := by
      intro candidate feasible
      cases candidate with
      | none =>
          exfalso
          have impossible := feasible .hidden (by simp [allEdges])
          simpa [problem, covers] using impossible
      | hiddenOnly =>
          exfalso
          have impossible := feasible .future (by simp [allEdges])
          simpa [problem, covers] using impossible
      | hiddenFuture =>
          exfalso
          have impossible := feasible .mutation (by simp [allEdges])
          simpa [problem, covers] using impossible
      | complete => simp [problem, cost]
  }

def transcript : FiniteCEGISTranscript problem :=
  {
    final := finalMaster
    discoveredWithinUniverse := by
      intro edge member
      exact member
    distinctRoundBound := by decide
    oracleComplete := finalMaster.feasible
  }

theorem three_distinct_rounds_are_enough :
    transcript.distinctRoundCount ≤ allEdges.length :=
  transcript.distinct_round_count_le_disagreement_edges

theorem final_candidate_is_globally_sound :
    FeasibleOn problem allEdges transcript.final.selected :=
  transcript.complete_oracle_implies_final_soundness

theorem final_candidate_is_globally_minimum
    (candidate : Candidate)
    (feasible : FeasibleOn problem allEdges candidate) :
    cost transcript.final.selected ≤ cost candidate :=
  transcript.exact_master_implies_global_optimality
    candidate feasible

end LeanFinance.Epistemic.CEGISConvergenceExample
