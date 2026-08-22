import LeanFinance.Epistemic.WorkflowTransition
import LeanFinance.Epistemic.FiniteSynthesis

namespace LeanFinance.Epistemic

universe u v w x

/-- One counterexample-guided refinement round. The current selection is
    refuted by a concrete history pair, while the next selection separates that
    same pair. -/
structure CEGISRefinementRound
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    (model : BoundedEvidenceModel History Channel Observation) where
  before : List Channel
  after : List Channel
  counterexample : BoundedCounterexample model before
  resolved :
    SelectedSeparates model after
      counterexample.left counterexample.right

namespace CEGISRefinementRound

theorem beforeDoesNotVerify
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    {model : BoundedEvidenceModel History Channel Observation}
    (round : CEGISRefinementRound model) :
    ¬ BoundedSelectionVerifies model round.before :=
  round.counterexample.notBoundedVerifies

theorem nextSelectionResolvesCounterexample
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    {model : BoundedEvidenceModel History Channel Observation}
    (round : CEGISRefinementRound model) :
    SelectedSeparates model round.after
      round.counterexample.left round.counterexample.right :=
  round.resolved

end CEGISRefinementRound

/-- Consecutive refinement rounds form a connected chain from the initial
    deployed selection to the final synthesized selection. -/
def CEGISChain
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    {model : BoundedEvidenceModel History Channel Observation} :
    List Channel → List (CEGISRefinementRound model) → List Channel → Prop
  | current, [], finalSelection => current = finalSelection
  | current, round :: rest, finalSelection =>
      round.before = current ∧
        CEGISChain round.after rest finalSelection

/-- The chain proposition is executable whenever channel equality is
    executable. Proof fields inside a refinement round are irrelevant: the
    decision procedure only compares the public `before`/`after` channel lists
    and recursively checks adjacency. -/
instance instDecidableCEGISChain
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    [DecidableEq Channel]
    {model : BoundedEvidenceModel History Channel Observation}
    (current : List Channel)
    (rounds : List (CEGISRefinementRound model))
    (finalSelection : List Channel) :
    Decidable (CEGISChain current rounds finalSelection) := by
  induction rounds generalizing current with
  | nil =>
      simp only [CEGISChain]
      infer_instance
  | cons round rest ih =>
      simp only [CEGISChain]
      letI : Decidable (CEGISChain round.after rest finalSelection) :=
        ih round.after
      infer_instance

/-- A proof-carrying CEGIS transcript combines connected refinement rounds with
    an independently checked final verifier and optimality theorem. This
    interface accepts either explicit lower-cost counterexamples or exhaustive
    finite kernel computation as the final exact certificate. -/
structure ProofCarryingCEGIS
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    (model : BoundedEvidenceModel History Channel Observation)
    (Candidate : Type x)
    (decode : Candidate → List Channel)
    (selected : Candidate) where
  initial : List Channel
  rounds : List (CEGISRefinementRound model)
  connected : CEGISChain initial rounds (decode selected)
  historyComplete : ∀ history, history ∈ model.histories
  finalVerified : BoundedSelectionVerifies model (decode selected)
  finalOptimal :
    ∀ candidate,
      BoundedSelectionVerifies model (decode candidate) →
        selectionCost model (decode selected) ≤
          selectionCost model (decode candidate)

namespace ProofCarryingCEGIS

theorem finalSemanticallyVerifies
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    {Candidate : Type x}
    {model : BoundedEvidenceModel History Channel Observation}
    {decode : Candidate → List Channel}
    {selected : Candidate}
    (certificate : ProofCarryingCEGIS model Candidate decode selected) :
    ChannelSelectionVerifies
      model.observe
      (fun evidenceChannel => evidenceChannel ∈ decode selected)
      model.ClaimHolds :=
  bounded_verification_semantically_sound
    model (decode selected)
    certificate.historyComplete
    certificate.finalVerified

theorem finalCostMinimal
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    {Candidate : Type x}
    {model : BoundedEvidenceModel History Channel Observation}
    {decode : Candidate → List Channel}
    {selected : Candidate}
    (certificate : ProofCarryingCEGIS model Candidate decode selected)
    (candidate : Candidate)
    (candidateVerifies :
      BoundedSelectionVerifies model (decode candidate)) :
    selectionCost model (decode selected) ≤
      selectionCost model (decode candidate) :=
  certificate.finalOptimal candidate candidateVerifies

end ProofCarryingCEGIS

end LeanFinance.Epistemic
