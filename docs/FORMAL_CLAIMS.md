# Formal Claims and Assurance Boundaries

Lean Finance Verification distinguishes four kinds of statements. They must not be collapsed into one generic claim that a strategy, alpha estimate, market mechanism, or research agent is “proved.”

## 1. Kernel-proved structural claims

Lean checks propositions derived from declared definitions and premises. Current examples include:

- observational verifiability and evidence cut-set duality;
- deterministic verification non-amplification;
- no self-certified exploration completeness;
- conservative workflow-refinement preservation;
- evidence-debt monotonicity;
- first-violation transition separation;
- channel and trust-domain connectivity under declared failures;
- finite CEGIS soundness and convergence premises;
- multi-claim evidence composition;
- attack-bias removal leaving model and sampling error;
- evidence-adjusted score monotonicity under declared nonnegative penalties;
- confidence-to-allocation-to-crowding implications under nonnegative response parameters;
- logical separation of epistemic, capacity, and ecological alpha-death mechanisms;
- positive evidence shock and allocator sensitivity implying withdrawal and modeled impact;
- candidate advancement requiring verified integrity and a positive deployable lower bound;
- registered event-study gate propositions and required research-stage order.

These theorems establish logical consequences of the formal model. They do not calibrate the model or establish that its premises hold in a real market.

## 2. Exact bounded computations

Python generators and finite Lean checkers enumerate explicitly declared histories, models, channels, portfolios, candidates, or failure scenarios. Within those bounds they can establish:

- complete finite trace catalogs to a declared depth;
- exact separator hypergraphs and minimum-cost evidence selections;
- constructive counterexamples for inadequate candidates;
- exact evidence repairs over the declared channel language;
- robust portfolios under enumerated channel or trust-domain failures;
- trace-consistent action-semantics version spaces;
- clean synthetic-alpha recovery for known injected distortions;
- minimum evidence meeting a declared certifiable-alpha interval width;
- exact evidence-adjusted portfolio selection over a finite candidate set;
- deterministic crowding, liquidation, and funding-feedback scenarios;
- preregistered matched event-study acceptance under declared thresholds;
- fail-closed candidate decisions and bounded multi-analysis certificates.

Exactness is relative to the supplied finite language. An unmodeled action, provider failure, strategy, dependency, distortion, model, event pair, or candidate is outside the conclusion.

## 3. Externally verified evidence

Python and OpenSSL verify cryptographic and file-system facts such as:

- canonical hashes and domain-separated artifact identities;
- signatures and verifier-selected public keys;
- RFC 3161 request/response pairing, nonce, message imprint, certificate chain, and generation time;
- transparency-log membership and provider quorum;
- vendor manifests, paths, schemas, row counts, and file digests;
- Merkle membership and selective-disclosure receipts;
- experimental commitment and zero-opening proof transcripts.

Lean receives normalized propositions or artifact references after these checks. The repository does not formally verify Python, OpenSSL, SHA-256, RSA, the host operating system, or the experimental private-proof implementation.

## 4. Operational and empirical assumptions

The following remain assumptions unless independent evidence is supplied:

- complete capture of every real execution event;
- truth and lawful provenance of external market data;
- truth of vendor publication and revision metadata;
- actual independence of named providers or trust domains;
- completeness of the adversarial workflow, action, dependency, and failure languages;
- statistical identification of expected economic alpha;
- validity of factor models, sampling intervals, and distortion upper bounds;
- market calibration of allocator response, capacity, price impact, evidence debt, robustness reward, or dependency penalties;
- validity of event-study matching and parallel-trend assumptions;
- absence of unobserved confounding in real methodology-shock studies;
- persistence of an economic edge after deployment;
- human approval, legal review, and operational controls after machine gating.

## Reading the fake-alpha benchmark

The checked-in fake-alpha benchmark has a controlled **synthetic distortion-free ground truth**. Because every injected distortion amount is known, complete modeled detection can collapse the synthetic interval to that fixture point.

This does not mean real economic expected alpha has been identified. The formal economic decomposition is:

```text
observed alpha
= economic alpha
+ research-process attack bias
+ risk-model bias
+ sampling noise
```

After complete attack-bias removal:

```text
attack-cleaned alpha
= economic alpha
+ risk-model bias
+ sampling noise
```

A real alpha claim therefore still requires model, sampling, deployment-cost, and market-capacity arguments.

## Reading certifiable-alpha intervals

A certifiable-alpha interval means:

> under the declared history/model family, evidence map, distortion bounds, and deployment-cost range, the represented alpha lies within the stated controlled or assumed bounds.

It does **not** mean future return is guaranteed. Narrowing an interval by adding evidence removes only distinctions that the new evidence actually separates.

## Reading evidence-adjusted portfolio results

The portfolio solver is exact over its finite strategy set and declared objective. Its score can include certifiable lower alpha, conventional risk, evidence debt, robustness reward, and shared dependency concentration.

The supplied weights are governance inputs. The result does not establish that markets price these dimensions linearly, that one weighting is universally optimal, or that the input alpha and dependency estimates are correct.

## Reading certifiability–crowding results

The formal mechanism is conditional:

```text
stronger evidence confidence
+ allocator capital response
+ nonnegative impact response
→ weakly lower deployable alpha for fixed gross economic alpha
```

A zero-impact control shows that verification itself is not the destructive mechanism. Capacity death can coexist with a positive certifiable lower bound, while epistemic death concerns the inability to support a positive edge. Ecological decay requires the gross economic edge itself to change and is not estimated by the current fixed-edge simulator.

These modules do not yet demonstrate that certifiability shocks attract real capital or cause measured post-verification alpha decay.

## Reading epistemic-liquidation results

The liquidation model distinguishes:

- latent hidden epistemic crowding: low return correlation plus shared research-validity dependencies;
- realized hidden common risk: a shared dependency fails and both strategies withdraw.

The theorem proves the modeled withdrawal consequence under positive evidence loss and allocator sensitivity. It does not prove that all real allocators respond this way, that the dependency graph is complete, or that the impact function is calibrated.

## Reading event-study certificates

A controlled event-study certificate means registration, failed-domain exposure, conventional matching distance, pretrend tolerance, and aggregate event-effect thresholds all passed for the supplied finite pairs.

It does not establish external validity, real-world causal identification, truthful dependency labels, or absence of unobserved confounding.

## Reading research-agent decisions

The multi-analysis certificate binds registered inputs, six deterministic reports, and their gate results. The candidate policy can only:

```text
advanceToHumanReview
repairEvidence
rejectCandidate
```

Advancement is not investment approval. It proves only that the declared integrity obligations are covered and the supplied impact- and capacity-adjusted lower bound is positive. Autonomous deployment is intentionally outside the formal state space.
