import LeanFinance.GameTheory.Belief

namespace LeanFinance.GameTheory

/-- Coordination intensity in a three-level Keynesian beauty-contest model.
    A value of zero places all weight on first-order fundamental belief; a
    value of one places all weight on the represented third-order belief. -/
structure CoordinationWeights where
  coordination : Scalar
  deriving Repr

def CoordinationWeights.WellFormed
    (weights : CoordinationWeights) : Prop :=
  0 <= weights.coordination ∧ weights.coordination <= 1

def firstOrderWeight (weights : CoordinationWeights) : Scalar :=
  1 - weights.coordination

def secondOrderWeight (weights : CoordinationWeights) : Scalar :=
  weights.coordination * (1 - weights.coordination)

def thirdOrderWeight (weights : CoordinationWeights) : Scalar :=
  weights.coordination * weights.coordination

/-- A finite truncation of the hierarchy

    B1: own fundamental expectation
    B2: expectation of the market's expectation
    B3: expectation of higher-order market belief.

    The geometric weighting preserves the intuitive extremes while keeping the
    formal core finite and auditable. -/
def beautyContestSignal
    (weights : CoordinationWeights)
    (belief : Belief) : Scalar :=
  firstOrderWeight weights * belief.fundamentalExpectation +
  secondOrderWeight weights * belief.marketExpectation +
  thirdOrderWeight weights * belief.higherOrderExpectation

def zeroCoordination : CoordinationWeights :=
  { coordination := 0 }

def fullCoordination : CoordinationWeights :=
  { coordination := 1 }

theorem zeroCoordination_wellFormed : zeroCoordination.WellFormed := by
  decide

theorem fullCoordination_wellFormed : fullCoordination.WellFormed := by
  decide

/-- With no coordination motive, higher-order beliefs cannot affect the signal. -/
theorem beautyContestSignal_zeroCoordination
    (belief : Belief) :
    beautyContestSignal zeroCoordination belief =
      belief.fundamentalExpectation := by
  simp [beautyContestSignal, zeroCoordination,
    firstOrderWeight, secondOrderWeight, thirdOrderWeight]

/-- At the represented full-coordination extreme, only B3 remains. -/
theorem beautyContestSignal_fullCoordination
    (belief : Belief) :
    beautyContestSignal fullCoordination belief =
      belief.higherOrderExpectation := by
  simp [beautyContestSignal, fullCoordination,
    firstOrderWeight, secondOrderWeight, thirdOrderWeight]

theorem zeroCoordination_dependsOnlyOnFundamental
    (left right : Belief)
    (sameFundamental :
      left.fundamentalExpectation = right.fundamentalExpectation) :
    beautyContestSignal zeroCoordination left =
      beautyContestSignal zeroCoordination right := by
  simpa [beautyContestSignal, zeroCoordination,
    firstOrderWeight, secondOrderWeight, thirdOrderWeight] using
      sameFundamental

theorem fullCoordination_dependsOnlyOnHigherOrder
    (left right : Belief)
    (sameHigherOrder :
      left.higherOrderExpectation = right.higherOrderExpectation) :
    beautyContestSignal fullCoordination left =
      beautyContestSignal fullCoordination right := by
  simpa [beautyContestSignal, fullCoordination,
    firstOrderWeight, secondOrderWeight, thirdOrderWeight] using
      sameHigherOrder

end LeanFinance.GameTheory
