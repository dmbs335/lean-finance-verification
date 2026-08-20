import LeanFinance.Market.KyleModel
import LeanFinance.GameTheory.Equilibrium

namespace LeanFinance

structure MarketEquilibrium where
  price : Rat
  impact : Rat


def consistentPrice (eq : MarketEquilibrium) : Prop :=
  eq.impact >= 0

end LeanFinance
