import LeanFinance.Epistemic.ProviderQuorum

namespace LeanFinance.Epistemic.ProviderQuorumExample

open LeanFinance.Epistemic

def logA : VerifiedExternalEvidence :=
  { providerId := "log-a"
    trustDomain := "operator-a"
    targetDigest := "ledger-root"
    anchoredAt := 8 }

def logB : VerifiedExternalEvidence :=
  { providerId := "log-b"
    trustDomain := "operator-b"
    targetDigest := "ledger-root"
    anchoredAt := 9 }

def certificate : ProviderQuorumCertificate :=
  { targetDigest := "ledger-root"
    cutoff := 10
    receipts := [logA, logB]
    domains := ["operator-a", "operator-b"]
    domainsNodup := by decide
    everyReceiptValid := by
      intro receipt member
      simp [logA, logB, VerifiedExternalEvidence.ValidFor] at member ⊢
      rcases member with rfl | rfl <;> simp [logA, logB]
    everyReceiptDomainDeclared := by
      intro receipt member
      simp [logA, logB] at member ⊢
      rcases member with rfl | rfl <;> simp [logA, logB]
    everyDomainWitnessed := by
      intro domain member
      simp at member
      rcases member with rfl | rfl
      · exact ⟨logA, by simp, rfl⟩
      · exact ⟨logB, by simp, rfl⟩
    requiredDomains := 2
    thresholdMet := by decide }

theorem independent_two_domain_quorum :
    certificate.requiredDomains ≤ certificate.domains.length :=
  certificate.quorum_meets_required_domains

end LeanFinance.Epistemic.ProviderQuorumExample
