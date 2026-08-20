import LeanFinance.Core

namespace LeanFinance.Market

structure OrderFlow where
  informed : Scalar
  noise : Scalar
  forced : Scalar
  deriving Repr

def OrderFlow.total (flow : OrderFlow) : Scalar :=
  flow.informed + flow.noise + flow.forced

theorem total_without_forced
    (flow : OrderFlow)
    (h : flow.forced = 0) :
    flow.total = flow.informed + flow.noise := by
  simp [OrderFlow.total, h]

end LeanFinance.Market
