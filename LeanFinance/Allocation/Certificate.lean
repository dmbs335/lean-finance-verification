import LeanFinance.Allocation.Evidence

namespace LeanFinance.Allocation

/-- Serializable claim emitted by an empirical allocation pipeline. -/
structure AllocationCertificate where
  strategyId : StrategyId
  decisionTime : Timestamp
  input : PolicyInput
  signals : SignalBundle
  declaredDecision : AllocationDecision
  parameterHash : ContentHash
  policyCodeHash : ContentHash
  deriving Repr

namespace AllocationCertificate

/-- Non-empty identifiers bind the decision to a strategy, parameter set, and
    policy implementation. -/
def Bound (certificate : AllocationCertificate) : Prop :=
  NonEmptyString certificate.strategyId ∧
  NonEmptyString certificate.parameterHash ∧
  NonEmptyString certificate.policyCodeHash

instance instDecidableBound (certificate : AllocationCertificate) :
    Decidable certificate.Bound := by
  unfold Bound NonEmptyString
  infer_instance

/-- The declared output must be exactly the deterministic policy output. -/
def PolicyCorrect (certificate : AllocationCertificate) : Prop :=
  certificate.declaredDecision = allocationDecision certificate.input

instance instDecidablePolicyCorrect (certificate : AllocationCertificate) :
    Decidable certificate.PolicyCorrect := by
  unfold PolicyCorrect
  infer_instance

/-- Validity deliberately proves implementation and data-integrity properties,
    not future profitability or statistical calibration. -/
def Valid (certificate : AllocationCertificate) : Prop :=
  certificate.signals.PointInTimeAt certificate.decisionTime ∧
  certificate.Bound ∧
  certificate.PolicyCorrect

instance instDecidableValid (certificate : AllocationCertificate) :
    Decidable certificate.Valid := by
  unfold Valid
  infer_instance

/-- Executable checker at the empirical/formal boundary. -/
def check (certificate : AllocationCertificate) : Bool :=
  decide certificate.Valid

theorem check_eq_true_iff_valid (certificate : AllocationCertificate) :
    certificate.check = true ↔ certificate.Valid := by
  by_cases valid : certificate.Valid
  · simp [check, valid]
  · simp [check, valid]

theorem check_sound
    (certificate : AllocationCertificate)
    (accepted : certificate.check = true) :
    certificate.Valid :=
  (check_eq_true_iff_valid certificate).mp accepted

end AllocationCertificate

/-- A proof-carrying allocation decision. -/
structure VerifiedAllocation where
  certificate : AllocationCertificate
  sound : certificate.Valid

namespace VerifiedAllocation

/-- Convert a successful executable check into a proof-carrying value. -/
def ofAccepted
    (certificate : AllocationCertificate)
    (accepted : certificate.check = true) : VerifiedAllocation :=
  {
    certificate := certificate
    sound := certificate.check_sound accepted
  }

theorem point_in_time (verified : VerifiedAllocation) :
    verified.certificate.signals.PointInTimeAt
      verified.certificate.decisionTime :=
  verified.sound.1

theorem bound (verified : VerifiedAllocation) :
    verified.certificate.Bound :=
  verified.sound.2.1

theorem policy_correct (verified : VerifiedAllocation) :
    verified.certificate.declaredDecision =
      allocationDecision verified.certificate.input :=
  verified.sound.2.2

/-- Every verified allocation preserves the strategic core. -/
theorem preserves_core (verified : VerifiedAllocation) :
    coreRiskBps ≤ verified.certificate.declaredDecision.riskBps := by
  rw [verified.policy_correct]
  exact core_floor
    verified.certificate.input.trend
    verified.certificate.input.fragility
    verified.certificate.input.volatility

/-- Every verified allocation remains unlevered under this policy contract. -/
theorem respects_full_investment_ceiling (verified : VerifiedAllocation) :
    verified.certificate.declaredDecision.riskBps ≤ fullRiskBps := by
  rw [verified.policy_correct]
  exact full_investment_ceiling
    verified.certificate.input.trend
    verified.certificate.input.fragility
    verified.certificate.input.volatility

/-- Every verified tactical allocation is within its declared ten-unit budget. -/
theorem respects_tactical_budget (verified : VerifiedAllocation) :
    verified.certificate.declaredDecision.tacticalUnits ≤ maxTacticalUnits := by
  rw [verified.policy_correct]
  exact targetTacticalUnits_le_max
    verified.certificate.input.trend
    verified.certificate.input.fragility
    verified.certificate.input.volatility

/-- If the certified input says the trend is falling, the tactical sleeve must
    be zero; a forged non-zero output cannot obtain this certificate. -/
theorem falling_has_no_tactical_exposure
    (verified : VerifiedAllocation)
    (falling : verified.certificate.input.trend = .falling) :
    verified.certificate.declaredDecision.tacticalUnits = 0 := by
  rw [verified.policy_correct]
  change targetTacticalUnits
    verified.certificate.input.trend
    verified.certificate.input.fragility
    verified.certificate.input.volatility = 0
  simpa [falling] using falling_has_zero_tactical
    verified.certificate.input.fragility
    verified.certificate.input.volatility

/-- Falling trend still cannot force a full liquidation of the strategic core. -/
theorem falling_keeps_core
    (verified : VerifiedAllocation)
    (falling : verified.certificate.input.trend = .falling) :
    verified.certificate.declaredDecision.riskBps = coreRiskBps := by
  rw [verified.policy_correct]
  change targetRiskBps
    verified.certificate.input.trend
    verified.certificate.input.fragility
    verified.certificate.input.volatility = coreRiskBps
  simpa [falling] using falling_preserves_core
    verified.certificate.input.fragility
    verified.certificate.input.volatility

end VerifiedAllocation

end LeanFinance.Allocation
