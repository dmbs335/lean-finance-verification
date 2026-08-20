import LeanFinance.StateSpace.Model

namespace LeanFinance.StateSpace

universe u

/-- Proof-carrying contract for a latent-state estimate. It certifies data
    timing, hashes, posterior normalization, and probability bounds, not whether
    the external statistical model is empirically correct. -/
structure StateEstimateCertificate
    {State : Type u}
    (estimate : StateEstimate State) where
  law : StructuralLawMetadata
  observations : List ObservedMarketSnapshot
  lawAdmissible : StructuralLawAdmissible estimate.asOf law
  observationsAdmissible :
    ∀ observation, observation ∈ observations →
      ObservationAdmissible estimate.asOf observation

theorem StateEstimateCertificate.observation_timestamp_ordered
    {State : Type u}
    {estimate : StateEstimate State}
    (certificate : StateEstimateCertificate estimate)
    (observation : ObservedMarketSnapshot)
    (used : observation ∈ certificate.observations) :
    observation.observedAt ≤ observation.availableAt :=
  (certificate.observationsAdmissible observation used).1

theorem StateEstimateCertificate.observation_available
    {State : Type u}
    {estimate : StateEstimate State}
    (certificate : StateEstimateCertificate estimate)
    (observation : ObservedMarketSnapshot)
    (used : observation ∈ certificate.observations) :
    observation.availableAt ≤ estimate.asOf :=
  (certificate.observationsAdmissible observation used).2.1

theorem StateEstimateCertificate.observation_hash_nonempty
    {State : Type u}
    {estimate : StateEstimate State}
    (certificate : StateEstimateCertificate estimate)
    (observation : ObservedMarketSnapshot)
    (used : observation ∈ certificate.observations) :
    NonEmptyString observation.contentHash :=
  (certificate.observationsAdmissible observation used).2.2

theorem StateEstimateCertificate.law_estimated_in_time
    {State : Type u}
    {estimate : StateEstimate State}
    (certificate : StateEstimateCertificate estimate) :
    certificate.law.estimatedAt ≤ estimate.asOf :=
  certificate.lawAdmissible.1

theorem StateEstimateCertificate.model_family_hash_nonempty
    {State : Type u}
    {estimate : StateEstimate State}
    (certificate : StateEstimateCertificate estimate) :
    NonEmptyString certificate.law.modelFamilyHash :=
  certificate.lawAdmissible.2.1

theorem StateEstimateCertificate.parameter_hash_nonempty
    {State : Type u}
    {estimate : StateEstimate State}
    (certificate : StateEstimateCertificate estimate) :
    NonEmptyString certificate.law.parameterHash :=
  certificate.lawAdmissible.2.2

theorem StateEstimateCertificate.posterior_normalized
    {State : Type u}
    {estimate : StateEstimate State}
    (certificate : StateEstimateCertificate estimate) :
    posteriorMass estimate.hypotheses = 10000 :=
  estimate.normalized

theorem StateEstimateCertificate.posterior_weight_valid
    {State : Type u}
    {estimate : StateEstimate State}
    (certificate : StateEstimateCertificate estimate)
    (hypothesis : WeightedState State)
    (member : hypothesis ∈ estimate.hypotheses) :
    ValidProbabilityBps hypothesis.weightBps :=
  estimate.weightsValid hypothesis member

end LeanFinance.StateSpace
