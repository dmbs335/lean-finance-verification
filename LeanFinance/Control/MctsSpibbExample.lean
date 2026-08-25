import LeanFinance.Control.MctsSpibb

namespace LeanFinance.Control.MctsSpibbExample

open LeanFinance.Control

inductive Action where
  | hold
  | increase
  | reduce
  | query
  deriving Repr, DecidableEq

def safe : Action → Prop
  | Action.hold | Action.increase | Action.reduce | Action.query => True

def count : Action → Nat
  | Action.hold => 500
  | Action.increase => 10
  | Action.reduce => 20
  | Action.query => 120

theorem query_is_spibb_admissible :
    MctsSpibbAdmissible safe count 50 Action.hold Action.query := by
  simp [MctsSpibbAdmissible, safe, count]

theorem unsupported_increase_is_not_admissible :
    ¬ MctsSpibbAdmissible safe count 50 Action.hold Action.increase := by
  simp [MctsSpibbAdmissible, safe, count]

def certificate : MctsSpibbRootCertificate Action :=
  { baseline := Action.hold
    proposal := Action.query
    selected := Action.query
    safe := safe
    count := count
    minimumCount := 50
    proposalAdmissible := query_is_spibb_admissible
    baselineLower := 1
    proposalLower := 2
    requiredMargin := 1
    selectedCorrect := by decide }

theorem controlled_query_is_safe : safe certificate.proposal :=
  certificate.proposal_is_safe

theorem exact_margin_preserves_query :
    gateMctsRootAction Action.hold Action.query 1 2 1 = Action.query := by
  decide

theorem higher_margin_falls_back_to_hold :
    gateMctsRootAction Action.hold Action.query 1 2 2 = Action.hold := by
  decide

end LeanFinance.Control.MctsSpibbExample
