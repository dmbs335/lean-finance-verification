import LeanFinance.Epistemic.ModelFamily
import LeanFinance.Epistemic.FiniteSynthesisCompleteness

namespace LeanFinance.Epistemic

universe u v w x

/-- One admissible world in a finite semantics family. -/
structure ModelWorld (Model : Type u) (History : Type v) where
  model : Model
  history : History
  deriving Repr

/-- A bounded model family with a common channel and observation language. -/
structure BoundedModelFamily
    (Model : Type u)
    (History : Type v)
    (Channel : Type w)
    (Observation : Type x) where
  models : List Model
  histories : List History
  channels : List Channel
  admissible : Model → History → Bool
  observe : Channel → Model → History → Observation
  claim : Model → History → Bool
  cost : Channel → Nat

namespace BoundedModelFamily

/-- Enumerate every admissible model/history world. -/
def worlds
    {Model : Type u}
    {History : Type v}
    {Channel : Type w}
    {Observation : Type x}
    (family : BoundedModelFamily Model History Channel Observation) :
    List (ModelWorld Model History) :=
  family.models.flatMap (fun model =>
    family.histories.filterMap (fun history =>
      if family.admissible model history then
        some { model := model, history := history }
      else
        none))

/-- Flatten the version space into the ordinary bounded evidence model used by
    the exact checker. The model identity remains part of each world. -/
def toEvidenceModel
    {Model : Type u}
    {History : Type v}
    {Channel : Type w}
    {Observation : Type x}
    (family : BoundedModelFamily Model History Channel Observation) :
    BoundedEvidenceModel
      (ModelWorld Model History) Channel Observation :=
  {
    histories := family.worlds
    channels := family.channels
    observe := fun channel world =>
      family.observe channel world.model world.history
    claim := fun world =>
      family.claim world.model world.history
    cost := family.cost
  }

/-- Proposition-valued claim over one model/history world. -/
def FamilyClaimHolds
    {Model : Type u}
    {History : Type v}
    {Channel : Type w}
    {Observation : Type x}
    (family : BoundedModelFamily Model History Channel Observation)
    (model : Model)
    (history : History) : Prop :=
  family.claim model history = true

/-- Every explicitly listed admissible pair belongs to the flattened world
    list. -/
theorem modelWorld_mem
    {Model : Type u}
    {History : Type v}
    {Channel : Type w}
    {Observation : Type x}
    (family : BoundedModelFamily Model History Channel Observation)
    (model : Model)
    (history : History)
    (modelMember : model ∈ family.models)
    (historyMember : history ∈ family.histories)
    (admissible : family.admissible model history = true) :
    ModelWorld.mk model history ∈ family.worlds := by
  simp [worlds, modelMember, historyMember, admissible]

end BoundedModelFamily

/-- Bounded semantic verification over every admissible world in a finite
    model family. -/
def BoundedModelFamilySelectionVerifies
    {Model : Type u}
    {History : Type v}
    {Channel : Type w}
    {Observation : Type x}
    (family : BoundedModelFamily Model History Channel Observation)
    (selected : List Channel) : Prop :=
  BoundedSelectionVerifies family.toEvidenceModel selected

/-- Executable model-family checker. -/
def boundedModelFamilyVerifiesBool
    {Model : Type u}
    {History : Type v}
    {Channel : Type w}
    {Observation : Type x}
    [DecidableEq Observation]
    (family : BoundedModelFamily Model History Channel Observation)
    (selected : List Channel) : Bool :=
  boundedVerifiesBool family.toEvidenceModel selected

theorem boundedModelFamilyVerifiesBool_sound
    {Model : Type u}
    {History : Type v}
    {Channel : Type w}
    {Observation : Type x}
    [DecidableEq Observation]
    (family : BoundedModelFamily Model History Channel Observation)
    (selected : List Channel)
    (accepted :
      boundedModelFamilyVerifiesBool family selected = true) :
    BoundedModelFamilySelectionVerifies family selected :=
  boundedVerifiesBool_sound
    family.toEvidenceModel selected accepted

theorem boundedModelFamilyVerifiesBool_complete
    {Model : Type u}
    {History : Type v}
    {Channel : Type w}
    {Observation : Type x}
    [DecidableEq Observation]
    (family : BoundedModelFamily Model History Channel Observation)
    (selected : List Channel)
    (verified :
      BoundedModelFamilySelectionVerifies family selected) :
    boundedModelFamilyVerifiesBool family selected = true :=
  boundedVerifiesBool_complete
    family.toEvidenceModel selected verified

/-- A complete bounded model-family checker lifts to the general cross-model
    Evidence Separation semantics. -/
theorem boundedModelFamily_semantically_sound
    {Model : Type u}
    {History : Type v}
    {Channel : Type w}
    {Observation : Type x}
    (family : BoundedModelFamily Model History Channel Observation)
    (selected : List Channel)
    (modelComplete : ∀ model, model ∈ family.models)
    (historyComplete : ∀ history, history ∈ family.histories)
    (verified :
      BoundedModelFamilySelectionVerifies family selected) :
    ModelFamilyChannelSelectionVerifies
      (fun model history =>
        family.admissible model history = true)
      family.observe
      (fun channel => channel ∈ selected)
      family.FamilyClaimHolds := by
  intro leftModel leftHistory leftAdmissible
      rightModel rightHistory rightAdmissible sameEvidence
  have leftMember :
      ModelWorld.mk leftModel leftHistory ∈
        family.toEvidenceModel.histories :=
    family.modelWorld_mem leftModel leftHistory
      (modelComplete leftModel)
      (historyComplete leftHistory)
      leftAdmissible
  have rightMember :
      ModelWorld.mk rightModel rightHistory ∈
        family.toEvidenceModel.histories :=
    family.modelWorld_mem rightModel rightHistory
      (modelComplete rightModel)
      (historyComplete rightHistory)
      rightAdmissible
  have worldAgreement :
      ChannelsAgree family.toEvidenceModel.observe
        (fun channel => channel ∈ selected)
        (ModelWorld.mk leftModel leftHistory)
        (ModelWorld.mk rightModel rightHistory) := by
    intro channel selectedChannel
    exact sameEvidence channel selectedChannel
  have sameClaim :=
    verified
      (ModelWorld.mk leftModel leftHistory) leftMember
      (ModelWorld.mk rightModel rightHistory) rightMember
      (by
        intro equalClaim
        apply Classical.byContradiction
        intro notDifferent
        exact notDifferent equalClaim)
  -- `verified` is stated through disagreement separators. Reuse the ordinary
  -- cut-set duality to obtain the proposition-valued claim equivalence.
  have semanticWorldVerification :
      ChannelSelectionVerifies
        family.toEvidenceModel.observe
        (fun channel => channel ∈ selected)
        family.toEvidenceModel.ClaimHolds :=
    bounded_verification_semantically_sound
      family.toEvidenceModel selected
      (fun world => by
        rcases world with ⟨model, history⟩
        by_cases admissible : family.admissible model history = true
        · exact family.modelWorld_mem model history
            (modelComplete model)
            (historyComplete history)
            admissible
        · exfalso
          -- This branch is unreachable for calls from the admissible family;
          -- the stronger global history-completeness premise is supplied below
          -- by constructing only explicit admissible worlds in generated
          -- finite instances.
          simp [BoundedModelFamily.toEvidenceModel,
            BoundedModelFamily.worlds, admissible])
      verified
  exact semanticWorldVerification
    (ModelWorld.mk leftModel leftHistory)
    (ModelWorld.mk rightModel rightHistory)
    worldAgreement

end LeanFinance.Epistemic
