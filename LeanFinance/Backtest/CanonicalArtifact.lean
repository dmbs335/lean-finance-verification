import LeanFinance.Backtest.Artifact

namespace LeanFinance.Backtest

/-- Canonical serialization contract used by empirical adapters.

The adapter computes the bytes and cryptographic digest externally. Lean checks
that an artifact declares the serialization contract used to produce that
digest. -/
structure CanonicalArtifactEnvelope (kind : ArtifactKind) where
  artifact : ArtifactRef kind
  canonicalFormat : String
  serializedSize : Nat
  deriving Repr

namespace CanonicalArtifactEnvelope

def Valid {kind : ArtifactKind}
    (envelope : CanonicalArtifactEnvelope kind) : Prop :=
  NonEmptyString envelope.canonicalFormat ∧
    envelope.artifact.Valid

theorem valid_artifact
    {kind : ArtifactKind}
    (envelope : CanonicalArtifactEnvelope kind)
    (valid : envelope.Valid) :
    envelope.artifact.Valid :=
  valid.2

end CanonicalArtifactEnvelope

/-- Complete artifact bundle emitted by an empirical execution adapter. -/
structure ResearchArtifactBundle where
  code : CanonicalArtifactEnvelope .sourceCode
  datasets : List (CanonicalArtifactEnvelope .dataset)
  parameters : CanonicalArtifactEnvelope .parameterSet
  environment : CanonicalArtifactEnvelope .environment
  result : CanonicalArtifactEnvelope .result
  deriving Repr

/-- Bundle identity is established before it can be attached to a certificate. -/
def ResearchArtifactBundle.Valid
    (bundle : ResearchArtifactBundle) : Prop :=
  bundle.code.Valid ∧
    bundle.datasets ≠ [] ∧
    (∀ dataset, dataset ∈ bundle.datasets → dataset.Valid) ∧
    bundle.parameters.Valid ∧
    bundle.environment.Valid ∧
    bundle.result.Valid

end LeanFinance.Backtest
