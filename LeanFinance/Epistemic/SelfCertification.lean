import LeanFinance.Epistemic.CutSet

namespace LeanFinance.Epistemic

universe u v w

/-- A complete research history separates the public record, the trials the
    researcher declared, and the trials that were actually executed. -/
structure ResearchHistory (Public : Type u) (Trial : Type v) where
  publicRecord : Public
  declaredTrials : List Trial
  executedTrials : List Trial

/-- There are no hidden trials when every executed trial appears in the
    declared history. Declared-but-unexecuted trials are allowed. -/
def NoHiddenTrials
    {Public : Type u}
    {Trial : Type v}
    (history : ResearchHistory Public Trial) : Prop :=
  ∀ trial,
    trial ∈ history.executedTrials →
      trial ∈ history.declaredTrials

/-- Evidence produced solely by the researcher exposes the public record and
    declared history but not the actual execution log. -/
structure SelfCertifiedObservation (Public : Type u) (Trial : Type v) where
  publicRecord : Public
  declaredTrials : List Trial

def selfCertifiedObserve
    {Public : Type u}
    {Trial : Type v}
    (history : ResearchHistory Public Trial) :
    SelfCertifiedObservation Public Trial :=
  {
    publicRecord := history.publicRecord
    declaredTrials := history.declaredTrials
  }

/-- No self-certified completeness: for any possible hidden trial, the public
    self-report is compatible with both an honest history and a history that
    executed that trial without declaring it. -/
theorem no_self_certified_completeness
    {Public : Type u}
    {Trial : Type v}
    (publicRecord : Public)
    (hiddenTrial : Trial) :
    ¬ Verifiable
      (selfCertifiedObserve (Public := Public) (Trial := Trial))
      (NoHiddenTrials (Public := Public) (Trial := Trial)) := by
  let honest : ResearchHistory Public Trial :=
    {
      publicRecord := publicRecord
      declaredTrials := []
      executedTrials := []
    }
  let hidden : ResearchHistory Public Trial :=
    {
      publicRecord := publicRecord
      declaredTrials := []
      executedTrials := [hiddenTrial]
    }
  apply VerificationCounterexample.notVerifiable
  exact {
    left := honest
    right := hidden
    sameEvidence := rfl
    leftClaim := by
      intro trial executed
      simpa [honest] using executed
    rightNotClaim := by
      intro noHidden
      have executed : hiddenTrial ∈ hidden.executedTrials := by
        simp [hidden]
      have declared := noHidden hiddenTrial executed
      simpa [hidden] using declared
  }

/-- Hashing, canonical serialization, report generation, or proof generation
    over a self-certified record cannot close the hidden-trial gap. -/
theorem no_postprocess_can_self_certify_completeness
    {Public : Type u}
    {Trial : Type v}
    {Output : Type w}
    (publicRecord : Public)
    (hiddenTrial : Trial)
    (postprocess : SelfCertifiedObservation Public Trial → Output) :
    ¬ Verifiable
      (fun history => postprocess (selfCertifiedObserve history))
      (NoHiddenTrials (Public := Public) (Trial := Trial)) :=
  no_free_verification
    (selfCertifiedObserve (Public := Public) (Trial := Trial))
    postprocess
    (NoHiddenTrials (Public := Public) (Trial := Trial))
    (no_self_certified_completeness publicRecord hiddenTrial)

/-- An independent executor exposes both the declared and actual execution
    histories. -/
structure ExecutorObservation (Public : Type u) (Trial : Type v) where
  publicRecord : Public
  declaredTrials : List Trial
  executedTrials : List Trial

def executorObserve
    {Public : Type u}
    {Trial : Type v}
    (history : ResearchHistory Public Trial) :
    ExecutorObservation Public Trial :=
  {
    publicRecord := history.publicRecord
    declaredTrials := history.declaredTrials
    executedTrials := history.executedTrials
  }

/-- Once the execution log is independently observed, hidden-trial absence is
    verifiable. -/
theorem executor_observation_verifies_completeness
    {Public : Type u}
    {Trial : Type v} :
    Verifiable
      (executorObserve (Public := Public) (Trial := Trial))
      (NoHiddenTrials (Public := Public) (Trial := Trial)) := by
  intro left right sameEvidence
  have declaredEq : left.declaredTrials = right.declaredTrials :=
    congrArg
      (fun evidence : ExecutorObservation Public Trial =>
        evidence.declaredTrials)
      sameEvidence
  have executedEq : left.executedTrials = right.executedTrials :=
    congrArg
      (fun evidence : ExecutorObservation Public Trial =>
        evidence.executedTrials)
      sameEvidence
  constructor
  · intro leftComplete trial executedRight
    have executedLeft : trial ∈ left.executedTrials := by
      rw [executedEq]
      exact executedRight
    have declaredLeft := leftComplete trial executedLeft
    rw [declaredEq] at declaredLeft
    exact declaredLeft
  · intro rightComplete trial executedLeft
    have executedRight : trial ∈ right.executedTrials := by
      rw [← executedEq]
      exact executedLeft
    have declaredRight := rightComplete trial executedRight
    rw [← declaredEq] at declaredRight
    exact declaredRight

/-- Two semantically distinct evidence channels for exploration integrity. -/
inductive SearchChannel where
  | selfReport
  | executorLog
  deriving Repr, DecidableEq

inductive SearchObservation (Public : Type u) (Trial : Type v) where
  | selfReport (publicRecord : Public) (declaredTrials : List Trial)
  | executorLog (executedTrials : List Trial)

def searchChannel
    {Public : Type u}
    {Trial : Type v} :
    SearchChannel → ResearchHistory Public Trial →
      SearchObservation Public Trial
  | .selfReport, history =>
      .selfReport history.publicRecord history.declaredTrials
  | .executorLog, history =>
      .executorLog history.executedTrials

/-- Both channels together verify that every execution was declared. -/
theorem all_search_channels_verify_completeness
    {Public : Type u}
    {Trial : Type v} :
    ChannelSelectionVerifies
      (searchChannel (Public := Public) (Trial := Trial))
      (fun _ => True)
      (NoHiddenTrials (Public := Public) (Trial := Trial)) := by
  intro left right sameEvidence
  have selfEq :=
    sameEvidence SearchChannel.selfReport True.intro
  have executorEq :=
    sameEvidence SearchChannel.executorLog True.intro
  change
    SearchObservation.selfReport left.publicRecord left.declaredTrials =
      SearchObservation.selfReport right.publicRecord right.declaredTrials
    at selfEq
  injection selfEq with _publicEq declaredEq
  change
    SearchObservation.executorLog left.executedTrials =
      SearchObservation.executorLog right.executedTrials
    at executorEq
  injection executorEq with executedEq
  constructor
  · intro leftComplete trial executedRight
    have executedLeft : trial ∈ left.executedTrials := by
      rw [executedEq]
      exact executedRight
    have declaredLeft := leftComplete trial executedLeft
    rw [declaredEq] at declaredLeft
    exact declaredLeft
  · intro rightComplete trial executedLeft
    have executedRight : trial ∈ right.executedTrials := by
      rw [← executedEq]
      exact executedLeft
    have declaredRight := rightComplete trial executedRight
    rw [← declaredEq] at declaredRight
    exact declaredRight

/-- Any channel selection that verifies hidden-trial absence must include the
    independent executor log. -/
theorem executor_log_is_necessary
    {Public : Type u}
    {Trial : Type v}
    (publicRecord : Public)
    (hiddenTrial : Trial)
    (selected : SearchChannel → Prop)
    (verified :
      ChannelSelectionVerifies
        (searchChannel (Public := Public) (Trial := Trial))
        selected
        (NoHiddenTrials (Public := Public) (Trial := Trial))) :
    selected SearchChannel.executorLog := by
  let honest : ResearchHistory Public Trial :=
    {
      publicRecord := publicRecord
      declaredTrials := []
      executedTrials := []
    }
  let hidden : ResearchHistory Public Trial :=
    {
      publicRecord := publicRecord
      declaredTrials := []
      executedTrials := [hiddenTrial]
    }
  have honestClaim : NoHiddenTrials honest := by
    intro trial executed
    simpa [honest] using executed
  have hiddenNotClaim : ¬ NoHiddenTrials hidden := by
    intro noHidden
    have executed : hiddenTrial ∈ hidden.executedTrials := by
      simp [hidden]
    have declared := noHidden hiddenTrial executed
    simpa [hidden] using declared
  have disagreement :
      ¬ (NoHiddenTrials honest ↔ NoHiddenTrials hidden) := by
    intro sameClaim
    exact hiddenNotClaim (sameClaim.mp honestClaim)
  have hits :=
    (evidence_cut_set_duality
      (searchChannel (Public := Public) (Trial := Trial))
      selected
      (NoHiddenTrials (Public := Public) (Trial := Trial))).mp verified
  rcases hits honest hidden disagreement with
    ⟨candidate, chosen, separates⟩
  cases candidate with
  | selfReport =>
      exact False.elim (separates rfl)
  | executorLog =>
      exact chosen

/-- Any channel selection that verifies hidden-trial absence must also include
    the declared self-report. An execution log alone cannot reveal whether an
    executed trial was registered. -/
theorem self_report_is_necessary
    {Public : Type u}
    {Trial : Type v}
    (publicRecord : Public)
    (trial : Trial)
    (selected : SearchChannel → Prop)
    (verified :
      ChannelSelectionVerifies
        (searchChannel (Public := Public) (Trial := Trial))
        selected
        (NoHiddenTrials (Public := Public) (Trial := Trial))) :
    selected SearchChannel.selfReport := by
  let declared : ResearchHistory Public Trial :=
    {
      publicRecord := publicRecord
      declaredTrials := [trial]
      executedTrials := [trial]
    }
  let undeclared : ResearchHistory Public Trial :=
    {
      publicRecord := publicRecord
      declaredTrials := []
      executedTrials := [trial]
    }
  have declaredClaim : NoHiddenTrials declared := by
    intro candidate executed
    simpa [declared] using executed
  have undeclaredNotClaim : ¬ NoHiddenTrials undeclared := by
    intro noHidden
    have executed : trial ∈ undeclared.executedTrials := by
      simp [undeclared]
    have registered := noHidden trial executed
    simpa [undeclared] using registered
  have disagreement :
      ¬ (NoHiddenTrials declared ↔ NoHiddenTrials undeclared) := by
    intro sameClaim
    exact undeclaredNotClaim (sameClaim.mp declaredClaim)
  have hits :=
    (evidence_cut_set_duality
      (searchChannel (Public := Public) (Trial := Trial))
      selected
      (NoHiddenTrials (Public := Public) (Trial := Trial))).mp verified
  rcases hits declared undeclared disagreement with
    ⟨candidate, chosen, separates⟩
  cases candidate with
  | selfReport =>
      exact chosen
  | executorLog =>
      exact False.elim (separates rfl)

/-- In this model, the public declaration and the independent executor log are
    jointly sufficient and each is individually necessary: they form a genuine
    minimal evidence cut set. -/
theorem all_search_channels_form_minimal_cut_set
    {Public : Type u}
    {Trial : Type v}
    (publicRecord : Public)
    (trial : Trial) :
    IsMinimalCutSet
      (searchChannel (Public := Public) (Trial := Trial))
      (fun _ => True)
      (NoHiddenTrials (Public := Public) (Trial := Trial)) := by
  constructor
  · exact all_search_channels_verify_completeness
  · intro removed _selected
    intro remainingVerifies
    cases removed with
    | selfReport =>
        have required :=
          self_report_is_necessary
            publicRecord trial
            (fun channel =>
              True ∧ channel ≠ SearchChannel.selfReport)
            remainingVerifies
        exact required.2 rfl
    | executorLog =>
        have required :=
          executor_log_is_necessary
            publicRecord trial
            (fun channel =>
              True ∧ channel ≠ SearchChannel.executorLog)
            remainingVerifies
        exact required.2 rfl

end LeanFinance.Epistemic
