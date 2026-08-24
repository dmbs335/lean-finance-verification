import LeanFinance.ResearchAgent.Workflow

namespace LeanFinance.ResearchAgent.Example

open LeanFinance.ResearchAgent

def certificate : BoundedResearchCertificate :=
  { planDigest := "registered-plan"
    artifactDigests := ["alpha-audit", "portfolio", "crowding", "liquidation"]
    completedStages := requiredStages
    alphaAuditPassed := true
    portfolioGatePassed := true
    crowdingGatePassed := true
    liquidationGatePassed := true
    stageOrder := rfl
    gateProof := ⟨rfl, rfl, rfl, rfl⟩ }

theorem fixture_passes_every_gate :
    certificate.alphaAuditPassed = true ∧
      certificate.portfolioGatePassed = true ∧
        certificate.crowdingGatePassed = true ∧
          certificate.liquidationGatePassed = true :=
  certificate.all_analysis_gates_pass

end LeanFinance.ResearchAgent.Example
