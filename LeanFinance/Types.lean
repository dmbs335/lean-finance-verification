import Init.Data.Rat

namespace LeanFinance

/-- Exact scalar used by the formal core. Empirical adapters may quantize
    floating-point observations into rational values before certification. -/
abbrev Scalar := Rat

/-- Logical market or publication time. -/
abbrev Time := Nat

end LeanFinance
