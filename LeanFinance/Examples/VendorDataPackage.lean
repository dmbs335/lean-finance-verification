import LeanFinance.Backtest.VendorDataPackage

namespace LeanFinance.Examples.VendorDataPackage

open LeanFinance.Backtest

def artifact (digest : String) : ArtifactRef .dataset :=
  { algorithm := .sha256
    schemaId := "vendor-csv-v1"
    digest := digest }

def prices : VendorFileEvidence :=
  { relativePath := "prices.csv"
    kind := .prices
    rowCount := 12
    content := artifact "prices-digest" }

def manifest : VendorPackageManifest :=
  { packageId := "pit-fixture-v1"
    vendorId := "fixture-vendor"
    licenseId := "fixture-license"
    redistributionPolicy := "metadata-only"
    signerKeySha256 := "public-key-hash"
    signedAt := 50
    files := [prices]
    manifestDigest := artifact "manifest-digest" }

theorem manifest_valid : manifest.Valid := by
  simp [VendorPackageManifest.Valid, manifest, prices, artifact,
    ArtifactRef.Valid, NonEmptyString]

end LeanFinance.Examples.VendorDataPackage
