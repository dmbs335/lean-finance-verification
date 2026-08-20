import LeanFinance.Types

namespace LeanFinance.GameTheory

abbrev PlayerId := Nat

/-- Economic role rather than legal entity. One institution may instantiate
    several players when it operates multiple strategy books. -/
inductive PlayerKind
  | retail
  | discretionaryFund
  | hedgeFund
  | cta
  | volatilityFund
  | marketMaker
  | optionsDealer
  | indexFund
  | pensionFund
  | insurer
  | leveragedFund
  | corporateIssuer
  | shortSeller
  | policyActor
  deriving DecidableEq, Repr

structure Player where
  id : PlayerId
  kind : PlayerKind
  riskAversion : Scalar
  leverageLimit : Scalar
  horizon : Time
  deriving Repr

def Player.WellFormed (p : Player) : Prop :=
  0 <= p.riskAversion ∧ 0 <= p.leverageLimit ∧ 0 < p.horizon

end LeanFinance.GameTheory
