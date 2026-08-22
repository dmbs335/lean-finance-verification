# Research-Integrity Attack Corpus and Symbolic Evidence Synthesis

The corpus contains 20 controlled research-manipulation scenarios across search, data, universe construction, evaluation, control-plane integrity, and external time. Each attack is represented by the causal boundary at which it occurs and the candidate channels capable of separating it from a relevant honest execution.

## Evidence-obligation compression

Technique names are not the primary taxonomy. Attacks with identical separator signatures form one epistemic class. The checked-in corpus compresses 20 techniques into 12 exact signatures spanning seven causal boundaries. Hidden parameter sweeps and failed-run deletion, for example, share an execution-boundary obligation even though their operational procedures differ.

## Branch-and-bound backend

The original exact solver enumerates every channel subset and is intentionally capped at 12 channels. `tools/symbolic_evidence` supports up to 30 channels and 120 attack obligations using integer bitsets and an exact branch-and-bound search:

1. choose one currently uncovered hyperedge;
2. branch on every channel capable of hitting it;
3. prune candidates exceeding the best known cost;
4. memoize the cheapest path to each covered-edge bitset;
5. retain a concrete selected separator for every attack.

Branching on an uncovered hyperedge is complete: every feasible hitting set must contain at least one of its separator channels. Python remains outside the formal trust boundary; the report carries per-attack coverage witnesses, and the Lean `CoverageCertificate` defines the independently checkable semantic contract.

In the fixture, one unified integrity attestation covers declaration, execution, data, universe, evaluation, and control-plane obligations. External-time attacks deliberately require either an independent transparency log or TSA anchor. The exact minimum therefore costs 10: the unified attestation plus one external-time channel.

The corpus is controlled and synthetic. It establishes the analysis pipeline and a reproducible epistemic taxonomy; it does not claim empirical prevalence estimates for the attack techniques.
