# Constraint-Driven Strategic Feedback

The local feedback model separates four quantities:

```text
external flow
  -> first price move       (price impact)
  -> induced forced flow    (constraint response)
  -> second price move      (price impact again)
```

The loop gain is

```text
priceImpact * forcedResponse
```

and the current local stability certificate requires this value to be below
one under nonnegative same-direction feedback.

The forced-flow module separately proves that when margin and VaR constraints
are both satisfied, mechanically forced order flow is exactly zero. This keeps
an economically important distinction explicit:

- information or discretionary flow may still exist;
- the formally classified *forced* component is absent.

The model is a local linearization, not a claim that real market crises are
globally linear. Nonlinear thresholds, cross-asset impact matrices, delayed
responses, and equilibrium-branch switches remain future extensions.
