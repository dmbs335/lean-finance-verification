from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tools.lfv_adapter.errors import ValidationError
from tools.lfv_adapter.spec import load_experiment_spec


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
FIXTURE = REPOSITORY_ROOT / "examples" / "reference_adapter"


class SpecTests(unittest.TestCase):
    def test_paths_cannot_escape_the_experiment_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copied = Path(temporary) / "fixture"
            shutil.copytree(FIXTURE, copied)
            spec_path = copied / "experiment.json"
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
            spec["code"]["paths"] = ["../outside.py"]
            spec_path.write_text(json.dumps(spec), encoding="utf-8")
            with self.assertRaisesRegex(ValidationError, "escapes experiment root"):
                load_experiment_spec(spec_path)

    def test_decision_requires_at_least_one_dataset(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copied = Path(temporary) / "fixture"
            shutil.copytree(FIXTURE, copied)
            spec_path = copied / "experiment.json"
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
            spec["decision"]["dataset_ids"] = []
            spec_path.write_text(json.dumps(spec), encoding="utf-8")
            with self.assertRaisesRegex(ValidationError, "at least one dataset"):
                load_experiment_spec(spec_path)


if __name__ == "__main__":
    unittest.main()
