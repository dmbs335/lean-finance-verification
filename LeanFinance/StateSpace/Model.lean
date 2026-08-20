import LeanFinance.Core

namespace LeanFinance.StateSpace

abbrev ProbabilityBps := Nat

def ValidProbabilityBps (probability : ProbabilityBps) : Prop :=
  probability ≤ 10000

instance decidableValidProbabilityBps (probability : ProbabilityBps) :
    Decidable (ValidProbabilityBps probability) := by
  unfold ValidProbabilityBps
  infer_instance

/-- Economically interpretable coordinates proposed for a latent market state.
    The coordinates are names, not a claim that every empirical model identifies
    them uniquely. -/
inductive LatentAxis where
  | valuation
  | marketLiquidity
  | fundingLiquidity
  | leverage
  | volatility
  | creditConditions
  | riskAppetite
  | positioning
  | crowding
  | inflationExpectation
  | growthExpectation
  | monetaryConditions
  | earningsExpectation
  deriving Repr, DecidableEq

/-- A serializable latent-state candidate. Signed quantities use `Scalar`;
    nonnegative stress, exposure, and basis-point quantities use `Nat`. -/
structure LatentMarketState where
  valuationGap : Scalar
  marketLiquidity : Nat
  fundingLiquidity : Nat
  leverageBps : Nat
  volatilityBps : Nat
  creditStressBps : Nat
  riskAppetiteBps : Nat
  positioning : Scalar
  crowdingBps : Nat
  inflationExpectationBps : Scalar
  growthExpectationBps : Scalar
  monetaryTightnessBps : Nat
  earningsExpectationBps : Scalar
  deriving Repr, DecidableEq

/-- Point-in-time public data supplied to an external state estimator. -/
structure ObservedMarketSnapshot where
  observedAt : Timestamp
  availableAt : Timestamp
  price : Scalar
  realizedVolatilityBps : Nat
  marketDepth : Nat
  creditSpreadBps : Nat
  fundingSpreadBps : Nat
  positioningProxy : Scalar
  contentHash : ContentHash
  deriving Repr, DecidableEq

/-- An observation is admissible when it was released no earlier than its
    reference timestamp, was available by the estimate time, and is hash-bound. -/
def ObservationAdmissible
    (asOf : Timestamp)
    (observation : ObservedMarketSnapshot) : Prop :=
  observation.observedAt ≤ observation.availableAt ∧
  observation.availableAt ≤ asOf ∧
  NonEmptyString observation.contentHash

instance decidableObservationAdmissible
    (asOf : Timestamp)
    (observation : ObservedMarketSnapshot) :
    Decidable (ObservationAdmissible asOf observation) := by
  unfold ObservationAdmissible
  infer_instance

/-- Policy, regulation, and private balance-sheet actions represented as inputs.
    The formal layer does not assume that these inputs are exogenous. -/
structure ControlInput where
  policyRateMoveBps : Scalar
  liquidityInjection : Nat
  marginReliefBps : Nat
  capitalBufferMoveBps : Scalar
  corporateBuybackFlow : Scalar
  deriving Repr, DecidableEq

/-- Metadata for the transition and observation law used by an estimator. -/
structure StructuralLawMetadata where
  modelFamilyHash : ContentHash
  parameterHash : ContentHash
  estimatedAt : Timestamp
  deriving Repr, DecidableEq

def StructuralLawAdmissible
    (asOf : Timestamp)
    (law : StructuralLawMetadata) : Prop :=
  law.estimatedAt ≤ asOf ∧
  NonEmptyString law.modelFamilyHash ∧
  NonEmptyString law.parameterHash

instance decidableStructuralLawAdmissible
    (asOf : Timestamp)
    (law : StructuralLawMetadata) :
    Decidable (StructuralLawAdmissible asOf law) := by
  unfold StructuralLawAdmissible
  infer_instance

universe u v w x

/-- A generic non-autonomous state-space contract. A time-indexed `Law` may
    represent drift, a structural break, or an externally selected model version. -/
structure StateSpaceModel
    (State : Type u)
    (Observation : Type v)
    (Input : Type w)
    (Law : Type x) where
  transition : Law → State → Input → State
  observe : Law → State → Observation

structure WeightedState (State : Type u) where
  state : State
  weightBps : ProbabilityBps
  deriving Repr, DecidableEq

def posteriorMass {State : Type u} :
    List (WeightedState State) → ProbabilityBps
  | [] => 0
  | hypothesis :: remaining =>
      hypothesis.weightBps + posteriorMass remaining

/-- A finite posterior approximation. Lean checks normalization and individual
    bounds, while an external estimator remains responsible for statistical fit. -/
structure StateEstimate (State : Type u) where
  asOf : Timestamp
  hypotheses : List (WeightedState State)
  normalized : posteriorMass hypotheses = 10000
  weightsValid :
    ∀ hypothesis, hypothesis ∈ hypotheses →
      ValidProbabilityBps hypothesis.weightBps

theorem StateEstimate.totalMass
    {State : Type u}
    (estimate : StateEstimate State) :
    posteriorMass estimate.hypotheses = 10000 :=
  estimate.normalized

/-- Iterate an autonomous step map for finite-horizon verification. -/
def iterateStep {State : Type u} (step : State → State) :
    Nat → State → State
  | 0, state => state
  | Nat.succ steps, state =>
      step (iterateStep step steps state)

end LeanFinance.StateSpace
