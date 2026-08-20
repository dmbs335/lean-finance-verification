import LeanFinance.Types

namespace LeanFinance.Dynamics

/-- A local linearization of price-impact and constraint-response feedback.
    `forcedResponse` maps a price move into induced order flow. -/
structure StrategicFeedback where
  externalFlow : Scalar
  priceImpact : Scalar
  forcedResponse : Scalar
  deriving Repr

def firstRoundPriceMove (system : StrategicFeedback) : Scalar :=
  system.priceImpact * system.externalFlow

def inducedForcedFlow (system : StrategicFeedback) : Scalar :=
  system.forcedResponse * firstRoundPriceMove system

def secondRoundPriceMove (system : StrategicFeedback) : Scalar :=
  system.priceImpact * inducedForcedFlow system

def loopGain (system : StrategicFeedback) : Scalar :=
  system.priceImpact * system.forcedResponse

/-- Local stability condition for same-direction linear feedback. -/
def LocallyStable (system : StrategicFeedback) : Prop :=
  loopGain system < 1

theorem inducedForcedFlow_eq_zero_of_zeroResponse
    (system : StrategicFeedback)
    (zeroResponse : system.forcedResponse = 0) :
    inducedForcedFlow system = 0 := by
  simp [inducedForcedFlow, zeroResponse]

theorem secondRoundPriceMove_eq_zero_of_zeroResponse
    (system : StrategicFeedback)
    (zeroResponse : system.forcedResponse = 0) :
    secondRoundPriceMove system = 0 := by
  simp [secondRoundPriceMove, inducedForcedFlow, zeroResponse]

theorem loopGain_eq_zero_of_zeroResponse
    (system : StrategicFeedback)
    (zeroResponse : system.forcedResponse = 0) :
    loopGain system = 0 := by
  simp [loopGain, zeroResponse]

end LeanFinance.Dynamics
