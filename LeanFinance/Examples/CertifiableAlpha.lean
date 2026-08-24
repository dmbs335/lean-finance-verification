import LeanFinance.Alpha

namespace LeanFinance.Examples.CertifiableAlpha

open LeanFinance.Alpha

def weakEvidence : EvidenceState :=
  { historySpaceSize := 100
    modelSpaceSize := 20
    evidenceCost := 1 }

def strongEvidence : EvidenceState :=
  { historySpaceSize := 10
    modelSpaceSize := 3
    evidenceCost := 5 }

theorem stronger_evidence_reduces_space :
    MoreInformative strongEvidence weakEvidence := by
  constructor <;> decide

end LeanFinance.Examples.CertifiableAlpha
