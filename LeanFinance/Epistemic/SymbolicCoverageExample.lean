import LeanFinance.Epistemic.SymbolicCoverage

namespace LeanFinance.Epistemic.SymbolicCoverageExample

open LeanFinance.Epistemic

inductive Attack where
  | hiddenExecution
  | futureData
  | timestampBackdating
  deriving Repr, DecidableEq

inductive Channel where
  | unifiedIntegrityAttestation
  | transparencyLog
  deriving Repr, DecidableEq

def hidden : AttackObligation Attack Channel :=
  { attack := .hiddenExecution
    separators := [.unifiedIntegrityAttestation]
    separatorsNonempty := by decide }

def future : AttackObligation Attack Channel :=
  { attack := .futureData
    separators := [.unifiedIntegrityAttestation]
    separatorsNonempty := by decide }

def timestamp : AttackObligation Attack Channel :=
  { attack := .timestampBackdating
    separators := [.transparencyLog]
    separatorsNonempty := by decide }

def obligations : List (AttackObligation Attack Channel) :=
  [hidden, future, timestamp]

def certificate : CoverageCertificate Attack Channel :=
  { selected := [.unifiedIntegrityAttestation, .transparencyLog]
    obligations := obligations
    covers := by
      intro obligation member
      simp [obligations] at member
      rcases member with rfl | rfl | rfl
      · exact ⟨.unifiedIntegrityAttestation, by simp, by simp [hidden]⟩
      · exact ⟨.unifiedIntegrityAttestation, by simp, by simp [future]⟩
      · exact ⟨.transparencyLog, by simp, by simp [timestamp]⟩ }

theorem selected_portfolio_covers_corpus :
    CoversAllObligations certificate.selected certificate.obligations :=
  certificate.sound

theorem hidden_and_future_share_obligation_signature :
    SameObligationSignature hidden future := by
  rfl

end LeanFinance.Epistemic.SymbolicCoverageExample
