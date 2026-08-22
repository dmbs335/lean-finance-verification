import LeanFinance.Epistemic.ZeroKnowledgeReceipt

namespace LeanFinance.Epistemic.ZeroKnowledgeReceiptExample

open LeanFinance.Epistemic

inductive Action where
  | baseline
  | hiddenSweep
  | futureData
  | publish
  deriving Repr, DecidableEq

def histogram : Action → Nat
  | .baseline => 1
  | .hiddenSweep => 0
  | .futureData => 0
  | .publish => 1

def hiddenProof : VerifiedPrivatePredicateProof Action :=
  { action := .hiddenSweep, predicate := .countZero }

def futureProof : VerifiedPrivatePredicateProof Action :=
  { action := .futureData, predicate := .countZero }

def certificate : PrivateAbsenceCertificate Action histogram :=
  { forbidden := [.hiddenSweep, .futureData]
    proofs := [hiddenProof, futureProof]
    everyForbiddenProved := by
      intro action member
      simp at member
      rcases member with rfl | rfl
      · exact ⟨hiddenProof, by simp, rfl, rfl⟩
      · exact ⟨futureProof, by simp, rfl, rfl⟩
    verifierSound := by
      intro proof member predicate
      simp [hiddenProof, futureProof] at member
      rcases member with rfl | rfl <;> rfl }

theorem private_receipt_proves_absence :
    PrivateAbsenceCertificate.NoForbiddenExecutions
      histogram certificate.forbidden :=
  certificate.proves_no_forbidden_execution

end LeanFinance.Epistemic.ZeroKnowledgeReceiptExample
