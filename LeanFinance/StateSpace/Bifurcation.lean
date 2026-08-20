import LeanFinance.StateSpace.Model

namespace LeanFinance.StateSpace

inductive StabilityClass where
  | contracting
  | nonexpansive
  | expanding
  deriving Repr, DecidableEq

inductive CrossingDirection where
  | upward
  | downward
  deriving Repr, DecidableEq

inductive TippingMechanism where
  | bifurcation
  | noiseEscape
  | rateInduced
  | borderCollision
  | jump
  deriving Repr, DecidableEq

structure StabilityAssessment where
  parameterValue : Nat
  classification : StabilityClass
  modelFamilyHash : ContentHash
  evidenceHash : ContentHash
  deriving Repr, DecidableEq

def CrossesCritical
    (direction : CrossingDirection)
    (before after critical : Nat) : Prop :=
  match direction with
  | .upward =>
      before < critical ∧ critical ≤ after
  | .downward =>
      after < critical ∧ critical ≤ before

instance decidableCrossesCritical
    (direction : CrossingDirection)
    (before after critical : Nat) :
    Decidable (CrossesCritical direction before after critical) := by
  cases direction <;>
    unfold CrossesCritical <;>
    infer_instance

/-- Bookkeeping required before calling a stability-class transition a
    bifurcation. This certificate does not derive the classifications from a
    Jacobian; those evidence artifacts remain at the trusted empirical boundary. -/
structure BifurcationClaimCertificate
    (direction : CrossingDirection)
    (before after : StabilityAssessment)
    (critical : Nat) : Prop where
  crossesCritical :
    CrossesCritical direction
      before.parameterValue after.parameterValue critical
  sameModelFamily :
    before.modelFamilyHash = after.modelFamilyHash
  modelFamilyHashNonempty :
    NonEmptyString before.modelFamilyHash
  beforeEvidenceHashNonempty :
    NonEmptyString before.evidenceHash
  afterEvidenceHashNonempty :
    NonEmptyString after.evidenceHash
  qualitativeChange :
    before.classification ≠ after.classification

theorem BifurcationClaimCertificate.sound
    (direction : CrossingDirection)
    (before after : StabilityAssessment)
    (critical : Nat)
    (certificate :
      BifurcationClaimCertificate
        direction before after critical) :
    CrossesCritical direction
        before.parameterValue after.parameterValue critical ∧
      before.classification ≠ after.classification ∧
      before.modelFamilyHash = after.modelFamilyHash :=
  ⟨certificate.crossesCritical,
    certificate.qualitativeChange,
    certificate.sameModelFamily⟩

end LeanFinance.StateSpace
