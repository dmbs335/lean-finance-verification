namespace LeanFinance.GameTheory

inductive Action
  | buy
  | sell
  | hold
  deriving DecidableEq, Repr

end LeanFinance.GameTheory
