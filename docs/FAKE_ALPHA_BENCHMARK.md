# Fake Alpha Benchmark

This benchmark models the distinction between observed backtest alpha and alpha that survives declared research-integrity distortions.

Distortion classes:

- future information
- survivorship bias
- parameter mining
- cost-model mutation
- benchmark switching

The benchmark does not claim to identify all real-world alpha failures. It provides a controlled finite environment for testing whether an evidence architecture detects known integrity violations.

Target output:

```text
observed alpha
      |
      v
integrity checks
      |
      v
certifiable alpha range
```
