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
  | .hold | .increase | .reduce | .query => True

def count : Action → Nat
  | .hold => 500
  | .increase => 10
  | .reduce => 20
  | .query => 120

theorem query_is_spibb_admissible :
    MctsSpibbAdmissible safe count 50 .hold .query := by
  simp [MctsSpibbAdmissible, safe, count]

theorem unsupported_increase_is_not_admissible :
    ¬ MctsSpibbAdmissible safe count 50 .hold .increase := by
  simp [MctsSpibbAdmissible, safe, count]

def certificate : MctsSpibbRootCertificate Action :=
  { baseline := .hold
    proposal := .query
    selected := .query
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
    gateMctsRootAction .hold .query 1 2 1 = .query := by
  decide

theorem higher_margin_falls_back_to_hold :
    gateMctsRootAction .hold .query 1 2 2 = .hold := by
  decide

end LeanFinance.Control.MctsSpibbExample
