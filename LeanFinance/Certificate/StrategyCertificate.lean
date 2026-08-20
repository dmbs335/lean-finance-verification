namespace LeanFinance.Certificate

/-- Identifies the exact strategy implementation and parameterization whose
    result is being certified. -/
structure StrategyCertificate where
  strategyId : String
  codeHash : String
  parameterHash : String
  strategyIdPresent : strategyId ≠ ""
  codeHashPresent : codeHash ≠ ""
  parameterHashPresent : parameterHash ≠ ""

end LeanFinance.Certificate
