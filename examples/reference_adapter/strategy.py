from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: strategy.py <prices.csv> <parameters.json>")
    prices_path = Path(sys.argv[1])
    parameters_path = Path(sys.argv[2])
    with prices_path.open("r", encoding="utf-8", newline="") as handle:
        closes = [int(row["close"]) for row in csv.DictReader(handle)]
    parameters = json.loads(parameters_path.read_text(encoding="utf-8"))
    lookback = int(parameters["lookback"])
    scale_bps = int(parameters["scale_bps"])
    if lookback <= 0 or len(closes) <= lookback:
        raise SystemExit("insufficient observations for lookback")
    momentum = closes[-1] - closes[-1 - lookback]
    output = {
        "features": {
            "momentum": {
                "lookback": lookback,
                "price_change": momentum,
            }
        },
        "metric_value": momentum * scale_bps,
    }
    print(json.dumps(output, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
