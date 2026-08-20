import LeanFinance.StrategyEcology.Kernel
import LeanFinance.StrategyEcology.Identification

namespace LeanFinance.StrategyEcology

/-- A proposition bundled with machine-checkable evidence. -/
structure Evidence where
  claim : Prop
  certified : claim

/-- An interaction edge carries its estimand context, moment certificate,
    interval ordering, and explicit evidence for the causal-design assumptions. -/
structure CausalEdgeCertificate (Strategy Regime : Type) where
  kernel : CausalKernel Strategy Regime
  source : Strategy
  target : Strategy
  context : InteractionContext Regime
  estimate : Scalar
  lowerBound : Scalar
  upperBound : Scalar
  orderedBounds : lowerBound <= estimate ∧ estimate <= upperBound
  kernelEffectMatches :
    kernel.effect target source context = estimate
  iv : ScalarIVCertificate
  effectMatches : iv.effect = estimate
  exogeneity : Evidence
  exclusion : Evidence
  noAnticipation : Evidence
  genomeStability : Evidence
  exposureValidity : Evidence
  marketClearing : Evidence

/-- The confidence or identified interval lies strictly above zero. -/
def CertifiesPositive
    {Strategy Regime : Type}
    (certificate : CausalEdgeCertificate Strategy Regime) : Prop :=
  0 < certificate.lowerBound

/-- The confidence or identified interval lies strictly below zero. -/
def CertifiesNegative
    {Strategy Regime : Type}
    (certificate : CausalEdgeCertificate Strategy Regime) : Prop :=
  certificate.upperBound < 0

theorem CausalEdgeCertificate.positiveEstimate
    {Strategy Regime : Type}
    (certificate : CausalEdgeCertificate Strategy Regime)
    (positive : CertifiesPositive certificate) :
    0 < certificate.estimate :=
  lt_of_lt_of_le positive certificate.orderedBounds.1

theorem CausalEdgeCertificate.negativeEstimate
    {Strategy Regime : Type}
    (certificate : CausalEdgeCertificate Strategy Regime)
    (negative : CertifiesNegative certificate) :
    certificate.estimate < 0 :=
  lt_of_le_of_lt certificate.orderedBounds.2 negative

theorem CausalEdgeCertificate.positiveKernelEffect
    {Strategy Regime : Type}
    (certificate : CausalEdgeCertificate Strategy Regime)
    (positive : CertifiesPositive certificate) :
    0 < certificate.kernel.effect
      certificate.target certificate.source certificate.context := by
  rw [certificate.kernelEffectMatches]
  exact certificate.positiveEstimate positive

theorem CausalEdgeCertificate.negativeKernelEffect
    {Strategy Regime : Type}
    (certificate : CausalEdgeCertificate Strategy Regime)
    (negative : CertifiesNegative certificate) :
    certificate.kernel.effect
      certificate.target certificate.source certificate.context < 0 := by
  rw [certificate.kernelEffectMatches]
  exact certificate.negativeEstimate negative

theorem CausalEdgeCertificate.certifiesOpportunityCreation
    {Strategy Regime : Type}
    (certificate : CausalEdgeCertificate Strategy Regime)
    (positive : CertifiesPositive certificate) :
    OpportunityCreatedBy certificate.kernel
      certificate.target certificate.source certificate.context :=
  certificate.positiveKernelEffect positive

theorem CausalEdgeCertificate.effectUnique
    {Strategy Regime : Type}
    (certificate : CausalEdgeCertificate Strategy Regime)
    (alternative : Scalar)
    (alternativeFits :
      FitsMoments certificate.iv.firstStage
        certificate.iv.reducedForm alternative) :
    alternative = certificate.estimate := by
  have identified : alternative = certificate.iv.effect :=
    certificate.iv.effectUnique alternative alternativeFits
  exact identified.trans certificate.effectMatches

theorem CausalEdgeCertificate.designClaimsHold
    {Strategy Regime : Type}
    (certificate : CausalEdgeCertificate Strategy Regime) :
    certificate.exogeneity.claim ∧
      certificate.exclusion.claim ∧
      certificate.noAnticipation.claim ∧
      certificate.genomeStability.claim ∧
      certificate.exposureValidity.claim ∧
      certificate.marketClearing.claim :=
  ⟨certificate.exogeneity.certified,
    certificate.exclusion.certified,
    certificate.noAnticipation.certified,
    certificate.genomeStability.certified,
    certificate.exposureValidity.certified,
    certificate.marketClearing.certified⟩

end LeanFinance.StrategyEcology
