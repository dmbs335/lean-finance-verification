namespace LeanFinance.Epistemic

universe u v

/-- One adversarial obligation and the evidence channels capable of separating
    it from the relevant honest world. -/
structure AttackObligation (Attack : Type u) (Channel : Type v) where
  attack : Attack
  separators : List Channel
  separatorsNonempty : separators ≠ []

/-- A selected evidence portfolio covers one attack obligation. -/
def CoversObligation
    {Attack : Type u}
    {Channel : Type v}
    (selected : List Channel)
    (obligation : AttackObligation Attack Channel) : Prop :=
  ∃ evidenceChannel,
    evidenceChannel ∈ selected ∧
      evidenceChannel ∈ obligation.separators

/-- Every declared attack obligation is covered. -/
def CoversAllObligations
    {Attack : Type u}
    {Channel : Type v}
    (selected : List Channel)
    (obligations : List (AttackObligation Attack Channel)) : Prop :=
  ∀ obligation,
    obligation ∈ obligations →
      CoversObligation selected obligation

/-- Proof-carrying output of an untrusted symbolic or branch-and-bound solver. -/
structure CoverageCertificate
    (Attack : Type u)
    (Channel : Type v) where
  selected : List Channel
  obligations : List (AttackObligation Attack Channel)
  covers : CoversAllObligations selected obligations

namespace CoverageCertificate

theorem sound
    {Attack : Type u}
    {Channel : Type v}
    (certificate : CoverageCertificate Attack Channel) :
    CoversAllObligations certificate.selected certificate.obligations :=
  certificate.covers

end CoverageCertificate

/-- Two attacks have the same epistemic obligation when the candidate
    separator lists coincide. -/
def SameObligationSignature
    {Attack : Type u}
    {Channel : Type v}
    (left right : AttackObligation Attack Channel) : Prop :=
  left.separators = right.separators

/-- Signature equality is an equivalence relation, providing a principled basis
    for compressing many attack techniques into fewer evidence classes. -/
theorem same_obligation_signature_equivalence
    {Attack : Type u}
    {Channel : Type v} :
    Equivalence
      (SameObligationSignature
        (Attack := Attack) (Channel := Channel)) := by
  constructor
  · intro obligation
    rfl
  · intro left right same
    exact same.symm
  · intro first second third firstSecond secondThird
    exact firstSecond.trans secondThird

end LeanFinance.Epistemic
