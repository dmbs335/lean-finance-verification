namespace LeanFinance.Epistemic

universe u

/-- One selectively opened action-count commitment. Cryptographic verification
    establishes that `count` is the value committed for `action`; this formal
    layer reasons only about the normalized disclosure. -/
structure CountDisclosure (Action : Type u) where
  action : Action
  count : Nat
  deriving Repr

/-- No forbidden action occurred in the trusted complete execution histogram. -/
def NoForbiddenExecutions
    {Action : Type u}
    (histogram : Action → Nat)
    (forbidden : List Action) : Prop :=
  ∀ action,
    action ∈ forbidden →
      histogram action = 0

/-- A proof-carrying selective receipt. Only forbidden action classes need be
    opened; the sequence and counts of allowed classes remain hidden. The
    `disclosureSound` field is supplied after signature/Merkle verification and
    therefore makes the runner-completeness trust boundary explicit. -/
structure SelectiveAbsenceCertificate
    (Action : Type u)
    (histogram : Action → Nat) where
  forbidden : List Action
  disclosures : List (CountDisclosure Action)
  everyForbiddenDisclosed :
    ∀ action,
      action ∈ forbidden →
        ∃ disclosure,
          disclosure ∈ disclosures ∧
            disclosure.action = action
  disclosureSound :
    ∀ disclosure,
      disclosure ∈ disclosures →
        histogram disclosure.action = disclosure.count
  disclosedZero :
    ∀ disclosure,
      disclosure ∈ disclosures →
        disclosure.count = 0

namespace SelectiveAbsenceCertificate

theorem proves_no_forbidden_execution
    {Action : Type u}
    {histogram : Action → Nat}
    (certificate : SelectiveAbsenceCertificate Action histogram) :
    NoForbiddenExecutions histogram certificate.forbidden := by
  intro action forbiddenMember
  rcases certificate.everyForbiddenDisclosed action forbiddenMember with
    ⟨disclosure, disclosureMember, actionEq⟩
  have committed := certificate.disclosureSound disclosure disclosureMember
  have zero := certificate.disclosedZero disclosure disclosureMember
  rw [actionEq] at committed
  exact committed.trans zero

end SelectiveAbsenceCertificate

end LeanFinance.Epistemic
