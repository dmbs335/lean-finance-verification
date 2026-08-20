# Higher-Order Beliefs

The formal core represents three belief levels carried by each player:

- `fundamentalExpectation`: B1, the player's own value expectation;
- `marketExpectation`: B2, the player's expectation of the market's view;
- `higherOrderExpectation`: B3, the represented expectation about higher-order
  market belief.

`CoordinationWeights.coordination` is a rational parameter `k` in `[0, 1]`.
The current finite beauty-contest signal is

```text
(1 - k) B1 + k (1 - k) B2 + k^2 B3.
```

This is a finite, auditable truncation rather than a claim that real belief
hierarchies end at B3. It has two machine-checked boundary properties:

1. at `k = 0`, the signal equals B1 and is independent of B2 and B3;
2. at `k = 1`, the signal equals B3 and is independent of B1 and B2.

The module therefore makes the role of strategic coordination explicit without
silently treating higher-order expectations as fundamentals.

The inverse-game identification layer also proves a related monotonicity result:
when a fine observation can be mapped back to a coarse observation, any target
already identified from the coarse observation remains identified under the
fine observation. More public information may distinguish additional states;
it cannot merge states that the coarser observation already separated.

Future work should replace the three-level truncation with recursive belief
objects, noisy private/public signals, common-knowledge operators, and global
-game threshold equilibria.
