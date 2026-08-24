namespace LeanFinance.ResearchAgent

/-- Ordered stages of the bounded research harness. The stage names describe
    checks performed by existing formal/executable components; they do not imply
    autonomous scientific truth discovery. -/
inductive ResearchStage where
  | registered
  | alphaAudited
  | alphaBounded
  | portfolioSelected
  | crowdingStressed
  | liquidationStressed
  | eventStudied
  | pipelineComposed
  | certified
  deriving Repr, DecidableEq

def requiredStages : List ResearchStage :=
  [.registered, .alphaAudited, .alphaBounded, .portfolioSelected,
    .crowdingStressed, .liquidationStressed, .eventStudied,
    .pipelineComposed, .certified]

/-- Normalized proof boundary emitted only after every registered finite gate
    passes. Digests bind the plan and externally generated reports, while the
    composition gate binds the local reports into one declared research
    pipeline. -/
structure BoundedResearchCertificate where
  planDigest : String
  artifactDigests : List String
  completedStages : List ResearchStage
  alphaAuditPassed : Bool
  alphaIntervalGatePassed : Bool
  portfolioGatePassed : Bool
  crowdingGatePassed : Bool
  liquidationGatePassed : Bool
  eventStudyGatePassed : Bool
  compositionGatePassed : Bool
  stageOrder : completedStages = requiredStages
  gateProof :
    alphaAuditPassed = true ∧
      alphaIntervalGatePassed = true ∧
        portfolioGatePassed = true ∧
          crowdingGatePassed = true ∧
            liquidationGatePassed = true ∧
              eventStudyGatePassed = true ∧
                compositionGatePassed = true

namespace BoundedResearchCertificate

theorem all_analysis_gates_pass
    (certificate : BoundedResearchCertificate) :
    certificate.alphaAuditPassed = true ∧
      certificate.alphaIntervalGatePassed = true ∧
        certificate.portfolioGatePassed = true ∧
          certificate.crowdingGatePassed = true ∧
            certificate.liquidationGatePassed = true ∧
              certificate.eventStudyGatePassed = true ∧
                certificate.compositionGatePassed = true :=
  certificate.gateProof

theorem follows_required_stage_order
    (certificate : BoundedResearchCertificate) :
    certificate.completedStages = requiredStages :=
  certificate.stageOrder

end BoundedResearchCertificate

end LeanFinance.ResearchAgent
