# ALFRED Revision and Release-Time Leakage Study

This study compares four reconstructions of one registered signal rule:

```text
1. date-granular ALFRED vintage
2. exact release-time strict path
3. latest revised values on the strict observation dates
4. naive latest-vintage reconstruction
```

The distinction matters because FRED/ALFRED real-time parameters identify a
calendar-date vintage. A decision made earlier on that calendar day can still
precede a scheduled release that the date-level vintage later includes.
Therefore `realtime_start = realtime_end = decision date` is necessary but not
sufficient for intraday point-in-time correctness.

## Input contract

A study package contains:

- the registered series, signal threshold, scale, costs, decision instants, and
  realized-return inputs;
- one raw FRED `series/observations` JSON response for each decision-date
  vintage;
- one later-vintage response reused as the counterfactual latest snapshot;
- a separately curated release calendar with exact UTC release instants;
- a manifest binding every file by safe relative path and SHA-256.

The downloader uses the official FRED observations endpoint with:

```text
file_type=json
output_type=1
realtime_start=realtime_end=as_of_date
```

Live downloads require an explicit API key or `FRED_API_KEY`. The key is used
only in the request and is not written into the package. The release calendar
is not inferred from a date-granular ALFRED response; it must be supplied and is
hash-bound as a separate provenance object.

## Four paths

### Date-granular vintage path

The final two observations present in the response for the decision's real-time
calendar date are used. This path proves a date-vintage property but may consume
a value released later on the same day.

### Release-time strict path

The same vintage response is filtered to observations whose `release_at` is no
later than the exact decision instant. This is the only path labeled strict
point-in-time in the study report.

### Revision-only counterfactual

The observation dates selected by the release-time strict path are held fixed,
but their values are replaced with the later vintage's revised values. This
isolates value revision from publication availability.

### Naive latest-vintage counterfactual

The final two observations in the later snapshot are used. This may combine
value revisions with observations that were not released by the original
decision, reproducing a common historical-reconstruction error.

## Controlled fixture

The checked-in fixture is synthetic but uses raw JSON shaped like the official
FRED observations response. It includes four decision instants and two exact
same-day boundaries:

- a February observation released at 14:00 UTC after a March 15 09:00 UTC
  decision;
- a May observation released at 16:00 UTC after a June 15 15:00 UTC decision.

Two transformations pass the date-vintage policy but fail the release-time
policy. Two other transformations pass both.

The controlled totals are:

```text
date-granular vintage path     -103 bps
release-time strict path        -23 bps
revision-only counterfactual     78 bps
naive latest counterfactual     -44 bps

intraday release leakage        -80 bps
revision-only leakage           101 bps
revision + availability leakage -21 bps
```

These numbers are fixture properties, not estimated market effects.

## Formal layer

`LeanFinance/Backtest/RevisionLeakage.lean` defines:

- `AvailableAtVintageDay`;
- `AvailableAtReleaseTime`;
- `VintageValidButReleaseTimeLeaking`;
- `AvailableUnderBothPolicies`;
- `HasSameDayPostDecisionInput`;
- four explicit strategy-return paths;
- a proof-carrying aggregate certificate.

The executable Lean example proves one date-valid/release-time-leaking
transformation, one transformation valid under both policies, and the exact
same-day boundary.

## Commands

Build the fixture manifest and run the deterministic study:

```bash
python -m tools.pit_study.alfred_manifest \
  --spec examples/alfred_revision_leakage/fixtures/package-spec.json \
  --out /tmp/alfred-manifest.json

python -m tools.pit_study.alfred_revision analyze \
  --config examples/alfred_revision_leakage/config.json \
  --manifest /tmp/alfred-manifest.json \
  --out /tmp/alfred-revision-report.json
```

The manifest must be generated inside the package directory when used with
relative response paths. For a simple local run, write it next to
`package-spec.json` or copy the fixture directory to a temporary location.

Verify a saved report by exact recomputation:

```bash
python -m tools.pit_study.alfred_revision verify \
  --config examples/alfred_revision_leakage/config.json \
  --manifest /path/to/fixture-copy/manifest.json \
  --report /tmp/alfred-revision-report.json
```

Create a live package after independently preparing a release calendar:

```bash
python -m tools.pit_study.alfred_revision download \
  --config /path/to/study-config.json \
  --release-calendar /path/to/release-calendar.json \
  --out-dir /tmp/alfred-package
```

## Assurance boundary

The module proves or exactly checks the registered finite transformation and
availability contracts. It does not prove:

- that a supplied release calendar is true merely because it is hashed;
- that the chosen series or signal identifies a causal economic mechanism;
- that supplied realized returns are independently verified;
- that all revisions or publication channels have been modeled;
- that the controlled return differences imply future profitability;
- that a date-granular API query alone establishes intraday availability.

A real study should source release instants from authoritative calendars, bind
market return data independently, preregister the decision rule, and preserve
all raw responses and execution evidence.
