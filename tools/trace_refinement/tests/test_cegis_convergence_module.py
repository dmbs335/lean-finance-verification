from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


class CegisConvergenceModuleTests(unittest.TestCase):
    def test_cegis_convergence_module_typechecks(self) -> None:
        result = subprocess.run(
            [
                "lake",
                "env",
                "lean",
                "LeanFinance/Epistemic/CEGISConvergence.lean",
            ],
            cwd=REPOSITORY_ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=180,
            check=False,
        )
        self.assertEqual(
            result.returncode,
            0,
            msg=(
                "Lean CEGIS convergence module failed to typecheck:\n"
                + result.stdout
            ),
        )


if __name__ == "__main__":
    unittest.main()
