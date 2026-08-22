import LeanFinance.Epistemic.SelfCertification

namespace LeanFinance.Epistemic.BacktestCompleteness

/-- Concrete trial labels for a small proof-carrying backtest example. -/
inductive Trial where
  | declaredBaseline
  | hiddenParameterSweep
  deriving Repr, DecidableEq

structure PublicBacktestRecord where
  strategyId : String
  resultHash : String
  reportedMetric : Int
  deriving Repr, DecidableEq

def visibleBacktest : PublicBacktestRecord :=
  {
    strategyId := "momentum-v1"
    resultHash := "result-demo"
    reportedMetric := 42
  }

/-- A toy digest-like deterministic summary of the researcher's declaration.
    The theorem below applies equally to real hashes and generated proof terms. -/
def digestLikeSummary
    (evidence : SelfCertifiedObservation PublicBacktestRecord Trial) : Nat :=
  evidence.declaredTrials.length

/-- The final public bundle cannot certify that no hidden parameter sweep was
    executed, because an honest and selective history produce the same bundle. -/
theorem visible_bundle_cannot_certify_no_hidden_trials :
    ¬ Verifiable
      (selfCertifiedObserve
        (Public := PublicBacktestRecord) (Trial := Trial))
      (NoHiddenTrials
        (Public := PublicBacktestRecord) (Trial := Trial)) :=
  no_self_certified_completeness
    visibleBacktest Trial.hiddenParameterSweep

/-- Deterministic reduction to a digest-like value cannot repair the missing
    execution observation. -/
theorem digest_like_postprocess_cannot_certify_no_hidden_trials :
    ¬ Verifiable
      (fun history =>
        digestLikeSummary (selfCertifiedObserve history))
      (NoHiddenTrials
        (Public := PublicBacktestRecord) (Trial := Trial)) :=
  no_postprocess_can_self_certify_completeness
    visibleBacktest Trial.hiddenParameterSweep digestLikeSummary

/-- For this search-completeness claim, the declaration channel and an
    independently observed execution log are a mechanically proved minimal
    evidence design. -/
theorem backtest_completeness_minimal_evidence_cut_set :
    IsMinimalCutSet
      (searchChannel
        (Public := PublicBacktestRecord) (Trial := Trial))
      (fun _ => True)
      (NoHiddenTrials
        (Public := PublicBacktestRecord) (Trial := Trial)) :=
  all_search_channels_form_minimal_cut_set
    visibleBacktest Trial.hiddenParameterSweep

end LeanFinance.Epistemic.BacktestCompleteness
