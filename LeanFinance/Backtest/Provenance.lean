import LeanFinance.Types

namespace LeanFinance.Backtest

structure Provenance where
  sourceId : String
  collectedAt : Time
  availableAt : Time
  datasetHash : String
  deriving DecidableEq, Repr

def AvailableBefore
    (provenance : Provenance)
    (decisionTime : Time) : Prop :=
  provenance.availableAt <= decisionTime

def Provenance.WellFormed (provenance : Provenance) : Prop :=
  provenance.collectedAt <= provenance.availableAt ∧
  provenance.sourceId ≠ "" ∧
  provenance.datasetHash ≠ ""

theorem availableBefore_mono
    {provenance : Provenance}
    {earlier later : Time}
    (available : AvailableBefore provenance earlier)
    (ordered : earlier <= later) :
    AvailableBefore provenance later :=
  Nat.le_trans available ordered

end LeanFinance.Backtest
