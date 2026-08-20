namespace LeanFinance

structure VaRConstraint where
  confidence : Rat
  limit : Rat

structure RiskState where
  estimatedVaR : Rat

 def riskBreached (c : VaRConstraint) (s : RiskState) : Prop :=
  s.estimatedVaR > c.limit

end LeanFinance
