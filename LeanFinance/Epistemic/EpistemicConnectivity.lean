import LeanFinance.Epistemic.CutSet

namespace LeanFinance.Epistemic

universe u v w x y

/-- Verification under a family of admissible evidence faults.

`survives fault channel` describes whether one selected channel remains usable
under one fault scenario. The fault representation is deliberately abstract:
it may denote individual channel loss, provider compromise, correlated cloud
failure, certificate-authority compromise, or another threat model. -/
def RobustlyVerifies
    {Fault : Type u}
    {Channel : Type v}
    {History : Type w}
    {Observation : Type x}
    (channel : Channel → History → Observation)
    (selected : Channel → Prop)
    (claim : History → Prop)
    (allowed : Fault → Prop)
    (survives : Fault → Channel → Prop) : Prop :=
  ∀ fault,
    allowed fault →
      ChannelSelectionVerifies channel
        (fun evidenceChannel =>
          selected evidenceChannel ∧
            survives fault evidenceChannel)
        claim

/-- Every claim-disagreement pair retains at least one selected separator under
    every allowed fault. -/
def RobustlyHitsEveryClaimDisagreement
    {Fault : Type u}
    {Channel : Type v}
    {History : Type w}
    {Observation : Type x}
    (channel : Channel → History → Observation)
    (selected : Channel → Prop)
    (claim : History → Prop)
    (allowed : Fault → Prop)
    (survives : Fault → Channel → Prop) : Prop :=
  ∀ left right,
    ¬ (claim left ↔ claim right) →
      ∀ fault,
        allowed fault →
          ∃ evidenceChannel,
            selected evidenceChannel ∧
              survives fault evidenceChannel ∧
                Separates channel evidenceChannel left right

/-- **Robust evidence cut-set duality.** Verification survives every admissible
    fault exactly when every claim-disagreement separator hyperedge retains a
    selected live channel under every admissible fault. -/
theorem robust_evidence_cut_set_duality
    {Fault : Type u}
    {Channel : Type v}
    {History : Type w}
    {Observation : Type x}
    (channel : Channel → History → Observation)
    (selected : Channel → Prop)
    (claim : History → Prop)
    (allowed : Fault → Prop)
    (survives : Fault → Channel → Prop) :
    RobustlyVerifies channel selected claim allowed survives ↔
      RobustlyHitsEveryClaimDisagreement
        channel selected claim allowed survives := by
  constructor
  · intro robust left right disagreement fault allowedFault
    apply Classical.byContradiction
    intro noLiveSeparator
    have sameEvidence :
        ChannelsAgree channel
          (fun evidenceChannel =>
            selected evidenceChannel ∧
              survives fault evidenceChannel)
          left right := by
      intro evidenceChannel liveSelected
      apply Classical.byContradiction
      intro different
      exact noLiveSeparator
        ⟨evidenceChannel, liveSelected.1, liveSelected.2, different⟩
    exact disagreement
      (robust fault allowedFault left right sameEvidence)
  · intro hits fault allowedFault left right sameEvidence
    apply Classical.byContradiction
    intro disagreement
    rcases hits left right disagreement fault allowedFault with
      ⟨evidenceChannel, selectedChannel, liveChannel, separates⟩
    exact separates
      (sameEvidence evidenceChannel
        ⟨selectedChannel, liveChannel⟩)

/-- Robust verification is antitone in the admitted fault family: surviving a
    larger threat model implies surviving each of its restrictions. -/
theorem robustVerification_antitone_in_fault_model
    {Fault : Type u}
    {Channel : Type v}
    {History : Type w}
    {Observation : Type x}
    (channel : Channel → History → Observation)
    (selected : Channel → Prop)
    (claim : History → Prop)
    (smallFaults largeFaults : Fault → Prop)
    (survives : Fault → Channel → Prop)
    (included : ∀ fault, smallFaults fault → largeFaults fault)
    (robustLarge :
      RobustlyVerifies channel selected claim largeFaults survives) :
    RobustlyVerifies channel selected claim smallFaults survives := by
  intro fault smallAllowed
  exact robustLarge fault (included fault smallAllowed)

/-- A bounded individual-channel failure scenario. `Nodup` ensures that the
    length bound counts distinct failed channels. -/
def ChannelFaultAllowed
    {Channel : Type v}
    (budget : Nat)
    (failed : List Channel) : Prop :=
  failed.Nodup ∧ failed.length ≤ budget

/-- One channel survives an individual-channel fault list when it is absent
    from that list. -/
def SurvivesChannelFault
    {Channel : Type v}
    (failed : List Channel)
    (channel : Channel) : Prop :=
  channel ∉ failed

/-- Verification resilient to every loss of at most `budget` distinct selected
    or unselected channels. Unselected failures are harmless but permitted. -/
def ChannelFaultResilientVerification
    {Channel : Type v}
    {History : Type w}
    {Observation : Type x}
    (channel : Channel → History → Observation)
    (selected : Channel → Prop)
    (claim : History → Prop)
    (budget : Nat) : Prop :=
  RobustlyVerifies channel selected claim
    (ChannelFaultAllowed budget)
    SurvivesChannelFault

/-- Epistemic connectivity at least `level`: every set of fewer than `level`
    distinct channel failures leaves the claim verifiable.

Level one means ordinary verification; level two tolerates any one channel
failure; level `k + 1` tolerates any `k` channel failures. -/
def ChannelConnectivityAtLeast
    {Channel : Type v}
    {History : Type w}
    {Observation : Type x}
    (channel : Channel → History → Observation)
    (selected : Channel → Prop)
    (claim : History → Prop)
    (level : Nat) : Prop :=
  RobustlyVerifies channel selected claim
    (fun failed : List Channel =>
      failed.Nodup ∧ failed.length < level)
    SurvivesChannelFault

/-- Higher channel connectivity implies every lower connectivity level. -/
theorem channelConnectivity_monotone
    {Channel : Type v}
    {History : Type w}
    {Observation : Type x}
    (channel : Channel → History → Observation)
    (selected : Channel → Prop)
    (claim : History → Prop)
    (smallLevel largeLevel : Nat)
    (levelIncluded : smallLevel ≤ largeLevel)
    (strong :
      ChannelConnectivityAtLeast
        channel selected claim largeLevel) :
    ChannelConnectivityAtLeast
      channel selected claim smallLevel := by
  intro failed allowedSmall
  exact strong failed
    ⟨allowedSmall.1,
      Nat.lt_of_lt_of_le allowedSmall.2 levelIncluded⟩

/-- Connectivity one already implies ordinary verification by choosing the
    empty fault set. -/
theorem channelConnectivity_one_implies_verification
    {Channel : Type v}
    {History : Type w}
    {Observation : Type x}
    (channel : Channel → History → Observation)
    (selected : Channel → Prop)
    (claim : History → Prop)
    (connected :
      ChannelConnectivityAtLeast channel selected claim 1) :
    ChannelSelectionVerifies channel selected claim := by
  have emptyFaultVerification :=
    connected ([] : List Channel) ⟨List.nodup_nil, by decide⟩
  intro left right sameEvidence
  apply emptyFaultVerification left right
  intro evidenceChannel liveSelected
  exact sameEvidence evidenceChannel liveSelected.1

/-- Individual-channel connectivity is characterized by live separator coverage
    under every bounded fault list. -/
theorem channelConnectivity_duality
    {Channel : Type v}
    {History : Type w}
    {Observation : Type x}
    (channel : Channel → History → Observation)
    (selected : Channel → Prop)
    (claim : History → Prop)
    (level : Nat) :
    ChannelConnectivityAtLeast channel selected claim level ↔
      RobustlyHitsEveryClaimDisagreement
        channel selected claim
        (fun failed : List Channel =>
          failed.Nodup ∧ failed.length < level)
        SurvivesChannelFault :=
  robust_evidence_cut_set_duality
    channel selected claim
    (fun failed : List Channel =>
      failed.Nodup ∧ failed.length < level)
    SurvivesChannelFault

/-- One channel survives a trust-domain failure when its provider domain is not
    compromised. Multiple channels in one failed domain disappear together. -/
def SurvivesTrustDomainFault
    {Domain : Type y}
    {Channel : Type v}
    (domain : Channel → Domain)
    (failedDomains : List Domain)
    (channel : Channel) : Prop :=
  domain channel ∉ failedDomains

/-- Trust-domain connectivity counts independent failure domains rather than
    raw evidence items. Replicating evidence inside one provider does not
    increase this connectivity level. -/
def TrustDomainConnectivityAtLeast
    {Domain : Type y}
    {Channel : Type v}
    {History : Type w}
    {Observation : Type x}
    (channel : Channel → History → Observation)
    (selected : Channel → Prop)
    (claim : History → Prop)
    (domain : Channel → Domain)
    (level : Nat) : Prop :=
  RobustlyVerifies channel selected claim
    (fun failedDomains : List Domain =>
      failedDomains.Nodup ∧ failedDomains.length < level)
    (SurvivesTrustDomainFault domain)

/-- Trust-domain connectivity has the same live-separator dual characterization,
    but correlated channels fail together through their shared domain map. -/
theorem trustDomainConnectivity_duality
    {Domain : Type y}
    {Channel : Type v}
    {History : Type w}
    {Observation : Type x}
    (channel : Channel → History → Observation)
    (selected : Channel → Prop)
    (claim : History → Prop)
    (domain : Channel → Domain)
    (level : Nat) :
    TrustDomainConnectivityAtLeast
        channel selected claim domain level ↔
      RobustlyHitsEveryClaimDisagreement
        channel selected claim
        (fun failedDomains : List Domain =>
          failedDomains.Nodup ∧ failedDomains.length < level)
        (SurvivesTrustDomainFault domain) :=
  robust_evidence_cut_set_duality
    channel selected claim
    (fun failedDomains : List Domain =>
      failedDomains.Nodup ∧ failedDomains.length < level)
    (SurvivesTrustDomainFault domain)

end LeanFinance.Epistemic
