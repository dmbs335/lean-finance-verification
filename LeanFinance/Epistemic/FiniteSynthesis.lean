import LeanFinance.Epistemic.CutSet

namespace LeanFinance.Epistemic

universe u v w x

/-- A finite history/channel projection used by the exact synthesis layer. The
    observation and claim functions remain semantic; the lists delimit the
    adversarial histories and channels explored by one bounded model. -/
structure BoundedEvidenceModel
    (History : Type u)
    (Channel : Type v)
    (Observation : Type w) where
  histories : List History
  channels : List Channel
  observe : Channel → History → Observation
  claim : History → Bool
  cost : Channel → Nat

/-- Proposition-valued interpretation of a Boolean bounded-model claim. -/
def BoundedEvidenceModel.ClaimHolds
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    (model : BoundedEvidenceModel History Channel Observation)
    (history : History) : Prop :=
  model.claim history = true

/-- One selected channel distinguishes a pair of histories. -/
def SelectedSeparates
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    (model : BoundedEvidenceModel History Channel Observation)
    (selected : List Channel)
    (left right : History) : Prop :=
  ∃ evidenceChannel,
    evidenceChannel ∈ selected ∧
      model.observe evidenceChannel left ≠
        model.observe evidenceChannel right

/-- Verification restricted to the explicitly enumerated adversarial histories. -/
def BoundedSelectionVerifies
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    (model : BoundedEvidenceModel History Channel Observation)
    (selected : List Channel) : Prop :=
  ∀ left,
    left ∈ model.histories →
      ∀ right,
        right ∈ model.histories →
          model.claim left ≠ model.claim right →
            SelectedSeparates model selected left right

/-- Executable separator test for one selected channel list. -/
def selectedSeparatesBool
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    [DecidableEq Observation]
    (model : BoundedEvidenceModel History Channel Observation)
    (selected : List Channel)
    (left right : History) : Bool :=
  selected.any (fun evidenceChannel =>
    decide
      (model.observe evidenceChannel left ≠
        model.observe evidenceChannel right))

theorem selectedSeparatesBool_sound
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    [DecidableEq Observation]
    (model : BoundedEvidenceModel History Channel Observation)
    (selected : List Channel)
    (left right : History)
    (accepted : selectedSeparatesBool model selected left right = true) :
    SelectedSeparates model selected left right := by
  induction selected with
  | nil =>
      simp [selectedSeparatesBool] at accepted
  | cons head tail ih =>
      by_cases headSeparates :
          model.observe head left ≠ model.observe head right
      · exact ⟨head, by simp, headSeparates⟩
      · have tailAccepted :
            selectedSeparatesBool model tail left right = true := by
          simpa [selectedSeparatesBool, headSeparates] using accepted
        rcases ih tailAccepted with
          ⟨evidenceChannel, member, separates⟩
        exact ⟨evidenceChannel, by simp [member], separates⟩

/-- One pair is accepted when either the claim agrees or the selected evidence
    contains a separator. -/
def checkPair
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    [DecidableEq Observation]
    (model : BoundedEvidenceModel History Channel Observation)
    (selected : List Channel)
    (left right : History) : Bool :=
  if model.claim left = model.claim right then
    true
  else
    selectedSeparatesBool model selected left right

theorem checkPair_sound
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    [DecidableEq Observation]
    (model : BoundedEvidenceModel History Channel Observation)
    (selected : List Channel)
    (left right : History)
    (accepted : checkPair model selected left right = true)
    (claimDifferent : model.claim left ≠ model.claim right) :
    SelectedSeparates model selected left right := by
  have separatorAccepted :
      selectedSeparatesBool model selected left right = true := by
    simpa [checkPair, claimDifferent] using accepted
  exact selectedSeparatesBool_sound
    model selected left right separatorAccepted

/-- Check one left history against a finite list of right histories. -/
def checkAgainst
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    [DecidableEq Observation]
    (model : BoundedEvidenceModel History Channel Observation)
    (selected : List Channel)
    (left : History) : List History → Bool
  | [] => true
  | right :: rest =>
      checkPair model selected left right &&
        checkAgainst model selected left rest

theorem checkAgainst_sound
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    [DecidableEq Observation]
    (model : BoundedEvidenceModel History Channel Observation)
    (selected : List Channel)
    (left : History)
    (rights : List History)
    (accepted : checkAgainst model selected left rights = true) :
    ∀ right,
      right ∈ rights →
        model.claim left ≠ model.claim right →
          SelectedSeparates model selected left right := by
  induction rights with
  | nil =>
      intro right member
      simp at member
  | cons head tail ih =>
      have acceptedParts :
          checkPair model selected left head = true ∧
            checkAgainst model selected left tail = true := by
        simpa [checkAgainst] using accepted
      intro right member claimDifferent
      rcases List.mem_cons.mp member with equalHead | memberTail
      · subst right
        exact checkPair_sound model selected left head
          acceptedParts.1 claimDifferent
      · exact ih acceptedParts.2 right memberTail claimDifferent

/-- Check every listed history against the complete finite history list. -/
def checkRows
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    [DecidableEq Observation]
    (model : BoundedEvidenceModel History Channel Observation)
    (selected : List Channel)
    (allHistories : List History) : List History → Bool
  | [] => true
  | left :: rest =>
      checkAgainst model selected left allHistories &&
        checkRows model selected allHistories rest

theorem checkRows_sound
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    [DecidableEq Observation]
    (model : BoundedEvidenceModel History Channel Observation)
    (selected : List Channel)
    (allHistories remaining : List History)
    (accepted : checkRows model selected allHistories remaining = true) :
    ∀ left,
      left ∈ remaining →
        ∀ right,
          right ∈ allHistories →
            model.claim left ≠ model.claim right →
              SelectedSeparates model selected left right := by
  induction remaining with
  | nil =>
      intro left member
      simp at member
  | cons head tail ih =>
      have acceptedParts :
          checkAgainst model selected head allHistories = true ∧
            checkRows model selected allHistories tail = true := by
        simpa [checkRows] using accepted
      intro left member
      rcases List.mem_cons.mp member with equalHead | memberTail
      · subst left
        exact checkAgainst_sound
          model selected head allHistories acceptedParts.1
      · exact ih acceptedParts.2 left memberTail

/-- Fully executable finite verification checker. -/
def boundedVerifiesBool
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    [DecidableEq Observation]
    (model : BoundedEvidenceModel History Channel Observation)
    (selected : List Channel) : Bool :=
  checkRows model selected model.histories model.histories

theorem boundedVerifiesBool_sound
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    [DecidableEq Observation]
    (model : BoundedEvidenceModel History Channel Observation)
    (selected : List Channel)
    (accepted : boundedVerifiesBool model selected = true) :
    BoundedSelectionVerifies model selected := by
  exact checkRows_sound model selected
    model.histories model.histories accepted

/-- If the bounded history list covers the complete history type, checker
    acceptance implies the unbounded semantic channel-verification statement. -/
theorem bounded_verification_semantically_sound
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    (model : BoundedEvidenceModel History Channel Observation)
    (selected : List Channel)
    (historyComplete : ∀ history, history ∈ model.histories)
    (verified : BoundedSelectionVerifies model selected) :
    ChannelSelectionVerifies
      model.observe
      (fun evidenceChannel => evidenceChannel ∈ selected)
      model.ClaimHolds := by
  intro left right sameEvidence
  by_cases sameClaim : model.claim left = model.claim right
  · rw [BoundedEvidenceModel.ClaimHolds,
      BoundedEvidenceModel.ClaimHolds, sameClaim]
  · rcases verified left (historyComplete left)
        right (historyComplete right) sameClaim with
      ⟨evidenceChannel, selectedChannel, separates⟩
    exact False.elim
      (separates (sameEvidence evidenceChannel selectedChannel))

/-- Exact scalar objective used by the generated bounded certificate. -/
def selectionCost
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    (model : BoundedEvidenceModel History Channel Observation) :
    List Channel → Nat
  | [] => 0
  | evidenceChannel :: rest =>
      model.cost evidenceChannel + selectionCost model rest

/-- A finite counterexample showing that a selected channel family misses one
    claim-disagreement separator edge. -/
structure BoundedCounterexample
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    (model : BoundedEvidenceModel History Channel Observation)
    (selected : List Channel) where
  left : History
  right : History
  leftMember : left ∈ model.histories
  rightMember : right ∈ model.histories
  claimDifferent : model.claim left ≠ model.claim right
  selectedAgree :
    ∀ evidenceChannel,
      evidenceChannel ∈ selected →
        model.observe evidenceChannel left =
          model.observe evidenceChannel right

namespace BoundedCounterexample

theorem notBoundedVerifies
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    {model : BoundedEvidenceModel History Channel Observation}
    {selected : List Channel}
    (counterexample : BoundedCounterexample model selected) :
    ¬ BoundedSelectionVerifies model selected := by
  intro verifies
  rcases verifies
      counterexample.left counterexample.leftMember
      counterexample.right counterexample.rightMember
      counterexample.claimDifferent with
    ⟨evidenceChannel, selectedChannel, separates⟩
  exact separates
    (counterexample.selectedAgree evidenceChannel selectedChannel)

theorem rejectsChecker
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    [DecidableEq Observation]
    {model : BoundedEvidenceModel History Channel Observation}
    {selected : List Channel}
    (counterexample : BoundedCounterexample model selected) :
    boundedVerifiesBool model selected ≠ true := by
  intro accepted
  exact counterexample.notBoundedVerifies
    (boundedVerifiesBool_sound model selected accepted)

end BoundedCounterexample

/-- A proof-carrying result from an external exact bounded synthesizer. Every
    lower-cost candidate is accompanied by a concrete missed disagreement pair. -/
structure BoundedSynthesisCertificate
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    (model : BoundedEvidenceModel History Channel Observation)
    (Candidate : Type x)
    (decode : Candidate → List Channel)
    (selected : Candidate) where
  historyComplete : ∀ history, history ∈ model.histories
  selectedVerifies : BoundedSelectionVerifies model (decode selected)
  lowerCostCounterexample :
    ∀ candidate,
      selectionCost model (decode candidate) <
          selectionCost model (decode selected) →
        BoundedCounterexample model (decode candidate)

namespace BoundedSynthesisCertificate

theorem selectedSemanticallyVerifies
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    {Candidate : Type x}
    {model : BoundedEvidenceModel History Channel Observation}
    {decode : Candidate → List Channel}
    {selected : Candidate}
    (certificate :
      BoundedSynthesisCertificate model Candidate decode selected) :
    ChannelSelectionVerifies
      model.observe
      (fun evidenceChannel =>
        evidenceChannel ∈ decode selected)
      model.ClaimHolds :=
  bounded_verification_semantically_sound
    model (decode selected)
    certificate.historyComplete
    certificate.selectedVerifies

theorem selectedCostLeOfCandidateVerifies
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    {Candidate : Type x}
    {model : BoundedEvidenceModel History Channel Observation}
    {decode : Candidate → List Channel}
    {selected : Candidate}
    (certificate :
      BoundedSynthesisCertificate model Candidate decode selected)
    (candidate : Candidate)
    (candidateVerifies :
      BoundedSelectionVerifies model (decode candidate)) :
    selectionCost model (decode selected) ≤
      selectionCost model (decode candidate) := by
  apply Nat.le_of_not_gt
  intro candidateCheaper
  exact
    (certificate.lowerCostCounterexample
      candidate candidateCheaper).notBoundedVerifies
      candidateVerifies

end BoundedSynthesisCertificate

end LeanFinance.Epistemic
