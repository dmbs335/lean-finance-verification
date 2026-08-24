import LeanFinance.Alpha.Certifiable

namespace LeanFinance.Alpha

/-- Conceptual decomposition of an observed alpha estimate. Research-integrity
    evidence can address `attackBias`; risk-model misspecification and finite-
    sample error remain separate empirical obligations. -/
structure EconomicAlphaDecomposition where
  economicAlpha : RealizedAlpha
  attackBias : RealizedAlpha
  modelBias : RealizedAlpha
  samplingNoise : RealizedAlpha
  deriving Repr, DecidableEq

namespace EconomicAlphaDecomposition

/-- The reported estimate before research-process integrity corrections. -/
def observedAlpha
    (decomposition : EconomicAlphaDecomposition) : RealizedAlpha :=
  decomposition.attackBias +
    (decomposition.economicAlpha +
      decomposition.modelBias + decomposition.samplingNoise)

/-- The estimate after every modeled research-process attack bias has been
    identified and removed. -/
def attackCleanedAlpha
    (decomposition : EconomicAlphaDecomposition) : RealizedAlpha :=
  decomposition.observedAlpha - decomposition.attackBias

/-- Complete attack-bias removal leaves economic alpha mixed with model bias and
    sampling noise. This is the semantic boundary between the synthetic
    distortion benchmark and a real expected-alpha claim. -/
theorem attack_cleaning_leaves_model_and_sampling_error
    (decomposition : EconomicAlphaDecomposition) :
    decomposition.attackCleanedAlpha =
      decomposition.economicAlpha +
        decomposition.modelBias + decomposition.samplingNoise := by
  simp [attackCleanedAlpha, observedAlpha]

/-- Exact recovery of economic alpha additionally requires the remaining model
    and sampling errors to cancel. -/
theorem exact_economic_alpha_of_zero_residual
    (decomposition : EconomicAlphaDecomposition)
    (residualZero :
      decomposition.modelBias + decomposition.samplingNoise = 0) :
    decomposition.attackCleanedAlpha = decomposition.economicAlpha := by
  rw [attack_cleaning_leaves_model_and_sampling_error]
  calc
    decomposition.economicAlpha + decomposition.modelBias +
        decomposition.samplingNoise =
      decomposition.economicAlpha +
        (decomposition.modelBias + decomposition.samplingNoise) := by
          exact add_assoc _ _ _
    _ = decomposition.economicAlpha := by simp [residualZero]

end EconomicAlphaDecomposition

/-- A concrete boundary example: removing 60 bps of future-information bias
    cleans 103 bps to 43 bps, not to the 40 bps economic alpha. -/
def economicBoundaryExample : EconomicAlphaDecomposition :=
  { economicAlpha := 40
    attackBias := 60
    modelBias := 5
    samplingNoise := -2 }

theorem economic_boundary_observed_alpha :
    economicBoundaryExample.observedAlpha = 103 := by
  decide

theorem economic_boundary_cleaned_alpha :
    economicBoundaryExample.attackCleanedAlpha = 43 := by
  decide

theorem attack_cleaning_does_not_make_alpha_exact :
    economicBoundaryExample.attackCleanedAlpha ≠
      economicBoundaryExample.economicAlpha := by
  decide

end LeanFinance.Alpha
