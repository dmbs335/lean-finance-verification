import LeanFinance.Types

namespace LeanFinance.Backtest

structure Security where
  id : String
  deriving DecidableEq, Repr

/-- Point-in-time membership interval. `excludedAt = none` means that no
    exclusion was known in the represented history. -/
structure UniverseMembership where
  security : Security
  includedAt : Time
  excludedAt : Option Time
  deriving DecidableEq, Repr

def UniverseMembership.ActiveAt
    (membership : UniverseMembership)
    (time : Time) : Prop :=
  membership.includedAt <= time ∧
  match membership.excludedAt with
  | none => True
  | some excludedAt => time < excludedAt

structure UniverseSnapshot where
  asOf : Time
  memberships : List UniverseMembership
  deriving Repr

def UniverseSnapshot.Valid (snapshot : UniverseSnapshot) : Prop :=
  ∀ membership, membership ∈ snapshot.memberships →
    membership.ActiveAt snapshot.asOf

theorem UniverseSnapshot.memberActive
    {snapshot : UniverseSnapshot}
    (valid : snapshot.Valid)
    {membership : UniverseMembership}
    (member : membership ∈ snapshot.memberships) :
    membership.ActiveAt snapshot.asOf :=
  valid membership member

end LeanFinance.Backtest
