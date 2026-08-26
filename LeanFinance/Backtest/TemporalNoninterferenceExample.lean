import LeanFinance.Backtest.TemporalNoninterference

namespace LeanFinance.Backtest.TemporalNoninterferenceExample

open LeanFinance.Backtest

structure ControlledData where
  pastValue : Int
  futureValue : Int
  deriving Repr, DecidableEq

structure ControlledPrefix where
  pastValue : Int
  deriving Repr, DecidableEq

structure ControlledOutput where
  mark : Int
  deriving Repr, DecidableEq

def causalPrefix
    (_cutoff : Timestamp)
    (data : ControlledData) : ControlledPrefix :=
  { pastValue := data.pastValue }

def outputPrefix
    (_cutoff : Timestamp)
    (output : ControlledOutput) : ControlledOutput :=
  output

def safeEngine :
    TemporalEngine ControlledData ControlledPrefix ControlledOutput :=
  { causalPrefix := causalPrefix
    run := fun data => { mark := data.pastValue }
    runFromPrefix := fun _cutoff inputPrefix =>
      { mark := inputPrefix.pastValue }
    outputPrefix := outputPrefix }

theorem safe_engine_factors :
    safeEngine.CausallyFactors := by
  intro cutoff data
  rfl

theorem safe_engine_is_temporally_noninterfering :
    safeEngine.TemporalNoninterference :=
  safeEngine.causal_factorization_implies_temporal_noninterference
    safe_engine_factors

def futureSensitiveEngine :
    TemporalEngine ControlledData ControlledPrefix ControlledOutput :=
  { causalPrefix := causalPrefix
    run := fun data => { mark := data.futureValue }
    runFromPrefix := fun _cutoff inputPrefix =>
      { mark := inputPrefix.pastValue }
    outputPrefix := outputPrefix }

def baseData : ControlledData :=
  { pastValue := 100, futureValue := 101 }

def futureExtendedData : ControlledData :=
  { pastValue := 100, futureValue := 999 }

def futureSensitiveCounterexample :
    TemporalCounterexample futureSensitiveEngine :=
  { cutoff := 25
    left := baseData
    right := futureExtendedData
    sameCausalPrefix := rfl
    differentOutput := by
      decide }

theorem future_sensitive_engine_is_not_safe :
    ¬ futureSensitiveEngine.TemporalNoninterference :=
  futureSensitiveCounterexample.refutes_temporal_noninterference

theorem safe_engine_ignores_future_extension :
    safeEngine.outputPrefix 25 (safeEngine.run baseData) =
      safeEngine.outputPrefix 25
        (safeEngine.run futureExtendedData) :=
  safeEngine.future_extension_invariance
    safe_engine_is_temporally_noninterfering
    25 baseData futureExtendedData rfl

def lateSameBarObservation : TimedObservation :=
  { observationAt := 25, availableAt := 26 }

theorem observation_time_does_not_imply_availability :
    ¬ lateSameBarObservation.UsableAt 25 := by
  simp [TimedObservation.UsableAt, lateSameBarObservation]

end LeanFinance.Backtest.TemporalNoninterferenceExample
