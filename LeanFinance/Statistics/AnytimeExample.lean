import LeanFinance.Statistics.EProcess

namespace LeanFinance.Statistics.AnytimeExample

open LeanFinance.Statistics

def finalEValue : RationalEvidence :=
  { numerator := 3917521
    denominator := 98304
    denominatorPositive := by decide }

def maximumEValue : RationalEvidence := finalEValue

def threshold : RationalEvidence :=
  { numerator := 20
    denominator := 1
    denominatorPositive := by decide }

def certificate : AnytimePolicyEvidenceCertificate :=
  { currentEValue := finalEValue
    maximumEValue := maximumEValue
    threshold := threshold
    sampleCount := 8
    minimumSampleCount := 7
    riskUcb := 30
    riskBudget := 40
    modelShift := false
    operationalBreach := false
    currentLeMaximum := RationalEvidence.le_refl _ }

theorem controlled_mixture_crosses_twenty :
    certificate.threshold ≤ certificate.maximumEValue := by
  decide

theorem controlled_anytime_monitor_is_eligible :
    certificate.Eligible := by
  exact ⟨controlled_mixture_crosses_twenty, by decide, by decide, rfl, rfl⟩

theorem shifted_monitor_is_not_eligible :
    ¬ ({ certificate with modelShift := true }).Eligible := by
  apply AnytimePolicyEvidenceCertificate.model_shift_blocks_eligibility
  rfl

end LeanFinance.Statistics.AnytimeExample
