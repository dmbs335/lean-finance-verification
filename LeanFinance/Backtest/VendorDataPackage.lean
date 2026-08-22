import LeanFinance.Backtest.Artifact

namespace LeanFinance.Backtest

inductive VendorFileKind where
  | vintages
  | listings
  | prices
  | corporateActions
  deriving Repr, DecidableEq

/-- Normalized evidence for one file after digest, row-count, and schema
    validation. -/
structure VendorFileEvidence where
  relativePath : String
  kind : VendorFileKind
  rowCount : Nat
  content : ArtifactRef .dataset
  deriving Repr

structure VendorPackageManifest where
  packageId : String
  vendorId : String
  licenseId : String
  redistributionPolicy : String
  signerKeySha256 : String
  signedAt : Timestamp
  files : List VendorFileEvidence
  manifestDigest : ArtifactRef .dataset
  deriving Repr

namespace VendorPackageManifest

def Valid (manifest : VendorPackageManifest) : Prop :=
  NonEmptyString manifest.packageId ∧
    NonEmptyString manifest.vendorId ∧
    NonEmptyString manifest.licenseId ∧
    NonEmptyString manifest.redistributionPolicy ∧
    NonEmptyString manifest.signerKeySha256 ∧
    manifest.files ≠ [] ∧
    (∀ file, file ∈ manifest.files →
      NonEmptyString file.relativePath ∧
        file.rowCount > 0 ∧
          file.content.Valid) ∧
    manifest.manifestDigest.Valid

end VendorPackageManifest

/-- Proof boundary after verifier-selected public-key signature validation and
    exact file checks.

    Each external verification statement is supplied as a proposition and the
    structure carries a proof of that proposition. Declaring a field merely as
    `Prop` would store a proposition value rather than evidence that it holds,
    and is invalid in a `Prop`-valued Lean structure. -/
structure VerifiedVendorPackage
    (manifest : VendorPackageManifest)
    (SignatureVerified FileDigestsMatch RowCountsMatch SchemasMatch : Prop) : Prop where
  manifestValid : manifest.Valid
  signatureVerified : SignatureVerified
  fileDigestsMatch : FileDigestsMatch
  rowCountsMatch : RowCountsMatch
  schemasMatch : SchemasMatch

namespace VerifiedVendorPackage

theorem has_valid_manifest
    {manifest : VendorPackageManifest}
    {SignatureVerified FileDigestsMatch RowCountsMatch SchemasMatch : Prop}
    (verified : VerifiedVendorPackage manifest SignatureVerified
      FileDigestsMatch RowCountsMatch SchemasMatch) :
    manifest.Valid :=
  verified.manifestValid

end VerifiedVendorPackage

end LeanFinance.Backtest
