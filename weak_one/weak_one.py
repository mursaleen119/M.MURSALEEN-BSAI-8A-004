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


def make_datasaurus_plot(df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(11, 7))

    palette = plt.get_cmap("tab10")
    datasets = sorted(df["dataset"].unique())

    for idx, dataset_name in enumerate(datasets):
        group = df[df["dataset"] == dataset_name]
        ax.scatter(
            group["x"],
            group["y"],
            s=18,
            alpha=0.7,
            color=palette(idx % 10),
            edgecolors="none",
            label=dataset_name,
        )

    ax.set_title("The same summary statistics can hide very different shapes", fontsize=16, fontweight="bold")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.grid(False)
    ax.legend(loc="best", title="Dataset", fontsize=8)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "weak_one_datasaurus.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    df = load_datasaurus()
    make_datasaurus_plot(df)
    print("Loaded official Week 1 dataset from the UsmarHaider/data-visualization repo.")
    print("This plot shows why visualization matters: datasets with similar summary statistics can look very different.")
    print(f"Saved output to: {OUTPUT_DIR / 'weak_one_datasaurus.png'}")


if __name__ == "__main__":
    main()
