import LeanFinance.Allocation.Certificate

namespace LeanFinance.Examples

open Backtest Allocation

private def signalEvidence
    (name hash : String)
    (availableAt generatedAt : Timestamp) : SignalEvidence :=
  {
    dataset :=
      {
        id := name ++ "-dataset"
        observedAt := availableAt
        availableAt := availableAt
        contentHash := hash
      }
    feature :=
      {
        featureName := name
        inputHashes := [hash]
        generatedAt := generatedAt
        codeHash := "sha256:" ++ name ++ "-feature-code"
      }
  }

def allocationSignals : SignalBundle :=
  {
    trend := signalEvidence "trend" "sha256:trend-source" 12 12
    fragility := signalEvidence "fragility" "sha256:fragility-source" 12 12
    volatility := signalEvidence "volatility" "sha256:volatility-source" 12 12
  }

def risingFragileCertificate : AllocationCertificate :=
  {
    strategyId := "core-trend-fragility-allocation"
    decisionTime := 12
    input :=
      {
        trend := .rising
        fragility := .high
        volatility := .normal
      }
    signals := allocationSignals
    declaredDecision :=
      allocationDecision
        {
          trend := .rising
          fragility := .high
          volatility := .normal
        }
    parameterHash := "sha256:allocation-parameters-v1"
    policyCodeHash := "sha256:allocation-policy-v1"
  }

example : risingFragileCertificate.check = true := by
  decide

def verifiedRisingFragile : VerifiedAllocation :=
  VerifiedAllocation.ofAccepted risingFragileCertificate (by decide)

example :
    verifiedRisingFragile.certificate.declaredDecision.riskBps = 9100 := by
  decide

example :
    coreRiskBps ≤
      verifiedRisingFragile.certificate.declaredDecision.riskBps :=
  verifiedRisingFragile.preserves_core

example :
    verifiedRisingFragile.certificate.declaredDecision.riskBps ≤
      fullRiskBps :=
  verifiedRisingFragile.respects_full_investment_ceiling

/-- A forged 100% declaration is rejected when high fragility requires 91%. -/
def tamperedOutputCertificate : AllocationCertificate :=
  {
    risingFragileCertificate with
    declaredDecision :=
      {
        tacticalUnits := 10
        riskBps := 10000
      }
  }

example : tamperedOutputCertificate.check = false := by
  decide

/-- A feature generated after the decision time is rejected as look-ahead. -/
def futureTrendSignals : SignalBundle :=
  {
    allocationSignals with
    trend := signalEvidence "trend" "sha256:future-trend-source" 12 13
  }

def lookaheadCertificate : AllocationCertificate :=
  {
    risingFragileCertificate with
    signals := futureTrendSignals
  }

example : lookaheadCertificate.check = false := by
  decide

/-- Falling trend removes the tactical sleeve but preserves the 70% core. -/
def fallingCertificate : AllocationCertificate :=
  {
    risingFragileCertificate with
    input :=
      {
        trend := .falling
        fragility := .high
        volatility := .stressed
      }
    declaredDecision :=
      allocationDecision
        {
          trend := .falling
          fragility := .high
          volatility := .stressed
        }
  }

example : fallingCertificate.check = true := by
  decide

def verifiedFalling : VerifiedAllocation :=
  VerifiedAllocation.ofAccepted fallingCertificate (by decide)

example : verifiedFalling.certificate.declaredDecision.tacticalUnits = 0 :=
  verifiedFalling.falling_has_no_tactical_exposure rfl

example : verifiedFalling.certificate.declaredDecision.riskBps = coreRiskBps :=
  verifiedFalling.falling_keeps_core rfl

end LeanFinance.Examples
