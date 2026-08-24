import LeanFinance.Control.Ambiguity
import LeanFinance.Control.EvidenceAction
import LeanFinance.Alpha.CertifiabilityCapitalRule

namespace LeanFinance.Control.RobustExample

inductive Model where
  | bear
  | base
  | bull
  deriving Repr, DecidableEq

def value : Model → Int
  | .bear => 1
  | .base => 7
  | .bull => 14

def outer : List Model := [.bear, .base, .bull]
def refined : List Model := [.base, .bull]

theorem outer_lower_is_one :
    GreatestLowerBound outer value 1 := by
  constructor
  · intro model member
    simp [outer] at member
    rcases member with rfl | rfl | rfl <;> decide
  · intro candidate lower
    have := lower .bear (by simp [outer])
    simpa [value] using this

theorem refined_lower_is_seven :
    GreatestLowerBound refined value 7 := by
  constructor
  · intro model member
    simp [refined] at member
    rcases member with rfl | rfl <;> decide
  · intro candidate lower
    have := lower .base (by simp [refined])
    simpa [value] using this

theorem refinement_raises_robust_value : (1 : Int) ≤ 7 :=
  evidence_refinement_improves_robust_lower_bound
    outer refined value 1 7
    (by
      intro model member
      simp [refined] at member
      rcases member with rfl | rfl
      · simp [outer]
      · simp [outer])
    outer_lower_is_one refined_lower_is_seven

inductive Observation where
  | stable
  | stress
  deriving Repr, DecidableEq

def query : EvidenceActionCertificate Observation :=
  { currentRobustValue := 1
    queryCost := 1
    postObservationValue := fun observation =>
      match observation with
      | .stable => 7
      | .stress => 4
    postQueryGuarantee := 4
    guarantee := by intro observation; cases observation <;> decide }

theorem query_has_positive_robust_value : query.ValueOfInformation := by
  change (1 : Int) < 4 - 1
  decide

def capital : LeanFinance.Alpha.CertifiabilityCapitalCertificate :=
  { robustValueBefore := 1
    robustValueAfter := 3
    crowdingCostBefore := 1
    crowdingCostAfter := 2 }

theorem controlled_capital_expansion_allowed :
    capital.MayIncreaseCapital := by
  change (2 : Int) - 1 < 3 - 1
  decide

end LeanFinance.Control.RobustExample
