import LeanFinance.Epistemic.EpistemicConnectivity
import LeanFinance.Epistemic.FiniteSynthesisCompleteness

namespace LeanFinance.Epistemic

universe u v w x

/-- Remove every selected channel whose trust domain appears in one fault
    scenario. -/
def liveSelection
    {Channel : Type u}
    {Domain : Type v}
    [DecidableEq Domain]
    (domain : Channel → Domain)
    (failedDomains : List Domain)
    (selected : List Channel) : List Channel :=
  selected.filter (fun channel =>
    decide (domain channel ∉ failedDomains))

/-- Bounded verification under every explicitly enumerated trust-domain fault. -/
def BoundedRobustSelectionVerifies
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    {Domain : Type x}
    [DecidableEq Domain]
    (model : BoundedEvidenceModel History Channel Observation)
    (domain : Channel → Domain)
    (faults : List (List Domain))
    (selected : List Channel) : Prop :=
  ∀ failedDomains,
    failedDomains ∈ faults →
      BoundedSelectionVerifies model
        (liveSelection domain failedDomains selected)

/-- Executable checker for all listed trust-domain fault scenarios. -/
def boundedRobustVerifiesBool
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    {Domain : Type x}
    [DecidableEq Observation]
    [DecidableEq Domain]
    (model : BoundedEvidenceModel History Channel Observation)
    (domain : Channel → Domain)
    (selected : List Channel) :
    List (List Domain) → Bool
  | [] => true
  | failedDomains :: rest =>
      boundedVerifiesBool model
          (liveSelection domain failedDomains selected) &&
        boundedRobustVerifiesBool model domain selected rest

theorem boundedRobustVerifiesBool_sound
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    {Domain : Type x}
    [DecidableEq Observation]
    [DecidableEq Domain]
    (model : BoundedEvidenceModel History Channel Observation)
    (domain : Channel → Domain)
    (faults : List (List Domain))
    (selected : List Channel)
    (accepted :
      boundedRobustVerifiesBool model domain selected faults = true) :
    BoundedRobustSelectionVerifies
      model domain faults selected := by
  intro failedDomains member
  induction faults with
  | nil =>
      simp at member
  | cons head tail inductionHypothesis =>
      have acceptedParts :
          boundedVerifiesBool model
              (liveSelection domain head selected) = true ∧
            boundedRobustVerifiesBool
              model domain selected tail = true := by
        simpa [boundedRobustVerifiesBool] using accepted
      rcases List.mem_cons.mp member with equalHead | memberTail
      · subst failedDomains
        exact boundedVerifiesBool_sound model
          (liveSelection domain head selected)
          acceptedParts.1
      · exact inductionHypothesis acceptedParts.2 memberTail

theorem boundedRobustVerifiesBool_complete
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    {Domain : Type x}
    [DecidableEq Observation]
    [DecidableEq Domain]
    (model : BoundedEvidenceModel History Channel Observation)
    (domain : Channel → Domain)
    (faults : List (List Domain))
    (selected : List Channel)
    (verified :
      BoundedRobustSelectionVerifies
        model domain faults selected) :
    boundedRobustVerifiesBool model domain selected faults = true := by
  induction faults with
  | nil =>
      simp [boundedRobustVerifiesBool]
  | cons head tail inductionHypothesis =>
      have headVerified :
          BoundedSelectionVerifies model
            (liveSelection domain head selected) :=
        verified head (by simp)
      have tailVerified :
          BoundedRobustSelectionVerifies
            model domain tail selected := by
        intro failedDomains member
        exact verified failedDomains (by simp [member])
      have headAccepted :=
        boundedVerifiesBool_complete model
          (liveSelection domain head selected) headVerified
      have tailAccepted := inductionHypothesis tailVerified
      simp [boundedRobustVerifiesBool,
        headAccepted, tailAccepted]

/-- The finite fault list covers every fault admitted by one semantic fault
    predicate. -/
def FaultListComplete
    {Domain : Type x}
    (allowed : List Domain → Prop)
    (faults : List (List Domain)) : Prop :=
  ∀ failedDomains,
    allowed failedDomains →
      failedDomains ∈ faults

/-- A bounded robust checker result lifts to the abstract trust-domain fault
    semantics when histories and fault scenarios are complete. -/
theorem boundedRobust_semantically_sound
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    {Domain : Type x}
    [DecidableEq Domain]
    (model : BoundedEvidenceModel History Channel Observation)
    (domain : Channel → Domain)
    (faults : List (List Domain))
    (selected : List Channel)
    (allowed : List Domain → Prop)
    (historyComplete : ∀ history, history ∈ model.histories)
    (faultsComplete : FaultListComplete allowed faults)
    (verified :
      BoundedRobustSelectionVerifies
        model domain faults selected) :
    RobustlyVerifies
      model.observe
      (fun channel => channel ∈ selected)
      model.ClaimHolds
      allowed
      (SurvivesTrustDomainFault domain) := by
  intro failedDomains allowedFault
  have faultMember : failedDomains ∈ faults :=
    faultsComplete failedDomains allowedFault
  have boundedLive :
      BoundedSelectionVerifies model
        (liveSelection domain failedDomains selected) :=
    verified failedDomains faultMember
  have semanticLive :=
    bounded_verification_semantically_sound
      model
      (liveSelection domain failedDomains selected)
      historyComplete boundedLive
  intro left right sameEvidence
  apply semanticLive left right
  intro channel liveMember
  have selectedAndLive :
      channel ∈ selected ∧
        domain channel ∉ failedDomains := by
    simpa [liveSelection] using liveMember
  exact sameEvidence channel
    ⟨selectedAndLive.1, selectedAndLive.2⟩

/-- A proof-carrying minimum-cost robust portfolio over one explicit finite
    candidate language. -/
structure BoundedRobustSynthesisCertificate
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    {Domain : Type x}
    [DecidableEq Domain]
    (model : BoundedEvidenceModel History Channel Observation)
    (domain : Channel → Domain)
    (faults : List (List Domain))
    (Candidate : Type _)
    (decode : Candidate → List Channel)
    (selected : Candidate) where
  selectedVerifies :
    BoundedRobustSelectionVerifies
      model domain faults (decode selected)
  minimum :
    ∀ candidate,
      BoundedRobustSelectionVerifies
          model domain faults (decode candidate) →
        selectionCost model (decode selected) ≤
          selectionCost model (decode candidate)

namespace BoundedRobustSynthesisCertificate

theorem selectedCostMinimal
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    {Domain : Type x}
    [DecidableEq Domain]
    {model : BoundedEvidenceModel History Channel Observation}
    {domain : Channel → Domain}
    {faults : List (List Domain)}
    {Candidate : Type _}
    {decode : Candidate → List Channel}
    {selected : Candidate}
    (certificate :
      BoundedRobustSynthesisCertificate
        model domain faults Candidate decode selected)
    (candidate : Candidate)
    (candidateVerifies :
      BoundedRobustSelectionVerifies
        model domain faults (decode candidate)) :
    selectionCost model (decode selected) ≤
      selectionCost model (decode candidate) :=
  certificate.minimum candidate candidateVerifies

end BoundedRobustSynthesisCertificate

end LeanFinance.Epistemic
