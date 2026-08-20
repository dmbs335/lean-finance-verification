import LeanFinance.Backtest.Artifact
import LeanFinance.Backtest.Certificate
import LeanFinance.Backtest.CommittedSearchLedger
import LeanFinance.Backtest.LineageClosure
import LeanFinance.Backtest.NoFutureInformation

namespace LeanFinance.Backtest

/-- End-to-end research-integrity certificate for one backtest claim.

The certificate does not prove profitability. It binds the claimed result to a
specific code/data/parameter/environment manifest, requires the selected trial
to have been preregistered, closes feature provenance recursively, and enforces
point-in-time admissibility. -/
structure ProofCarryingBacktestCertificate
    (claim : BacktestClaim) : Prop where
  manifest : BoundExperimentManifest
  ledger : CommittedSearchLedger
  lineageCatalog : LineageCatalog
  manifestBound : StronglyReproducible manifest
  resultBound : manifest.result.digest = claim.resultHash
  parameterBound : manifest.parameters.digest = claim.decision.parameterHash
  dataBound :
    ∀ dataset,
      dataset ∈ claim.decision.datasets →
      ∃ artifact,
        artifact ∈ manifest.datasets ∧
        artifact.digest = dataset.contentHash
  noFutureInformation : NoFutureInformation claim.decision
  lineageClosed : DecisionLineageClosed lineageCatalog claim.decision
  ledgerValid : ledger.Valid
  selectedTrialPreRegistered :
    ∃ trial,
      trial ∈ ledger.entries ∧
      trial.hypothesisId = claim.decision.strategyId ∧
      trial.parameters.digest = manifest.parameters.digest ∧
      trial.code.digest = manifest.code.digest ∧
      trial.registeredAt ≤ claim.decision.decisionTime

namespace ProofCarryingBacktestCertificate

theorem selected_parameter_registered_before_decision
    (claim : BacktestClaim)
    (certificate : ProofCarryingBacktestCertificate claim) :
    ∃ trial,
      trial ∈ certificate.ledger.entries ∧
      trial.parameters.digest = claim.decision.parameterHash ∧
      trial.registeredAt ≤ claim.decision.decisionTime := by
  rcases certificate.selectedTrialPreRegistered with
    ⟨trial, member, _strategyMatches, trialParameter,
      _codeMatches, registeredBefore⟩
  refine ⟨trial, member, ?_, registeredBefore⟩
  exact trialParameter.trans certificate.parameterBound

theorem used_dataset_is_manifest_bound
    (claim : BacktestClaim)
    (certificate : ProofCarryingBacktestCertificate claim)
    (dataset : Dataset)
    (used : dataset ∈ claim.decision.datasets) :
    ∃ artifact,
      artifact ∈ certificate.manifest.datasets ∧
      artifact.digest = dataset.contentHash :=
  certificate.dataBound dataset used

theorem used_dataset_available_before_decision
    (claim : BacktestClaim)
    (certificate : ProofCarryingBacktestCertificate claim)
    (dataset : Dataset)
    (used : dataset ∈ claim.decision.datasets) :
    dataset.availableAt ≤ claim.decision.decisionTime := by
  change DatasetAvailableAt dataset claim.decision.decisionTime
  exact (no_future_information_data claim.decision
    certificate.noFutureInformation) dataset used

theorem used_feature_has_recursive_lineage
    (claim : BacktestClaim)
    (certificate : ProofCarryingBacktestCertificate claim)
    (feature : FeatureLineage)
    (used : feature ∈ claim.decision.features) :
    ∃ derived,
      derived.lineage = feature ∧
      ArtifactAvailableAt certificate.lineageCatalog
        claim.decision.decisionTime derived.outputHash :=
  DecisionLineageClosed.feature_has_recursive_proof
    certificate.lineageCatalog
    claim.decision
    certificate.lineageClosed
    feature
    used

end ProofCarryingBacktestCertificate

end LeanFinance.Backtest
