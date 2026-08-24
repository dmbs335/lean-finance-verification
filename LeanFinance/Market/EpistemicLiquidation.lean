import LeanFinance.Core

namespace LeanFinance.Market

/-- A loss of confidence in one strategy's research evidence. Positive values
    are scaled confidence losses in the bounded market model. -/
structure EvidenceShock where
  confidenceLoss : Scalar
  deriving Repr

/-- Strategy-level response to an evidence shock. Allocation sensitivity turns
    a confidence loss into forced capital withdrawal; market impact converts
    that withdrawal into price pressure. -/
structure LiquidationParameters where
  allocationSensitivity : Scalar
  impactCoefficient : Scalar
  deriving Repr

def evidenceWithdrawal
    (shock : EvidenceShock)
    (parameters : LiquidationParameters) : Scalar :=
  shock.confidenceLoss * parameters.allocationSensitivity

def liquidationImpact
    (shock : EvidenceShock)
    (parameters : LiquidationParameters) : Scalar :=
  evidenceWithdrawal shock parameters * parameters.impactCoefficient

/-- Positive evidence loss and positive allocation sensitivity produce a
    positive forced withdrawal. This is a structural implication, not an
    empirical calibration claim. -/
theorem positive_evidence_shock_forces_withdrawal
    (shock : EvidenceShock)
    (parameters : LiquidationParameters)
    (lossPositive : 0 < shock.confidenceLoss)
    (sensitivityPositive : 0 < parameters.allocationSensitivity) :
    0 < evidenceWithdrawal shock parameters := by
  exact Int.mul_pos lossPositive sensitivityPositive

/-- Positive forced withdrawal and positive price-impact coefficient produce a
    nonzero liquidation impact. -/
theorem positive_withdrawal_moves_price
    (shock : EvidenceShock)
    (parameters : LiquidationParameters)
    (withdrawalPositive : 0 < evidenceWithdrawal shock parameters)
    (impactPositive : 0 < parameters.impactCoefficient) :
    0 < liquidationImpact shock parameters := by
  exact Int.mul_pos withdrawalPositive impactPositive

/-- Funding feedback converts a first-round mark-to-market loss into a second
    withdrawal channel. -/
structure FundingFeedback where
  markLoss : Scalar
  marginSensitivity : Scalar
  deriving Repr

def marginWithdrawal (feedback : FundingFeedback) : Scalar :=
  feedback.markLoss * feedback.marginSensitivity

theorem positive_mark_loss_amplifies_withdrawal
    (feedback : FundingFeedback)
    (lossPositive : 0 < feedback.markLoss)
    (marginPositive : 0 < feedback.marginSensitivity) :
    0 < marginWithdrawal feedback := by
  exact Int.mul_pos lossPositive marginPositive

/-- Two strategies experience synchronized evidence liquidation when the same
    shock produces positive withdrawals in both. -/
def SynchronizedLiquidation
    (shock : EvidenceShock)
    (left right : LiquidationParameters) : Prop :=
  0 < evidenceWithdrawal shock left ∧
    0 < evidenceWithdrawal shock right

theorem shared_positive_shock_synchronizes_liquidation
    (shock : EvidenceShock)
    (left right : LiquidationParameters)
    (lossPositive : 0 < shock.confidenceLoss)
    (leftSensitivity : 0 < left.allocationSensitivity)
    (rightSensitivity : 0 < right.allocationSensitivity) :
    SynchronizedLiquidation shock left right :=
  ⟨positive_evidence_shock_forces_withdrawal
      shock left lossPositive leftSensitivity,
    positive_evidence_shock_forces_withdrawal
      shock right lossPositive rightSensitivity⟩

end LeanFinance.Market
