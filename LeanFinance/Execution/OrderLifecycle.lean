import LeanFinance.Control.Authority

namespace LeanFinance.Execution

inductive OrderState where
  | proposed
  | shielded
  | authorized
  | submitted
  | acknowledged
  | partiallyFilled
  | filled
  | cancelled
  | expired
  | reconciled
  deriving Repr, DecidableEq

namespace OrderState

def canTransition : OrderState → OrderState → Bool
  | .proposed, .shielded | .proposed, .cancelled => true
  | .shielded, .authorized | .shielded, .cancelled => true
  | .authorized, .submitted | .authorized, .cancelled | .authorized, .expired => true
  | .submitted, .acknowledged | .submitted, .cancelled | .submitted, .expired => true
  | .acknowledged, .partiallyFilled | .acknowledged, .filled |
      .acknowledged, .cancelled | .acknowledged, .expired => true
  | .partiallyFilled, .partiallyFilled | .partiallyFilled, .filled |
      .partiallyFilled, .cancelled | .partiallyFilled, .expired => true
  | .filled, .reconciled | .cancelled, .reconciled | .expired, .reconciled => true
  | _, _ => false

end OrderState

def lifecycleValid : List OrderState → Bool
  | [] | [_] => true
  | first :: second :: rest =>
      first.canTransition second && lifecycleValid (second :: rest)

def endsReconciled (states : List OrderState) : Bool :=
  states.reverse.head? == some .reconciled

def authorityCanSubmit : LeanFinance.Control.AuthorityLevel → Bool
  | .microAutonomy | .boundedAutonomy => true
  | _ => false

structure OrderAuthorization where
  orderId : String
  authority : LeanFinance.Control.AuthorityLevel
  capitalCapUnits : Nat
  authorizedQty : Nat
  deriving Repr, DecidableEq

namespace OrderAuthorization

def admissible (authorization : OrderAuthorization) : Bool :=
  authorityCanSubmit authorization.authority &&
    decide (0 < authorization.authorizedQty) &&
      decide (authorization.authorizedQty ≤ authorization.capitalCapUnits)

theorem revoked_cannot_submit
    (authorization : OrderAuthorization)
    (revoked : authorization.authority = .revoked) :
    authorization.admissible = false := by
  simp [admissible, authorityCanSubmit, revoked]

theorem recommendation_cannot_submit
    (authorization : OrderAuthorization)
    (recommendation : authorization.authority = .recommend) :
    authorization.admissible = false := by
  simp [admissible, authorityCanSubmit, recommendation]

end OrderAuthorization

end LeanFinance.Execution
