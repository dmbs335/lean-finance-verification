from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tools.evidence_synth.canonical import load_json

from .errors import EpistemicLiquidationError
from .model import load_scenario
from .simulator import simulate, verify


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="lfv-epistemic-liquidation")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("simulate")
    run.add_argument("--scenario", required=True, type=Path)
    run.add_argument("--out", required=True, type=Path)

    check = subparsers.add_parser("verify")
    check.add_argument("--scenario", required=True, type=Path)
    check.add_argument("--report", required=True, type=Path)

    args = parser.parse_args(argv)
    try:
        scenario = load_scenario(args.scenario)
        if args.command == "simulate":
            report = simulate(scenario)
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(
                json.dumps(report, sort_keys=True, separators=(",", ":")),
                encoding="utf-8",
            )
            print(
                f"impact={report['final_market_impact_bps']}bps "
                f"withdrawal={report['aggregate']['total_withdrawal_units']} "
                f"hidden_pairs={report['aggregate']['hidden_common_risk_pairs']}"
            )
        else:
            verify(scenario, load_json(args.report))
            print(f"verified {args.report}")
        return 0
    except (EpistemicLiquidationError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
