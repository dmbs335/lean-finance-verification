import LeanFinance.Epistemic.CutSet

namespace LeanFinance.Epistemic

universe u v

/-- Evidence for three local certificates and the two bindings that connect
    them into one research pipeline. -/
structure PipelineEvidence
    (DatasetEvidence DecisionEvidence ResultEvidence
      DataDecisionEvidence DecisionResultEvidence : Type u) where
  dataset : DatasetEvidence
  decision : DecisionEvidence
  result : ResultEvidence
  dataDecision : DataDecisionEvidence
  decisionResult : DecisionResultEvidence

/-- Combine local and bridge observations without discarding any component. -/
def pipelineObserve
    {History : Type v}
    {DatasetEvidence DecisionEvidence ResultEvidence
      DataDecisionEvidence DecisionResultEvidence : Type u}
    (datasetObserve : History → DatasetEvidence)
    (decisionObserve : History → DecisionEvidence)
    (resultObserve : History → ResultEvidence)
    (dataDecisionObserve : History → DataDecisionEvidence)
    (decisionResultObserve : History → DecisionResultEvidence)
    (history : History) :
    PipelineEvidence DatasetEvidence DecisionEvidence ResultEvidence
      DataDecisionEvidence DecisionResultEvidence :=
  { dataset := datasetObserve history
    decision := decisionObserve history
    result := resultObserve history
    dataDecision := dataDecisionObserve history
    decisionResult := decisionResultObserve history }

/-- Certificate Composition Law.

    Local verifiability is not enough by itself. When every local claim and each
    cross-certificate binding claim is verifiable from its own evidence, the
    combined evidence verifies the global conjunction. -/
theorem certificate_composition_law
    {History : Type v}
    {DatasetEvidence DecisionEvidence ResultEvidence
      DataDecisionEvidence DecisionResultEvidence : Type u}
    (datasetObserve : History → DatasetEvidence)
    (decisionObserve : History → DecisionEvidence)
    (resultObserve : History → ResultEvidence)
    (dataDecisionObserve : History → DataDecisionEvidence)
    (decisionResultObserve : History → DecisionResultEvidence)
    (datasetClaim decisionClaim resultClaim
      dataDecisionBound decisionResultBound : History → Prop)
    (datasetVerified : Verifiable datasetObserve datasetClaim)
    (decisionVerified : Verifiable decisionObserve decisionClaim)
    (resultVerified : Verifiable resultObserve resultClaim)
    (dataDecisionVerified :
      Verifiable dataDecisionObserve dataDecisionBound)
    (decisionResultVerified :
      Verifiable decisionResultObserve decisionResultBound) :
    Verifiable
      (pipelineObserve datasetObserve decisionObserve resultObserve
        dataDecisionObserve decisionResultObserve)
      (fun history =>
        datasetClaim history ∧
          decisionClaim history ∧
            resultClaim history ∧
              dataDecisionBound history ∧
                decisionResultBound history) := by
  intro left right sameEvidence
  unfold EvidenceEquivalent at sameEvidence
  have sameDataset : datasetObserve left = datasetObserve right :=
    congrArg (fun evidence => evidence.dataset) sameEvidence
  have sameDecision : decisionObserve left = decisionObserve right :=
    congrArg (fun evidence => evidence.decision) sameEvidence
  have sameResult : resultObserve left = resultObserve right :=
    congrArg (fun evidence => evidence.result) sameEvidence
  have sameDataDecision :
      dataDecisionObserve left = dataDecisionObserve right :=
    congrArg (fun evidence => evidence.dataDecision) sameEvidence
  have sameDecisionResult :
      decisionResultObserve left = decisionResultObserve right :=
    congrArg (fun evidence => evidence.decisionResult) sameEvidence
  have datasetIff := datasetVerified left right sameDataset
  have decisionIff := decisionVerified left right sameDecision
  have resultIff := resultVerified left right sameResult
  have dataDecisionIff :=
    dataDecisionVerified left right sameDataDecision
  have decisionResultIff :=
    decisionResultVerified left right sameDecisionResult
  constructor
  · intro leftClaims
    exact ⟨datasetIff.mp leftClaims.1,
      ⟨decisionIff.mp leftClaims.2.1,
        ⟨resultIff.mp leftClaims.2.2.1,
          ⟨dataDecisionIff.mp leftClaims.2.2.2.1,
            decisionResultIff.mp leftClaims.2.2.2.2⟩⟩⟩⟩
  · intro rightClaims
    exact ⟨datasetIff.mpr rightClaims.1,
      ⟨decisionIff.mpr rightClaims.2.1,
        ⟨resultIff.mpr rightClaims.2.2.1,
          ⟨dataDecisionIff.mpr rightClaims.2.2.2.1,
            decisionResultIff.mpr rightClaims.2.2.2.2⟩⟩⟩⟩

/-- Controlled worlds where every local certificate remains valid but the
    objects bound by those certificates can be substituted or relabeled. -/
inductive CompositionWorld where
  | matched
  | datasetSubstituted
  | resultRelabeled
  | bothSubstituted
  deriving Repr, DecidableEq

def datasetCertificateValid (_ : CompositionWorld) : Prop := True
def decisionCertificateValid (_ : CompositionWorld) : Prop := True
def resultCertificateValid (_ : CompositionWorld) : Prop := True

def dataDecisionBound : CompositionWorld → Prop
  | .matched | .resultRelabeled => True
  | .datasetSubstituted | .bothSubstituted => False

def decisionResultBound : CompositionWorld → Prop
  | .matched | .datasetSubstituted => True
  | .resultRelabeled | .bothSubstituted => False

def globalPipelineClaim (world : CompositionWorld) : Prop :=
  datasetCertificateValid world ∧
    decisionCertificateValid world ∧
      resultCertificateValid world ∧
        dataDecisionBound world ∧
          decisionResultBound world

theorem every_local_certificate_passes
    (world : CompositionWorld) :
    datasetCertificateValid world ∧
      decisionCertificateValid world ∧
        resultCertificateValid world := by
  simp [datasetCertificateValid, decisionCertificateValid,
    resultCertificateValid]

inductive LocalCertificateSummary where
  | allLocalValid
  deriving Repr, DecidableEq

def localSummaryObserve (_ : CompositionWorld) : LocalCertificateSummary :=
  .allLocalValid

/-- Matched and dataset-substituted worlds look identical to the local
    pass/fail summary while the global pipeline claim differs. -/
def localCertificatesCounterexample :
    VerificationCounterexample localSummaryObserve globalPipelineClaim :=
  { left := .matched
    right := .datasetSubstituted
    sameEvidence := rfl
    leftClaim := by
      simp [globalPipelineClaim, datasetCertificateValid,
        decisionCertificateValid, resultCertificateValid,
        dataDecisionBound, decisionResultBound]
    rightNotClaim := by
      simp [globalPipelineClaim, datasetCertificateValid,
        decisionCertificateValid, resultCertificateValid,
        dataDecisionBound, decisionResultBound] }

theorem local_certificates_do_not_compose_without_bindings :
    ¬ Verifiable localSummaryObserve globalPipelineClaim :=
  localCertificatesCounterexample.notVerifiable

inductive CompositionChannel where
  | localValiditySummary
  | dataDecisionBindingReceipt
  | decisionResultBindingReceipt
  | globalBundleBinding
  deriving Repr, DecidableEq

inductive CompositionObservation where
  | allLocalValid
  | bound
  | unbound
  deriving Repr, DecidableEq

def compositionObserve :
    CompositionChannel → CompositionWorld → CompositionObservation
  | .localValiditySummary, _ => .allLocalValid
  | .dataDecisionBindingReceipt, .matched => .bound
  | .dataDecisionBindingReceipt, .resultRelabeled => .bound
  | .dataDecisionBindingReceipt, _ => .unbound
  | .decisionResultBindingReceipt, .matched => .bound
  | .decisionResultBindingReceipt, .datasetSubstituted => .bound
  | .decisionResultBindingReceipt, _ => .unbound
  | .globalBundleBinding, .matched => .bound
  | .globalBundleBinding, _ => .unbound

def narrowBridgeSelection (channel : CompositionChannel) : Prop :=
  channel = .dataDecisionBindingReceipt ∨
    channel = .decisionResultBindingReceipt

def globalBundleSelection (channel : CompositionChannel) : Prop :=
  channel = .globalBundleBinding

/-- The two narrow bridge receipts jointly verify the global pipeline claim. -/
theorem narrow_bridge_receipts_verify_global_pipeline :
    ChannelSelectionVerifies compositionObserve
      narrowBridgeSelection globalPipelineClaim := by
  intro left right sameEvidence
  have sameDataDecision :
      compositionObserve .dataDecisionBindingReceipt left =
        compositionObserve .dataDecisionBindingReceipt right :=
    sameEvidence .dataDecisionBindingReceipt (by
      simp [narrowBridgeSelection])
  have sameDecisionResult :
      compositionObserve .decisionResultBindingReceipt left =
        compositionObserve .decisionResultBindingReceipt right :=
    sameEvidence .decisionResultBindingReceipt (by
      simp [narrowBridgeSelection])
  cases left <;> cases right <;>
    simp_all [compositionObserve, globalPipelineClaim,
      datasetCertificateValid, decisionCertificateValid,
      resultCertificateValid, dataDecisionBound, decisionResultBound]

/-- One integrated global bundle also verifies the claim, although the executable
    cost model can prefer the two narrower receipts. -/
theorem global_bundle_verifies_global_pipeline :
    ChannelSelectionVerifies compositionObserve
      globalBundleSelection globalPipelineClaim := by
  intro left right sameEvidence
  have sameBundle :
      compositionObserve .globalBundleBinding left =
        compositionObserve .globalBundleBinding right :=
    sameEvidence .globalBundleBinding (by
      simp [globalBundleSelection])
  cases left <;> cases right <;>
    simp_all [compositionObserve, globalPipelineClaim,
      datasetCertificateValid, decisionCertificateValid,
      resultCertificateValid, dataDecisionBound, decisionResultBound]

/-- The data→decision receipt alone cannot detect a result relabeling. -/
def dataReceiptCounterexample :
    VerificationCounterexample
      (fun world =>
        compositionObserve .dataDecisionBindingReceipt world)
      globalPipelineClaim :=
  { left := .matched
    right := .resultRelabeled
    sameEvidence := rfl
    leftClaim := by
      simp [globalPipelineClaim, datasetCertificateValid,
        decisionCertificateValid, resultCertificateValid,
        dataDecisionBound, decisionResultBound]
    rightNotClaim := by
      simp [globalPipelineClaim, datasetCertificateValid,
        decisionCertificateValid, resultCertificateValid,
        dataDecisionBound, decisionResultBound] }

/-- The decision→result receipt alone cannot detect a dataset substitution. -/
def resultReceiptCounterexample :
    VerificationCounterexample
      (fun world =>
        compositionObserve .decisionResultBindingReceipt world)
      globalPipelineClaim :=
  { left := .matched
    right := .datasetSubstituted
    sameEvidence := rfl
    leftClaim := by
      simp [globalPipelineClaim, datasetCertificateValid,
        decisionCertificateValid, resultCertificateValid,
        dataDecisionBound, decisionResultBound]
    rightNotClaim := by
      simp [globalPipelineClaim, datasetCertificateValid,
        decisionCertificateValid, resultCertificateValid,
        dataDecisionBound, decisionResultBound] }

theorem data_receipt_alone_is_insufficient :
    ¬ Verifiable
      (fun world =>
        compositionObserve .dataDecisionBindingReceipt world)
      globalPipelineClaim :=
  dataReceiptCounterexample.notVerifiable

theorem result_receipt_alone_is_insufficient :
    ¬ Verifiable
      (fun world =>
        compositionObserve .decisionResultBindingReceipt world)
      globalPipelineClaim :=
  resultReceiptCounterexample.notVerifiable

end LeanFinance.Epistemic
