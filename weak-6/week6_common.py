"""Shared paths, pinned inputs, and plotting helpers for the Week 6 task."""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
RAW_DIR = ROOT / "data"
CLEAN_DIR = ROOT / "clean"
CHART_DIR = ROOT / "charts"
SOURCE_REVISION = "095acf496b9dd19f448d83ad1220a65f493d9b9d"
SOURCE_BASE = (
    "https://raw.githubusercontent.com/UsmarHaider/data-visualization/"
    f"{SOURCE_REVISION}/week6/assignments/data"
)
SOURCE_FILES = (
    "district_grid.csv",
    "grid_daily.csv",
    "generation_mix.csv",
    "regions.geojson",
)


def ensure_source_files() -> None:
    """Fetch missing raw inputs from the instructor's pinned public revision."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for name in SOURCE_FILES:
        destination = RAW_DIR / name
        if destination.is_file() and destination.stat().st_size:
            continue
        url = f"{SOURCE_BASE}/{name}"
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                body = response.read()
        except OSError as error:
            raise RuntimeError(f"Unable to fetch required source file {url}: {error}") from error
        if not body:
            raise RuntimeError(f"Source file download was empty: {url}")
        temporary = destination.with_suffix(destination.suffix + ".part")
        temporary.write_bytes(body)
        temporary.replace(destination)


def load_clean() -> dict[str, Any]:
    """Load generated clean tables and their GeoJSON or fail with setup guidance."""
    required = {
        "districts": "district_grid.csv",
        "daily": "grid_daily.csv",
        "generation": "generation_mix.csv",
    }
    missing = [name for name in required.values() if not (CLEAN_DIR / name).is_file()]
    if not (CLEAN_DIR / "regions.geojson").is_file():
        missing.append("regions.geojson")
    if missing:
        raise FileNotFoundError(
            "Cleaned files are missing. Run `python weak-6\\partA_process.py` first; "
            f"missing: {', '.join(missing)}"
        )
    import pandas as pd

    data: dict[str, Any] = {
        key: pd.read_csv(
            CLEAN_DIR / filename,
            parse_dates=["date"] if key == "daily" else None,
        )
        for key, filename in required.items()
    }
    with (CLEAN_DIR / "regions.geojson").open(encoding="utf-8") as file:
        data["geojson"] = json.load(file)
    return data


def project_laea(
    lon: float,
    lat: float,
    lon0: float = 70.0,
    lat0: float = 30.0,
) -> tuple[float, float]:
    """Project longitude/latitude to Lambert azimuthal equal-area coordinates."""
    radius = 6_371_008.8
    lam, phi = np.radians([lon, lat])
    lam0, phi0 = np.radians([lon0, lat0])
    delta = lam - lam0
    denominator = (
        1 + np.sin(phi0) * np.sin(phi) + np.cos(phi0) * np.cos(phi) * np.cos(delta)
    )
    if denominator <= 0:
        raise ValueError(f"Point ({lon}, {lat}) is outside the projection's visible hemisphere.")
    scale = np.sqrt(2 / denominator)
    x = radius * scale * np.cos(phi) * np.sin(delta)
    y = radius * scale * (
        np.cos(phi0) * np.sin(phi) - np.sin(phi0) * np.cos(phi) * np.cos(delta)
    )
    return float(x), float(y)


def month_boundary_energy(daily: Any, zone: str) -> Any:
    """Compute month energy as the meter change between consecutive month-start readings."""
    series = (
        daily.loc[daily["zone"].eq(zone)]
        .set_index("date")["cumulative_mwh"]
        .sort_index()
    )
    first_days = series.loc[series.index.day == 1]
    month_values = first_days.groupby(first_days.index.to_period("M")).last()
    all_months = pd.period_range("2025-04", "2026-08", freq="M")
    values = []
    for month in all_months:
        start = month_values.get(month)
        end = month_values.get(month + 1)
        values.append(np.nan if start is None or end is None else float(end - start))
    return pd.Series(values, index=all_months, name="energy_mwh")


def style_axes() -> None:
    """Set consistent, accessible defaults for the submitted figures."""
    import matplotlib as mpl

    mpl.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "axes.titlesize": 11,
            "axes.labelsize": 9,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "savefig.facecolor": "white",
        }
    )


def add_source_note(fig: Any, text: str) -> None:
    fig.text(0.02, 0.012, text, ha="left", va="bottom", fontsize=7, color="#444444")
