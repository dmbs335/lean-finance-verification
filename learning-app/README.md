# Lean Finance Verification Academy

`learning-app/` is a dependency-free static tutorial built from the repository's actual Lean modules, Python tools, examples, design documents, and CI boundaries.

Run `python -m http.server 8000` from the repository root and open `http://localhost:8000/learning-app/`.

The curriculum contains six tracks and 39 lessons. It now spans finance and market models, proof-carrying backtests, temporal noninterference, evidence separation, action-semantics and unified research version spaces, robust synthesis, certifiable-alpha uncertainty, evidence-adjusted portfolios, certifiability–crowding, epistemic liquidation, preregistered matched event studies, certificate composition, signed evidence infrastructure, privacy receipts, and fail-closed research-agent orchestration.

Every lesson states both what the referenced source can prove or mechanically check and what remains an empirical, cryptographic, model-completeness, provider, or operational assumption.

Run the maintained curriculum contract with:

```bash
python -m tools.learning_app.check_curriculum
python -m unittest discover -s tools/learning_app/tests -v
```

The validator fails when a source/document is missing, prerequisites cycle, a path references an unknown lesson, a required project/tool area is omitted, quiz answers are invalid, browser assets are absent, or an external script/style dependency is introduced.
