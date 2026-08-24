# Controlled ALFRED Revision-Leakage Fixture

Run from the repository root without mutating checked-in fixtures:

```bash
rm -rf /tmp/alfred-fixture
cp -R examples/alfred_revision_leakage/fixtures /tmp/alfred-fixture

python -m tools.pit_study.alfred_manifest \
  --spec /tmp/alfred-fixture/package-spec.json \
  --out /tmp/alfred-fixture/manifest.json

python -m tools.pit_study.alfred_revision analyze \
  --config examples/alfred_revision_leakage/config.json \
  --manifest /tmp/alfred-fixture/manifest.json \
  --out /tmp/alfred-revision-report.json
```

Expected controlled totals:

```text
vintage-date path:        -103 bps
release-time strict path:  -23 bps
revision-only path:         78 bps
naive latest path:         -44 bps
```

The fixture intentionally contains two transformations that pass a calendar-date
ALFRED vintage check but consume values released later than the decision instant.
It also contains two transformations that pass both date and exact release-time
availability policies.

The manifest builder hashes the copied release calendar and every raw response.
The inputs are synthetic and do not represent a real investment result.
