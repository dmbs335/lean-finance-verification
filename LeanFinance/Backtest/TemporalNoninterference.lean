import LeanFinance.Core

namespace LeanFinance.Backtest

universe u v w

/-- A backtest engine together with the causal-prefix abstraction through which
    past output should factor. `run` may inspect the full dataset; the
    factorization property is the actual safety obligation. -/
structure TemporalEngine
    (Data : Type u)
    (Prefix : Type v)
    (Output : Type w) where
  causalPrefix : Timestamp → Data → Prefix
  run : Data → Output
  runFromPrefix : Timestamp → Prefix → Output
  outputPrefix : Timestamp → Output → Output

namespace TemporalEngine

/-- Two complete datasets are causally equivalent at `cutoff` when the engine's
    declared information prefix is equal at that time. -/
def DataEquivalentAt
    {Data : Type u}
    {Prefix : Type v}
    {Output : Type w}
    (engine : TemporalEngine Data Prefix Output)
    (cutoff : Timestamp)
    (left right : Data) : Prop :=
  engine.causalPrefix cutoff left =
    engine.causalPrefix cutoff right

/-- The observed output prefix of a full run factors through only the declared
    causal data prefix. -/
def CausallyFactors
    {Data : Type u}
    {Prefix : Type v}
    {Output : Type w}
    (engine : TemporalEngine Data Prefix Output) : Prop :=
  ∀ cutoff data,
    engine.outputPrefix cutoff (engine.run data) =
      engine.outputPrefix cutoff
        (engine.runFromPrefix cutoff
          (engine.causalPrefix cutoff data))

/-- Temporal noninterference: changing anything outside the causal prefix cannot
    change the output visible through the same cutoff. -/
def TemporalNoninterference
    {Data : Type u}
    {Prefix : Type v}
    {Output : Type w}
    (engine : TemporalEngine Data Prefix Output) : Prop :=
  ∀ cutoff left right,
    engine.DataEquivalentAt cutoff left right →
      engine.outputPrefix cutoff (engine.run left) =
        engine.outputPrefix cutoff (engine.run right)

/-- Any engine whose past output factors through its causal input prefix is
    temporally noninterfering. -/
theorem causal_factorization_implies_temporal_noninterference
    {Data : Type u}
    {Prefix : Type v}
    {Output : Type w}
    (engine : TemporalEngine Data Prefix Output)
    (factors : engine.CausallyFactors) :
    engine.TemporalNoninterference := by
  intro cutoff left right samePrefix
  calc
    engine.outputPrefix cutoff (engine.run left) =
        engine.outputPrefix cutoff
          (engine.runFromPrefix cutoff
            (engine.causalPrefix cutoff left)) :=
      factors cutoff left
    _ = engine.outputPrefix cutoff
          (engine.runFromPrefix cutoff
            (engine.causalPrefix cutoff right)) := by
      rw [samePrefix]
    _ = engine.outputPrefix cutoff (engine.run right) :=
      (factors cutoff right).symm

/-- A future extension is simply a full dataset that preserves the causal prefix
    at the audited cutoff. -/
def FutureExtensionAt
    {Data : Type u}
    {Prefix : Type v}
    {Output : Type w}
    (engine : TemporalEngine Data Prefix Output)
    (cutoff : Timestamp)
    (base extended : Data) : Prop :=
  engine.DataEquivalentAt cutoff base extended

theorem future_extension_invariance
    {Data : Type u}
    {Prefix : Type v}
    {Output : Type w}
    (engine : TemporalEngine Data Prefix Output)
    (safe : engine.TemporalNoninterference)
    (cutoff : Timestamp)
    (base extended : Data)
    (extension : engine.FutureExtensionAt cutoff base extended) :
    engine.outputPrefix cutoff (engine.run base) =
      engine.outputPrefix cutoff (engine.run extended) :=
  safe cutoff base extended extension

/-- Quantitative relaxation used by executable leakage metrics. -/
def EpsilonTemporalNoninterference
    {Data : Type u}
    {Prefix : Type v}
    {Output : Type w}
    (engine : TemporalEngine Data Prefix Output)
    (distance : Output → Output → Nat)
    (epsilon : Nat) : Prop :=
  ∀ cutoff left right,
    engine.DataEquivalentAt cutoff left right →
      distance
        (engine.outputPrefix cutoff (engine.run left))
        (engine.outputPrefix cutoff (engine.run right)) ≤ epsilon

theorem exact_noninterference_implies_zero_leakage
    {Data : Type u}
    {Prefix : Type v}
    {Output : Type w}
    (engine : TemporalEngine Data Prefix Output)
    (distance : Output → Output → Nat)
    (selfZero : ∀ output, distance output output = 0)
    (safe : engine.TemporalNoninterference) :
    engine.EpsilonTemporalNoninterference distance 0 := by
  intro cutoff left right samePrefix
  rw [safe cutoff left right samePrefix]
  simp [selfZero]

end TemporalEngine

/-- Constructive witness that two causally equivalent datasets produce different
    past outputs. -/
structure TemporalCounterexample
    {Data : Type u}
    {Prefix : Type v}
    {Output : Type w}
    (engine : TemporalEngine Data Prefix Output) where
  cutoff : Timestamp
  left : Data
  right : Data
  sameCausalPrefix :
    engine.DataEquivalentAt cutoff left right
  differentOutput :
    engine.outputPrefix cutoff (engine.run left) ≠
      engine.outputPrefix cutoff (engine.run right)

namespace TemporalCounterexample

theorem refutes_temporal_noninterference
    {Data : Type u}
    {Prefix : Type v}
    {Output : Type w}
    {engine : TemporalEngine Data Prefix Output}
    (counterexample : TemporalCounterexample engine) :
    ¬ engine.TemporalNoninterference := by
  intro safe
  exact counterexample.differentOutput
    (safe counterexample.cutoff
      counterexample.left counterexample.right
      counterexample.sameCausalPrefix)

end TemporalCounterexample

/-- Observation and release time are separate causal dimensions. -/
structure TimedObservation where
  observationAt : Timestamp
  availableAt : Timestamp
  deriving Repr, DecidableEq

namespace TimedObservation

def UsableAt
    (observation : TimedObservation)
    (decisionAt : Timestamp) : Prop :=
  observation.observationAt ≤ decisionAt ∧
    observation.availableAt ≤ decisionAt

end TimedObservation

end LeanFinance.Backtest
