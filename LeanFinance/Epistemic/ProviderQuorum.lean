import LeanFinance.Core

namespace LeanFinance.Epistemic

/-- Normalized evidence after provider-specific cryptographic verification. -/
structure VerifiedExternalEvidence where
  providerId : String
  trustDomain : String
  targetDigest : ContentHash
  anchoredAt : Timestamp
  deriving Repr, DecidableEq

def VerifiedExternalEvidence.ValidFor
    (target : ContentHash)
    (cutoff : Timestamp)
    (evidence : VerifiedExternalEvidence) : Prop :=
  evidence.targetDigest = target ∧
    evidence.anchoredAt ≤ cutoff

/-- Proof-carrying quorum over verifier-selected trust domains. The domain list
    is explicit so aliases or duplicate providers cannot silently increase the
    threshold. -/
structure ProviderQuorumCertificate where
  targetDigest : ContentHash
  cutoff : Timestamp
  receipts : List VerifiedExternalEvidence
  domains : List String
  domainsNodup : domains.Nodup
  everyReceiptValid :
    ∀ receipt,
      receipt ∈ receipts →
        receipt.ValidFor targetDigest cutoff
  everyReceiptDomainDeclared :
    ∀ receipt,
      receipt ∈ receipts →
        receipt.trustDomain ∈ domains
  everyDomainWitnessed :
    ∀ domain,
      domain ∈ domains →
        ∃ receipt,
          receipt ∈ receipts ∧
            receipt.trustDomain = domain
  requiredDomains : Nat
  thresholdMet : requiredDomains ≤ domains.length

namespace ProviderQuorumCertificate

theorem all_receipts_bind_same_target
    (certificate : ProviderQuorumCertificate)
    (receipt : VerifiedExternalEvidence)
    (member : receipt ∈ certificate.receipts) :
    receipt.targetDigest = certificate.targetDigest :=
  (certificate.everyReceiptValid receipt member).1

theorem all_receipts_precede_cutoff
    (certificate : ProviderQuorumCertificate)
    (receipt : VerifiedExternalEvidence)
    (member : receipt ∈ certificate.receipts) :
    receipt.anchoredAt ≤ certificate.cutoff :=
  (certificate.everyReceiptValid receipt member).2

theorem quorum_meets_required_domains
    (certificate : ProviderQuorumCertificate) :
    certificate.requiredDomains ≤ certificate.domains.length :=
  certificate.thresholdMet

end ProviderQuorumCertificate

end LeanFinance.Epistemic
