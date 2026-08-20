import LeanFinance.Backtest.Dataset

structure Decision where
  strategyId : String
  decisionTime : Nat
  dataset : Dataset


def UsesDataBeforeDecision (d : Decision) : Prop :=
  d.dataset.timestamp <= d.decisionTime
