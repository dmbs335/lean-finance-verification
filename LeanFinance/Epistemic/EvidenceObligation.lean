import LeanFinance.Epistemic.CutSet

namespace LeanFinance.Epistemic

universe u v w

/-- A selected channel family covers one attack history when it separates that
    attack from every designated honest history on which the claim truth value
    disagrees. -/
def CoversAttack
    {Channel : Type u}
    {History : Type v}
    {Observation : Type w}
    (channel : Channel → History → Observation)
    (selected : Channel → Prop)
    (claim : History → Prop)
    (honest : History → Prop)
    (attack : History) : Prop :=
  ∀ baseline,
    honest baseline →
      ¬ (claim baseline ↔ claim attack) →
        ∃ evidenceChannel,
          selected evidenceChannel ∧
            Separates channel evidenceChannel baseline attack

/-- Attack `stronger` evidence-subsumes attack `weaker` when every portfolio
    that covers the stronger obligation also covers the weaker one. -/
def EvidenceObligationSubsumes
    {Channel : Type u}
    {History : Type v}
    {Observation : Type w}
    (channel : Channel → History → Observation)
    (claim : History → Prop)
    (honest : History → Prop)
    (stronger weaker : History) : Prop :=
  ∀ selected,
    CoversAttack channel selected claim honest stronger →
      CoversAttack channel selected claim honest weaker

/-- Two attacks are epistemically equivalent when exactly the same selected
    channel families cover them relative to the declared honest histories. -/
def EvidenceObligationEquivalent
    {Channel : Type u}
    {History : Type v}
    {Observation : Type w}
    (channel : Channel → History → Observation)
    (claim : History → Prop)
    (honest : History → Prop)
    (left right : History) : Prop :=
  ∀ selected,
    CoversAttack channel selected claim honest left ↔
      CoversAttack channel selected claim honest right

/-- Obligation equivalence is exactly mutual subsumption. -/
theorem evidenceObligationEquivalent_iff_mutualSubsumption
    {Channel : Type u}
    {History : Type v}
    {Observation : Type w}
    (channel : Channel → History → Observation)
    (claim : History → Prop)
    (honest : History → Prop)
    (left right : History) :
    EvidenceObligationEquivalent channel claim honest left right ↔
      EvidenceObligationSubsumes channel claim honest left right ∧
        EvidenceObligationSubsumes channel claim honest right left := by
  constructor
  · intro equivalent
    constructor
    · intro selected coversLeft
      exact (equivalent selected).mp coversLeft
    · intro selected coversRight
      exact (equivalent selected).mpr coversRight
  · intro mutual selected
    exact ⟨mutual.1 selected, mutual.2 selected⟩

theorem evidenceObligationEquivalent_refl
    {Channel : Type u}
    {History : Type v}
    {Observation : Type w}
    (channel : Channel → History → Observation)
    (claim : History → Prop)
    (honest : History → Prop)
    (attack : History) :
    EvidenceObligationEquivalent channel claim honest attack attack := by
  intro selected
  exact Iff.rfl

theorem evidenceObligationEquivalent_symm
    {Channel : Type u}
    {History : Type v}
    {Observation : Type w}
    {channel : Channel → History → Observation}
    {claim : History → Prop}
    {honest : History → Prop}
    {left right : History}
    (equivalent :
      EvidenceObligationEquivalent channel claim honest left right) :
    EvidenceObligationEquivalent channel claim honest right left := by
  intro selected
  exact (equivalent selected).symm

theorem evidenceObligationEquivalent_trans
    {Channel : Type u}
    {History : Type v}
    {Observation : Type w}
    {channel : Channel → History → Observation}
    {claim : History → Prop}
    {honest : History → Prop}
    {first second third : History}
    (firstSecond :
      EvidenceObligationEquivalent channel claim honest first second)
    (secondThird :
      EvidenceObligationEquivalent channel claim honest second third) :
    EvidenceObligationEquivalent channel claim honest first third := by
  intro selected
  exact (firstSecond selected).trans (secondThird selected)

/-- Pointwise equality of separator signatures relative to every honest history.
    The claim-disagreement condition is included because attacks with different
    truth-value relations to the honest baseline do not induce the same
    verification obligation. -/
def SameSeparatorSignature
    {Channel : Type u}
    {History : Type v}
    {Observation : Type w}
    (channel : Channel → History → Observation)
    (claim : History → Prop)
    (honest : History → Prop)
    (left right : History) : Prop :=
  ∀ baseline,
    honest baseline →
      (¬ (claim baseline ↔ claim left) ↔
        ¬ (claim baseline ↔ claim right)) ∧
      ∀ evidenceChannel,
        Separates channel evidenceChannel baseline left ↔
          Separates channel evidenceChannel baseline right

/-- Equal separator signatures induce the same evidence obligation. -/
theorem sameSeparatorSignature_implies_obligationEquivalent
    {Channel : Type u}
    {History : Type v}
    {Observation : Type w}
    (channel : Channel → History → Observation)
    (claim : History → Prop)
    (honest : History → Prop)
    (left right : History)
    (sameSignature :
      SameSeparatorSignature channel claim honest left right) :
    EvidenceObligationEquivalent channel claim honest left right := by
  intro selected
  constructor
  · intro coversLeft baseline honestBaseline disagreementRight
    have signature := sameSignature baseline honestBaseline
    have disagreementLeft : ¬ (claim baseline ↔ claim left) :=
      signature.1.mpr disagreementRight
    rcases coversLeft baseline honestBaseline disagreementLeft with
      ⟨evidenceChannel, selectedChannel, separatesLeft⟩
    exact ⟨evidenceChannel, selectedChannel,
      (signature.2 evidenceChannel).mp separatesLeft⟩
  · intro coversRight baseline honestBaseline disagreementLeft
    have signature := sameSignature baseline honestBaseline
    have disagreementRight : ¬ (claim baseline ↔ claim right) :=
      signature.1.mp disagreementLeft
    rcases coversRight baseline honestBaseline disagreementRight with
      ⟨evidenceChannel, selectedChannel, separatesRight⟩
    exact ⟨evidenceChannel, selectedChannel,
      (signature.2 evidenceChannel).mpr separatesRight⟩

/-- A constructive witness that two attacks have different evidence
    obligations. -/
structure EvidenceObligationCounterexample
    {Channel : Type u}
    {History : Type v}
    {Observation : Type w}
    (channel : Channel → History → Observation)
    (claim : History → Prop)
    (honest : History → Prop)
    (left right : History) where
  selected : Channel → Prop
  coversLeft : CoversAttack channel selected claim honest left
  notCoversRight : ¬ CoversAttack channel selected claim honest right

namespace EvidenceObligationCounterexample

theorem notEquivalent
    {Channel : Type u}
    {History : Type v}
    {Observation : Type w}
    {channel : Channel → History → Observation}
    {claim : History → Prop}
    {honest : History → Prop}
    {left right : History}
    (counterexample :
      EvidenceObligationCounterexample
        channel claim honest left right) :
    ¬ EvidenceObligationEquivalent channel claim honest left right := by
  intro equivalent
  exact counterexample.notCoversRight
    ((equivalent counterexample.selected).mp
      counterexample.coversLeft)

end EvidenceObligationCounterexample

/-- A channel is necessary for one attack obligation when every covering
    selection contains it. -/
def RequiredChannelForAttack
    {Channel : Type u}
    {History : Type v}
    {Observation : Type w}
    (channel : Channel → History → Observation)
    (claim : History → Prop)
    (honest : History → Prop)
    (attack : History)
    (required : Channel) : Prop :=
  ∀ selected,
    CoversAttack channel selected claim honest attack →
      selected required

/-- One honest baseline with a unique separator establishes a necessary channel
    for the attack's complete evidence obligation. -/
theorem requiredChannel_of_uniqueHonestSeparator
    {Channel : Type u}
    {History : Type v}
    {Observation : Type w}
    (channel : Channel → History → Observation)
    (claim : History → Prop)
    (honest : History → Prop)
    (attack baseline : History)
    (required : Channel)
    (honestBaseline : honest baseline)
    (claimDifferent : ¬ (claim baseline ↔ claim attack))
    (unique :
      ∀ candidate,
        Separates channel candidate baseline attack →
          candidate = required) :
    RequiredChannelForAttack
      channel claim honest attack required := by
  intro selected covers
  rcases covers baseline honestBaseline claimDifferent with
    ⟨candidate, candidateSelected, separates⟩
  have candidateEq : candidate = required :=
    unique candidate separates
  cases candidateEq
  exact candidateSelected

/-- A new attack is epistemically novel relative to a finite catalog when it is
    obligation-inequivalent to every catalog entry. -/
def EvidenceNovelAgainst
    {Channel : Type u}
    {History : Type v}
    {Observation : Type w}
    (channel : Channel → History → Observation)
    (claim : History → Prop)
    (honest : History → Prop)
    (catalog : List History)
    (attack : History) : Prop :=
  ∀ known,
    known ∈ catalog →
      ¬ EvidenceObligationEquivalent
        channel claim honest known attack

end LeanFinance.Epistemic
