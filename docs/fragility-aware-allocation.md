# Fragility-aware allocation verification

This module formalizes the safety contract of a **70% strategic core + 30%
tactical sleeve** policy. It does not prove that the policy is optimal or
profitable.

## Policy table

The tactical sleeve is represented by ten units. One unit is 300 basis points
of total portfolio exposure.

| Trend | Low fragility | Medium fragility | High fragility |
|---|---:|---:|---:|
| Rising | 10 units | 8 units | 7 units |
| Mixed | 5 units | 4 units | 2 units |
| Falling | 0 units | 0 units | 0 units |

Volatility then caps the result at 10 units in a normal state, 8 units in an
elevated state, and 5 units in a stressed state. It is a position-size cap,
not an independent directional signal.

Buy, hold, and sell are derived by comparing current exposure with the certified
target:

- current exposure below target: buy;
- current exposure equal to target: hold;
- current exposure above target: sell.

## Machine-checked guarantees

Lean proves that:

- total exposure is always between 70% and 100%;
- tactical exposure never exceeds the 30% sleeve;
- weakening trend cannot increase exposure;
- worsening fragility cannot increase exposure;
- worsening volatility cannot increase exposure;
- a falling trend removes the tactical sleeve but retains the core;
- accepted certificates use source datasets and generated features available at
  the decision time;
- feature lineage directly names the source-data hash;
- the typed trend, fragility, and volatility values in the evidence bundle equal
  the values consumed by the policy;
- the certificate carries the exact policy strategy identifier and non-empty
  parameter and implementation hashes;
- a declared decision must equal the deterministic policy output;
- rebalance direction cannot disagree with current exposure versus the certified
  target.

The examples include negative controls for a forged 100% allocation under a 91%
policy state, a trend feature generated after the decision, mismatched typed
signal values, and an incorrect strategy identifier. All are rejected by
computation.

## Trusted empirical boundary

Lean verifies that the typed classifications carried by the certificate are the
ones used by the policy and that their source artifacts satisfy the declared
lineage contract. The empirical adapter still has to compute those
classifications correctly from the referenced feature artifacts. A future
serialization layer should bind canonical encoded feature outputs and their
hashes directly into the certificate.

## Explicit non-guarantees

The proof does not establish expected return, crash prediction accuracy,
calibration of trend or fragility classifiers, transaction-cost efficiency, or
superiority to buy-and-hold. Those are empirical claims and require a
point-in-time out-of-sample evaluation whose artifacts can later be bound to a
certificate.
