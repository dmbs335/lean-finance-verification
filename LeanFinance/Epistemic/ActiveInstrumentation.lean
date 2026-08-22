import LeanFinance.Epistemic.ModelFamily

namespace LeanFinance.Epistemic

universe u v w x y

/-- An adaptive evidence policy first observes one model-identifying probe
    outcome and then chooses an outcome-specific evidence-channel family.

    `branchVerifies` is the scientific obligation: within every posterior model
    family induced by one outcome, the selected branch channels verify the
    claim uniformly over all admissible model/history worlds. -/
structure AdaptiveEvidencePolicy
    (Model : Type u)
    (History : Type v)
    (Outcome : Type w)
    (Channel : Type x)
    (Observation : Type y)
    (admissible : Model → History → Prop)
    (observe : Channel → Model → History → Observation)
    (claim : Model → History → Prop) where
  probe : Model → Outcome
  selected : Outcome → Channel → Prop
  branchVerifies :
    ∀ outcome,
      ModelFamilyChannelSelectionVerifies
        (fun model history =>
          admissible model history ∧
            probe model = outcome)
        observe
        (selected outcome)
        claim

/-- The semantic verification condition for the complete adaptive policy.

    If two worlds produce different probe outcomes, the probe separates them.
    If they produce the same outcome, the branch-specific selected evidence
    must determine the claim. -/
def AdaptivePolicyVerifies
    {Model : Type u}
    {History : Type v}
    {Outcome : Type w}
    {Channel : Type x}
    {Observation : Type y}
    (admissible : Model → History → Prop)
    (observe : Channel → Model → History → Observation)
    (claim : Model → History → Prop)
    (probe : Model → Outcome)
    (selected : Outcome → Channel → Prop) : Prop :=
  ∀ leftModel leftHistory,
    admissible leftModel leftHistory →
      ∀ rightModel rightHistory,
        admissible rightModel rightHistory →
          probe leftModel = probe rightModel →
            ModelFamilyChannelsAgree observe
                (selected (probe leftModel))
                leftModel leftHistory rightModel rightHistory →
              (claim leftModel leftHistory ↔
                claim rightModel rightHistory)

namespace AdaptiveEvidencePolicy

/-- Correct branch verification implies correctness of the complete adaptive
    policy. -/
theorem verifies
    {Model : Type u}
    {History : Type v}
    {Outcome : Type w}
    {Channel : Type x}
    {Observation : Type y}
    {admissible : Model → History → Prop}
    {observe : Channel → Model → History → Observation}
    {claim : Model → History → Prop}
    (policy :
      AdaptiveEvidencePolicy Model History Outcome Channel Observation
        admissible observe claim) :
    AdaptivePolicyVerifies
      admissible observe claim policy.probe policy.selected := by
  intro leftModel leftHistory leftAdmissible
      rightModel rightHistory rightAdmissible sameOutcome sameEvidence
  apply policy.branchVerifies (policy.probe leftModel)
    leftModel leftHistory
    ⟨leftAdmissible, rfl⟩
    rightModel rightHistory
    ⟨rightAdmissible, sameOutcome.symm⟩
    sameEvidence

end AdaptiveEvidencePolicy

/-- A finite adaptive portfolio with an explicit probe cost and branch channel
    lists. -/
structure FiniteAdaptiveEvidencePolicy
    (Model : Type u)
    (History : Type v)
    (Outcome : Type w)
    (Channel : Type x)
    (Observation : Type y)
    (admissible : Model → History → Prop)
    (observe : Channel → Model → History → Observation)
    (claim : Model → History → Prop)
    (channelCost : Channel → Nat) where
  probe : Model → Outcome
  probeCost : Nat
  selected : Outcome → List Channel
  branchVerifies :
    ∀ outcome,
      ModelFamilyChannelSelectionVerifies
        (fun model history =>
          admissible model history ∧ probe model = outcome)
        observe
        (fun channel => channel ∈ selected outcome)
        claim

namespace FiniteAdaptiveEvidencePolicy

/-- Cost paid in one actual model world: the probe plus only the portfolio
    selected for that model's outcome. -/
def costAt
    {Model : Type u}
    {History : Type v}
    {Outcome : Type w}
    {Channel : Type x}
    {Observation : Type y}
    {admissible : Model → History → Prop}
    {observe : Channel → Model → History → Observation}
    {claim : Model → History → Prop}
    {channelCost : Channel → Nat}
    (policy :
      FiniteAdaptiveEvidencePolicy Model History Outcome Channel Observation
        admissible observe claim channelCost)
    (model : Model) : Nat :=
  policy.probeCost +
    (policy.selected (policy.probe model)).foldl
      (fun total channel => total + channelCost channel) 0

/-- A declared worst-case cost upper bound over all models. -/
def WorstCaseCostAtMost
    {Model : Type u}
    {History : Type v}
    {Outcome : Type w}
    {Channel : Type x}
    {Observation : Type y}
    {admissible : Model → History → Prop}
    {observe : Channel → Model → History → Observation}
    {claim : Model → History → Prop}
    {channelCost : Channel → Nat}
    (policy :
      FiniteAdaptiveEvidencePolicy Model History Outcome Channel Observation
        admissible observe claim channelCost)
    (bound : Nat) : Prop :=
  ∀ model, policy.costAt model ≤ bound

/-- A finite adaptive policy induces the generic adaptive-policy semantics. -/
def toAdaptivePolicy
    {Model : Type u}
    {History : Type v}
    {Outcome : Type w}
    {Channel : Type x}
    {Observation : Type y}
    {admissible : Model → History → Prop}
    {observe : Channel → Model → History → Observation}
    {claim : Model → History → Prop}
    {channelCost : Channel → Nat}
    (policy :
      FiniteAdaptiveEvidencePolicy Model History Outcome Channel Observation
        admissible observe claim channelCost) :
    AdaptiveEvidencePolicy Model History Outcome Channel Observation
      admissible observe claim :=
  {
    probe := policy.probe
    selected := fun outcome channel =>
      channel ∈ policy.selected outcome
    branchVerifies := policy.branchVerifies
  }

/-- Every finite adaptive policy verifies the model-family claim when each
    posterior branch carries its verification proof. -/
theorem verifies
    {Model : Type u}
    {History : Type v}
    {Outcome : Type w}
    {Channel : Type x}
    {Observation : Type y}
    {admissible : Model → History → Prop}
    {observe : Channel → Model → History → Observation}
    {claim : Model → History → Prop}
    {channelCost : Channel → Nat}
    (policy :
      FiniteAdaptiveEvidencePolicy Model History Outcome Channel Observation
        admissible observe claim channelCost) :
    AdaptivePolicyVerifies
      admissible observe claim policy.probe
        (fun outcome channel => channel ∈ policy.selected outcome) :=
  policy.toAdaptivePolicy.verifies

/-- A strict cost comparison between an adaptive policy and one static
    portfolio. -/
def StrictlyCheaperThanStatic
    {Model : Type u}
    {History : Type v}
    {Outcome : Type w}
    {Channel : Type x}
    {Observation : Type y}
    {admissible : Model → History → Prop}
    {observe : Channel → Model → History → Observation}
    {claim : Model → History → Prop}
    {channelCost : Channel → Nat}
    (policy :
      FiniteAdaptiveEvidencePolicy Model History Outcome Channel Observation
        admissible observe claim channelCost)
    (models : List Model)
    (staticCost : Nat) : Prop :=
  ∀ model,
    model ∈ models →
      policy.costAt model < staticCost

end FiniteAdaptiveEvidencePolicy

end LeanFinance.Epistemic
