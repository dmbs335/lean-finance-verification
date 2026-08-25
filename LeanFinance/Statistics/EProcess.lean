namespace LeanFinance.Statistics

/-- Exact nonnegative rational evidence value. -/
structure RationalEvidence where
  numerator : Nat
  denominator : Nat
  denominatorPositive : 0 < denominator
  deriving Repr, DecidableEq

namespace RationalEvidence

/-- Exact rational order by cross multiplication. -/
def Le (left right : RationalEvidence) : Prop :=
  left.numerator * right.denominator ≤
    right.numerator * left.denominator

instance : LE RationalEvidence := ⟨Le⟩

/-- Finite rational evidence comparisons are executable because both sides reduce
    to a decidable natural-number inequality. -/
instance (left right : RationalEvidence) : Decidable (left ≤ right) := by
  change Decidable (
    left.numerator * right.denominator ≤
      right.numerator * left.denominator)
  infer_instance

theorem le_iff_cross_multiply
    (left right : RationalEvidence) :
    left ≤ right ↔
      left.numerator * right.denominator ≤
        right.numerator * left.denominator := by
  rfl

theorem le_refl (value : RationalEvidence) : value ≤ value := by
  change value.numerator * value.denominator ≤
    value.numerator * value.denominator
  exact Nat.le_refl _

end RationalEvidence

/-- One exact betting factor emitted by the executable mixture e-process. -/
structure BettingFactorCertificate where
  numerator : Int
  denominator : Nat
  denominatorPositive : 0 < denominator
  nonnegative : 0 ≤ numerator
  deriving Repr

namespace BettingFactorCertificate

theorem factor_is_nonnegative
    (certificate : BettingFactorCertificate) :
    0 ≤ certificate.numerator :=
  certificate.nonnegative

end BettingFactorCertificate

/-- Arithmetic and governance certificate for an anytime evidence process.
    Statistical e-validity is conditional on the registered bounded conditional
    null assumptions. -/
structure AnytimePolicyEvidenceCertificate where
  currentEValue : RationalEvidence
  maximumEValue : RationalEvidence
  threshold : RationalEvidence
  sampleCount : Nat
  minimumSampleCount : Nat
  riskUcb : Nat
  riskBudget : Nat
  modelShift : Bool
  operationalBreach : Bool
  currentLeMaximum : currentEValue ≤ maximumEValue
  deriving Repr

namespace AnytimePolicyEvidenceCertificate

def crossed
    (certificate : AnytimePolicyEvidenceCertificate) : Prop :=
  certificate.threshold ≤ certificate.maximumEValue

def Eligible
    (certificate : AnytimePolicyEvidenceCertificate) : Prop :=
  certificate.crossed ∧
    certificate.minimumSampleCount ≤ certificate.sampleCount ∧
      certificate.riskUcb ≤ certificate.riskBudget ∧
        certificate.modelShift = false ∧
          certificate.operationalBreach = false

/-- A research promotion certificate exposes every load-bearing gate. -/
theorem eligible_has_all_gates
    (certificate : AnytimePolicyEvidenceCertificate)
    (eligible : certificate.Eligible) :
    certificate.threshold ≤ certificate.maximumEValue ∧
      certificate.minimumSampleCount ≤ certificate.sampleCount ∧
        certificate.riskUcb ≤ certificate.riskBudget ∧
          certificate.modelShift = false ∧
            certificate.operationalBreach = false :=
  eligible

/-- Model shift invalidates research promotion regardless of the e-value. -/
theorem model_shift_blocks_eligibility
    (certificate : AnytimePolicyEvidenceCertificate)
    (shift : certificate.modelShift = true) :
    ¬ certificate.Eligible := by
  intro eligible
  have impossible : true = false :=
    shift.symm.trans eligible.2.2.2.1
  exact Bool.noConfusion impossible

/-- Operational breach also invalidates research promotion. -/
theorem operational_breach_blocks_eligibility
    (certificate : AnytimePolicyEvidenceCertificate)
    (breach : certificate.operationalBreach = true) :
    ¬ certificate.Eligible := by
  intro eligible
  have impossible : true = false :=
    breach.symm.trans eligible.2.2.2.2
  exact Bool.noConfusion impossible

end AnytimePolicyEvidenceCertificate

end LeanFinance.Statistics
