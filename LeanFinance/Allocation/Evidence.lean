import LeanFinance.Allocation.Policy
import LeanFinance.Backtest.Dataset
import LeanFinance.Backtest.FeatureLineage

namespace LeanFinance.Allocation

/-- Point-in-time evidence for one classified policy signal. The empirical
    adapter supplies the data and feature artifacts; Lean checks availability,
    hashes, and the direct lineage link between them. -/
structure SignalEvidence where
  dataset : Backtest.Dataset
  feature : Backtest.FeatureLineage
  deriving Repr

namespace SignalEvidence

/-- A signal is admissible only if both its source and generated feature existed
    by decision time and the feature names the source hash as an input. -/
def ValidAt (evidence : SignalEvidence) (decisionTime : Timestamp) : Prop :=
  Backtest.DatasetAvailableAt evidence.dataset decisionTime ∧
  Backtest.DatasetHashBound evidence.dataset ∧
  Backtest.FeatureAvailableAt evidence.feature decisionTime ∧
  Backtest.FeatureBoundToInputs evidence.feature ∧
  evidence.dataset.contentHash ∈ evidence.feature.inputHashes

instance instDecidableValidAt
    (evidence : SignalEvidence)
    (decisionTime : Timestamp) :
    Decidable (evidence.ValidAt decisionTime) := by
  unfold ValidAt Backtest.DatasetAvailableAt Backtest.DatasetHashBound
    Backtest.FeatureAvailableAt Backtest.FeatureBoundToInputs
    NonEmptyString
  infer_instance

theorem source_available
    (evidence : SignalEvidence)
    (decisionTime : Timestamp)
    (valid : evidence.ValidAt decisionTime) :
    Backtest.DatasetAvailableAt evidence.dataset decisionTime :=
  valid.1

theorem feature_available
    (evidence : SignalEvidence)
    (decisionTime : Timestamp)
    (valid : evidence.ValidAt decisionTime) :
    Backtest.FeatureAvailableAt evidence.feature decisionTime :=
  valid.2.2.1

theorem feature_linked_to_source
    (evidence : SignalEvidence)
    (decisionTime : Timestamp)
    (valid : evidence.ValidAt decisionTime) :
    evidence.dataset.contentHash ∈ evidence.feature.inputHashes :=
  valid.2.2.2.2

end SignalEvidence

/-- The policy uses separately evidenced trend, fragility, and volatility
    classifications. -/
structure SignalBundle where
  trend : SignalEvidence
  fragility : SignalEvidence
  volatility : SignalEvidence
  deriving Repr

namespace SignalBundle

/-- All three signals must satisfy the point-in-time contract. -/
def PointInTimeAt
    (signals : SignalBundle)
    (decisionTime : Timestamp) : Prop :=
  signals.trend.ValidAt decisionTime ∧
  signals.fragility.ValidAt decisionTime ∧
  signals.volatility.ValidAt decisionTime

instance instDecidablePointInTimeAt
    (signals : SignalBundle)
    (decisionTime : Timestamp) :
    Decidable (signals.PointInTimeAt decisionTime) := by
  unfold PointInTimeAt
  infer_instance

theorem trend_valid
    (signals : SignalBundle)
    (decisionTime : Timestamp)
    (valid : signals.PointInTimeAt decisionTime) :
    signals.trend.ValidAt decisionTime :=
  valid.1

theorem fragility_valid
    (signals : SignalBundle)
    (decisionTime : Timestamp)
    (valid : signals.PointInTimeAt decisionTime) :
    signals.fragility.ValidAt decisionTime :=
  valid.2.1

theorem volatility_valid
    (signals : SignalBundle)
    (decisionTime : Timestamp)
    (valid : signals.PointInTimeAt decisionTime) :
    signals.volatility.ValidAt decisionTime :=
  valid.2.2

end SignalBundle

end LeanFinance.Allocation
