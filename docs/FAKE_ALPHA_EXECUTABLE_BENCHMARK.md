# Executable Fake Alpha Benchmark

The controlled benchmark separates distortion-free alpha from observed backtest alpha and asks which evidence architecture is sufficient to recover the clean ranking.

Seven experiments include a clean control plus future-information, survivorship, parameter-mining, cost-model, benchmark, and compound distortions. Each distortion contributes a declared number of basis points to the observed result. This ground truth is available only because the benchmark is synthetic.

For a selected evidence portfolio, the evaluator subtracts inflation from every distortion detected by at least one selected channel. Undetected inflation remains as the width of the certifiable interval:

```text
lower endpoint = controlled clean alpha
upper endpoint = observed alpha - detected inflation
```

The exact solver enumerates every channel subset. The checked-in instance finds a minimum cost of 7 using:

- `pitDataReceipt` for future information and survivorship bias;
- `searchLedger` for parameter mining;
- `evaluationContract` for cost and benchmark mutation.

The more expensive unified attestation also works at cost 8. Every lower-cost candidate carries the first experiment and unresolved distortion classes it fails to recover.

The compound attack has only 60 bps of clean alpha but 1,660 bps of observed alpha, making it the apparent winner. Complete evidence collapses every interval to its clean point and restores the true ranking led by `cleanControl` at 250 bps.

This does not estimate alpha in an arbitrary real market. It tests a narrower claim: under known injected distortions, does the declared evidence architecture identify every integrity failure and recover the controlled ground truth?
