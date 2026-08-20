import LeanFinance.Types

namespace LeanFinance.Market

/-- Decomposes order flow into informational, noise, and mechanically forced
    components. -/
structure OrderFlow where
  informed : Scalar
  noise : Scalar
  forced : Scalar
  deriving Repr

def OrderFlow.totalFlow (flow : OrderFlow) : Scalar :=
  flow.informed + flow.noise + flow.forced

theorem OrderFlow.totalFlow_def (flow : OrderFlow) :
    flow.totalFlow = flow.informed + flow.noise + flow.forced :=
  rfl

end LeanFinance.Market
