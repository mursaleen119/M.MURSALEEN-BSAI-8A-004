from __future__ import annotations

import argparse
from pathlib import Path
from urllib.request import Request, urlopen


FILES = [
    "case01_orders_stringdate.csv",
    "case02_shop_closed.csv",
    "case03_bandwidth_levels.csv",
    "case04_intervention_lag.csv",
    "case05_revenue_window.csv",
    "case06_monthly_partial.csv",
    "case07_stacked_products.csv",
    "case08_channel_attrib.csv",
    "case09_premium_share.csv",
    "revenue_catalogue.csv",
    "sessions_hourly.csv",
    "shares_eight.csv",
]
BASE = "https://raw.githubusercontent.com/UsmarHaider/data-visualization/main/week4/assignments/data"


def main() -> None:
    parser = argparse.ArgumentParser(description="Cache the official Week 4 input data locally.")
    parser.add_argument("--force", action="store_true", help="replace cached inputs")
    args = parser.parse_args()
    target_dir = Path(__file__).resolve().parent / "data"
    target_dir.mkdir(exist_ok=True)
    for name in FILES:
        target = target_dir / name
        if target.exists() and not args.force:
            print("cached", name)
            continue
        request = Request(f"{BASE}/{name}", headers={"User-Agent": "CDB601220-week4-runner"})
        with urlopen(request, timeout=60) as response:
            target.write_bytes(response.read())
        print("downloaded", name)


if __name__ == "__main__":
    main()
