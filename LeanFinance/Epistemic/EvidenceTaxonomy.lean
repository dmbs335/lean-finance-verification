import LeanFinance.Epistemic.FiniteSynthesis

namespace LeanFinance.Epistemic

universe u v w

/-- The evidence obligation of one attack relative to one trusted reference
    history: exactly the channels whose observations distinguish them. -/
def SeparatorSignatureAt
    {Channel : Type u}
    {History : Type v}
    {Observation : Type w}
    (channel : Channel → History → Observation)
    (reference attack : History) : Channel → Prop :=
  fun evidenceChannel =>
    Separates channel evidenceChannel reference attack

/-- Two attacks occupy the same epistemic class relative to a reference when
    every evidence channel distinguishes either both attacks or neither. -/
def SameSeparatorSignatureAt
    {Channel : Type u}
    {History : Type v}
    {Observation : Type w}
    (channel : Channel → History → Observation)
    (reference left right : History) : Prop :=
  ∀ evidenceChannel,
    SeparatorSignatureAt channel reference left evidenceChannel ↔
      SeparatorSignatureAt channel reference right evidenceChannel

/-- Signature inclusion. If every separator for `source` also separates
    `target`, then any evidence selection detecting `source` also detects
    `target`. Smaller signatures are therefore stricter evidence obligations. -/
def SeparatorSignatureIncludedAt
    {Channel : Type u}
    {History : Type v}
    {Observation : Type w}
    (channel : Channel → History → Observation)
    (reference source target : History) : Prop :=
  ∀ evidenceChannel,
    SeparatorSignatureAt channel reference source evidenceChannel →
      SeparatorSignatureAt channel reference target evidenceChannel

/-- One selected channel list detects an attack relative to one reference. -/
def SelectionSeparatesAt
    {Channel : Type u}
    {History : Type v}
    {Observation : Type w}
    (channel : Channel → History → Observation)
    (selected : List Channel)
    (reference attack : History) : Prop :=
  ∃ evidenceChannel,
    evidenceChannel ∈ selected ∧
      SeparatorSignatureAt channel reference attack evidenceChannel

/-- No currently selected channel observes the new attack distinction. -/
def BasisNovelAt
    {Channel : Type u}
    {History : Type v}
    {Observation : Type w}
    (channel : Channel → History → Observation)
    (selected : List Channel)
    (reference attack : History) : Prop :=
  ¬ SelectionSeparatesAt channel selected reference attack

/-- The new attack has no exact separator-signature match among known attacks. -/
def EpistemicallyNovelAt
    {Channel : Type u}
    {History : Type v}
    {Observation : Type w}
    (channel : Channel → History → Observation)
    (reference : History)
    (known : List History)
    (attack : History) : Prop :=
  ∀ previous,
    previous ∈ known →
      ¬ SameSeparatorSignatureAt channel reference previous attack

/-- A new attack introduces at least one separator channel that was irrelevant
    to every known attack in the supplied catalog. -/
def IntroducesUnseenSeparatorAt
    {Channel : Type u}
    {History : Type v}
    {Observation : Type w}
    (channel : Channel → History → Observation)
    (reference : History)
    (known : List History)
    (attack : History) : Prop :=
  ∃ evidenceChannel,
    SeparatorSignatureAt channel reference attack evidenceChannel ∧
      ∀ previous,
        previous ∈ known →
          ¬ SeparatorSignatureAt channel reference previous evidenceChannel

/-- Strong novelty: no existing exact class, no current-basis coverage, and at
    least one previously unseen separator boundary. -/
def NewObservationBoundaryAt
    {Channel : Type u}
    {History : Type v}
    {Observation : Type w}
    (channel : Channel → History → Observation)
    (selected : List Channel)
    (reference : History)
    (known : List History)
    (attack : History) : Prop :=
  EpistemicallyNovelAt channel reference known attack ∧
    BasisNovelAt channel selected reference attack ∧
    IntroducesUnseenSeparatorAt channel reference known attack

theorem sameSeparatorSignature_refl
    {Channel : Type u}
    {History : Type v}
    {Observation : Type w}
    (channel : Channel → History → Observation)
    (reference attack : History) :
    SameSeparatorSignatureAt channel reference attack attack := by
  intro evidenceChannel
  exact Iff.rfl

theorem sameSeparatorSignature_symm
    {Channel : Type u}
    {History : Type v}
    {Observation : Type w}
    {channel : Channel → History → Observation}
    {reference left right : History}
    (same : SameSeparatorSignatureAt channel reference left right) :
    SameSeparatorSignatureAt channel reference right left := by
  intro evidenceChannel
  exact (same evidenceChannel).symm

theorem sameSeparatorSignature_trans
    {Channel : Type u}
    {History : Type v}
    {Observation : Type w}
    {channel : Channel → History → Observation}
    {reference first second third : History}
    (firstSecond :
      SameSeparatorSignatureAt channel reference first second)
    (secondThird :
      SameSeparatorSignatureAt channel reference second third) :
    SameSeparatorSignatureAt channel reference first third := by
  intro evidenceChannel
  exact Iff.trans
    (firstSecond evidenceChannel)
    (secondThird evidenceChannel)

theorem signatureIncluded_refl
    {Channel : Type u}
    {History : Type v}
    {Observation : Type w}
    (channel : Channel → History → Observation)
    (reference attack : History) :
    SeparatorSignatureIncludedAt channel reference attack attack := by
  intro evidenceChannel separates
  exact separates

theorem signatureIncluded_trans
    {Channel : Type u}
    {History : Type v}
    {Observation : Type w}
    {channel : Channel → History → Observation}
    {reference first second third : History}
    (firstSecond :
      SeparatorSignatureIncludedAt channel reference first second)
    (secondThird :
      SeparatorSignatureIncludedAt channel reference second third) :
    SeparatorSignatureIncludedAt channel reference first third := by
  intro evidenceChannel separates
  exact secondThird evidenceChannel
    (firstSecond evidenceChannel separates)

theorem same_signature_iff_mutual_inclusion
    {Channel : Type u}
    {History : Type v}
    {Observation : Type w}
    (channel : Channel → History → Observation)
    (reference left right : History) :
    SameSeparatorSignatureAt channel reference left right ↔
      SeparatorSignatureIncludedAt channel reference left right ∧
        SeparatorSignatureIncludedAt channel reference right left := by
  constructor
  · intro same
    exact
      ⟨fun evidenceChannel separates =>
          (same evidenceChannel).mp separates,
        fun evidenceChannel separates =>
          (same evidenceChannel).mpr separates⟩
  · intro included evidenceChannel
    exact
      ⟨included.1 evidenceChannel,
        included.2 evidenceChannel⟩

/-- Exact epistemic equivalence transfers detection by every selected basis. -/
theorem same_signature_transfers_selection
    {Channel : Type u}
    {History : Type v}
    {Observation : Type w}
    {channel : Channel → History → Observation}
    {selected : List Channel}
    {reference left right : History}
    (same : SameSeparatorSignatureAt channel reference left right) :
    SelectionSeparatesAt channel selected reference left ↔
      SelectionSeparatesAt channel selected reference right := by
  constructor
  · rintro ⟨evidenceChannel, member, separates⟩
    exact
      ⟨evidenceChannel, member,
        (same evidenceChannel).mp separates⟩
  · rintro ⟨evidenceChannel, member, separates⟩
    exact
      ⟨evidenceChannel, member,
        (same evidenceChannel).mpr separates⟩

/-- Signature inclusion transfers detection in its declared direction. -/
theorem included_signature_transfers_selection
    {Channel : Type u}
    {History : Type v}
    {Observation : Type w}
    {channel : Channel → History → Observation}
    {selected : List Channel}
    {reference source target : History}
    (included :
      SeparatorSignatureIncludedAt channel reference source target)
    (sourceDetected :
      SelectionSeparatesAt channel selected reference source) :
    SelectionSeparatesAt channel selected reference target := by
  rcases sourceDetected with
    ⟨evidenceChannel, member, separates⟩
  exact
    ⟨evidenceChannel, member,
      included evidenceChannel separates⟩

/-- Exact signature equivalence also transfers basis novelty. -/
theorem same_signature_transfers_basis_novelty
    {Channel : Type u}
    {History : Type v}
    {Observation : Type w}
    {channel : Channel → History → Observation}
    {selected : List Channel}
    {reference left right : History}
    (same : SameSeparatorSignatureAt channel reference left right) :
    BasisNovelAt channel selected reference left ↔
      BasisNovelAt channel selected reference right := by
  unfold BasisNovelAt
  rw [same_signature_transfers_selection same]

end LeanFinance.Epistemic
