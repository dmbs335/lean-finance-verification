namespace LeanFinance.Alpha

/-- Capital may expand only when evidence-driven robust-value gain exceeds the
    incremental crowding burden. All values are controlled signed basis-point
    units; calibration remains external. -/
structure CertifiabilityCapitalCertificate where
  robustValueBefore : Int
  robustValueAfter : Int
  crowdingCostBefore : Int
  crowdingCostAfter : Int
  deriving Repr, DecidableEq

namespace CertifiabilityCapitalCertificate

def robustGain
    (certificate : CertifiabilityCapitalCertificate) : Int :=
  certificate.robustValueAfter - certificate.robustValueBefore

def crowdingCostIncrease
    (certificate : CertifiabilityCapitalCertificate) : Int :=
  certificate.crowdingCostAfter - certificate.crowdingCostBefore

def MayIncreaseCapital
    (certificate : CertifiabilityCapitalCertificate) : Prop :=
  certificate.crowdingCostIncrease < certificate.robustGain

/-- Evidence confidence alone never appears in the conclusion: capital expansion
    requires robust-value gain to dominate the additional crowding cost. -/
theorem capital_increase_requires_net_certifiability_gain
    (certificate : CertifiabilityCapitalCertificate)
    (allowed : certificate.MayIncreaseCapital) :
    certificate.crowdingCostAfter - certificate.crowdingCostBefore <
      certificate.robustValueAfter - certificate.robustValueBefore :=
  allowed

end CertifiabilityCapitalCertificate

end LeanFinance.Alpha
