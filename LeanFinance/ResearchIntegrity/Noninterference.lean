import Init.Data.List.Lemmas
import LeanFinance.Types

namespace LeanFinance.ResearchIntegrity

/-- A content-addressed research input or intermediate artifact. -/
structure Artifact where
  id : String
  contentHash : String
  availableAt : Time
  deriving DecidableEq, Repr

abbrev ResearchHistory := List Artifact

/-- The exact view that a decision procedure was allowed to observe. -/
def visibleAt (history : ResearchHistory) (decisionTime : Time) : ResearchHistory :=
  history.filter fun artifact => decide (artifact.availableAt <= decisionTime)

/-- Every artifact in the extension became available strictly after the
    decision time. -/
def FutureOnlyAfter (future : ResearchHistory) (decisionTime : Time) : Prop :=
  ∀ artifact, artifact ∈ future → decisionTime < artifact.availableAt

theorem visibleAt_futureOnlyAfter_eq_nil
    {future : ResearchHistory}
    {decisionTime : Time}
    (futureOnly : FutureOnlyAfter future decisionTime) :
    visibleAt future decisionTime = [] := by
  unfold visibleAt
  apply List.filter_eq_nil_iff.mpr
  intro artifact member
  have unavailable : ¬ artifact.availableAt <= decisionTime :=
    Nat.not_le_of_lt (futureOnly artifact member)
  simp [unavailable]

theorem visibleAt_append_future
    (history future : ResearchHistory)
    (decisionTime : Time)
    (futureOnly : FutureOnlyAfter future decisionTime) :
    visibleAt (history ++ future) decisionTime = visibleAt history decisionTime := by
  unfold visibleAt
  rw [List.filter_append]
  have futureFiltered :
      future.filter (fun artifact => decide (artifact.availableAt <= decisionTime)) = [] := by
    simpa [visibleAt] using visibleAt_futureOnlyAfter_eq_nil futureOnly
  rw [futureFiltered]
  simp

structure DecisionProcedure where
  decide : ResearchHistory → String

def DecisionProcedure.runAt
    (procedure : DecisionProcedure)
    (history : ResearchHistory)
    (decisionTime : Time) : String :=
  procedure.decide (visibleAt history decisionTime)

/-- Appending artifacts that were unavailable at the decision time cannot
    change a point-in-time decision. -/
theorem futureArtifacts_noninterference
    (procedure : DecisionProcedure)
    (history future : ResearchHistory)
    (decisionTime : Time)
    (futureOnly : FutureOnlyAfter future decisionTime) :
    procedure.runAt (history ++ future) decisionTime =
      procedure.runAt history decisionTime := by
  unfold DecisionProcedure.runAt
  rw [visibleAt_append_future history future decisionTime futureOnly]

end LeanFinance.ResearchIntegrity
