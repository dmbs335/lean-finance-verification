import LeanFinance.Control.BaselinePolicy
import LeanFinance.Control.Authority

namespace LeanFinance.Control.Example

open LeanFinance.Control

inductive State where
  | normal
  | stressed
  | margin
  | ruin
  deriving Repr, DecidableEq

inductive Action where
  | hold
  | increase
  | reduce
  deriving Repr, DecidableEq

def admissible : State → Action → Bool
  | .normal, _ => true
  | .stressed, .increase => false
  | .stressed, _ => true
  | .margin, .reduce => true
  | .margin, _ => false
  | .ruin, _ => false

def fallback : State → Action
  | .normal => .hold
  | .stressed | .margin => .reduce
  | .ruin => .hold

/-- The controlled runtime never calls the shield from `ruin`; its fallback is
    intentionally outside the admissible domain to keep the terminal state
    explicit. -/
def liveAdmissible : State → Action → Bool
  | .ruin, .hold => true
  | state, action => admissible state action

def shield : SafetyShield State Action :=
  { admissible := liveAdmissible
    fallback := fallback
    fallbackAdmissible := by
      intro state
      cases state <;> rfl }

theorem unsafe_stress_increase_uses_reduce :
    shield.apply .stressed .increase = .reduce := by
  decide

theorem normal_increase_survives_the_shield :
    shield.apply .normal .increase = .increase := by
  decide

def improvement : PessimisticValueCertificate :=
  { baselineLower := 2
    candidateLower := 8
    requiredMargin := 5
    improvement := by decide }

theorem controlled_policy_clears_margin :
    improvement.baselineLower + improvement.requiredMargin ≤
      improvement.candidateLower :=
  improvement.candidate_meets_registered_margin

def promotionEvidence : PromotionEvidence :=
  { improvementLcb := 6
    effectiveSampleSize := 200
    minimumEffectiveSampleSize := 100
    riskUcb := 30
    riskBudget := 40
    modelShift := false
    operationalBreach := false }

theorem recommendation_promotes_only_to_micro_autonomy :
    governAuthority .recommend promotionEvidence = .microAutonomy := by
  decide

theorem micro_autonomy_cap_is_ten :
    AuthorityLevel.capitalCap
      (governAuthority .recommend promotionEvidence) = 10 := by
  decide

end LeanFinance.Control.Example
