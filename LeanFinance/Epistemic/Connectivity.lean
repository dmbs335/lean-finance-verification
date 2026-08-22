import LeanFinance.Epistemic.FiniteSynthesisCompleteness

namespace LeanFinance.Epistemic

universe u v w x y

/-- The channels that remain selected under one declared failure scenario. -/
def SurvivingSelection
    {Failure : Type u}
    {Channel : Type v}
    (selected : Channel → Prop)
    (survives : Failure → Channel → Prop)
    (failure : Failure) : Channel → Prop :=
  fun channel => selected channel ∧ survives failure channel

/-- Verification resilient to every scenario in a declared failure family. -/
def FailureRobustVerifies
    {Failure : Type u}
    {Channel : Type v}
    {History : Type w}
    {Observation : Type x}
    (channel : Channel → History → Observation)
    (selected : Channel → Prop)
    (claim : History → Prop)
    (survives : Failure → Channel → Prop) : Prop :=
  ∀ failure,
    ChannelSelectionVerifies channel
      (SurvivingSelection selected survives failure) claim

/-- Epistemic connectivity under a failure family: after every allowed failure,
    every claim-disagreement pair still has one surviving selected separator. -/
def FailureConnectivity
    {Failure : Type u}
    {Channel : Type v}
    {History : Type w}
    {Observation : Type x}
    (channel : Channel → History → Observation)
    (selected : Channel → Prop)
    (claim : History → Prop)
    (survives : Failure → Channel → Prop) : Prop :=
  ∀ failure,
    HitsEveryClaimDisagreement channel
      (SurvivingSelection selected survives failure) claim

/-- Robust verification is exactly failure-relative separator connectivity. -/
theorem failure_robust_verification_iff_connectivity
    {Failure : Type u}
    {Channel : Type v}
    {History : Type w}
    {Observation : Type x}
    (channel : Channel → History → Observation)
    (selected : Channel → Prop)
    (claim : History → Prop)
    (survives : Failure → Channel → Prop) :
    FailureRobustVerifies channel selected claim survives ↔
      FailureConnectivity channel selected claim survives := by
  constructor
  · intro robust failure
    exact
      (evidence_cut_set_duality
        channel
        (SurvivingSelection selected survives failure)
        claim).mp (robust failure)
  · intro connected failure
    exact
      (evidence_cut_set_duality
        channel
        (SurvivingSelection selected survives failure)
        claim).mpr (connected failure)

/-- Adding selected channels cannot destroy failure robustness. -/
theorem failure_robust_monotone_in_selection
    {Failure : Type u}
    {Channel : Type v}
    {History : Type w}
    {Observation : Type x}
    (channel : Channel → History → Observation)
    (smaller larger : Channel → Prop)
    (claim : History → Prop)
    (survives : Failure → Channel → Prop)
    (included : ∀ evidenceChannel,
      smaller evidenceChannel → larger evidenceChannel)
    (robust :
      FailureRobustVerifies channel smaller claim survives) :
    FailureRobustVerifies channel larger claim survives := by
  intro failure
  exact verification_monotone_in_channels
    channel
    (SurvivingSelection smaller survives failure)
    (SurvivingSelection larger survives failure)
    claim
    (by
      intro evidenceChannel chosen
      exact ⟨included evidenceChannel chosen.1, chosen.2⟩)
    (robust failure)

/-- If one failure model always leaves at least as many channels alive as a
    harder model, robustness to the harder model implies robustness to the
    easier one. -/
theorem failure_robust_monotone_in_survival
    {Failure : Type u}
    {Channel : Type v}
    {History : Type w}
    {Observation : Type x}
    (channel : Channel → History → Observation)
    (selected : Channel → Prop)
    (claim : History → Prop)
    (harder easier : Failure → Channel → Prop)
    (survivalIncluded :
      ∀ failure evidenceChannel,
        harder failure evidenceChannel →
          easier failure evidenceChannel)
    (robust : FailureRobustVerifies channel selected claim harder) :
    FailureRobustVerifies channel selected claim easier := by
  intro failure
  exact verification_monotone_in_channels
    channel
    (SurvivingSelection selected harder failure)
    (SurvivingSelection selected easier failure)
    claim
    (by
      intro evidenceChannel chosen
      exact
        ⟨chosen.1,
          survivalIncluded failure evidenceChannel chosen.2⟩)
    (robust failure)

/-- Executable survivor projection for bounded evidence models. -/
def survivingChannels
    {Failure : Type u}
    {Channel : Type v}
    (selected : List Channel)
    (survives : Failure → Channel → Bool)
    (failure : Failure) : List Channel :=
  selected.filter (survives failure)

theorem mem_survivingChannels
    {Failure : Type u}
    {Channel : Type v}
    {selected : List Channel}
    {survives : Failure → Channel → Bool}
    {failure : Failure}
    {evidenceChannel : Channel} :
    evidenceChannel ∈
        survivingChannels selected survives failure ↔
      evidenceChannel ∈ selected ∧
        survives failure evidenceChannel = true := by
  simp [survivingChannels]

/-- Bounded robust verification checks every declared failure scenario against
    the complete finite history catalog. -/
def FailureRobustBoundedVerifies
    {Failure : Type u}
    {History : Type v}
    {Channel : Type w}
    {Observation : Type x}
    (model : BoundedEvidenceModel History Channel Observation)
    (selected : List Channel)
    (survives : Failure → Channel → Bool) : Prop :=
  ∀ failure,
    BoundedSelectionVerifies model
      (survivingChannels selected survives failure)

/-- Bounded robust verification lifts scenario by scenario to the semantic
    channel-verification contract when the history catalog is complete. -/
theorem failure_robust_bounded_semantically_sound
    {Failure : Type u}
    {History : Type v}
    {Channel : Type w}
    {Observation : Type x}
    (model : BoundedEvidenceModel History Channel Observation)
    (selected : List Channel)
    (survives : Failure → Channel → Bool)
    (historyComplete : ∀ history, history ∈ model.histories)
    (robust :
      FailureRobustBoundedVerifies model selected survives) :
    ∀ failure,
      ChannelSelectionVerifies model.observe
        (fun evidenceChannel =>
          evidenceChannel ∈
            survivingChannels selected survives failure)
        model.ClaimHolds := by
  intro failure
  exact bounded_verification_semantically_sound
    model
    (survivingChannels selected survives failure)
    historyComplete
    (robust failure)

/-- A single failed trust domain removes every channel controlled by that
    domain. `none` represents the no-failure scenario. -/
def survivesDomainFailure
    {Domain : Type u}
    {Channel : Type v}
    [DecidableEq Domain]
    (domain : Channel → Domain) :
    Option Domain → Channel → Bool
  | none, _ => true
  | some failedDomain, evidenceChannel =>
      decide (domain evidenceChannel ≠ failedDomain)

end LeanFinance.Epistemic
