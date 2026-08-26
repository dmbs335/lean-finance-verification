import LeanFinance.Core

namespace LeanFinance.Backtest

universe u v w x

/-- Two hidden input histories are indistinguishable by a cutoff when every key
    whose value was available by that cutoff has the same value in both worlds.
    Later keys may differ arbitrarily. -/
def HistoryPrefixEquivalent
    {Key : Type u}
    {Value : Type v}
    (availableAt : Key → Timestamp)
    (left right : Key → Option Value)
    (cutoff : Timestamp) : Prop :=
  ∀ key,
    availableAt key ≤ cutoff →
      left key = right key

/-- Temporal noninterference for one time-indexed computation. Fixing the
    strategy and execution environment is represented by fixing `run`; only the
    hidden input history varies. -/
def TemporalNoninterference
    {Key : Type u}
    {Value : Type v}
    {Output : Type w}
    (availableAt : Key → Timestamp)
    (run : (Key → Option Value) → Timestamp → Output) : Prop :=
  ∀ cutoff left right,
    HistoryPrefixEquivalent availableAt left right cutoff →
      run left cutoff = run right cutoff

/-- Equality of a derived time series through one cutoff. -/
def SeriesPrefixEquivalent
    {Value : Type v}
    (left right : Timestamp → Value)
    (cutoff : Timestamp) : Prop :=
  ∀ time,
    time ≤ cutoff →
      left time = right time

/-- A feature transform preserves every input-prefix equivalence through the
    corresponding output prefix. -/
def PrefixNoninterferingSeries
    {Key : Type u}
    {Input : Type v}
    {Feature : Type w}
    (availableAt : Key → Timestamp)
    (feature : (Key → Option Input) → Timestamp → Feature) : Prop :=
  ∀ cutoff left right,
    HistoryPrefixEquivalent availableAt left right cutoff →
      SeriesPrefixEquivalent (feature left) (feature right) cutoff

/-- A downstream consumer uses only the derived prefix available by its current
    decision time. -/
def PrefixCausalConsumer
    {Feature : Type v}
    {Output : Type w}
    (consumer : (Timestamp → Feature) → Timestamp → Output) : Prop :=
  ∀ cutoff left right,
    SeriesPrefixEquivalent left right cutoff →
      consumer left cutoff = consumer right cutoff

/-- Temporal Composition Law. A prefix-noninterfering feature transform followed
    by a prefix-causal consumer yields a temporally noninterfering pipeline. -/
theorem temporal_pipeline_composition
    {Key : Type u}
    {Input : Type v}
    {Feature : Type w}
    {Output : Type x}
    (availableAt : Key → Timestamp)
    (feature : (Key → Option Input) → Timestamp → Feature)
    (consumer : (Timestamp → Feature) → Timestamp → Output)
    (featureSafe : PrefixNoninterferingSeries availableAt feature)
    (consumerSafe : PrefixCausalConsumer consumer) :
    TemporalNoninterference availableAt
      (fun history => consumer (feature history)) := by
  intro cutoff left right sameInput
  exact consumerSafe cutoff (feature left) (feature right)
    (featureSafe cutoff left right sameInput)

/-- Pointwise deterministic post-processing preserves temporal
    noninterference. -/
theorem pointwise_postprocessing_preserves_noninterference
    {Key : Type u}
    {Input : Type v}
    {Intermediate : Type w}
    {Output : Type x}
    (availableAt : Key → Timestamp)
    (run : (Key → Option Input) → Timestamp → Intermediate)
    (postprocess : Intermediate → Output)
    (safe : TemporalNoninterference availableAt run) :
    TemporalNoninterference availableAt
      (fun history cutoff => postprocess (run history cutoff)) := by
  intro cutoff left right sameInput
  exact congrArg postprocess (safe cutoff left right sameInput)

/-- Constructive witness for a future-information leak. -/
structure TemporalCounterexample
    {Key : Type u}
    {Input : Type v}
    {Output : Type w}
    (availableAt : Key → Timestamp)
    (run : (Key → Option Input) → Timestamp → Output) where
  cutoff : Timestamp
  left : Key → Option Input
  right : Key → Option Input
  sameAvailablePrefix :
    HistoryPrefixEquivalent availableAt left right cutoff
  outputDifferent : run left cutoff ≠ run right cutoff

namespace TemporalCounterexample

/-- One prefix-equivalent counterexample refutes temporal noninterference. -/
theorem not_temporally_noninterfering
    {Key : Type u}
    {Input : Type v}
    {Output : Type w}
    {availableAt : Key → Timestamp}
    {run : (Key → Option Input) → Timestamp → Output}
    (counterexample : TemporalCounterexample availableAt run) :
    ¬ TemporalNoninterference availableAt run := by
  intro safe
  exact counterexample.outputDifferent
    (safe counterexample.cutoff counterexample.left counterexample.right
      counterexample.sameAvailablePrefix)

end TemporalCounterexample

end LeanFinance.Backtest
