import LeanFinance.Backtest.IntegrityCertificate

namespace LeanFinance.Backtest

/-- External execution metadata supplied by an empirical adapter.

The adapter performs actual serialization, hashing, data collection, and
execution. Lean verifies that the resulting claims satisfy the declared
research-integrity contracts.
-/
structure AdapterExecutionRecord where
  claim : BacktestClaim
  certificate : ProofCarryingBacktestCertificate claim
  deriving Repr

/-- A valid adapter handoff must expose a certificate whose bound manifest
contains the emitted result artifact.
-/
def AdapterOutputValid
    (record : AdapterExecutionRecord) : Prop :=
  record.certificate.manifest.result.digest = record.claim.resultHash

/-- A successful adapter handoff exposes a proof object rather than an opaque
performance number.
-/
structure CertifiedAdapterOutput where
  record : AdapterExecutionRecord
  valid : AdapterOutputValid record

theorem adapter_preserves_result_binding
    (output : CertifiedAdapterOutput) :
    output.record.certificate.manifest.result.digest =
      output.record.claim.resultHash :=
  output.valid

end LeanFinance.Backtest
