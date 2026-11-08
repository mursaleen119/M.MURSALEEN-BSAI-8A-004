from __future__ import annotations

import argparse
from pathlib import Path
from urllib.request import Request, urlopen


FILES = [
    "case05_flat_rates.csv",
    "county_crime.csv",
    "district_health.csv",
    "districts.geojson",
    "districts_alt.geojson",
    "districts_coarse.geojson",
    "health_indicators.csv",
    "region_profiles.csv",
    "scatter_dense.csv",
    "smallarea_cases.csv",
]
BASE = "https://raw.githubusercontent.com/UsmarHaider/data-visualization/main/week5/assignments/data"


def main() -> None:
    parser = argparse.ArgumentParser(description="Cache the official Week 5 input data locally.")
    parser.add_argument("--force", action="store_true", help="replace cached inputs")
    args = parser.parse_args()
    target_dir = Path(__file__).resolve().parent / "data"
    target_dir.mkdir(exist_ok=True)
    for name in FILES:
        target = target_dir / name
        if target.exists() and not args.force:
            print("cached", name)
            continue
        request = Request(f"{BASE}/{name}", headers={"User-Agent": "CDB601220-week5-runner"})
        with urlopen(request, timeout=60) as response:
            target.write_bytes(response.read())
        print("downloaded", name)


if __name__ == "__main__":
    main()
