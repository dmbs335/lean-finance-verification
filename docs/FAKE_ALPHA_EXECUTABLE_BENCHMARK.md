# Executable Fake Alpha Benchmark

The controlled benchmark separates **synthetic distortion-free ground truth** from observed backtest alpha and asks which evidence architecture is sufficient to recover the clean ranking.

Seven experiments include a clean control plus future-information, survivorship, parameter-mining, cost-model, benchmark, and compound distortions. Each distortion contributes a declared number of basis points to the observed result. This ground truth is available only because the benchmark is synthetic.

For a selected evidence portfolio, the evaluator subtracts inflation from every distortion detected by at least one selected channel. Undetected inflation remains as the width of the controlled certifiable interval:

```text
lower endpoint = controlled synthetic ground truth
upper endpoint = observed alpha - detected inflation
```

The exact solver enumerates every channel subset. The checked-in instance finds a minimum cost of 7 using:

- `pitDataReceipt` for future information and survivorship bias;
- `searchLedger` for parameter mining;
- `evaluationContract` for cost and benchmark mutation.

The more expensive unified attestation also works at cost 8. Every lower-cost candidate carries the first experiment and unresolved distortion classes it fails to recover.

The compound attack has only 60 bps of controlled distortion-free alpha but 1,660 bps of observed alpha, making it the apparent winner. Complete evidence collapses every **synthetic benchmark interval** to its fixture point and restores the controlled ranking led by `cleanControl` at 250 bps.

## Semantic boundary

This collapse must not be interpreted as exact recovery of real economic expected alpha. In a real study, an observed estimate may be decomposed as:

```text
observed alpha
= economic alpha
+ research-process attack bias
+ risk-model bias
+ sampling noise
```

Evidence can remove attack bias only to the extent that the attack is observed and its magnitude is defensibly bounded. Even complete modeled attack-bias removal leaves economic alpha mixed with model bias and sampling noise. `LeanFinance/Alpha/EconomicDecomposition.lean` formalizes that boundary, while `LeanFinance/Alpha/Uncertainty.lean` carries residual model and deployment ranges.

This benchmark therefore tests a narrower claim: under known injected distortions, does the declared evidence architecture identify every integrity failure and recover the controlled synthetic ground truth? It does not estimate arbitrary real-market alpha or guarantee future profitability.
