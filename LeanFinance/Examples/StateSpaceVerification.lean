import LeanFinance.StateSpace.Certificate
import LeanFinance.StateSpace.Regime
import LeanFinance.StateSpace.Stability
import LeanFinance.StateSpace.Control
import LeanFinance.StateSpace.Operator
import LeanFinance.StateSpace.Bifurcation

namespace LeanFinance.Examples

open StateSpace

def calmLatentState : LatentMarketState :=
  {
    valuationGap := 0
    marketLiquidity := 9000
    fundingLiquidity := 8500
    leverageBps := 3500
    volatilityBps := 1200
    creditStressBps := 800
    riskAppetiteBps := 6000
    positioning := 100
    crowdingBps := 2500
    inflationExpectationBps := 220
    growthExpectationBps := 180
    monetaryTightnessBps := 3000
    earningsExpectationBps := 450
  }

def calmHypothesis : WeightedState LatentMarketState :=
  {
    state := calmLatentState
    weightBps := 10000
  }

def calmEstimate : StateEstimate LatentMarketState :=
  {
    asOf := 10
    hypotheses := [calmHypothesis]
    normalized := by decide
    weightsValid := by
      intro hypothesis member
      have matches : hypothesis = calmHypothesis := by
        simpa using member
      subst hypothesis
      decide
  }

def calmObservation : ObservedMarketSnapshot :=
  {
    observedAt := 8
    availableAt := 9
    price := 100
    realizedVolatilityBps := 1200
    marketDepth := 9000
    creditSpreadBps := 80
    fundingSpreadBps := 15
    positioningProxy := 100
    contentHash := "sha256:calm-market-snapshot"
  }

def calmLaw : StructuralLawMetadata :=
  {
    modelFamilyHash := "sha256:nonlinear-hybrid-state-space-v1"
    parameterHash := "sha256:state-space-parameters-v1"
    estimatedAt := 9
  }

def calmEstimateCertificate :
    StateEstimateCertificate calmEstimate :=
  {
    law := calmLaw
    observations := [calmObservation]
    lawAdmissible := by decide
    observationsAdmissible := by
      intro observation member
      have matches : observation = calmObservation := by
        simpa using member
      subst observation
      decide
  }

example :
    calmObservation.availableAt ≤ calmEstimate.asOf :=
  calmEstimateCertificate.observation_available
    calmObservation (by simp)

def calmMetastability : MetastabilityWitness :=
  {
    internalMixingSteps := 3
    expectedExitSteps := 20
    retentionBps := 9700
  }

def calmMetastabilityCertificate :
    MetastabilityCertificate calmMetastability 9500 :=
  {
    timeScaleSeparated := by decide
    retentionThresholdValid := by decide
    observedRetentionValid := by decide
    retainsMass := by decide
  }

def boundaryEstimate : CommittorEstimate :=
  {
    returnToSourceFirstBps := 4500
    reachTargetFirstBps := 5000
    unresolvedBps := 500
    normalized := by decide
  }

def boundaryCertificate :
    TransitionBoundaryCertificate boundaryEstimate 4000 6000 :=
  {
    ordered := by decide
    inside := by decide
    targetProbabilityValid := by decide
  }

example :
    ¬ CommittedToTarget 7000 boundaryEstimate :=
  boundaryCertificate.not_committed_to_target 7000
    (by decide)

def crisisFirstPassage : FirstPassageForecast :=
  {
    shortHorizon := 5
    longHorizon := 20
    shortHorizonBps := 1200
    longHorizonBps := 3300
    horizonMonotone := by decide
    probabilityMonotone := by decide
    longProbabilityValid := by decide
  }

example :
    ValidProbabilityBps crisisFirstPassage.shortHorizonBps :=
  crisisFirstPassage.shortProbabilityValid

def identityStability : LocalStabilityCertificate Nat :=
  {
    step := fun state => state
    perturbation := fun left right =>
      if left = right then 0 else 1
    domain := fun _ => True
    forwardInvariant := by
      intro state inDomain
      exact inDomain
    nonexpansive := by
      intro left right leftInDomain rightInDomain
      exact Nat.le_refl _
  }

example (steps left right : Nat) :
    identityStability.perturbation
        (iterateStep identityStability.step steps left)
        (iterateStep identityStability.step steps right) ≤
      identityStability.perturbation left right :=
  identityStability.nonexpansive_iterate
    steps left right True.intro True.intro

inductive ReliefInput where
  | reduceOne
  deriving Repr, DecidableEq

def reliefSystem : ControlledSystem Nat ReliefInput :=
  {
    step := fun stress _ => stress - 1
  }

def reliefPlan :
    ControlPlanCertificate reliefSystem 2 0 :=
  {
    controls := [.reduceOne, .reduceOne]
    reaches := by decide
  }

example : Reachable reliefSystem 2 0 :=
  reliefPlan.sound

def transparentSystem :
    PartiallyObservedSystem Nat ReliefInput Nat :=
  {
    step := fun stress _ => stress - 1
    observe := fun stress => stress
  }

def transparentPairCertificate :
    PairObservabilityCertificate transparentSystem 2 1 :=
  {
    controls := []
    distinguishes := by decide
  }

example : PairObservable transparentSystem 2 1 :=
  transparentPairCertificate.sound

def identityKoopman :
    KoopmanCertificate Nat Nat (fun _ => True) :=
  {
    stateStep := fun state => state
    lift := fun state => state
    operator := fun feature => feature
    linear := True.intro
    intertwines := by
      intro state
      rfl
  }

example (steps state : Nat) :
    identityKoopman.lift
        (iterateStep identityKoopman.stateStep steps state) =
      iterateStep identityKoopman.operator steps
        (identityKoopman.lift state) :=
  identityKoopman.intertwines_iterate steps state

def stableBeforeThreshold : StabilityAssessment :=
  {
    parameterValue := 90
    classification := .contracting
    modelFamilyHash := "sha256:leverage-liquidity-family"
    evidenceHash := "sha256:stable-jacobian-evidence"
  }

def unstableAfterThreshold : StabilityAssessment :=
  {
    parameterValue := 110
    classification := .expanding
    modelFamilyHash := "sha256:leverage-liquidity-family"
    evidenceHash := "sha256:unstable-jacobian-evidence"
  }

def leverageBifurcationClaim :
    BifurcationClaimCertificate .upward
      stableBeforeThreshold unstableAfterThreshold 100 :=
  {
    crossesCritical := by decide
    sameModelFamily := rfl
    modelFamilyHashNonempty := by decide
    beforeEvidenceHashNonempty := by decide
    afterEvidenceHashNonempty := by decide
    qualitativeChange := by decide
  }

example :
    CrossesCritical .upward
      stableBeforeThreshold.parameterValue
      unstableAfterThreshold.parameterValue 100 :=
  leverageBifurcationClaim.crossesCritical

end LeanFinance.Examples
