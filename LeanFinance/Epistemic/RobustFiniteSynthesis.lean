import LeanFinance.Epistemic.FiniteSynthesisCompleteness
import LeanFinance.Epistemic.Connectivity

namespace LeanFinance.Epistemic

universe u v w x y

/-- Finite fault semantics for an exact bounded evidence model. -/
structure BoundedFaultModel
    (Channel : Type u)
    (Fault : Type v) where
  faults : List Fault
  compromised : Fault → Channel → Bool
  faultRank : Fault → Nat

/-- Selected channels that survive one concrete fault. -/
def survivingSelection
    {Channel : Type u}
    {Fault : Type v}
    (faultModel : BoundedFaultModel Channel Fault)
    (fault : Fault)
    (selected : List Channel) : List Channel :=
  selected.filter (fun evidenceChannel =>
    !(faultModel.compromised fault evidenceChannel))

/-- Exact bounded verification under every listed fault whose rank is below the
requested connectivity level. -/
def RobustBoundedSelectionVerifies
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    {Fault : Type x}
    (model : BoundedEvidenceModel History Channel Observation)
    (faultModel : BoundedFaultModel Channel Fault)
    (selected : List Channel)
    (connectivity : Nat) : Prop :=
  ∀ fault,
    fault ∈ faultModel.faults →
      faultModel.faultRank fault < connectivity →
        BoundedSelectionVerifies
          model (survivingSelection faultModel fault selected)

/-- Boolean checker for one finite fault list. -/
def checkRobustFaults
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    {Fault : Type x}
    [DecidableEq Observation]
    (model : BoundedEvidenceModel History Channel Observation)
    (faultModel : BoundedFaultModel Channel Fault)
    (selected : List Channel)
    (connectivity : Nat) : List Fault → Bool
  | [] => true
  | fault :: rest =>
      (if faultModel.faultRank fault < connectivity then
        boundedVerifiesBool model
          (survivingSelection faultModel fault selected)
      else
        true) &&
      checkRobustFaults model faultModel selected connectivity rest

/-- Fully executable robust bounded verification checker. -/
def finiteFaultRobustBoundedVerifiesBool
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    {Fault : Type x}
    [DecidableEq Observation]
    (model : BoundedEvidenceModel History Channel Observation)
    (faultModel : BoundedFaultModel Channel Fault)
    (selected : List Channel)
    (connectivity : Nat) : Bool :=
  checkRobustFaults
    model faultModel selected connectivity faultModel.faults

theorem checkRobustFaults_sound
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    {Fault : Type x}
    [DecidableEq Observation]
    (model : BoundedEvidenceModel History Channel Observation)
    (faultModel : BoundedFaultModel Channel Fault)
    (selected : List Channel)
    (connectivity : Nat)
    (faults : List Fault)
    (accepted :
      checkRobustFaults
        model faultModel selected connectivity faults = true) :
    ∀ fault,
      fault ∈ faults →
        faultModel.faultRank fault < connectivity →
          BoundedSelectionVerifies
            model (survivingSelection faultModel fault selected) := by
  induction faults with
  | nil =>
      intro fault member
      simp at member
  | cons head tail ih =>
      have acceptedParts :
          (if faultModel.faultRank head < connectivity then
              boundedVerifiesBool model
                (survivingSelection faultModel head selected)
            else true) = true ∧
          checkRobustFaults
              model faultModel selected connectivity tail = true := by
        simpa [checkRobustFaults] using accepted
      intro fault member withinRank
      rcases List.mem_cons.mp member with equalHead | memberTail
      · subst fault
        have checkerAccepted :
            boundedVerifiesBool model
                (survivingSelection faultModel head selected) = true := by
          simpa [withinRank] using acceptedParts.1
        exact boundedVerifiesBool_sound
          model
          (survivingSelection faultModel head selected)
          checkerAccepted
      · exact ih acceptedParts.2 fault memberTail withinRank

/-- Checker acceptance implies robust semantic verification. -/
theorem finiteFaultRobustBoundedVerifiesBool_sound
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    {Fault : Type x}
    [DecidableEq Observation]
    (model : BoundedEvidenceModel History Channel Observation)
    (faultModel : BoundedFaultModel Channel Fault)
    (selected : List Channel)
    (connectivity : Nat)
    (accepted :
      finiteFaultRobustBoundedVerifiesBool
        model faultModel selected connectivity = true) :
    RobustBoundedSelectionVerifies
      model faultModel selected connectivity := by
  exact checkRobustFaults_sound
    model faultModel selected connectivity faultModel.faults accepted

theorem checkRobustFaults_complete
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    {Fault : Type x}
    [DecidableEq Observation]
    (model : BoundedEvidenceModel History Channel Observation)
    (faultModel : BoundedFaultModel Channel Fault)
    (selected : List Channel)
    (connectivity : Nat)
    (faults : List Fault)
    (verified :
      ∀ fault,
        fault ∈ faults →
          faultModel.faultRank fault < connectivity →
            BoundedSelectionVerifies
              model (survivingSelection faultModel fault selected)) :
    checkRobustFaults
      model faultModel selected connectivity faults = true := by
  induction faults with
  | nil =>
      rfl
  | cons head tail ih =>
      have tailAccepted :
          checkRobustFaults
            model faultModel selected connectivity tail = true := by
        apply ih
        intro fault member withinRank
        exact verified fault (by simp [member]) withinRank
      by_cases withinRank :
          faultModel.faultRank head < connectivity
      · have headAccepted :
            boundedVerifiesBool model
                (survivingSelection faultModel head selected) = true :=
          boundedVerifiesBool_complete
            model
            (survivingSelection faultModel head selected)
            (verified head (by simp) withinRank)
        simp [checkRobustFaults, withinRank,
          headAccepted, tailAccepted]
      · simp [checkRobustFaults, withinRank, tailAccepted]

/-- The finite checker is complete for the declared robust semantics. -/
theorem finiteFaultRobustBoundedVerifiesBool_complete
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    {Fault : Type x}
    [DecidableEq Observation]
    (model : BoundedEvidenceModel History Channel Observation)
    (faultModel : BoundedFaultModel Channel Fault)
    (selected : List Channel)
    (connectivity : Nat)
    (verified :
      RobustBoundedSelectionVerifies
        model faultModel selected connectivity) :
    finiteFaultRobustBoundedVerifiesBool
      model faultModel selected connectivity = true := by
  apply checkRobustFaults_complete
  exact verified

/-- Concrete witness that a selected design fails under one admitted fault. -/
structure RobustBoundedCounterexample
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    {Fault : Type x}
    (model : BoundedEvidenceModel History Channel Observation)
    (faultModel : BoundedFaultModel Channel Fault)
    (selected : List Channel)
    (connectivity : Nat) where
  fault : Fault
  faultMember : fault ∈ faultModel.faults
  withinRank : faultModel.faultRank fault < connectivity
  counterexample :
    BoundedCounterexample
      model (survivingSelection faultModel fault selected)

namespace RobustBoundedCounterexample

theorem notRobustlyVerifies
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    {Fault : Type x}
    {model : BoundedEvidenceModel History Channel Observation}
    {faultModel : BoundedFaultModel Channel Fault}
    {selected : List Channel}
    {connectivity : Nat}
    (counterexample :
      RobustBoundedCounterexample
        model faultModel selected connectivity) :
    ¬ RobustBoundedSelectionVerifies
      model faultModel selected connectivity := by
  intro verified
  exact counterexample.counterexample.notBoundedVerifies
    (verified counterexample.fault
      counterexample.faultMember counterexample.withinRank)

end RobustBoundedCounterexample

/-- Proof-carrying minimum-cost robust evidence design. -/
structure RobustSynthesisCertificate
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    {Fault : Type x}
    (model : BoundedEvidenceModel History Channel Observation)
    (faultModel : BoundedFaultModel Channel Fault)
    (Candidate : Type y)
    (decode : Candidate → List Channel)
    (selected : Candidate)
    (connectivity : Nat) where
  selectedVerifies :
    RobustBoundedSelectionVerifies
      model faultModel (decode selected) connectivity
  lowerCostCounterexample :
    ∀ candidate,
      selectionCost model (decode candidate) <
          selectionCost model (decode selected) →
        RobustBoundedCounterexample
          model faultModel (decode candidate) connectivity

namespace RobustSynthesisCertificate

theorem selectedCostLeOfRobustCandidate
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    {Fault : Type x}
    {Candidate : Type y}
    {model : BoundedEvidenceModel History Channel Observation}
    {faultModel : BoundedFaultModel Channel Fault}
    {decode : Candidate → List Channel}
    {selected : Candidate}
    {connectivity : Nat}
    (certificate :
      RobustSynthesisCertificate
        model faultModel Candidate decode selected connectivity)
    (candidate : Candidate)
    (candidateVerifies :
      RobustBoundedSelectionVerifies
        model faultModel (decode candidate) connectivity) :
    selectionCost model (decode selected) ≤
      selectionCost model (decode candidate) := by
  apply Nat.le_of_not_gt
  intro cheaper
  exact RobustBoundedCounterexample.notRobustlyVerifies
    (certificate.lowerCostCounterexample candidate cheaper)
    candidateVerifies

end RobustSynthesisCertificate

end LeanFinance.Epistemic
