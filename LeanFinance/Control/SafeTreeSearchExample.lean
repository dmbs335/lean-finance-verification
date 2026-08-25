import LeanFinance.Control.SafeTreeSearch

namespace LeanFinance.Control.SafeTreeSearchExample

open LeanFinance.Control

def selected : TreeActionCertificate :=
  { actionId := 1
    supportCount := 120
    minimumSupport := 50
    safe := true
    isBaseline := false
    lowerValue := 11 }

def certificate : SafeTreeSelectionCertificate :=
  { selected := selected
    alternatives := [5, 9, 11]
    selectedAdmissible := by decide
    dominates := by
      intro value member
      simp at member
      rcases member with rfl | rfl | rfl <;> decide }

theorem controlled_selected_action_is_safe :
    certificate.selected.safe = true :=
  certificate.selected_action_is_safe

theorem controlled_selection_respects_support :
    certificate.selected.minimumSupport ≤
      certificate.selected.supportCount ∨
      certificate.selected.isBaseline = true :=
  certificate.selected_action_respects_baseline_constraint

theorem controlled_selection_dominates_nine : (9 : Int) ≤ 11 := by
  exact certificate.selected_dominates_registered_alternatives
    9 (by simp [certificate])

end LeanFinance.Control.SafeTreeSearchExample
