import LeanFinance.Market.KyleModel
import LeanFinance.GameTheory.Equilibrium

namespace LeanFinance.Market

structure MarketEquilibrium where
  price : Scalar
  impact : Scalar
  deriving Repr

def consistentPrice (equilibrium : MarketEquilibrium) : Prop :=
  0 <= equilibrium.price ∧ 0 <= equilibrium.impact

end LeanFinance.Market
