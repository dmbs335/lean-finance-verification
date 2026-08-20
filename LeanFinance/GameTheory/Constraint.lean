import LeanFinance.Types

namespace LeanFinance.GameTheory

/-- Observable or inferred exposure state against which a mandate is checked. -/
structure Exposure where
  leverage : Scalar
  risk : Scalar
  absolutePosition : Scalar
  deriving Repr

structure Constraint where
  leverageLimit : Scalar
  riskLimit : Scalar
  positionLimit : Scalar
  deriving Repr

def Constraint.WellFormed (constraint : Constraint) : Prop :=
  0 <= constraint.leverageLimit ∧
  0 <= constraint.riskLimit ∧
  0 <= constraint.positionLimit

def Feasible (exposure : Exposure) (constraint : Constraint) : Prop :=
  exposure.leverage <= constraint.leverageLimit ∧
  exposure.risk <= constraint.riskLimit ∧
  exposure.absolutePosition <= constraint.positionLimit

end LeanFinance.GameTheory
