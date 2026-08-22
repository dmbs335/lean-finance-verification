import LeanFinance.Epistemic.FiniteSynthesis

namespace LeanFinance.Epistemic

universe u v w

/-- The executable separator check is complete for an explicitly supplied
    separator witness. -/
theorem selectedSeparatesBool_complete
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    [DecidableEq Observation]
    (model : BoundedEvidenceModel History Channel Observation)
    (selected : List Channel)
    (left right : History)
    (separates : SelectedSeparates model selected left right) :
    selectedSeparatesBool model selected left right = true := by
  rcases separates with ⟨evidenceChannel, member, different⟩
  induction selected with
  | nil =>
      simp at member
  | cons head tail ih =>
      rcases List.mem_cons.mp member with equalHead | memberTail
      · subst evidenceChannel
        simp [selectedSeparatesBool, different]
      · by_cases headDifferent :
          model.observe head left ≠ model.observe head right
        · simp [selectedSeparatesBool, headDifferent]
        · have tailAccepted :
              selectedSeparatesBool model tail left right = true :=
            ih memberTail
          simpa [selectedSeparatesBool, headDifferent] using
            tailAccepted

/-- Pair checking is complete whenever equal claims or a separator witness is
    supplied. -/
theorem checkPair_complete
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    [DecidableEq Observation]
    (model : BoundedEvidenceModel History Channel Observation)
    (selected : List Channel)
    (left right : History)
    (valid :
      model.claim left = model.claim right ∨
        SelectedSeparates model selected left right) :
    checkPair model selected left right = true := by
  rcases valid with sameClaim | separates
  · simp [checkPair, sameClaim]
  · by_cases sameClaim : model.claim left = model.claim right
    · simp [checkPair, sameClaim]
    · simp [checkPair, sameClaim,
        selectedSeparatesBool_complete model selected left right separates]

/-- One finite row of the checker is complete relative to the semantic bounded
    verification premise. -/
theorem checkAgainst_complete
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    [DecidableEq Observation]
    (model : BoundedEvidenceModel History Channel Observation)
    (selected : List Channel)
    (left : History)
    (rights : List History)
    (valid :
      ∀ right,
        right ∈ rights →
          model.claim left ≠ model.claim right →
            SelectedSeparates model selected left right) :
    checkAgainst model selected left rights = true := by
  induction rights with
  | nil =>
      simp [checkAgainst]
  | cons head tail ih =>
      have headAccepted : checkPair model selected left head = true := by
        by_cases sameClaim : model.claim left = model.claim head
        · exact checkPair_complete model selected left head (Or.inl sameClaim)
        · exact checkPair_complete model selected left head
            (Or.inr (valid head (by simp) sameClaim))
      have tailAccepted : checkAgainst model selected left tail = true := by
        apply ih
        intro right member claimDifferent
        exact valid right (by simp [member]) claimDifferent
      simp [checkAgainst, headAccepted, tailAccepted]

/-- The complete finite checker accepts every semantically verifying bounded
    selection. -/
theorem checkRows_complete
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    [DecidableEq Observation]
    (model : BoundedEvidenceModel History Channel Observation)
    (selected : List Channel)
    (allHistories remaining : List History)
    (valid :
      ∀ left,
        left ∈ remaining →
          ∀ right,
            right ∈ allHistories →
              model.claim left ≠ model.claim right →
                SelectedSeparates model selected left right) :
    checkRows model selected allHistories remaining = true := by
  induction remaining with
  | nil =>
      simp [checkRows]
  | cons head tail ih =>
      have headAccepted :
          checkAgainst model selected head allHistories = true := by
        apply checkAgainst_complete
        intro right member claimDifferent
        exact valid head (by simp) right member claimDifferent
      have tailAccepted :
          checkRows model selected allHistories tail = true := by
        apply ih
        intro left member right rightMember claimDifferent
        exact valid left (by simp [member]) right rightMember claimDifferent
      simp [checkRows, headAccepted, tailAccepted]

/-- Boolean and semantic bounded verification coincide in the direction needed
    to validate externally synthesized candidates. -/
theorem boundedVerifiesBool_complete
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    [DecidableEq Observation]
    (model : BoundedEvidenceModel History Channel Observation)
    (selected : List Channel)
    (verified : BoundedSelectionVerifies model selected) :
    boundedVerifiesBool model selected = true := by
  apply checkRows_complete
  exact verified

end LeanFinance.Epistemic
