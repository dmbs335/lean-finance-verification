import LeanFinance.Market.CertifiabilityCrowding

namespace LeanFinance.Examples.CertifiabilityCrowding

open LeanFinance.Market

def before : CertifiabilityCrowdingState :=
  { certifiability := 20
    allocatedCapital := 100
    economicAlphaBps := 40
    impactBps := 10 }

def after : CertifiabilityCrowdingState :=
  { certifiability := 80
    allocatedCapital := 500
    economicAlphaBps := 40
    impactBps := 45 }

def transition : CertifiabilityCrowdingTransition :=
  { before := before
    after := after
    certifiabilityIncreased := by decide
    allocationIncreased := by decide
    impactIncreased := by decide
    economicAlphaPreserved := rfl }

theorem gross_alpha_is_unchanged :
    transition.before.economicAlphaBps =
      transition.after.economicAlphaBps :=
  transition.economicAlphaPreserved

theorem deployable_alpha_falls_from_thirty_to_negative_five :
    deployableAlphaBps transition.before = 30 ∧
      deployableAlphaBps transition.after = -5 := by
  decide

def extinctionWitness : CrowdingExtinctionWitness :=
  { transition := transition
    beforeInvestable := by decide
    afterCapacityDead := by decide }

theorem stronger_certifiability_crosses_capacity_boundary :
    Investable transition.before ∧ CapacityDeath transition.after :=
  extinctionWitness.certifiability_success_can_destroy_deployability

end LeanFinance.Examples.CertifiabilityCrowding
