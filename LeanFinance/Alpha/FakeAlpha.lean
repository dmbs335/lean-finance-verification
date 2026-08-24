import LeanFinance.Alpha.Certifiable

namespace LeanFinance.Alpha

/-- Research-integrity failures that can inflate a reported alpha without
    changing the underlying economic edge. -/
inductive IntegrityAttack where
  | futureInformation
  | survivorshipBias
  | parameterMining
  | costManipulation
  | benchmarkSwitching
  | hiddenExecution
  deriving Repr, DecidableEq

/-- Synthetic decomposition used to distinguish economic alpha from research
    bias, risk-model misspecification, and finite-sample noise. -/
structure AlphaDecomposition where
  economicAlpha : Int
  attackBias : Int
  modelBias : Int
  samplingNoise : Int
  deriving Repr, DecidableEq

namespace AlphaDecomposition

/-- The attack component is placed first so removing a completely identified
    attack bias has a simple executable normal form. -/
def observedAlpha (decomposition : AlphaDecomposition) : Int :=
  decomposition.attackBias +
    (decomposition.economicAlpha +
      decomposition.modelBias + decomposition.samplingNoise)

end AlphaDecomposition

/-- One evidence-backed finding. `estimatedBias` is deliberately separate from
    the attack label: identifying an attack and quantifying its distortion are
    different empirical obligations. -/
structure AttackFinding where
  attack : IntegrityAttack
  estimatedBias : Int
  detected : Bool
  deriving Repr, DecidableEq

/-- Sum of the attack biases that the selected evidence architecture actually
    identifies. -/
def identifiedBias : List AttackFinding → Int
  | [] => 0
  | finding :: rest =>
      (match finding.detected with
       | true => finding.estimatedBias
       | false => 0) + identifiedBias rest

/-- Alpha after subtracting only evidence-supported attack bias. -/
def cleanedAlpha (observed : Int) (findings : List AttackFinding) : Int :=
  observed - identifiedBias findings

/-- Even perfect attack identification leaves risk-model bias and sampling
    noise. Therefore attack detection cleans the estimate but does not by itself
    identify the economic alpha. -/
theorem cleaned_alpha_after_complete_attack_identification
    (decomposition : AlphaDecomposition)
    (findings : List AttackFinding)
    (complete : identifiedBias findings = decomposition.attackBias) :
    cleanedAlpha decomposition.observedAlpha findings =
      decomposition.economicAlpha +
        decomposition.modelBias + decomposition.samplingNoise := by
  simp [cleanedAlpha, AlphaDecomposition.observedAlpha, complete]

/-- A certifiable interval is meaningful only after the research-integrity
    claim is supported by the selected evidence architecture. -/
structure CertifiableAlphaInterval where
  lower : Int
  upper : Int
  integrityVerified : Bool
  ordered : lower ≤ upper
  deriving Repr

namespace CertifiableAlphaInterval

def Contains
    (interval : CertifiableAlphaInterval)
    (alpha : Int) : Prop :=
  interval.lower ≤ alpha ∧ alpha ≤ interval.upper

/-- Narrowing both ends preserves membership when the target remains between
    the refined bounds. -/
theorem contains_of_refined_bounds
    (outer inner : CertifiableAlphaInterval)
    (alpha : Int)
    (lowerTighter : outer.lower ≤ inner.lower)
    (upperTighter : inner.upper ≤ outer.upper)
    (insideInner : inner.Contains alpha) :
    outer.Contains alpha :=
  ⟨le_trans lowerTighter insideInner.1,
    le_trans insideInner.2 upperTighter⟩

end CertifiableAlphaInterval

end LeanFinance.Alpha
