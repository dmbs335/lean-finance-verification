import LeanFinance.Core

namespace LeanFinance.Market

/-- Shared dependency between strategies that can create common epistemic
    failure modes. -/
structure EvidenceDependency where
  dataShared : Bool
  modelShared : Bool
  providerShared : Bool
  executionShared : Bool
  deriving Repr

structure StrategyEvidenceLink (Strategy : Type) where
  left : Strategy
  right : Strategy
  dependency : EvidenceDependency
  deriving Repr

/-- Count shared evidence boundaries as a simple bounded prototype metric. -/
def dependencyScore
    (dependency : EvidenceDependency) : Nat :=
  (if dependency.dataShared then 1 else 0) +
  (if dependency.modelShared then 1 else 0) +
  (if dependency.providerShared then 1 else 0) +
  (if dependency.executionShared then 1 else 0)

/-- Two strategies can have low return correlation while high evidence
    dependency. This prototype separates economic interaction from evidence
    interaction. -/
structure EpistemicCrowdingProfile where
  returnCorrelation : Int
  evidenceOverlap : Nat
  deriving Repr

/-- A higher evidence overlap represents a larger common verification surface. -/
def crowded
    (profile : EpistemicCrowdingProfile) : Prop :=
  profile.evidenceOverlap > 0

end LeanFinance.Market
