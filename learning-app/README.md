# Lean Finance Verification Academy

`learning-app/` is a dependency-free static tutorial built from the repository's
actual Lean modules, Python tools, examples, design documents, and CI boundaries.

## Run locally

From the repository root:

```bash
python -m http.server 8000
```

Then open:

```text
http://localhost:8000/learning-app/
```

Opening `index.html` directly also works in most modern browsers, but a local HTTP
server gives more predictable clipboard and navigation behavior.

## What it covers

The curriculum contains six connected tracks:

1. project map and Lean reading;
2. game theory, market microstructure, constraints, dynamics, inference,
   strategy ecology, and supply-chain models;
3. proof-carrying backtests, PIT lineage, search commitments, adapters, and
   certificates;
4. evidence separation, impossibility, exact synthesis, workflow CEGIS,
   trace refinement, and evidence debt;
5. version spaces, trust-domain resilience, multi-claim synthesis, taxonomy,
   and symbolic scaling;
6. PIT vendor packages, timestamp/quorum evidence, selective disclosure,
   experimental zero-count receipts, generated witnesses, and CI.

Every lesson states both:

- what the referenced source can prove or mechanically check;
- what remains an empirical, cryptographic, provider, model-completeness, or
  operational assumption.

## Features

- six goal-oriented learning paths;
- track and full-text filtering;
- browser-local completion and quiz state;
- source, design-document, fixture, and command links;
- project coverage dashboard;
- glossary derived from lesson concepts;
- progress export and reset;
- responsive light/dark UI;
- no external JavaScript, CSS, fonts, analytics, or backend.

## Curriculum contract

`data/meta.js` and the six track files contain JSON wrapped in simple browser
assignments. `data/curriculum.js` publishes the assembled object as
`window.LFV_CURRICULUM`; the Python validator parses the same JSON fragments used by
the browser.

Run the validator and tests with:

```bash
python -m tools.learning_app.check_curriculum
python -m unittest discover -s tools/learning_app/tests -v
```

The validator fails when:

- a lesson points to a missing repository source or document;
- a prerequisite or learning-path lesson is unknown;
- prerequisites contain a cycle;
- a project coverage area or required tool is omitted;
- quiz answers are invalid;
- app assets are missing;
- the page adds an external script/style dependency.

This makes educational coverage a maintained repository contract rather than a
one-off presentation.
