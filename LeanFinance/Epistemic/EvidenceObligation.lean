import LeanFinance.Epistemic.CutSet
import LeanFinance.Epistemic.EvidenceDebt

namespace LeanFinance.Epistemic

universe u v w

/-- Two attacks have the same evidence obligation when every honest reference
history is separated from them by exactly the same evidence channels. -/
def SameSeparatorSignature
    {Channel : Type u}
    {History : Type v}
    {Observation : Type w}
    (channel : Channel → History → Observation)
    (honest : History → Prop)
    (leftAttack rightAttack : History) : Prop :=
  ∀ honestHistory,
    honest honestHistory →
      ∀ evidenceChannel,
        Separates channel evidenceChannel honestHistory leftAttack ↔
          Separates channel evidenceChannel honestHistory rightAttack

/-- One attack's evidence obligation is contained in another's when every
separator of the first attack also separates the second attack from the same
honest reference history. -/
def SeparatorSignatureSubsumedBy
    {Channel : Type u}
    {History : Type v}
    {Observation : Type w}
    (channel : Channel → History → Observation)
    (honest : History → Prop)
    (smallerAttack largerAttack : History) : Prop :=
  ∀ honestHistory,
    honest honestHistory →
      ∀ evidenceChannel,
        Separates channel evidenceChannel honestHistory smallerAttack →
          Separates channel evidenceChannel honestHistory largerAttack

/-- Separator-signature equality is reflexive. -/
theorem sameSeparatorSignature_refl
    {Channel : Type u}
    {History : Type v}
    {Observation : Type w}
    (channel : Channel → History → Observation)
    (honest : History → Prop)
    (attack : History) :
    SameSeparatorSignature channel honest attack attack := by
  intro honestHistory _ evidenceChannel
  exact Iff.rfl

/-- Separator-signature equality is symmetric. -/
theorem sameSeparatorSignature_symm
    {Channel : Type u}
    {History : Type v}
    {Observation : Type w}
    {channel : Channel → History → Observation}
    {honest : History → Prop}
    {leftAttack rightAttack : History}
    (same : SameSeparatorSignature
      channel honest leftAttack rightAttack) :
    SameSeparatorSignature channel honest rightAttack leftAttack := by
  intro honestHistory honestReference evidenceChannel
  exact (same honestHistory honestReference evidenceChannel).symm

/-- Separator-signature equality is transitive. -/
theorem sameSeparatorSignature_trans
    {Channel : Type u}
    {History : Type v}
    {Observation : Type w}
    {channel : Channel → History → Observation}
    {honest : History → Prop}
    {first second third : History}
    (firstSecond : SameSeparatorSignature channel honest first second)
    (secondThird : SameSeparatorSignature channel honest second third) :
    SameSeparatorSignature channel honest first third := by
  intro honestHistory honestReference evidenceChannel
  exact
    (firstSecond honestHistory honestReference evidenceChannel).trans
      (secondThird honestHistory honestReference evidenceChannel)

/-- Signature subsumption is reflexive. -/
theorem separatorSignatureSubsumedBy_refl
    {Channel : Type u}
    {History : Type v}
    {Observation : Type w}
    (channel : Channel → History → Observation)
    (honest : History → Prop)
    (attack : History) :
    SeparatorSignatureSubsumedBy channel honest attack attack := by
  intro honestHistory _ evidenceChannel separates
  exact separates

/-- Signature subsumption is transitive. -/
theorem separatorSignatureSubsumedBy_trans
    {Channel : Type u}
    {History : Type v}
    {Observation : Type w}
    {channel : Channel → History → Observation}
    {honest : History → Prop}
    {first second third : History}
    (firstSecond :
      SeparatorSignatureSubsumedBy channel honest first second)
    (secondThird :
      SeparatorSignatureSubsumedBy channel honest second third) :
    SeparatorSignatureSubsumedBy channel honest first third := by
  intro honestHistory honestReference evidenceChannel separates
  exact secondThird honestHistory honestReference evidenceChannel
    (firstSecond honestHistory honestReference evidenceChannel separates)

/-- Exact evidence-obligation equality is mutual signature subsumption. -/
theorem sameSeparatorSignature_iff_mutual_subsumption
    {Channel : Type u}
    {History : Type v}
    {Observation : Type w}
    (channel : Channel → History → Observation)
    (honest : History → Prop)
    (leftAttack rightAttack : History) :
    SameSeparatorSignature channel honest leftAttack rightAttack ↔
      SeparatorSignatureSubsumedBy
          channel honest leftAttack rightAttack ∧
        SeparatorSignatureSubsumedBy
          channel honest rightAttack leftAttack := by
  constructor
  · intro same
    constructor
    · intro honestHistory honestReference evidenceChannel separates
      exact
        (same honestHistory honestReference evidenceChannel).mp separates
    · intro honestHistory honestReference evidenceChannel separates
      exact
        (same honestHistory honestReference evidenceChannel).mpr separates
  · intro mutual honestHistory honestReference evidenceChannel
    constructor
    · exact mutual.1 honestHistory honestReference evidenceChannel
    · exact mutual.2 honestHistory honestReference evidenceChannel

/-- A set of previously known attacks is represented as a history predicate.
A new attack is epistemically novel when no known attack has the same separator
signature. -/
def EpistemicallyNovel
    {Channel : Type u}
    {History : Type v}
    {Observation : Type w}
    (channel : Channel → History → Observation)
    (honest knownAttack : History → Prop)
    (attack : History) : Prop :=
  ∀ prior,
    knownAttack prior →
      ¬ SameSeparatorSignature channel honest prior attack

/-- A new separator obligation is a channel that separates the new attack from
at least one honest history but separates no previously known attack from that
same honest history. -/
def IntroducesSeparatorObligation
    {Channel : Type u}
    {History : Type v}
    {Observation : Type w}
    (channel : Channel → History → Observation)
    (honest knownAttack : History → Prop)
    (attack : History)
    (evidenceChannel : Channel) : Prop :=
  ∃ honestHistory,
    honest honestHistory ∧
      Separates channel evidenceChannel honestHistory attack ∧
        ∀ prior,
          knownAttack prior →
            ¬ Separates channel evidenceChannel honestHistory prior

/-- Introducing one genuinely new separator obligation is sufficient to prove
that an attack does not belong to any previously known epistemic class. -/
theorem introduced_separator_implies_epistemic_novelty
    {Channel : Type u}
    {History : Type v}
    {Observation : Type w}
    (channel : Channel → History → Observation)
    (honest knownAttack : History → Prop)
    (attack : History)
    (evidenceChannel : Channel)
    (introduced :
      IntroducesSeparatorObligation
        channel honest knownAttack attack evidenceChannel) :
    EpistemicallyNovel channel honest knownAttack attack := by
  rcases introduced with
    ⟨honestHistory, honestReference, separatesAttack, separatesNoPrior⟩
  intro prior known same
  have separatesPrior :
      Separates channel evidenceChannel honestHistory prior :=
    (same honestHistory honestReference evidenceChannel).mpr separatesAttack
  exact separatesNoPrior prior known separatesPrior

/-- The marginal evidence debt of a model refinement. Positive values represent
additional verification obligation; zero means the new histories are covered
without increasing the minimum cost under the supplied channel language. -/
def MarginalEvidenceDebt (oldDebt refinedDebt : Nat) : Nat :=
  refinedDebt - oldDebt

/-- Strict evidence-debt growth produces a positive marginal obligation. -/
theorem marginalEvidenceDebt_positive
    {oldDebt refinedDebt : Nat}
    (increased : oldDebt < refinedDebt) :
    0 < MarginalEvidenceDebt oldDebt refinedDebt := by
  unfold MarginalEvidenceDebt
  exact Nat.sub_pos_iff_lt.mpr increased

/-- If evidence debt does not increase, the marginal obligation is zero. -/
theorem marginalEvidenceDebt_zero_of_not_increased
    {oldDebt refinedDebt : Nat}
    (notIncreased : refinedDebt ≤ oldDebt) :
    MarginalEvidenceDebt oldDebt refinedDebt = 0 := by
  unfold MarginalEvidenceDebt
  exact Nat.sub_eq_zero_of_le notIncreased

end LeanFinance.Epistemic
