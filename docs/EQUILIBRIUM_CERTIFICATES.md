# Finite Equilibrium Certificates

An external solver may search a finite approximation of a market game. The
formal verifier does not trust the solver's “equilibrium” label. It checks a
certificate containing:

- the proposed strategy profile;
- proof that each selected action belongs to the declared action set;
- proof that no player has a profitable admissible unilateral deviation.

`FiniteEquilibriumCertificate.sound` converts those obligations into a
`FiniteNashEquilibrium` theorem.

This separates search from trust:

```text
Python/Rust/SMT equilibrium search
  -> candidate profile and deviation witnesses
  -> Lean certificate construction
  -> kernel-checked finite Nash equilibrium
```

The result is only as broad as the declared finite action space. Discretization
error and omitted actions remain outside the theorem and must be represented as
separate approximation assumptions in later work.
