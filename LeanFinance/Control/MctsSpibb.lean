namespace LeanFinance.Control

/-- SPIBB-style admissibility for one tree edge. The candidate action must be
    safe and must either have enough logged support or be the registered
    baseline action. -/
def MctsSpibbAdmissible
    (safe : Action → Prop)
    (count : Action → Nat)
    (minimumCount : Nat)
    (baseline action : Action) : Prop :=
  safe action ∧
    (minimumCount ≤ count action ∨ action = baseline)

/-- Every action admitted to tree expansion is safe. -/
theorem mcts_spibb_admitted_is_safe
    (safe : Action → Prop)
    (count : Action → Nat)
    (minimumCount : Nat)
    (baseline action : Action)
    (admitted :
      MctsSpibbAdmissible safe count minimumCount baseline action) :
    safe action :=
  admitted.1

/-- An admitted action without enough support is exactly the baseline. -/
theorem mcts_spibb_unsupported_is_baseline
    (safe : Action → Prop)
    (count : Action → Nat)
    (minimumCount : Nat)
    (baseline action : Action)
    (admitted :
      MctsSpibbAdmissible safe count minimumCount baseline action)
    (unsupported : ¬ minimumCount ≤ count action) :
    action = baseline := by
  rcases admitted.2 with supported | baselineAction
  · exact False.elim (unsupported supported)
  · exact baselineAction

/-- Final trusted root gate. MCTS is only a proposal generator; the candidate is
    returned only when its exact pessimistic lower bound clears the registered
    baseline-relative margin. -/
def gateMctsRootAction
    (baseline candidate : Action)
    (baselineLower candidateLower requiredMargin : Int) : Action :=
  if baselineLower + requiredMargin ≤ candidateLower then
    candidate
  else
    baseline

/-- A failed exact margin gate returns the baseline. -/
theorem failed_mcts_root_gate_uses_baseline
    (baseline candidate : Action)
    (baselineLower candidateLower requiredMargin : Int)
    (failed : ¬ baselineLower + requiredMargin ≤ candidateLower) :
    gateMctsRootAction baseline candidate
      baselineLower candidateLower requiredMargin = baseline := by
  simp [gateMctsRootAction, failed]

/-- A passing exact margin gate preserves the MCTS proposal. -/
theorem passed_mcts_root_gate_uses_candidate
    (baseline candidate : Action)
    (baselineLower candidateLower requiredMargin : Int)
    (passed : baselineLower + requiredMargin ≤ candidateLower) :
    gateMctsRootAction baseline candidate
      baselineLower candidateLower requiredMargin = candidate := by
  simp [gateMctsRootAction, passed]

/-- Proof-carrying summary of a bounded search proposal. The search algorithm is
    external; Lean checks the support/safety and exact-root-gate consequences. -/
structure MctsSpibbRootCertificate (Action : Type) where
  baseline : Action
  proposal : Action
  selected : Action
  safe : Action → Prop
  count : Action → Nat
  minimumCount : Nat
  proposalAdmissible :
    MctsSpibbAdmissible safe count minimumCount baseline proposal
  baselineLower : Int
  proposalLower : Int
  requiredMargin : Int
  selectedCorrect :
    selected = gateMctsRootAction baseline proposal
      baselineLower proposalLower requiredMargin

namespace MctsSpibbRootCertificate

theorem proposal_is_safe
    (certificate : MctsSpibbRootCertificate Action) :
    certificate.safe certificate.proposal :=
  mcts_spibb_admitted_is_safe
    certificate.safe certificate.count certificate.minimumCount
    certificate.baseline certificate.proposal
    certificate.proposalAdmissible

end MctsSpibbRootCertificate

end LeanFinance.Control
