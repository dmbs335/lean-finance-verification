import LeanFinance.Epistemic.SelectiveReceipt

namespace LeanFinance.Epistemic.SelectiveReceiptExample

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

def hiddenDisclosure : CountDisclosure Action :=
  { action := .hiddenSweep, count := 0 }

def futureDisclosure : CountDisclosure Action :=
  { action := .futureData, count := 0 }

def certificate : SelectiveAbsenceCertificate Action histogram :=
  { forbidden := [.hiddenSweep, .futureData]
    disclosures := [hiddenDisclosure, futureDisclosure]
    everyForbiddenDisclosed := by
      intro action member
      simp at member
      rcases member with rfl | rfl
      · exact ⟨hiddenDisclosure, by simp, rfl⟩
      · exact ⟨futureDisclosure, by simp, rfl⟩
    disclosureSound := by
      intro disclosure member
      simp [hiddenDisclosure, futureDisclosure] at member
      rcases member with rfl | rfl <;> rfl
    disclosedZero := by
      intro disclosure member
      simp [hiddenDisclosure, futureDisclosure] at member
      rcases member with rfl | rfl <;> rfl }

theorem receipt_reveals_only_forbidden_absence :
    NoForbiddenExecutions histogram certificate.forbidden :=
  certificate.proves_no_forbidden_execution

end LeanFinance.Epistemic.SelectiveReceiptExample
