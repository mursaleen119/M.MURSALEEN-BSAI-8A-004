"""Shared, original helpers for the Federal Transit Authority Week 7 work."""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path
from typing import Any

import matplotlib.colors as mcolors
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.collections import PatchCollection
from matplotlib.patches import Polygon as MplPolygon


ROOT = Path(__file__).resolve().parent
RAW_DIR = ROOT / "data"
CLEAN_DIR = ROOT / "clean"
CHART_DIR = ROOT / "charts"
SOURCE_REVISION = "095acf496b9dd19f448d83ad1220a65f493d9b9d"
SOURCE_BASE = (
    "https://raw.githubusercontent.com/UsmarHaider/data-visualization/"
    f"{SOURCE_REVISION}/week7/assignments/data"
)
SOURCE_FILES = (
    "district_transit.csv",
    "routes.csv",
    "ridership_daily.csv",
    "fare_revenue.csv",
    "regions.geojson",
)
MODES = ["Metro", "BRT", "Bus", "Ferry"]
MODE_COLORS = dict(zip(MODES, sns.color_palette("colorblind", 4).as_hex()))
CONTINENT_PALETTE = sns.color_palette("colorblind", 5).as_hex()
SEQUENTIAL = "viridis"


def ensure_source_files() -> None:
    """Fetch missing source inputs from the instructor's pinned public revision."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for name in SOURCE_FILES:
        destination = RAW_DIR / name
        if destination.is_file() and destination.stat().st_size:
            continue
        url = f"{SOURCE_BASE}/{name}"
        temporary = destination.with_suffix(destination.suffix + ".part")
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                body = response.read()
        except OSError as error:
            raise RuntimeError(f"Unable to fetch required source file {url}: {error}") from error
        if not body:
            raise RuntimeError(f"Source file download was empty: {url}")
        temporary.write_bytes(body)
        temporary.replace(destination)


def load_clean() -> dict[str, pd.DataFrame]:
    """Read the processing script's outputs or fail with the required run order."""
    required = {
        "districts": "district_transit.csv",
        "routes": "routes.csv",
        "daily": "ridership_daily.csv",
        "fares": "fare_revenue.csv",
    }
    missing = [name for name in required.values() if not (CLEAN_DIR / name).is_file()]
    if missing:
        raise FileNotFoundError(
            "Cleaned inputs are missing. Run `python weak-7\\partA_process.py` first; "
            f"missing: {', '.join(missing)}"
        )
    data = {
        key: pd.read_csv(CLEAN_DIR / filename, parse_dates=["date"] if key == "daily" else None)
        for key, filename in required.items()
    }
    return data


def load_geojson() -> dict[str, Any]:
    path = CLEAN_DIR / "regions.geojson"
    if not path.is_file():
        raise FileNotFoundError("Run `python weak-7\\partA_process.py` to prepare regions.geojson.")
    with path.open(encoding="utf-8") as file:
        return json.load(file)


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
    denominator = 1 + np.sin(phi0) * np.sin(phi) + np.cos(phi0) * np.cos(phi) * np.cos(delta)
    if denominator <= 0:
        raise ValueError(f"Point ({lon}, {lat}) is outside the projection's visible hemisphere.")
    scale = np.sqrt(2 / denominator)
    x = radius * scale * np.cos(phi) * np.sin(delta)
    y = radius * scale * (
        np.cos(phi0) * np.sin(phi) - np.sin(phi0) * np.cos(phi) * np.cos(delta)
    )
    return float(x), float(y)


def add_district_choropleth(
    ax: Any,
    geojson: dict[str, Any],
    values: pd.Series,
    *,
    title: str,
    colorbar_label: str,
    breaks: np.ndarray | None = None,
) -> np.ndarray:
    """Draw a projected district choropleth with labelled, reproducible breaks."""
    features = geojson.get("features", [])
    codes = [feature["properties"]["code"] for feature in features]
    missing = sorted(set(codes) - set(values.index))
    if missing:
        raise ValueError(f"District map has unmatched feature codes: {missing}")
    ordered = np.asarray([float(values.loc[code]) for code in codes])
    if not np.isfinite(ordered).all():
        raise ValueError("Choropleth values must be finite.")
    if breaks is None:
        breaks = np.unique(np.quantile(ordered, np.linspace(0, 1, 6)))
    if len(breaks) < 2:
        raise ValueError("At least two distinct choropleth break values are required.")
    classes = np.searchsorted(breaks[1:-1], ordered, side="right")
    patches = []
    for feature in features:
        code = feature["properties"]["code"]
        geom = feature["geometry"]
        if geom["type"] != "Polygon":
            raise ValueError(f"Expected Polygon geometry for {code}, got {geom['type']}.")
        ring = geom["coordinates"][0]
        points = [project_laea(lon, lat) for lon, lat in ring]
        patches.append(MplPolygon(points, closed=True, label=code))
    collection = PatchCollection(
        patches,
        cmap=SEQUENTIAL,
        edgecolor="#ffffff",
        linewidth=0.7,
        antialiased=True,
    )
    collection.set_array(classes.astype(float))
    collection.set_clim(0, len(breaks) - 1)
    ax.add_collection(collection)
    ax.autoscale_view()
    ax.set_aspect("equal", adjustable="datalim")
    ax.set_axis_off()
    ax.set_title(title, loc="left", fontsize=11, fontweight="bold")
    ticks = np.arange(len(breaks) - 1)
    labels = [
        f"{breaks[i]:,.0f}–{breaks[i + 1]:,.0f}" for i in range(len(breaks) - 1)
    ]
    colorbar = ax.figure.colorbar(collection, ax=ax, fraction=0.045, pad=0.02, ticks=ticks)
    colorbar.ax.set_yticklabels(labels)
    colorbar.set_label(colorbar_label)
    for feature, patch in zip(features, patches):
        if "centroid" in feature["properties"]:
            x, y = project_laea(*feature["properties"]["centroid"])
            ax.text(x, y, feature["properties"]["code"][-2:], ha="center", va="center", fontsize=6)
        else:
            points = np.asarray(patch.get_xy())
            center = points[:-1].mean(axis=0)
            ax.text(*center, feature["properties"]["code"][-2:], ha="center", va="center", fontsize=6)
    return breaks


def channel_conflicts(panels: list[dict[str, str]]) -> dict[str, Any]:
    """Check that identity channels have one meaning across the dashboard."""
    identity_channels = {"hue", "size", "shape", "lightness", "angle", "width"}
    seen: dict[str, set[str]] = {}
    positional: dict[str, set[str]] = {}
    for panel in panels:
        for channel, variable in panel.items():
            if channel in identity_channels:
                seen.setdefault(channel, set()).add(variable)
            elif channel in {"x", "y"}:
                positional.setdefault(channel, set()).add(variable)
            elif channel != "panel":
                raise ValueError(f"Unknown visual channel: {channel}")
    conflicts = {key: sorted(value) for key, value in seen.items() if len(value) > 1}
    return {
        "conflicts": conflicts,
        "channels_used": {key: sorted(value) for key, value in seen.items()},
        "positional": {key: sorted(value) for key, value in positional.items()},
        "ok": not conflicts,
    }


def cvd_report(palette: dict[str, str]) -> dict[str, Any]:
    """Report pairwise separation after a simple deuteranopia color simulation."""
    names = list(palette)
    rgb = np.asarray([mcolors.to_rgb(palette[name]) for name in names])
    deuteranopia = np.asarray(
        [
            [0.367322, 0.860646, -0.227968],
            [0.280085, 0.672501, 0.047413],
            [-0.011820, 0.042940, 0.968881],
        ]
    )
    simulated = np.clip(rgb @ deuteranopia.T, 0, 1)
    distances = []
    for i, first in enumerate(names):
        for j in range(i + 1, len(names)):
            distance = float(np.linalg.norm(simulated[i] - simulated[j]))
            distances.append((first, names[j], distance))
    minimum = min((item[2] for item in distances), default=1.0)
    return {
        "method": "linear RGB deuteranopia approximation; marker shapes also identify modes",
        "minimum_rgb_distance": minimum,
        "pairs_below_0_12": [(a, b, d) for a, b, d in distances if d < 0.12],
        "pair_distances": distances,
        "colors": dict(palette),
    }


def style_axes() -> None:
    import matplotlib.pyplot as plt

    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.color": "#e6e6e6",
            "grid.linewidth": 0.7,
            "font.size": 9,
        }
    )
