# Formal Claims and Assurance Boundaries

Lean Finance Verification distinguishes four kinds of statements. They must not
be collapsed into one generic claim that a strategy or market model is
"proved."

## 1. Kernel-proved structural claims

Lean checks propositions derived from declared definitions and premises. Current
examples include:

- evidence cut-set duality;
- deterministic verification non-amplification;
- conservative workflow-refinement preservation;
- evidence-debt monotonicity;
- first-violation transition separation;
- trust-domain connectivity under declared failures;
- finite CEGIS soundness and optimality premises;
- evidence-adjusted score monotonicity;
- certifiability-to-allocation and crowding implications under nonnegative
  response parameters.

These theorems establish logical consequences of the model. They do not
calibrate the model or prove that its premises hold in a real market.

## 2. Exact bounded computations

Python generators and finite Lean checkers enumerate explicitly declared
histories, models, channels, portfolios, or failure scenarios. Within those
bounds they can establish:

- complete finite trace catalogs;
- exact minimum-cost evidence selections;
- constructive counterexamples for inadequate candidates;
- robust portfolios under enumerated trust-domain failures;
- clean-alpha recovery for known injected distortions;
- exact evidence-adjusted portfolio selection over a finite candidate set.

Exactness is relative to the supplied finite language. An unmodeled action,
provider failure, strategy, or distortion is outside the conclusion.

## 3. Externally verified evidence

Python and OpenSSL verify cryptographic and file-system facts such as hashes,
signatures, timestamp responses, Merkle paths, vendor manifests, schemas, row
counts, and public-key bindings. Lean receives normalized propositions or
artifact references after these checks.

The repository does not formally verify Python, OpenSSL, SHA-256, RSA, the host
operating system, or the experimental private-proof implementation.

## 4. Operational and empirical assumptions

The following remain assumptions unless independent evidence is supplied:

- complete capture of every real execution event;
- truth of vendor publication and revision metadata;
- actual independence of named trust domains;
- completeness of the adversarial workflow model;
- statistical identification of expected alpha;
- market calibration of allocator response, capacity, price impact, evidence
  debt, robustness reward, or dependency penalties;
- persistence of an economic edge after deployment.

## Reading certifiable alpha results

A certifiable-alpha interval means:

> under the declared history/model family and evidence map, the represented
> alpha lies within the stated controlled or assumed bounds.

It does **not** mean future return is guaranteed. In the fake-alpha benchmark,
clean alpha is known because distortions are synthetically injected. In a real
study, the lower and upper bounds would additionally require statistical,
market-impact, and model-uncertainty arguments.

## Reading the investment-law modules

The certifiability–crowding and epistemic-liquidation modules establish
structural mechanisms and falsifiable hypotheses:

```text
stronger evidence → allocator confidence → capital → crowding cost
shared evidence failure → synchronized withdrawal → market/funding contagion
```

Their controlled simulations show that these mechanisms are internally
coherent and machine-reproducible. They do not yet demonstrate that the effects
are priced, prevalent, or causal in observed financial markets.
