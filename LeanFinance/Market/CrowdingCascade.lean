import LeanFinance.Market.StateModel
import LeanFinance.Market.RegimeTransition

namespace LeanFinance.Market

/-- Increased imitation and crowding pressure in a market mechanism. -/
structure CrowdingPressure where
  imitation : Scalar
  strategyConcentration : Scalar
  liquiditySensitivity : Scalar
  deriving Repr

/-- Concentrated strategies become more sensitive to liquidity shocks as
    imitation increases. -/
def CrowdingAmplifiesInstability
    (pressure : CrowdingPressure) : Prop :=
  pressure.imitation > 0 ∧
    pressure.strategyConcentration > 0 ∧
    pressure.liquiditySensitivity > 0

/-- A market transition caused by crowding pressure refines the shared state
    representation. -/
structure CrowdingDrivenTransition where
  pressure : CrowdingPressure
  transition : MarketTransition
  crowdingIncreased :
    transition.destination.crowding > transition.source.crowding

/-- Structural link between crowding amplification and latent-state movement. -/
theorem crowding_transition_increases_crowding
    (driven : CrowdingDrivenTransition)
    (_amplified : CrowdingAmplifiesInstability driven.pressure) :
    driven.transition.destination.crowding >
      driven.transition.source.crowding :=
  driven.crowdingIncreased

end LeanFinance.Market
