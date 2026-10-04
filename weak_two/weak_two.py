from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

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


def make_bad_example(df: pd.DataFrame) -> None:
    summary = df.groupby("day", as_index=False)["total_bill"].mean().sort_values("total_bill", ascending=False)

    fig, ax = plt.subplots(figsize=(11, 7))
    colors = sns.color_palette("husl", n_colors=len(summary))
    bars = ax.bar(
        summary["day"],
        summary["total_bill"],
        color=colors,
        edgecolor="black",
        linewidth=1.4,
    )

    ax.set_title("BAD EXAMPLE: Total Bill by Day", fontsize=16, fontweight="bold")
    ax.set_xlabel("Day")
    ax.set_ylabel("Average total bill")
    ax.grid(True, axis="y", linestyle="--", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.legend(bars, summary["day"], title="Day", loc="upper right")

    for bar, value in zip(bars, summary["total_bill"]):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + 1,
            f"{value:.1f}",
            ha="center",
            va="bottom",
            rotation=90,
            fontsize=8,
        )

    plt.xticks(rotation=45)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "bad_example.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def make_clean_example(df: pd.DataFrame) -> None:
    summary = df.groupby("day", as_index=False)["total_bill"].mean().sort_values("total_bill", ascending=False)

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(
        data=summary,
        x="day",
        y="total_bill",
        color="#4c78a8",
        ax=ax,
    )

    ax.set_title("Average total bill is highest on Saturday and Sunday", loc="left", fontsize=14)
    ax.set_xlabel("Day of week")
    ax.set_ylabel("Average total bill ($)")
    ax.grid(False)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "clean_example.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def summarize_reasoning() -> None:
    explanation = """
    Week 2 visual-perception insight:

    The bad example adds many extraneous elements: a legend for every bar, gridlines in both directions,
    repeated labels, and a design that makes the reader decode color and text instead of noticing the main message.
    This raises cognitive load because the reader must process many chunks at once.

    The cleaner chart removes the noise, keeps a single message, and presents the data with fewer visual tasks.
    The result is a higher data-ink ratio because more visual marks are used to encode the real values and fewer
    marks are used for decoration.
    """
    print(explanation)


def main() -> None:
    df = load_tips_data()
    make_bad_example(df)
    make_clean_example(df)
    summarize_reasoning()
    print(f"Saved charts to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
