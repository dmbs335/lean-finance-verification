import LeanFinance.Market.EpistemicLiquidation

namespace LeanFinance.Examples.EpistemicLiquidation

open LeanFinance.Market

def momentumShock : EvidenceConfidenceShock :=
  { confidenceBefore := 100
    confidenceAfter := 40
    capitalBefore := 1000
    capitalAfter := 600 }

def valueShock : EvidenceConfidenceShock :=
  { confidenceBefore := 90
    confidenceAfter := 35
    capitalBefore := 800
    capitalAfter := 500 }

def commonVendorShock : SharedEvidenceShock :=
  { left := momentumShock
    right := valueShock
    leftResponds := by decide
    rightResponds := by decide }

def lowReturnCorrelationPair : EpistemicCrowdingPair :=
  { returnCorrelation := 0
    sharedDependencyCount := 2 }

theorem low_return_correlation_hides_dependency_overlap :
    HiddenEpistemicCrowding lowReturnCorrelationPair := by
  decide

theorem common_vendor_failure_causes_synchronized_liquidation :
    SynchronizedLiquidation commonVendorShock :=
  shared_evidence_shock_implies_synchronized_liquidation commonVendorShock

theorem aggregate_unwind_is_seven_hundred :
    aggregateLiquidationPressure commonVendorShock = 700 := by
  decide

theorem aggregate_unwind_is_positive :
    0 < aggregateLiquidationPressure commonVendorShock :=
  synchronized_liquidation_has_positive_aggregate_pressure
    commonVendorShock
    common_vendor_failure_causes_synchronized_liquidation

end LeanFinance.Examples.EpistemicLiquidation
