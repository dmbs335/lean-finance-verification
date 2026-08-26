import Mathlib

namespace LeanFinance.Formula

/-- Exact scalar specification and one concrete implementation result. Integer
    outputs keep the controlled proof layer deterministic; production adapters
    may scale decimals, prices, or risk measures into an exact integer unit. -/
structure ScalarApproximation where
  specified : Int
  implemented : Int
  deriving Repr, DecidableEq

namespace ScalarApproximation

/-- Absolute implementation error in the declared scaled output unit. -/
def error (approximation : ScalarApproximation) : Nat :=
  Int.natAbs (approximation.implemented - approximation.specified)

/-- The implementation conforms to the specification within a declared error
    budget. -/
def Within
    (approximation : ScalarApproximation)
    (tolerance : Nat) : Prop :=
  approximation.error ≤ tolerance

/-- Exact equality is zero-error conformance. -/
theorem exact_within_zero
    (approximation : ScalarApproximation)
    (exact : approximation.implemented = approximation.specified) :
    approximation.Within 0 := by
  simp [Within, error, exact]

end ScalarApproximation

/-- Add two independently implemented scalar terms. This is the basic error
    composition needed by PnL attribution: each local approximation contributes
    at most its own declared error budget to the aggregate sum. -/
def addApproximation
    (left right : ScalarApproximation) : ScalarApproximation :=
  { specified := left.specified + right.specified
    implemented := left.implemented + right.implemented }

/-- Additive approximation composition theorem.

    If two local formula applications are within `leftTolerance` and
    `rightTolerance`, their sum is within the sum of those budgets. -/
theorem additive_approximation_error_bound
    (left right : ScalarApproximation)
    (leftTolerance rightTolerance : Nat)
    (leftWithin : left.Within leftTolerance)
    (rightWithin : right.Within rightTolerance) :
    (addApproximation left right).Within
      (leftTolerance + rightTolerance) := by
  unfold ScalarApproximation.Within ScalarApproximation.error addApproximation
  have rearrange :
      (left.implemented + right.implemented) -
          (left.specified + right.specified) =
        (left.implemented - left.specified) +
          (right.implemented - right.specified) := by
    ring
  rw [rearrange]
  exact le_trans
    (Int.natAbs_add_le
      (left.implemented - left.specified)
      (right.implemented - right.specified))
    (Nat.add_le_add leftWithin rightWithin)

/-- A pipeline-level error certificate is constructive: it carries the local
    approximations, their budgets, and proofs that the declared aggregate error
    follows from those local contracts. -/
structure AdditiveErrorCertificate where
  left : ScalarApproximation
  right : ScalarApproximation
  leftTolerance : Nat
  rightTolerance : Nat
  leftWithin : left.Within leftTolerance
  rightWithin : right.Within rightTolerance

namespace AdditiveErrorCertificate

def totalTolerance (certificate : AdditiveErrorCertificate) : Nat :=
  certificate.leftTolerance + certificate.rightTolerance

 theorem aggregate_within_total_tolerance
    (certificate : AdditiveErrorCertificate) :
    (addApproximation certificate.left certificate.right).Within
      certificate.totalTolerance :=
  additive_approximation_error_bound
    certificate.left certificate.right
    certificate.leftTolerance certificate.rightTolerance
    certificate.leftWithin certificate.rightWithin

end AdditiveErrorCertificate

end LeanFinance.Formula
