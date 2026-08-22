import LeanFinance.Epistemic.CutSet

namespace LeanFinance.Epistemic

universe u v w x

/-- Agreement of selected evidence channels across two potentially different
    model/history worlds. -/
def ModelFamilyChannelsAgree
    {Model : Type u}
    {History : Type v}
    {Channel : Type w}
    {Observation : Type x}
    (observe : Channel → Model → History → Observation)
    (selected : Channel → Prop)
    (leftModel : Model)
    (leftHistory : History)
    (rightModel : Model)
    (rightHistory : History) : Prop :=
  ∀ channel,
    selected channel →
      observe channel leftModel leftHistory =
        observe channel rightModel rightHistory

/-- A channel selection verifies a claim uniformly over every admissible
    model/history world in one semantics version space. -/
def ModelFamilyChannelSelectionVerifies
    {Model : Type u}
    {History : Type v}
    {Channel : Type w}
    {Observation : Type x}
    (admissible : Model → History → Prop)
    (observe : Channel → Model → History → Observation)
    (selected : Channel → Prop)
    (claim : Model → History → Prop) : Prop :=
  ∀ leftModel leftHistory,
    admissible leftModel leftHistory →
      ∀ rightModel rightHistory,
        admissible rightModel rightHistory →
          ModelFamilyChannelsAgree observe selected
              leftModel leftHistory rightModel rightHistory →
            (claim leftModel leftHistory ↔
              claim rightModel rightHistory)

/-- One channel separates two model/history worlds. -/
def SeparatesModelWorlds
    {Model : Type u}
    {History : Type v}
    {Channel : Type w}
    {Observation : Type x}
    (observe : Channel → Model → History → Observation)
    (channel : Channel)
    (leftModel : Model)
    (leftHistory : History)
    (rightModel : Model)
    (rightHistory : History) : Prop :=
  observe channel leftModel leftHistory ≠
    observe channel rightModel rightHistory

/-- A selected family hits every admissible cross-model claim disagreement. -/
def ModelFamilyHitsEveryClaimDisagreement
    {Model : Type u}
    {History : Type v}
    {Channel : Type w}
    {Observation : Type x}
    (admissible : Model → History → Prop)
    (observe : Channel → Model → History → Observation)
    (selected : Channel → Prop)
    (claim : Model → History → Prop) : Prop :=
  ∀ leftModel leftHistory,
    admissible leftModel leftHistory →
      ∀ rightModel rightHistory,
        admissible rightModel rightHistory →
          ¬ (claim leftModel leftHistory ↔
            claim rightModel rightHistory) →
            ∃ channel,
              selected channel ∧
                SeparatesModelWorlds observe channel
                  leftModel leftHistory rightModel rightHistory

/-- Evidence cut-set duality extends unchanged from one fixed semantics to a
    version space of model/history worlds. -/
theorem model_family_evidence_cut_set_duality
    {Model : Type u}
    {History : Type v}
    {Channel : Type w}
    {Observation : Type x}
    (admissible : Model → History → Prop)
    (observe : Channel → Model → History → Observation)
    (selected : Channel → Prop)
    (claim : Model → History → Prop) :
    ModelFamilyChannelSelectionVerifies
        admissible observe selected claim ↔
      ModelFamilyHitsEveryClaimDisagreement
        admissible observe selected claim := by
  constructor
  · intro verifies leftModel leftHistory leftAdmissible
      rightModel rightHistory rightAdmissible disagreement
    apply Classical.byContradiction
    intro noSeparator
    have sameEvidence :
        ModelFamilyChannelsAgree observe selected
          leftModel leftHistory rightModel rightHistory := by
      intro channel selectedChannel
      apply Classical.byContradiction
      intro different
      exact noSeparator ⟨channel, selectedChannel, different⟩
    exact disagreement
      (verifies leftModel leftHistory leftAdmissible
        rightModel rightHistory rightAdmissible sameEvidence)
  · intro hits leftModel leftHistory leftAdmissible
      rightModel rightHistory rightAdmissible sameEvidence
    apply Classical.byContradiction
    intro disagreement
    rcases hits leftModel leftHistory leftAdmissible
        rightModel rightHistory rightAdmissible disagreement with
      ⟨channel, selectedChannel, separates⟩
    exact separates (sameEvidence channel selectedChannel)

/-- One admissible model-family world set is included in another. -/
def ModelFamilyIncluded
    {Model : Type u}
    {History : Type v}
    (small large : Model → History → Prop) : Prop :=
  ∀ model history,
    small model history → large model history

/-- **Model-family expansion antitonicity.** If one channel family verifies a
    larger semantics version space, it verifies every restriction of that
    family. Admitting more consistent models can only remove feasible evidence
    selections. -/
theorem verification_antitone_under_model_family_expansion
    {Model : Type u}
    {History : Type v}
    {Channel : Type w}
    {Observation : Type x}
    (small large : Model → History → Prop)
    (observe : Channel → Model → History → Observation)
    (selected : Channel → Prop)
    (claim : Model → History → Prop)
    (included : ModelFamilyIncluded small large)
    (verifiesLarge :
      ModelFamilyChannelSelectionVerifies
        large observe selected claim) :
    ModelFamilyChannelSelectionVerifies
      small observe selected claim := by
  intro leftModel leftHistory leftSmall
      rightModel rightHistory rightSmall sameEvidence
  exact verifiesLarge
    leftModel leftHistory (included leftModel leftHistory leftSmall)
    rightModel rightHistory (included rightModel rightHistory rightSmall)
    sameEvidence

/-- A constructive pair showing that one selected family fails only when model
    uncertainty is retained. -/
structure CrossModelVerificationCounterexample
    {Model : Type u}
    {History : Type v}
    {Channel : Type w}
    {Observation : Type x}
    (admissible : Model → History → Prop)
    (observe : Channel → Model → History → Observation)
    (selected : Channel → Prop)
    (claim : Model → History → Prop) where
  leftModel : Model
  leftHistory : History
  rightModel : Model
  rightHistory : History
  leftAdmissible : admissible leftModel leftHistory
  rightAdmissible : admissible rightModel rightHistory
  sameEvidence :
    ModelFamilyChannelsAgree observe selected
      leftModel leftHistory rightModel rightHistory
  leftClaim : claim leftModel leftHistory
  rightNotClaim : ¬ claim rightModel rightHistory

namespace CrossModelVerificationCounterexample

/-- A single cross-model indistinguishable pair refutes uniform verification
    over the complete version space. -/
theorem notFamilyVerifiable
    {Model : Type u}
    {History : Type v}
    {Channel : Type w}
    {Observation : Type x}
    {admissible : Model → History → Prop}
    {observe : Channel → Model → History → Observation}
    {selected : Channel → Prop}
    {claim : Model → History → Prop}
    (counterexample :
      CrossModelVerificationCounterexample
        admissible observe selected claim) :
    ¬ ModelFamilyChannelSelectionVerifies
      admissible observe selected claim := by
  intro verifies
  exact counterexample.rightNotClaim
    ((verifies
      counterexample.leftModel counterexample.leftHistory
      counterexample.leftAdmissible
      counterexample.rightModel counterexample.rightHistory
      counterexample.rightAdmissible
      counterexample.sameEvidence).mp
      counterexample.leftClaim)

end CrossModelVerificationCounterexample

/-- Fixing one convenient model can underestimate the evidence required over a
    larger semantics family. The first premise records point-model verification;
    the constructive counterexample records failure of the full family. -/
theorem point_model_verification_can_underestimate_family
    {Model : Type u}
    {History : Type v}
    {Channel : Type w}
    {Observation : Type x}
    (admissible : Model → History → Prop)
    (observe : Channel → Model → History → Observation)
    (selected : Channel → Prop)
    (claim : Model → History → Prop)
    (pointModel : Model)
    (_pointVerifies :
      ModelFamilyChannelSelectionVerifies
        (fun model history =>
          model = pointModel ∧ admissible model history)
        observe selected claim)
    (familyCounterexample :
      CrossModelVerificationCounterexample
        admissible observe selected claim) :
    ¬ ModelFamilyChannelSelectionVerifies
      admissible observe selected claim :=
  familyCounterexample.notFamilyVerifiable

end LeanFinance.Epistemic
