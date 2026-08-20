import LeanFinance.Dynamics.StrategicFeedback

namespace LeanFinance.Certificate

open Dynamics

/-- Certifies the assumptions and local loop-gain inequality used to classify a
    strategic feedback state as stable. -/
structure FeedbackStabilityCertificate where
  system : StrategicFeedback
  priceImpactNonnegative : 0 <= system.priceImpact
  forcedResponseNonnegative : 0 <= system.forcedResponse
  stable : LocallyStable system

theorem FeedbackStabilityCertificate.sound
    (certificate : FeedbackStabilityCertificate) :
    LocallyStable certificate.system :=
  certificate.stable

theorem FeedbackStabilityCertificate.loopGainBelowOne
    (certificate : FeedbackStabilityCertificate) :
    loopGain certificate.system < 1 :=
  certificate.stable

end LeanFinance.Certificate
