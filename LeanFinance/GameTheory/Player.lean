import LeanFinance.Core

namespace LeanFinance.GameTheory

inductive PlayerKind
  | retail
  | discretionaryFund
  | hedgeFund
  | cta
  | volatilityFund
  | marketMaker
  | optionsDealer
  | etfIndexFund
  | pensionFund
  | insuranceCompany
  | leveragedFund
  | corporateIssuer
  | shortSeller
  | policyActor
  deriving DecidableEq, Repr

structure Player where
  id : PlayerId
  kind : PlayerKind
  riskAversion : Nat
  leverageLimit : Nat
  horizon : Nat
  benchmark : String
  deriving Repr

end LeanFinance.GameTheory
