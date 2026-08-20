import LeanFinance.Backtest.IntegrityCertificate

namespace LeanFinance.Examples.ProofCarryingBacktest

open LeanFinance.Backtest

def demoCode : ArtifactRef .sourceCode :=
  { algorithm := .sha256
    schemaId := "git-tree-v1"
    digest := "code-demo-001" }

def demoDatasetArtifact : ArtifactRef .dataset :=
  { algorithm := .sha256
    schemaId := "dataset-v1"
    digest := "dataset-demo-001" }

def demoParameters : ArtifactRef .parameterSet :=
  { algorithm := .sha256
    schemaId := "parameters-v1"
    digest := "params-demo-001" }

def demoEnvironment : ArtifactRef .environment :=
  { algorithm := .sha256
    schemaId := "environment-v1"
    digest := "env-demo-001" }

def demoResult : ArtifactRef .result :=
  { algorithm := .sha256
    schemaId := "result-v1"
    digest := "result-demo-001" }

def demoLedgerCommitment : ArtifactRef .searchLedger :=
  { algorithm := .sha256
    schemaId := "search-ledger-v1"
    digest := "ledger-demo-001" }

def demoDataset : Dataset :=
  { id := "prices-demo"
    observedAt := 4
    availableAt := 5
    contentHash := demoDatasetArtifact.digest }

def demoFeatureLineage : FeatureLineage :=
  { featureName := "momentum-demo"
    inputHashes := [demoDataset.contentHash]
    generatedAt := 6
    codeHash := "feature-code-demo-001" }

def demoDerivedFeature : DerivedFeature :=
  { outputHash := "feature-demo-001"
    lineage := demoFeatureLineage }

def demoCatalog : LineageCatalog :=
  { datasets := [demoDataset]
    features := [demoDerivedFeature] }

def demoDecision : Decision :=
  { strategyId := "momentum-v1"
    decisionTime := 10
    datasets := [demoDataset]
    features := [demoFeatureLineage]
    parameterHash := demoParameters.digest }

def demoManifest : BoundExperimentManifest :=
  { name := "proof-carrying-demo"
    code := demoCode
    datasets := [demoDatasetArtifact]
    parameters := demoParameters
    environment := demoEnvironment
    result := demoResult }

def demoTrial : RegisteredTrial :=
  { hypothesisId := demoDecision.strategyId
    parameters := demoParameters
    code := demoCode
    registeredAt := 7
    previousCommitment := none
    commitment := demoLedgerCommitment }

def demoLedger : CommittedSearchLedger :=
  { entries := [demoTrial] }

def demoAnchor : LedgerAnchor :=
  { commitment := demoLedgerCommitment
    entryCount := 1
    anchoredAt := 8 }

def demoClaim : BacktestClaim :=
  { decision := demoDecision
    resultHash := demoResult.digest
    metricName := "net-alpha-bps"
    metricValue := 42 }

theorem demoManifestBound : StronglyReproducible demoManifest := by
  simp [StronglyReproducible, demoManifest, ArtifactRef.Valid,
    NonEmptyString, demoCode, demoDatasetArtifact, demoParameters,
    demoEnvironment, demoResult]

theorem demoDatasetAvailable :
    ArtifactAvailableAt demoCatalog demoDecision.decisionTime
      demoDataset.contentHash := by
  apply ArtifactAvailableAt.dataset demoDataset
  · simp [demoCatalog]
  · simp [DatasetAvailableAt, demoDataset, demoDecision]
  · simp [DatasetHashBound, demoDataset, demoDatasetArtifact, NonEmptyString]

theorem demoFeatureAvailable :
    ArtifactAvailableAt demoCatalog demoDecision.decisionTime
      demoDerivedFeature.outputHash := by
  apply ArtifactAvailableAt.feature demoDerivedFeature
  · simp [demoCatalog]
  · simp [demoDerivedFeature, NonEmptyString]
  · simp [FeatureAvailableAt, demoDerivedFeature, demoFeatureLineage,
      demoDecision]
  · simp [FeatureBoundToInputs, demoDerivedFeature, demoFeatureLineage,
      NonEmptyString]
  · intro inputHash member
    simp [demoDerivedFeature, demoFeatureLineage] at member
    subst inputHash
    exact demoDatasetAvailable

theorem demoNoFutureInformation : NoFutureInformation demoDecision := by
  constructor
  · intro dataset used
    simp [demoDecision] at used
    subst dataset
    simp [DatasetAvailableAt, demoDataset, demoDecision]
  · intro feature used
    simp [demoDecision] at used
    subst feature
    simp [FeatureAvailableAt, demoFeatureLineage, demoDecision]

theorem demoLineageClosed : DecisionLineageClosed demoCatalog demoDecision := by
  intro lineage used
  simp [demoDecision] at used
  subst lineage
  refine ⟨demoDerivedFeature, ?_, rfl, demoFeatureAvailable⟩
  simp [demoCatalog]

theorem demoLedgerValid : demoLedger.Valid := by
  simp [CommittedSearchLedger.Valid, ValidCommittedChain,
    ValidCommittedSuffix, demoLedger, demoTrial, RegisteredTrial.Bound,
    ArtifactRef.Valid, NonEmptyString, demoDecision, demoCode, demoParameters,
    demoLedgerCommitment]

theorem demoLedgerAnchored : AnchorsLedger demoAnchor demoLedger := by
  simp [AnchorsLedger, demoAnchor, demoLedger, lastCommitment, demoTrial,
    ArtifactRef.Valid, NonEmptyString, demoLedgerCommitment]

theorem demoAnchorAvailable : AnchorAvailableAt demoAnchor demoDecision := by
  simp [AnchorAvailableAt, demoAnchor, demoDecision]

def demoCertificate : ProofCarryingBacktestCertificate demoClaim :=
  { manifest := demoManifest
    ledger := demoLedger
    ledgerAnchor := demoAnchor
    lineageCatalog := demoCatalog
    manifestBound := demoManifestBound
    resultBound := rfl
    parameterBound := rfl
    dataBound := by
      intro dataset used
      simp [demoClaim, demoDecision] at used
      subst dataset
      refine ⟨demoDatasetArtifact, ?_, rfl⟩
      simp [demoManifest]
    noFutureInformation := demoNoFutureInformation
    lineageClosed := demoLineageClosed
    ledgerValid := demoLedgerValid
    ledgerAnchored := demoLedgerAnchored
    anchorAvailable := demoAnchorAvailable
    selectedTrialPreRegistered := by
      refine ⟨demoTrial, ?_, rfl, rfl, rfl, ?_⟩
      · simp [demoLedger]
      · simp [demoTrial, demoClaim, demoDecision] }

theorem demo_selected_parameter_was_registered_before_decision :
    ∃ trial,
      trial ∈ demoCertificate.ledger.entries ∧
      trial.parameters.digest = demoClaim.decision.parameterHash ∧
      trial.registeredAt ≤ demoClaim.decision.decisionTime :=
  ProofCarryingBacktestCertificate.selected_parameter_registered_before_decision
    demoClaim demoCertificate

theorem demo_ledger_was_anchored_before_decision :
    demoCertificate.ledgerAnchor.anchoredAt ≤
      demoClaim.decision.decisionTime :=
  ProofCarryingBacktestCertificate.ledger_was_anchored_before_decision
    demoClaim demoCertificate

theorem demo_feature_has_recursive_point_in_time_lineage :
    ∃ derived : DerivedFeature,
      derived.lineage = demoFeatureLineage ∧
      ArtifactAvailableAt demoCertificate.lineageCatalog
        demoClaim.decision.decisionTime derived.outputHash :=
  ProofCarryingBacktestCertificate.used_feature_has_recursive_lineage
    demoClaim demoCertificate demoFeatureLineage (by simp [demoClaim, demoDecision])

end LeanFinance.Examples.ProofCarryingBacktest
