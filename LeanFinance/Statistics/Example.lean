import LeanFinance.Statistics.Promotion

namespace LeanFinance.Statistics.Example

open LeanFinance.Statistics
open LeanFinance.Control

def interval : ConfidenceSequenceCertificate :=
  { lowerBps := 3
    estimateBps := 5
    upperBps := 8
    sampleCount := 4
    lowerBounded := by decide
    upperBounded := by decide }

def ess : EffectiveSampleSizeCertificate :=
  { sumWeights := 7
    sumSquaredWeights := 15
    minimumESS := 3
    denominatorPositive := by decide
    threshold := by decide }

def promotion : OffPolicyPromotionCertificate :=
  { improvement := interval
    requiredImprovementBps := 2
    effectiveSampleSize := ess
    riskUcb := 30
    riskBudget := 40
    modelShift := false
    operationalBreach := false
    lowerClearsMargin := by decide
    riskWithinBudget := by decide
    noModelShift := rfl
    noOperationalBreach := rfl }

theorem controlled_interval_contains_estimate :
    interval.Contains interval.estimateBps :=
  interval.estimate_is_contained

theorem controlled_ess_clears_three :
    ess.minimumESS * ess.sumSquaredWeights ≤
      ess.sumWeights * ess.sumWeights :=
  ess.clears_registered_threshold

theorem controlled_monitor_promotes_one_level :
    governAuthority .recommend promotion.toAuthorityEvidence =
      .microAutonomy := by
  decide

end LeanFinance.Statistics.Example
