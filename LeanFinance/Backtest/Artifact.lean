import LeanFinance.Core

namespace LeanFinance.Backtest

/-- Hash algorithms accepted at the empirical/formal boundary. Lean does not
    recompute these digests; adapters must supply digests produced by the named
    algorithm. The algorithm tag prevents silent cross-algorithm comparison. -/
inductive HashAlgorithm where
  | sha256
  | sha512
  | blake3
  deriving Repr, DecidableEq

/-- Domain separation for content-addressed research artifacts. -/
inductive ArtifactKind where
  | sourceCode
  | dataset
  | parameterSet
  | environment
  | result
  | feature
  | searchLedger
  deriving Repr, DecidableEq

/-- A digest indexed by its artifact domain. The kind is part of the type, so a
    dataset digest cannot be substituted for a code digest without an explicit
    conversion at the trusted boundary. -/
structure ArtifactRef (kind : ArtifactKind) where
  algorithm : HashAlgorithm
  digest : ContentHash
  deriving Repr, DecidableEq

namespace ArtifactRef

/-- The formal layer requires a concrete digest value. Cryptographic correctness
    of that digest remains an adapter obligation. -/
def Valid {kind : ArtifactKind} (artifact : ArtifactRef kind) : Prop :=
  NonEmptyString artifact.digest

theorem valid_digest_nonempty
    {kind : ArtifactKind}
    (artifact : ArtifactRef kind)
    (valid : artifact.Valid) :
    artifact.digest ≠ "" :=
  valid

end ArtifactRef

/-- A domain-separated experiment manifest. Compared with the legacy manifest,
    each field carries both its hash algorithm and its artifact domain. -/
structure BoundExperimentManifest where
  name : String
  code : ArtifactRef .sourceCode
  datasets : List (ArtifactRef .dataset)
  parameters : ArtifactRef .parameterSet
  environment : ArtifactRef .environment
  result : ArtifactRef .result
  deriving Repr

/-- Stronger reproducibility contract for a bound manifest. This contract is
    intentionally about artifact identity, not about statistical correctness. -/
def StronglyReproducible (manifest : BoundExperimentManifest) : Prop :=
  NonEmptyString manifest.name ∧
    manifest.code.Valid ∧
    manifest.datasets ≠ [] ∧
    (∀ dataset, dataset ∈ manifest.datasets → dataset.Valid) ∧
    manifest.parameters.Valid ∧
    manifest.environment.Valid ∧
    manifest.result.Valid

theorem stronglyReproducible_code_bound
    (manifest : BoundExperimentManifest)
    (reproducible : StronglyReproducible manifest) :
    manifest.code.Valid :=
  reproducible.2.1

theorem stronglyReproducible_result_bound
    (manifest : BoundExperimentManifest)
    (reproducible : StronglyReproducible manifest) :
    manifest.result.Valid :=
  reproducible.2.2.2.2.2.2

end LeanFinance.Backtest
