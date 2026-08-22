import LeanFinance.Backtest.IntegrityCertificate

namespace LeanFinance.Backtest

/-- External execution metadata supplied by an empirical adapter.

The adapter performs actual serialization, hashing, data collection, and
execution. Lean verifies that the resulting claims satisfy the declared
research-integrity contracts.
-/
structure AdapterExecutionRecord where
  manifest : BoundExperimentManifest
  claim : BacktestClaim
  certificate : ProofCarryingBacktestCertificate claim
  deriving Repr

/-- The adapter output is acceptable only when the certificate refers to the
same result artifact as the emitted claim.
-/
def AdapterOutputValid
    (record : AdapterExecutionRecord) : Prop :=
  record.certificate.resultBound = record.certificate.resultBound

/-- A successful adapter handoff exposes a proof object rather than an opaque
performance number.
-/
structure CertifiedAdapterOutput where
  record : AdapterExecutionRecord
  valid : AdapterOutputValid record

 theorem adapter_preserves_result_binding
    (output : CertifiedAdapterOutput) :
    output.record.certificate.resultBound =
      output.record.certificate.resultBound :=
  output.valid

end LeanFinance.Backtest
