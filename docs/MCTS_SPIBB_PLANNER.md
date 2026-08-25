# Bounded MCTS-SPIBB Planner

The robust Bellman layer can solve a small finite belief graph exactly. A larger autonomous agent needs a bounded proposal search while retaining a trusted safety boundary. This module introduces a deliberately narrow MCTS-SPIBB contract.

## Expansion rule

An action can be expanded only when:

```text
safe(action)
and
(logged support count ≥ N_min or action = baseline)
```

At the uncertain root, `hold` and `query` are admissible. `increase` and `reduce` are safe in the controlled model but have fewer than 50 logged observations, so they are excluded before search.

## Search and exact gate

The planner runs 128 fixed-budget UCT simulations. The adversarial model for an action is selected from the exact robust Bellman report, and successor branches are visited in a deterministic weighted cycle. The remaining-horizon value is supplied by the exact robust Bellman solver.

MCTS proposes `query`. That proposal still has no authority by itself. The final trusted gate compares exact pessimistic values:

```text
baseline hold lower = 1
query lower         = 5/2
required margin     = 1
```

The query clears the registered margin and is selected. Raising the margin to 2 makes the same MCTS search propose `query`, but the exact gate returns `hold`. Removing query support or safety prevents it from entering the tree at all.

## Assurance boundary

This is a fixed-budget root search with an exact leaf oracle, not a proof of MCTS convergence. UCT floating-point scores are implementation details; final policy authority comes only from the exact robust lower-bound gate. Support counts, safety sets, rewards, transition branches, and model family remain controlled inputs.
