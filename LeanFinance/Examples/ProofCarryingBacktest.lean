import LeanFinance.Certificate.Verification

namespace LeanFinance.Examples

open Backtest Certificate

def sampleDataset : Dataset :=
  {
    id := "prices-2026-01-02"
    snapshotAt := 10
    availableAt := 12
    contentHash := "sha256:prices"
  }

def sampleStrategy : StrategyCertificate :=
  {
    strategyId := "toy-momentum"
    codeHash := "sha256:code"
    parameterHash := "sha256:parameters"
    strategyIdPresent := by decide
    codeHashPresent := by decide
    parameterHashPresent := by decide
  }

def sampleDataCertificate : DataCertificate :=
  {
    decisionTime := 20
    datasets := [sampleDataset]
    available := by
      intro dataset member
      simp at member
      subst dataset
      decide
    hashed := by
      intro dataset member
      simp at member
      subst dataset
      decide
    wellFormed := by
      intro dataset member
      simp at member
      subst dataset
      decide
  }

def sampleFeature : FeatureLineage :=
  {
    featureName := "twenty-day-return"
    inputDatasetHashes := [sampleDataset.contentHash]
    generatedAt := 18
    codeHash := "sha256:feature-code"
  }

def sampleSearchEntry : SearchEntry :=
  {
    hypothesis := "positive trailing return"
    parameterHash := sampleStrategy.parameterHash
    createdAt := 15
  }

def sampleSearchLedger : SearchLedger :=
  { entries := [sampleSearchEntry] }

def sampleExperiment : Experiment :=
  {
    name := "toy-momentum-run"
    codeVersion := sampleStrategy.codeHash
    dataVersion := sampleDataset.contentHash
    parameterVersion := sampleStrategy.parameterHash
    environmentHash := "sha256:lean-environment"
  }

def sampleClaim : BacktestClaim :=
  {
    description := "Toy point-in-time backtest result"
    result :=
      {
        observations := 100
        grossReturnBps := 240
        netReturnBps := 180
        generatedAt := 25
      }
  }

def sampleCertificate : BacktestCertificate :=
  {
    strategy := sampleStrategy
    data := sampleDataCertificate
    features := [sampleFeature]
    searchLedger := sampleSearchLedger
    experiment := sampleExperiment
    claim := sampleClaim
    reproducible := by decide
    searchRecorded := by
      refine ⟨sampleSearchEntry, ?_, rfl⟩
      simp [sampleSearchLedger]
    featuresValid := by
      intro feature member
      simp at member
      subst feature
      decide
    featureInputsBound := by
      intro feature featureMember inputHash inputMember
      simp at featureMember
      subst feature
      simp at inputMember
      subst inputHash
      exact sampleDataCertificate.containsHash_of_member
        sampleDataset
        (by simp [sampleDataCertificate])
    claimWellFormed := by decide
    resultAfterDecision := by decide
  }

example : VerifiedResearchClaim sampleCertificate :=
  certificate_sound sampleCertificate

example : Backtest.NoFutureInformation sampleCertificate.toDecision :=
  sampleCertificate.noFutureInformation

end LeanFinance.Examples
