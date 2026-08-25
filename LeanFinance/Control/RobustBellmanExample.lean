import LeanFinance.Control.RobustBellman

namespace LeanFinance.Control.RobustBellmanExample

open LeanFinance.Control

inductive Model where
  | optimistic
  | adverse
  deriving Repr, DecidableEq

inductive Action where
  | hold
  | increase
  | reduce
  | query
  deriving Repr, DecidableEq

def optimisticQueryBackup : BellmanBackup :=
  { reward := -1
    discountNumerator := 1
    discountDenominator := 1
    continuation :=
      [ { weight := 3, value := 5 }
      , { weight := 1, value := 3 } ] }

def adverseQueryBackup : BellmanBackup :=
  { reward := -1
    discountNumerator := 1
    discountDenominator := 1
    continuation :=
      [ { weight := 1, value := 5 }
      , { weight := 3, value := 3 } ] }

def queryBackup : Model → BellmanBackup
  | .optimistic => optimisticQueryBackup
  | .adverse => adverseQueryBackup

theorem optimistic_query_numerator_is_fourteen :
    optimisticQueryBackup.numerator = 14 := by
  decide

theorem adverse_query_numerator_is_ten :
    adverseQueryBackup.numerator = 10 := by
  decide

/-- Both model-specific query values are at least 2 bps after flooring:
    optimistic is 14/4 and adverse is 10/4. -/
def queryCertificate : RobustBellmanActionCertificate Model :=
  { models := [.optimistic, .adverse]
    lowerBound := 2
    backup := queryBackup
    valid := by
      intro model _member
      cases model
      · change 0 < 1 ∧ 0 < 4
        decide
      · change 0 < 1 ∧ 0 < 4
        decide
    sound := by
      intro model _member
      cases model
      · change (4 : Int) * 2 ≤ 14
        decide
      · change (4 : Int) * 2 ≤ 10
        decide }

def stateCertificate : RobustBellmanStateCertificate Model Action :=
  { selectedAction := .query
    selected := queryCertificate
    declaredActionLower := fun
      | .hold => 1
      | .increase => -8
      | .reduce => -3
      | .query => 2
    selectedMatches := rfl
    selectedDominates := by
      intro action
      cases action <;> decide }

theorem query_is_the_best_declared_robust_action
    (action : Action) :
    stateCertificate.declaredActionLower action ≤
      stateCertificate.selected.lowerBound :=
  stateCertificate.selected_dominates_every_declared_action action

theorem query_lower_holds_in_the_adverse_model :
    (queryBackup .adverse).LowerBound 2 := by
  change (4 : Int) * 2 ≤ 10
  decide

end LeanFinance.Control.RobustBellmanExample
