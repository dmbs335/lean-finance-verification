import LeanFinance.ResearchAgent.Workflow

namespace LeanFinance.ResearchAgent.Example

open LeanFinance.ResearchAgent

def certificate : BoundedResearchCertificate :=
  { planDigest := "registered-plan"
    artifactDigests :=
      ["alpha-audit", "alpha-interval", "portfolio", "crowding",
        "liquidation", "event-study", "certificate-composition"]
    completedStages := requiredStages
    alphaAuditPassed := true
    alphaIntervalGatePassed := true
    portfolioGatePassed := true
    crowdingGatePassed := true
    liquidationGatePassed := true
    eventStudyGatePassed := true
    compositionGatePassed := true
    stageOrder := rfl
    gateProof := ⟨rfl, rfl, rfl, rfl, rfl, rfl, rfl⟩ }

theorem fixture_passes_every_gate :
    certificate.alphaAuditPassed = true ∧
      certificate.alphaIntervalGatePassed = true ∧
        certificate.portfolioGatePassed = true ∧
          certificate.crowdingGatePassed = true ∧
            certificate.liquidationGatePassed = true ∧
              certificate.eventStudyGatePassed = true ∧
                certificate.compositionGatePassed = true :=
  certificate.all_analysis_gates_pass

end LeanFinance.ResearchAgent.Example
