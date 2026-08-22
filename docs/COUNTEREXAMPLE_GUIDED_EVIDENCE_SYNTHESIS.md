# Counterexample-Guided Evidence Synthesis

The exact cut-set synthesizer assumes that complete adversarial histories have already
been enumerated. `tools/workflow_cegis` generates those histories from executable
workflow semantics and closes the loop between attack discovery and evidence design:

```text
finite workflow transition system
        ↓
all terminal traces up to a declared depth
        ↓
current evidence equivalence classes
        ↓
claim-disagreement counterexample oracle
        ↓
exact minimum-cost repair master
        ↓
new observation constraint
        ↺
proof-carrying final repair
```

The result is a bounded form of counterexample-guided inductive synthesis. The master
chooses the cheapest repair satisfying all counterexamples discovered so far. The
oracle searches the complete bounded history catalog for another pair with different
claim values but equal selected evidence. The loop terminates with either an exact
repair or a concrete unresolved evidence gap.

## Finite workflow language

Version 1 uses finite Boolean state. A model declares:

- Boolean state variables and initial values;
- deterministic actions with Boolean guards and simultaneous assignments;
- an explicit occurrence bound for every action;
- a terminal-state predicate;
- a Boolean integrity claim on terminal states;
- already-deployed evidence channels;
- optional channels and sensor templates;
- operational, privacy, and external-trust costs.

The Python explorer performs breadth-first trace generation up to `max_depth` and does
not extend terminal traces. Every action must change state. `max_histories` prevents an
accidentally explosive model from silently consuming unbounded resources.

The generated Lean workflow contains the same enablement rule, including each action's
occurrence bound. Lean then computes its own terminal trace catalog and proves:

```lean
generatedTraces = enumerateTerminalTraces workflow maxDepth
```

Thus the Python history list is not accepted as an arbitrary oracle output.

## Evidence channels and templates

A channel projects one terminal history into:

```json
{
  "actions": ["visible", "events", "in-order"],
  "state": [true, false]
}
```

Action sensor templates are instantiated once for every matching action tag. State
sensor templates are instantiated once for every listed state variable. The expanded
channel language is capped at 12 channels so every repair subset can be enumerated
exactly.

A cryptographic channel can authenticate a visible record without observing hidden
actions. For example, a correct RFC 3161 timestamp over a researcher-visible ledger has
the same observation in an honest execution and in a history that ran an unreported
sweep outside that ledger.

## Exact CEGIS algorithm

Let `M` be the channels already deployed and `O` the optional repair channels.

Each iteration executes:

1. **Master:** enumerate every subset of `O` and choose the minimum incremental-cost
   repair satisfying all discovered separator constraints; `M` is mandatory in every
   candidate.
2. **Oracle:** search every claim-disagreement pair in the bounded terminal history
   catalog and return the most atomic uncovered pair. Pairs with fewer separators are
   preferred, then a deterministic lexical order is used.
3. **Refinement:** add that pair's separator hyperedge to the master and repeat.

The final candidate is checked against every bounded disagreement pair and compared to
an independent exact repair synthesis. A mismatch is treated as an implementation
error.

If the channel language cannot separate a pair, the report returns the traces and
primitive differences that a future channel would have to observe:

- action receipts for differing action projections;
- state attestations for differing terminal bits.

This is a model-refinement request, not a claim that such a trustworthy sensor already
exists.

## Search-integrity example

The checked-in model contains six workflow actions:

```text
declareBaseline
executeBaseline
executeHiddenSweep
readFutureData
publishResult
anchorLedger
```

The transition system automatically generates ten terminal histories, including both
orders of the composed hidden-sweep/future-data attack. Five representative aliases
are provided only to make the output readable:

```text
honest
undeclaredBaseline
hiddenSweep
futureLeak
dualAttack
```

The initial deployment is:

```text
selfReport
resultBundle
rfc3161Anchor
```

The CEGIS transcript is:

```text
round 0
  counterexample: honest ↔ futureLeak
  repair: targetedReceipt_readFutureData

round 1
  counterexample: honest ↔ hiddenSweep
  repair: targetedReceipt_executeHiddenSweep

round 2
  no bounded counterexample remains
```

The optional repair language also contains a privacy-heavier `fullExecutorLog`.
Exact repair synthesis finds:

```text
minimum incremental repair
  targetedReceipt_executeHiddenSweep
  targetedReceipt_readFutureData

weighted incremental cost
  4

full executor log cost
  6
```

The global, greenfield optimum is:

```text
selfReport
+ both targeted receipts
```

Under this claim, `resultBundle` and `rfc3161Anchor` are globally redundant. They still
protect other properties—artifact integrity and existence time—but do not distinguish
omitted execution or future-data access.

## Proof-carrying transcript

`LeanFinance/Epistemic/WorkflowTransition.lean` defines the executable transition
semantics.

`LeanFinance/Epistemic/CounterexampleGuided.lean` defines:

- `CEGISRefinementRound`, containing a concrete counterexample for the current
  selection and proof that the next selection separates it;
- `CEGISChain`, connecting the deployed baseline through every repair round;
- `ProofCarryingCEGIS`, combining the connected transcript with an independently
  checked final verifier and cost-optimality theorem.

`FiniteSynthesisCompleteness.lean` proves the converse direction needed for exact
kernel search: every semantically verifying bounded candidate is accepted by the
Boolean checker. This lets generated finite candidate languages establish minimum
cost by exhaustive `decide` computation without trusting the Python optimizer.

The generator emits three modules:

### `WorkflowIntegrity.Search`

Concrete state, actions, guards, transitions, sensors, trace replay, and the proved
terminal trace catalog.

### `WorkflowIntegrity.Evidence`

The greenfield evidence problem over all six channels. Candidates are represented by
`Fin 64` bitmasks. Lean checks every candidate in the kernel, proves the selected
three-channel design semantically verifies the bounded claim, and proves no lower-cost
greenfield candidate verifies it.

### `WorkflowIntegrity.CEGIS`

A bridge proving:

- evidence histories equal the workflow-generated traces;
- claim values equal replayed workflow claims;
- channel observations equal workflow projections;
- each CEGIS round refutes its before-selection and resolves the same pair afterward;
- the refinement rounds form one connected chain;
- every repair candidate retains the three already-deployed channels;
- the final repair semantically verifies the claim;
- exhaustive kernel computation over the eight optional-channel masks proves no
  lower-cost repair in that constrained language verifies it.

## Commands

```bash
python -m tools.workflow_cegis synth \
  --model examples/workflow_cegis/search_integrity.json \
  --report /tmp/lfv-workflow-cegis/report.canonical.json \
  --evidence-model /tmp/lfv-workflow-cegis/evidence-model.canonical.json \
  --synthesis /tmp/lfv-workflow-cegis/global-synthesis.canonical.json \
  --repair-synthesis /tmp/lfv-workflow-cegis/repair-synthesis.canonical.json \
  --workflow-lean LeanFinance/Generated/WorkflowSearch.lean \
  --evidence-lean LeanFinance/Generated/WorkflowEvidence.lean \
  --bridge-lean LeanFinance/Generated/WorkflowCEGIS.lean \
  --pretty
```

CI executes the generator twice, compares every canonical JSON and Lean output
byte-for-byte, checks the generated Lean files against the repository copies, and then
runs the full Lean build.

## Three completeness boundaries

1. **Transition exploration completeness:** all terminal traces of the declared finite
   workflow up to `max_depth` are generated. The Lean trace equality checks this.
2. **Repair-language completeness:** every subset of the declared optional channels is
   enumerated exactly.
3. **Real-world model completeness:** every materially relevant implementation action,
   attack, and sensor failure is represented.

Only the first two are mechanically established. The third is an open scientific
modeling obligation. The natural continuation is to ingest newly observed attack
traces, determine whether the transition system can reproduce them, extend the action
semantics when it cannot, and rerun the proof-carrying synthesis. In that form, each
new attack grows a separator basis rather than merely adding another checklist item.
