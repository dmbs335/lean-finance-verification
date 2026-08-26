from __future__ import annotations

import ast
import inspect
import textwrap
import unittest

try:
    from gs_quant.backtests.backtest_objects import BackTest
except ImportError:  # optional upstream conformance dependency
    BackTest = None  # type: ignore[assignment]


@unittest.skipUnless(BackTest is not None, "gs-quant is not installed")
class GsQuantPnLExplainSourceContractTests(unittest.TestCase):
    def setUp(self) -> None:
        assert BackTest is not None
        self.method = BackTest.pnl_explain
        self.source = textwrap.dedent(inspect.getsource(self.method))
        self.tree = ast.parse(self.source)

    def test_public_method_and_formula_markers_exist(self) -> None:
        self.assertTrue(callable(self.method))
        self.assertIn("pnl_explain", self.method.__name__)
        self.assertIn("scaling_factor", self.source)
        self.assertIn("second_order", self.source)

    def test_source_contains_market_move_and_multiplicative_attribution(self) -> None:
        operations = [
            node.op
            for node in ast.walk(self.tree)
            if isinstance(node, ast.BinOp)
        ]
        self.assertTrue(any(isinstance(op, ast.Sub) for op in operations))
        self.assertGreaterEqual(
            sum(isinstance(op, ast.Mult) for op in operations), 2
        )

    def test_second_order_branch_contains_half_or_division_structure(self) -> None:
        constants = {
            node.value
            for node in ast.walk(self.tree)
            if isinstance(node, ast.Constant)
            and isinstance(node.value, (int, float))
        }
        operations = [
            node.op
            for node in ast.walk(self.tree)
            if isinstance(node, ast.BinOp)
        ]
        has_half = 0.5 in constants
        has_division = any(isinstance(op, ast.Div) for op in operations)
        has_two = 2 in constants
        self.assertTrue(has_half or (has_division and has_two))


if __name__ == "__main__":
    unittest.main()
