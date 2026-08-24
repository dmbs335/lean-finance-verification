# Lean Finance Verification Academy

`learning-app/` is a dependency-free static tutorial built from the repository's actual Lean modules, Python tools, examples, design documents, and CI boundaries.

## Run locally

From the repository root:

```bash
python -m http.server 8000
```

Then open `http://localhost:8000/learning-app/`.

## What it covers

The curriculum contains six connected tracks and 35 lessons. In addition to the original finance, backtest, epistemic, robustness, and evidence-infrastructure material, it now covers:

- certifiable alpha and executable fake-alpha recovery;
- residual model, attack, and deployment-cost uncertainty;
- exact evidence-adjusted portfolio selection;
- certifiability–crowding and capacity limits;
- epistemic-liquidation and funding contagion;
- a fail-closed proof-carrying research-agent harness.

Every lesson states both what the referenced source can prove or mechanically check and what remains an empirical, cryptographic, model-completeness, or operational assumption.

## Features

- eight goal-oriented learning paths;
- track and full-text filtering;
- browser-local completion and quiz state;
- source, design-document, fixture, and command links;
- project coverage dashboard and derived glossary;
- progress export and reset;
- responsive light/dark UI;
- no external JavaScript, CSS, fonts, analytics, or backend.

## Curriculum contract

`data/meta.js` and the track files contain JSON wrapped in simple browser assignments. `data/curriculum.js` publishes the assembled object as `window.LFV_CURRICULUM`; the Python validator parses the same fragments used by the browser.

Run:

```bash
python -m tools.learning_app.check_curriculum
python -m unittest discover -s tools/learning_app/tests -v
```

The validator fails when a source/document is missing, prerequisites cycle, a learning path references an unknown lesson, a project coverage area or required tool is omitted, quiz answers are invalid, browser assets are absent, or an external script/style dependency is introduced.
