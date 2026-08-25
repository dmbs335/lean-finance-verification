# Safe Support-Constrained Tree Policy Search

This layer is the deterministic finite-horizon foundation for a future MCTS-SPIBB planner. It combines three restrictions before an action can enter the search tree:

```text
safe under the declared runtime model
AND
(sufficient logged support OR exact baseline action)
```

Unsafe actions are never expanded. Safe but under-supported non-baseline actions are also excluded, even when their immediate reward lower bound is high. The baseline action is exempt from the support threshold so the controller remains total.

## Robust finite-horizon recursion

For each admissible action, the exact planner computes:

```text
Q_h(s, a)
= rewardLower(s, a)
  + discount × min_{s' in declared successors} V_{h-1}(s')
```

The minimum successor implements a finite ambiguity-set lower bound rather than an expected value over uncalibrated probabilities. The planner chooses the admissible action with the greatest exact rational lower value and uses a deterministic identifier tie-break.

## Controlled result

At a one-step horizon, `normal/increase` appears attractive and is supported:

```text
horizon 1 → increase
```

At horizons two and three, its stressed successor dominates the worst-case continuation, so the robust planner returns to the `hold` baseline:

```text
horizon 2 → hold
horizon 3 → hold
root lower value = 157/40
```

Two superficially attractive alternatives never enter the tree:

- `leverage`: safe in the declared local model but only 5 logged observations, below the minimum 50;
- `jump`: 100 observations and immediate reward 30, but explicitly unsafe because it reaches `ruin`.

The terminal `ruin/hold` baseline has zero logged support but remains admissible as the total fallback.

## Relationship to MCTS-SPIBB

This is exact finite dynamic programming, not stochastic Monte Carlo Tree Search. It establishes the action language, baseline restriction, robust backup, and certificates that an approximate MCTS implementation must preserve. A later MCTS layer may change how the tree is sampled, but it must produce a checkable certificate containing:

- every expanded state-action pair;
- support count and baseline identity;
- shield/safety acceptance;
- declared successor set;
- pessimistic backup value;
- root action and approximation residual.

## Assurance boundary

State/action sets, successor supports, lower rewards, support counts, discount factor, and baseline policy are controlled inputs. The module does not calibrate transition probabilities, prove confidence coverage, model market impact, or grant autonomous trading authority.
