import LeanFinance.Backtest.CanonicalArtifact

namespace LeanFinance.Examples.CanonicalArtifactBundle

open LeanFinance.Backtest

def demoDataset : CanonicalArtifactEnvelope .dataset :=
  { artifact :=
      { algorithm := .sha256
        schemaId := "dataset-v1"
        digest := "dataset-hash" }
    canonicalFormat := "json-canonical-v1"
    serializedSize := 128 }

theorem demoDatasetValid : demoDataset.Valid := by
  simp [demoDataset, CanonicalArtifactEnvelope.Valid,
    ArtifactRef.Valid, NonEmptyString]

end LeanFinance.Examples.CanonicalArtifactBundle
