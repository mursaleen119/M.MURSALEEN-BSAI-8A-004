from __future__ import annotations

import json
import urllib.request
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
OUTPUT_DIR = Path(__file__).resolve().parent / "outputs"
DATA_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

TARGET_DATASET = "datasaurus.csv"


def github_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def find_datasaurus_url() -> str:
    for branch in ("main", "master"):
        tree_url = f"https://api.github.com/repos/UsmarHaider/data-visualization/git/trees/{branch}?recursive=1"
        try:
            payload = github_json(tree_url)
        except Exception:
            continue

        for item in payload.get("tree", []):
            path = item.get("path", "")
            if path.endswith(TARGET_DATASET):
                return f"https://raw.githubusercontent.com/UsmarHaider/data-visualization/{branch}/{path}"

    raise FileNotFoundError(f"Could not locate {TARGET_DATASET} in the official Week 1 reference repo.")


def load_datasaurus() -> pd.DataFrame:
    local_file = DATA_DIR / TARGET_DATASET
    if not local_file.exists():
        dataset_url = find_datasaurus_url()
        df = pd.read_csv(dataset_url)
        df.to_csv(local_file, index=False)
        return df
    return pd.read_csv(local_file)


def compute_summary(df: pd.DataFrame) -> pd.DataFrame:
    summary = (
        df.groupby("dataset")
        .apply(
            lambda g: pd.Series(
                {
                    "mean_x": g["x"].mean(),
                    "mean_y": g["y"].mean(),
                    "std_x": g["x"].std(ddof=1),
                    "std_y": g["y"].std(ddof=1),
                    "corr_xy": g["x"].corr(g["y"]),
                }
            )
        )
        .reset_index()
    )
    return summary.sort_values("dataset").reset_index(drop=True)


def save_summary(summary: pd.DataFrame) -> None:
    summary_path = OUTPUT_DIR / "weak_one_summary_table.csv"
    summary.to_csv(summary_path, index=False)
    print(f"Saved summary table to: {summary_path}")


def make_datasaurus_grid(df: pd.DataFrame) -> None:
    datasets = sorted(df["dataset"].unique())
    n = len(datasets)
    ncols = 4
    nrows = (n + ncols - 1) // ncols

    fig, axes = plt.subplots(nrows, ncols, figsize=(16, 12), squeeze=False)
    axes_flat = axes.flatten()

    for ax in axes_flat:
        ax.set_visible(False)

    for idx, dataset_name in enumerate(datasets):
        ax = axes_flat[idx]
        ax.set_visible(True)
        group = df[df["dataset"] == dataset_name]
        ax.scatter(group["x"], group["y"], s=14, alpha=0.8, color="#4c78a8")
        ax.set_title(dataset_name, fontsize=8)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_facecolor("#f7f7f7")

    fig.suptitle("Datasaurus: 13 datasets, near-identical summary statistics", fontsize=18, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(OUTPUT_DIR / "weak_one_datasaurus_grid.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    df = load_datasaurus()
    summary = compute_summary(df)
    save_summary(summary)
    make_datasaurus_grid(df)

    print("Loaded official Week 1 dataset from the UsmarHaider/data-visualization repo.")
    print("This task follows the datasaurus assignment: compute summary statistics, then plot all 13 datasets to show why visualization matters.")
    print(f"Saved summary table to: {OUTPUT_DIR / 'weak_one_summary_table.csv'}")
    print(f"Saved grid plot to: {OUTPUT_DIR / 'weak_one_datasaurus_grid.png'}")


if __name__ == "__main__":
    main()
