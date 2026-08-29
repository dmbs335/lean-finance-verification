from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from tools.evidence_synth.canonical import load_json, write_canonical_json
from tools.pnl_explain_closure.errors import ValidationError
from tools.pnl_explain_closure.gs_quant_conformance import (
    load_conformance_model,
    method_source_sha256,
    recompute_lfv_output,
    run_conformance,
    verify_conformance,
)


ROOT = Path(__file__).resolve().parents[3]
MODEL = ROOT / "examples" / "pnl_explain_closure" / "gs_quant_conformance.json"


class CompatibleBackTest:
    def pnl_explain(self):
        if self.pnl_explain_def is None:
            return None
        risk_results = self.results
        exit_risk_results = self.trade_exit_risk_results
        dates = sorted(set(risk_results.keys()).union(exit_risk_results.keys()))
        pnl_explain_results = {}
        for attribute in self.pnl_explain_def.attributes:
            result = {}
            cum_total = 0.0
            for idx in range(1, len(dates)):
                metric_pnl = 0.0
                cur_date = dates[idx]
                prev_date = dates[idx - 1]
                if prev_date not in risk_results:
                    result[cur_date] = cum_total
                    continue
                for prev_date_inst in risk_results[prev_date].portfolio.all_instruments:
                    prev_date_risk = risk_results[prev_date][prev_date_inst][attribute.attribute_metric]
                    if prev_date_risk == 0:
                        continue
                    prev_date_mkt_data = risk_results[prev_date][prev_date_inst][attribute.market_data_metric]
                    if cur_date in risk_results and prev_date_inst in risk_results[cur_date].portfolio:
                        cur_date_mkt_data = risk_results[cur_date][prev_date_inst][attribute.market_data_metric]
                    else:
                        cur_date_mkt_data = exit_risk_results[cur_date][prev_date_inst][attribute.market_data_metric]
                    if attribute.second_order:
                        metric_pnl += 0.5 * attribute.scaling_factor * prev_date_risk * (
                            cur_date_mkt_data - prev_date_mkt_data
                        ) * (cur_date_mkt_data - prev_date_mkt_data)
                    else:
                        metric_pnl += attribute.scaling_factor * prev_date_risk * (
                            cur_date_mkt_data - prev_date_mkt_data
                        )
                cum_total += metric_pnl
                result[cur_date] = cum_total
            pnl_explain_results[attribute.attribute_name] = result
        return pnl_explain_results


class IncorrectBackTest:
    def pnl_explain(self):
        return {
            attribute.attribute_name: {}
            for attribute in self.pnl_explain_def.attributes
        }


class GsQuantControlledConformanceTests(unittest.TestCase):
    def _model_for(self, backtest_type: type[object]):
        raw = copy.deepcopy(load_json(MODEL))
        raw["upstream"]["method_source_sha256"] = method_source_sha256(
            backtest_type.pnl_explain
        )
        temporary = tempfile.TemporaryDirectory()
        path = Path(temporary.name) / "model.json"
        write_canonical_json(path, raw)
        return temporary, load_conformance_model(path)

    def test_exact_lfv_recomputation_matches_registered_output(self) -> None:
        model = load_conformance_model(MODEL)
        self.assertEqual(recompute_lfv_output(model), model.expected_output)

    def test_controlled_runtime_executes_portfolio_and_exit_paths(self) -> None:
        temporary, model = self._model_for(CompatibleBackTest)
        with temporary:
            report = run_conformance(
                model,
                backtest_type=CompatibleBackTest,
                distribution_version="2.1.6",
            )
        self.assertEqual(report["runtime_output"], model.expected_output)
        self.assertTrue(all(report["checks"].values()))
        self.assertEqual(report["coverage_status"], "DIRECT_TESTED_CONTROLLED_INPUT")

    def test_same_date_result_and_exit_snapshots_are_supported(self) -> None:
        model = load_conformance_model(MODEL)
        same_date_locations = {
            snapshot.location
            for snapshot in model.snapshots
            if snapshot.date.isoformat() == "2026-01-05"
        }
        self.assertEqual(same_date_locations, {"results", "exit_results"})

    def test_overlapping_current_and_exit_instrument_is_rejected(self) -> None:
        raw = copy.deepcopy(load_json(MODEL))
        raw["snapshots"][2]["instruments"]["instrument-a"] = {"spot": 103}
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "overlap.json"
            write_canonical_json(path, raw)
            with self.assertRaisesRegex(ValidationError, "both current and exited"):
                load_conformance_model(path)

    def test_unaccounted_previous_instrument_is_rejected(self) -> None:
        raw = copy.deepcopy(load_json(MODEL))
        del raw["snapshots"][2]
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "unaccounted.json"
            write_canonical_json(path, raw)
            with self.assertRaisesRegex(ValidationError, "does not account"):
                load_conformance_model(path)

    def test_duplicate_date_location_is_rejected(self) -> None:
        raw = copy.deepcopy(load_json(MODEL))
        raw["snapshots"].insert(2, copy.deepcopy(raw["snapshots"][1]))
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "duplicate.json"
            write_canonical_json(path, raw)
            with self.assertRaisesRegex(ValidationError, "date/location pair"):
                load_conformance_model(path)

    def test_fixture_missing_required_runtime_path_is_rejected(self) -> None:
        raw = copy.deepcopy(load_json(MODEL))
        raw["upstream"]["method_source_sha256"] = method_source_sha256(
            CompatibleBackTest.pnl_explain
        )
        raw["snapshots"][0]["instruments"]["instrument-c"]["delta"] = 1
        raw["expected_output"]["first_order"] = {
            "2026-01-05": "48",
            "2026-01-06": "47",
            "2026-01-07": "68",
        }
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "missing-zero-risk-path.json"
            write_canonical_json(path, raw)
            model = load_conformance_model(path)
            with self.assertRaisesRegex(ValidationError, "zero_risk_skip"):
                run_conformance(
                    model,
                    backtest_type=CompatibleBackTest,
                    distribution_version="2.1.6",
                )

    def test_source_substitution_is_rejected_before_execution(self) -> None:
        model = load_conformance_model(MODEL)
        with self.assertRaisesRegex(ValidationError, "source digest"):
            run_conformance(
                model,
                backtest_type=CompatibleBackTest,
                distribution_version="2.1.6",
            )

    def test_runtime_arithmetic_divergence_is_rejected(self) -> None:
        temporary, model = self._model_for(IncorrectBackTest)
        with temporary, self.assertRaisesRegex(
            ValidationError, "runtime output"
        ):
            run_conformance(
                model,
                backtest_type=IncorrectBackTest,
                distribution_version="2.1.6",
            )

    def test_distribution_version_drift_is_rejected(self) -> None:
        temporary, model = self._model_for(CompatibleBackTest)
        with temporary, self.assertRaisesRegex(ValidationError, "expected gs-quant"):
            run_conformance(
                model,
                backtest_type=CompatibleBackTest,
                distribution_version="2.1.5",
            )

    def test_missing_runtime_metric_is_rejected_at_load_time(self) -> None:
        raw = copy.deepcopy(load_json(MODEL))
        del raw["snapshots"][0]["instruments"]["instrument-a"]["gamma"]
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "missing-metric.json"
            write_canonical_json(path, raw)
            with self.assertRaisesRegex(ValidationError, "missing metrics"):
                load_conformance_model(path)

    def test_conformance_report_tampering_is_rejected(self) -> None:
        temporary, model = self._model_for(CompatibleBackTest)
        with temporary:
            report = run_conformance(
                model,
                backtest_type=CompatibleBackTest,
                distribution_version="2.1.6",
            )
            tampered = copy.deepcopy(report)
            tampered["runtime_output"]["first_order"]["2026-01-05"] = "31"
            with self.assertRaisesRegex(ValidationError, "does not match replay"):
                verify_conformance(
                    model,
                    tampered,
                    backtest_type=CompatibleBackTest,
                    distribution_version="2.1.6",
                )


try:
    from gs_quant.backtests.backtest_objects import BackTest
except ImportError:
    BackTest = None


@unittest.skipUnless(BackTest is not None, "gs-quant is not installed")
class GsQuantPinnedRuntimeTests(unittest.TestCase):
    def test_pinned_public_runtime_matches_exact_lfv_recomputation(self) -> None:
        report = run_conformance(load_conformance_model(MODEL))
        self.assertTrue(report["checks"]["runtime_matches_lfv"])


if __name__ == "__main__":
    unittest.main()
