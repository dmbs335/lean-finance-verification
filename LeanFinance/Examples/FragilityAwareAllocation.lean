import LeanFinance.ComplexSystems.Certificate

namespace LeanFinance.Examples

open Backtest ComplexSystems

def marketSnapshot : Dataset :=
  {
    id := "cross-asset-market-snapshot"
    observedAt := 10
    availableAt := 11
    contentHash := "sha256:market-snapshot-v1"
  }

def marketStateFeature : FeatureLineage :=
  {
    featureName := "trend-fragility-volatility-state"
    inputHashes := [marketSnapshot.contentHash]
    generatedAt := 11
    codeHash := "sha256:market-state-estimator-v1"
  }

def allocationDecision : Decision :=
  {
    strategyId := "core-trend-fragility-overlay"
    decisionTime := 12
    datasets := [marketSnapshot]
    features := [marketStateFeature]
    parameterHash := "sha256:allocation-policy-70-30-v1"
  }

/-- Mixed trend plus high fragility gives a 75-unit risky-asset target. -/
def cautiousMarketState : MarketState :=
  {
    trend := .mixed
    fragility := .high
    volatility := .normal
  }

def sellClaim : AllocationClaim :=
  {
    decisionTime := 12
    state := cautiousMarketState
    currentRiskUnits := 90
    claimedTargetRiskUnits := 75
    claimedAction := .sell
    stateHash := "sha256:cautious-market-state"
    policyHash := "sha256:allocation-policy-70-30-v1"
  }

example : targetRiskUnits cautiousMarketState = 75 := by
  decide

example : sellClaim.check = true := by
  decide

def sellCertificate :
    AllocationCertificate sellClaim allocationDecision :=
  {
    accepted := by decide
    noFutureInformation := by
      constructor
      · intro dataset used
        have datasetMatches : dataset = marketSnapshot := by
          simpa [allocationDecision] using used
        subst dataset
        change (11 : Timestamp) ≤ 12
        decide
      · intro feature used
        have featureMatches : feature = marketStateFeature := by
          simpa [allocationDecision] using used
        subst feature
        change (11 : Timestamp) ≤ 12
        decide
    decisionTimeBound := rfl
    policyHashBound := rfl
    stateFeature := marketStateFeature
    stateFeatureUsed := by
      simp [allocationDecision]
    stateFeatureBound := by
      decide
  }

example : coreRiskUnits ≤ sellClaim.claimedTargetRiskUnits :=
  AllocationCertificate.target_preserves_core
    sellClaim allocationDecision sellCertificate

example : sellClaim.claimedTargetRiskUnits ≤ 100 :=
  AllocationCertificate.target_is_unlevered
    sellClaim allocationDecision sellCertificate

example : sellClaim.claimedTargetRiskUnits < sellClaim.currentRiskUnits :=
  AllocationCertificate.certified_sell_sound
    sellClaim allocationDecision sellCertificate rfl

/-- A favorable state stages back into the full tactical allocation. -/
def favorableMarketState : MarketState :=
  {
    trend := .strong
    fragility := .low
    volatility := .normal
  }

example : targetRiskUnits favorableMarketState = 100 := by
  decide

example : rebalanceAction 70 favorableMarketState = .buy := by
  decide

example : rebalanceAction 100 favorableMarketState = .hold := by
  decide

/-- Weak trend removes only the tactical overlay; the strategic core remains. -/
def defensiveMarketState : MarketState :=
  {
    trend := .weak
    fragility := .high
    volatility := .stressed
  }

example : targetRiskUnits defensiveMarketState = 70 := by
  decide

example : rebalanceAction 90 defensiveMarketState = .sell := by
  decide

/-- Negative control: the checker rejects an all-in target in the cautious state. -/
def invalidAllInClaim : AllocationClaim :=
  { sellClaim with claimedTargetRiskUnits := 100 }

example : invalidAllInClaim.check = false := by
  decide

end LeanFinance.Examples
