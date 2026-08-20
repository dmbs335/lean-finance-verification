namespace LeanFinance

abbrev Timestamp := Nat
abbrev Scalar := Int
abbrev PlayerId := Nat
abbrev StrategyId := String
abbrev ContentHash := String

def NonEmptyString (value : String) : Prop :=
  value ≠ ""

end LeanFinance
