import LeanFinance.Backtest.Dataset

namespace LeanFinance.Certificate

structure DataCertificate where
  dataset : Backtest.Dataset
  hashBound : Backtest.DatasetHashBound dataset

end LeanFinance.Certificate
