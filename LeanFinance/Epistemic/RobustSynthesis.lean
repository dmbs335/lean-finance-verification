import LeanFinance.Epistemic.Connectivity
import LeanFinance.Epistemic.FiniteSynthesisCompleteness

namespace LeanFinance.Epistemic

universe u v w x y

/-- Robust verification restricted to an explicitly enumerated finite failure
    family. This is the semantic target of the executable robust checker. -/
def FailureRobustBoundedVerifiesOn
    {Failure : Type u}
    {History : Type v}
    {Channel : Type w}
    {Observation : Type x}
    (model : BoundedEvidenceModel History Channel Observation)
    (selected : List Channel)
    (failures : List Failure)
    (survives : Failure → Channel → Bool) : Prop :=
  ∀ failure,
    failure ∈ failures →
      BoundedSelectionVerifies model
        (survivingChannels selected survives failure)

/-- Check one selected evidence family against every declared failure. -/
def robustCheckFailures
    {Failure : Type u}
    {History : Type v}
    {Channel : Type w}
    {Observation : Type x}
    [DecidableEq Observation]
    (model : BoundedEvidenceModel History Channel Observation)
    (selected : List Channel)
    (survives : Failure → Channel → Bool) :
    List Failure → Bool
  | [] => true
  | failure :: rest =>
      boundedVerifiesBool model
          (survivingChannels selected survives failure) &&
        robustCheckFailures model selected survives rest

/-- Fully executable robust-verification checker for a finite failure list. -/
def robustBoundedVerifiesBool
    {Failure : Type u}
    {History : Type v}
    {Channel : Type w}
    {Observation : Type x}
    [DecidableEq Observation]
    (model : BoundedEvidenceModel History Channel Observation)
    (selected : List Channel)
    (failures : List Failure)
    (survives : Failure → Channel → Bool) : Bool :=
  robustCheckFailures model selected survives failures

/-- Acceptance of the finite robust checker implies semantic bounded
    verification after every listed failure. -/
theorem robustCheckFailures_sound
    {Failure : Type u}
    {History : Type v}
    {Channel : Type w}
    {Observation : Type x}
    [DecidableEq Observation]
    (model : BoundedEvidenceModel History Channel Observation)
    (selected : List Channel)
    (survives : Failure → Channel → Bool)
    (failures : List Failure)
    (accepted :
      robustCheckFailures model selected survives failures = true) :
    FailureRobustBoundedVerifiesOn
      model selected failures survives := by
  induction failures with
  | nil =>
      intro failure member
      simp at member
  | cons head tail ih =>
      have acceptedParts :
          boundedVerifiesBool model
              (survivingChannels selected survives head) = true ∧
            robustCheckFailures model selected survives tail = true := by
        simpa [robustCheckFailures] using accepted
      intro failure member
      rcases List.mem_cons.mp member with equalHead | memberTail
      · subst failure
        exact boundedVerifiesBool_sound model
          (survivingChannels selected survives head)
          acceptedParts.1
      · exact ih acceptedParts.2 failure memberTail

/-- The finite robust checker is complete for semantic bounded robust
    verification over the listed scenarios. -/
theorem robustCheckFailures_complete
    {Failure : Type u}
    {History : Type v}
    {Channel : Type w}
    {Observation : Type x}
    [DecidableEq Observation]
    (model : BoundedEvidenceModel History Channel Observation)
    (selected : List Channel)
    (survives : Failure → Channel → Bool)
    (failures : List Failure)
    (robust :
      FailureRobustBoundedVerifiesOn
        model selected failures survives) :
    robustCheckFailures model selected survives failures = true := by
  induction failures with
  | nil => rfl
  | cons head tail ih =>
      have headVerified :
          BoundedSelectionVerifies model
            (survivingChannels selected survives head) :=
        robust head (by simp)
      have headAccepted :
          boundedVerifiesBool model
              (survivingChannels selected survives head) = true :=
        boundedVerifiesBool_complete model
          (survivingChannels selected survives head)
          headVerified
      have tailRobust :
          FailureRobustBoundedVerifiesOn
            model selected tail survives := by
        intro failure member
        exact robust failure (by simp [member])
      have tailAccepted := ih tailRobust
      simp [robustCheckFailures, headAccepted, tailAccepted]

theorem robustBoundedVerifiesBool_sound
    {Failure : Type u}
    {History : Type v}
    {Channel : Type w}
    {Observation : Type x}
    [DecidableEq Observation]
    (model : BoundedEvidenceModel History Channel Observation)
    (selected : List Channel)
    (failures : List Failure)
    (survives : Failure → Channel → Bool)
    (accepted :
      robustBoundedVerifiesBool
        model selected failures survives = true) :
    FailureRobustBoundedVerifiesOn
      model selected failures survives :=
  robustCheckFailures_sound
    model selected survives failures accepted

theorem robustBoundedVerifiesBool_complete
    {Failure : Type u}
    {History : Type v}
    {Channel : Type w}
    {Observation : Type x}
    [DecidableEq Observation]
    (model : BoundedEvidenceModel History Channel Observation)
    (selected : List Channel)
    (failures : List Failure)
    (survives : Failure → Channel → Bool)
    (robust :
      FailureRobustBoundedVerifiesOn
        model selected failures survives) :
    robustBoundedVerifiesBool
      model selected failures survives = true :=
  robustCheckFailures_complete
    model selected survives failures robust

/-- A proof-carrying exact robust optimum over one complete finite candidate
    language and one declared finite failure family. -/
structure RobustEvidenceDebtCertificate
    {Failure : Type u}
    {History : Type v}
    {Channel : Type w}
    {Observation : Type x}
    (model : BoundedEvidenceModel History Channel Observation)
    (Candidate : Type y)
    (decode : Candidate → List Channel)
    (failures : List Failure)
    (survives : Failure → Channel → Bool) where
  selected : Candidate
  selectedRobust :
    FailureRobustBoundedVerifiesOn
      model (decode selected) failures survives
  minimal :
    ∀ candidate,
      FailureRobustBoundedVerifiesOn
          model (decode candidate) failures survives →
        selectionCost model (decode selected) ≤
          selectionCost model (decode candidate)

namespace RobustEvidenceDebtCertificate

/-- The exact robust certificate exposes its minimum selected cost. -/
def cost
    {Failure : Type u}
    {History : Type v}
    {Channel : Type w}
    {Observation : Type x}
    {Candidate : Type y}
    {model : BoundedEvidenceModel History Channel Observation}
    {decode : Candidate → List Channel}
    {failures : List Failure}
    {survives : Failure → Channel → Bool}
    (certificate :
      RobustEvidenceDebtCertificate
        model Candidate decode failures survives) : Nat :=
  selectionCost model (decode certificate.selected)

end RobustEvidenceDebtCertificate

/-- A complete failure list upgrades list-relative robustness to the full
    failure-family predicate. -/
theorem failure_list_complete_implies_full_robustness
    {Failure : Type u}
    {History : Type v}
    {Channel : Type w}
    {Observation : Type x}
    (model : BoundedEvidenceModel History Channel Observation)
    (selected : List Channel)
    (failures : List Failure)
    (survives : Failure → Channel → Bool)
    (failureComplete : ∀ failure, failure ∈ failures)
    (robust :
      FailureRobustBoundedVerifiesOn
        model selected failures survives) :
    FailureRobustBoundedVerifies model selected survives := by
  intro failure
  exact robust failure (failureComplete failure)

end LeanFinance.Epistemic
