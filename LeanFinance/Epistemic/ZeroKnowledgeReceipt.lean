namespace LeanFinance.Epistemic

universe u

/-- Normalized result of an external private-predicate verifier. The formal
    layer intentionally does not axiomatize one cryptographic proof system. -/
inductive PrivateExecutionPredicate where
  | countZero
  deriving Repr, DecidableEq

structure VerifiedPrivatePredicateProof (Action : Type u) where
  action : Action
  predicate : PrivateExecutionPredicate
  deriving Repr

/-- A private absence certificate reveals only that each forbidden action's
    committed count satisfies the zero predicate. `verifierSound` is supplied
    after the selected ZK backend, commitment membership, and runner signature
    have been verified. -/
structure PrivateAbsenceCertificate
    (Action : Type u)
    (histogram : Action → Nat) where
  forbidden : List Action
  proofs : List (VerifiedPrivatePredicateProof Action)
  everyForbiddenProved :
    ∀ action,
      action ∈ forbidden →
        ∃ proof,
          proof ∈ proofs ∧
            proof.action = action ∧
              proof.predicate = .countZero
  verifierSound :
    ∀ proof,
      proof ∈ proofs →
        proof.predicate = .countZero →
          histogram proof.action = 0

namespace PrivateAbsenceCertificate

/-- The normalized private proof portfolio entails absence of every forbidden
    action without exposing allowed action counts or order. -/
def NoForbiddenExecutions
    {Action : Type u}
    (histogram : Action → Nat)
    (forbidden : List Action) : Prop :=
  ∀ action,
    action ∈ forbidden → histogram action = 0

theorem proves_no_forbidden_execution
    {Action : Type u}
    {histogram : Action → Nat}
    (certificate : PrivateAbsenceCertificate Action histogram) :
    NoForbiddenExecutions histogram certificate.forbidden := by
  intro action forbiddenMember
  rcases certificate.everyForbiddenProved action forbiddenMember with
    ⟨proof, proofMember, actionEq, predicateEq⟩
  have sound := certificate.verifierSound proof proofMember predicateEq
  simpa [actionEq] using sound

end PrivateAbsenceCertificate

end LeanFinance.Epistemic
