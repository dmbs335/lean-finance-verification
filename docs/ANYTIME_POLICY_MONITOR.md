# Anytime Mixture E-Process Policy Monitor

A fixed confidence radius is unsafe when a policy is inspected repeatedly and promoted at the first favorable snapshot. This module replaces that governance input with an exact bounded mixture e-process.

For centered policy-improvement observations `X_t` satisfying the registered assumptions:

```text
-B ≤ X_t ≤ B
E[X_t | past] ≤ 0 under the null
```

each fixed betting fraction `0 ≤ λ ≤ 1` uses the nonnegative factor:

```text
1 + λ X_t / B
```

and wealth:

```text
E_t(λ) = product over i ≤ t of (1 + λ X_i / B)
```

A convex mixture of these component wealth processes is also an e-process under the same assumptions. The monitor inspects every prefix and records the first time the mixture reaches:

```text
1 / alpha
```

Under e-validity, Ville's inequality gives an anytime false-crossing probability at most `alpha`, including optional stopping. The executable layer performs every factor, product, mixture, maximum, and threshold comparison with exact rational arithmetic.

## Controlled result

The fixture uses `B=10`, `alpha=1/20`, equal mixture weights, and betting fractions `1/4`, `1/2`, and `3/4`. Eight controlled `+10` bps observations produce:

```text
first threshold crossing  observation 7
mixture at crossing       98467 / 4096 ≈ 24.04
final / maximum e-value   3917521 / 98304 ≈ 39.85
threshold                 20
```

The minimum-observation and risk gates also pass, so research authority advances one level:

```text
recommend → microAutonomy
```

A nonpositive sequence never crosses, an out-of-bound observation is rejected, invalid mixture weights are rejected, and model shift revokes authority.

## Formal boundary

Lean represents exact rational evidence values, proves threshold comparison is cross multiplication, and checks that an eligible certificate exposes the threshold, sample, risk, model-shift, and operational-breach gates. The executable checker proves exact replay of the declared finite sequence.

The measure-theoretic supermartingale and Ville-inequality proof is not yet formalized in Lean. Therefore the optional-stopping guarantee remains conditional on:

- the conditional null-mean assumption;
- predictable bets;
- checked bounded observations;
- authentic sequential outcome data.

The module does not establish profitability or grant live authority.
