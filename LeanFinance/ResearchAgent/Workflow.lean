namespace LeanFinance.ResearchAgent

/-- Ordered stages of the bounded research harness. The stage names describe
    checks performed by existing formal/executable components; they do not imply
    autonomous scientific truth discovery. -/
inductive ResearchStage where
  | registered
  | alphaAudited
  | portfolioSelected
  | crowdingStressed
  | liquidationStressed
  | certified
  deriving Repr, DecidableEq

def requiredStages : List ResearchStage :=
  [.registered, .alphaAudited, .portfolioSelected,
    .crowdingStressed, .liquidationStressed, .certified]

/-- Normalized proof boundary emitted only after the finite analysis gates pass.
    Digests bind the registered plan and externally generated reports. -/
structure BoundedResearchCertificate where
  planDigest : String
  artifactDigests : List String
  completedStages : List ResearchStage
  alphaAuditPassed : Bool
  portfolioGatePassed : Bool
  crowdingGatePassed : Bool
  liquidationGatePassed : Bool
  stageOrder : completedStages = requiredStages
  gateProof :
    alphaAuditPassed = true ∧
      portfolioGatePassed = true ∧
        crowdingGatePassed = true ∧
          liquidationGatePassed = true

namespace BoundedResearchCertificate

theorem all_analysis_gates_pass
    (certificate : BoundedResearchCertificate) :
    certificate.alphaAuditPassed = true ∧
      certificate.portfolioGatePassed = true ∧
        certificate.crowdingGatePassed = true ∧
          certificate.liquidationGatePassed = true :=
  certificate.gateProof

theorem follows_required_stage_order
    (certificate : BoundedResearchCertificate) :
    certificate.completedStages = requiredStages :=
  certificate.stageOrder

end BoundedResearchCertificate

end LeanFinance.ResearchAgent
