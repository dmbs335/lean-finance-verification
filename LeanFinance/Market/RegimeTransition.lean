import LeanFinance.Market.StateModel

namespace LeanFinance.Market

/-- A market regime classifies regions of the latent state space. -/
inductive MarketRegime where
  | stable
  | stressed
  | crisis
  deriving Repr, DecidableEq

/-- Abstract regime classifier. Concrete empirical models may refine it while
    preserving the same state/transition interface. -/
def classifyRegime (state : MarketState) : MarketRegime :=
  if NearInstability state then .stressed else .stable

/-- State movement, rather than price movement alone, determines a regime
    transition. -/
def EntersStressRegime
    (transition : MarketTransition) : Prop :=
  classifyRegime transition.source = .stable ∧
    classifyRegime transition.destination = .stressed

/-- A mechanism can explain a regime transition. This connects game, network,
    and ecology models to the common state representation. -/
def MechanismExplainsTransition
    (mechanism : MarketMechanism)
    (transition : MarketTransition) : Prop :=
  mechanism.transition transition

/-- Any future concrete mechanism must refine the same transition interface. -/
theorem transition_refinement_contract
    (mechanism : MarketMechanism)
    (transition : MarketTransition)
    (explains : MechanismExplainsTransition mechanism transition) :
    mechanism.transition transition :=
  explains

end LeanFinance.Market
