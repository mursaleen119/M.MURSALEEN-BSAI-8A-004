from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
OUTPUT_DIR = Path(__file__).resolve().parent / "outputs"
DATA_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

DATASET_URL = "https://raw.githubusercontent.com/mwaskom/seaborn-data/master/tips.csv"
DATA_FILE = DATA_DIR / "tips.csv"


def load_tips_data() -> pd.DataFrame:
    if not DATA_FILE.exists():
        df = pd.read_csv(DATASET_URL)
        df.to_csv(DATA_FILE, index=False)
    return pd.read_csv(DATA_FILE)


def prepare_summary(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("day", as_index=False)["total_bill"]
        .mean()
        .sort_values("total_bill", ascending=False)
        .reset_index(drop=True)
    )


def make_bad_example(summary: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(11, 7))
    colors = ["#d95f02", "#1b9e77", "#7570b3", "#e7298a"]
    bars = ax.bar(
        summary["day"],
        summary["total_bill"],
        color=colors,
        edgecolor="black",
        linewidth=1.2,
    )

    ax.set_title("BAD EXAMPLE: Average total bill by day", fontsize=18, fontweight="bold")
    ax.set_xlabel("Day")
    ax.set_ylabel("Average total bill")
    ax.grid(True, axis="y", linestyle="--", linewidth=0.8, alpha=0.6)
    ax.set_axisbelow(True)
    ax.legend(bars, summary["day"], title="Day", loc="upper right")
    for bar, value in zip(bars, summary["total_bill"]):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + 0.8,
            f"{value:.1f}",
            ha="center",
            va="bottom",
            rotation=90,
            fontsize=8,
        )
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "bad_example.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

    # This bad example follows the Week 2 principle that strong clutter and
    # unnecessary labels raise cognitive load and reduce readability.


def make_five_panel(summary: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 5, figsize=(18, 4), sharey=True)
    steps = [
        ("legend removed", "remove legend"),
        ("frame and extra grid removed", "remove frame + extra grid"),
        ("one colour used", "single hue"),
        ("sorted bars", "sort bars by value"),
        ("clean final view", "label only the key message"),
    ]

    for idx, ax in enumerate(axes):
        data = summary.copy()
        if idx == 3:
            data = data.sort_values("total_bill", ascending=True).reset_index(drop=True)
        if idx >= 3:
            ax.bar(data["day"], data["total_bill"], color="#4c78a8", edgecolor="black")
        else:
            ax.bar(data["day"], data["total_bill"], color=["#d95f02", "#1b9e77", "#7570b3", "#e7298a"], edgecolor="black")

        ax.set_title(steps[idx][0], fontsize=10)
        ax.set_xlabel("Day")
        if idx == 0:
            ax.set_ylabel("Average total bill")
        else:
            ax.set_ylabel("")
        if idx in (0, 1):
            ax.grid(True, axis="y", linestyle="--", alpha=0.5)
        else:
            ax.grid(False)
        if idx in (1, 2, 3, 4):
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
        if idx == 4:
            ax.set_title("clean final view", fontsize=10)
            ax.set_ylabel("Average total bill")

    fig.suptitle("Five-step reduction of extraneous load", fontsize=14, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(OUTPUT_DIR / "five_panel.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def make_clean_example(summary: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(summary["day"], summary["total_bill"], color="#4c78a8")
    ax.set_title("Average total bill is highest on Saturday and Sunday", loc="left", fontsize=14)
    ax.set_xlabel("Day of week")
    ax.set_ylabel("Average total bill ($)")
    ax.grid(False)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for bar, value in zip(bars, summary["total_bill"]):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + 0.6,
            f"{value:.1f}",
            ha="center",
            va="bottom",
            fontsize=9,
        )
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "clean_example.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def write_reasoning_file() -> None:
    report = """# Weak Two reasoning

## What the bad chart does wrong

The overloaded chart adds many extraneous elements: a legend, colour used for every category, gridlines, and labels on every bar. That creates more cognitive load than the data itself needs. A reader must decode the legend, compare categories, and identify the key message while also managing the chart's visual noise.

## Why the clean chart is easier

The corrected version keeps one visual question: which day has the highest average bill? The design removes decoration, restricts the colour to one role, and keeps the message in a stronger, more readable form. This raises the data-ink ratio because more of the ink is used for the actual numbers and less for decoration.

## Week 2 rule used

The design goal is to reduce extraneous load and improve readability without hiding the real pattern.
"""
    (Path(__file__).resolve().parent / "weak_two_report.md").write_text(report, encoding="utf-8")


def summarize_reasoning() -> None:
    explanation = """
    Week 2 visual-perception insight:

    The BAD EXAMPLE chart adds extraneous load: a legend, many colours, heavy gridlines, and repeated labels. The reader has to decode the chart instead of reading the main message, so the working-memory cost rises.

    The cleaner design removes the unnecessary marks, uses one consistent colour, and keeps the title focused on the finding. This is a better use of data-ink because more of the drawing carries information, and less is just decoration.
    """
    print(explanation)


def main() -> None:
    df = load_tips_data()
    summary = prepare_summary(df)
    make_bad_example(summary)
    make_five_panel(summary)
    make_clean_example(summary)
    write_reasoning_file()
    summarize_reasoning()
    print(f"Saved charts to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
