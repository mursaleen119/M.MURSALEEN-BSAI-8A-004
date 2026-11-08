"""Interactive fare-mix view with a static default-state export."""

from __future__ import annotations

import argparse
import sys

if "--interactive" in sys.argv:
    import matplotlib

    matplotlib.use("TkAgg")
else:
    import matplotlib

    matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.widgets import Button, CheckButtons

from week7_common import CHART_DIR, MODE_COLORS, MODES, load_clean, style_axes


ROOT = __import__("pathlib").Path(__file__).resolve().parent
COMPLETE_MONTHS = pd.period_range("2025-04", "2026-08", freq="M").astype(str).tolist()


def build_interactive(show: bool = True) -> plt.Figure:
    style_axes()
    fares = load_clean()["fares"]
    monthly = fares.loc[fares["month"].isin(COMPLETE_MONTHS)].groupby(
        ["month", "mode"], as_index=False
    )[["trips", "revenue_pkr"]].sum()
    monthly["mean_fare"] = monthly["revenue_pkr"] / monthly["trips"]
    fig = plt.figure(figsize=(11, 6.3))
    ax = fig.add_axes([0.09, 0.19, 0.66, 0.67])
    check_ax = fig.add_axes([0.79, 0.43, 0.17, 0.31])
    reset_ax = fig.add_axes([0.81, 0.29, 0.14, 0.075])
    lines = {}
    x = np.arange(len(COMPLETE_MONTHS))
    for mode in MODES:
        group = monthly.loc[monthly["mode"].eq(mode)].set_index("month").reindex(COMPLETE_MONTHS)
        lines[mode], = ax.plot(
            x,
            group["mean_fare"],
            color=MODE_COLORS[mode],
            marker={"Metro": "o", "BRT": "s", "Bus": "^", "Ferry": "D"}[mode],
            linewidth=1.8,
            markersize=4,
            label=mode,
        )
    ax.set_xticks(x[::2], [pd.Period(COMPLETE_MONTHS[i]).strftime("%b\n%Y") for i in x[::2]])
    ax.set_xlim(-0.4, len(x) - 0.6)
    ax.set_ylabel("Mean fare (PKR per journey)")
    ax.set_xlabel("Complete month")
    ax.set_title("Blended fares diverge by mode", loc="left", fontweight="bold")
    fig.suptitle("Filter the fare series by mode", x=0.09, y=0.98, ha="left", fontsize=15, fontweight="bold")
    fig.text(
        0.09,
        0.09,
        "Each point is monthly revenue ÷ journeys (PKR/journey); complete months 2025-04–2026-08. "
        "Exclusive mode categories; this view contains journeys, not boardings.",
        fontsize=8,
    )
    checks = CheckButtons(check_ax, MODES, [True] * len(MODES))
    for mode, label in zip(MODES, checks.labels):
        label.set_color(MODE_COLORS[mode])
    reset = Button(reset_ax, "Reset: all modes")

    def toggle(mode: str) -> None:
        lines[mode].set_visible(not lines[mode].get_visible())
        fig.canvas.draw_idle()

    def restore(_event: object) -> None:
        for index, checked in enumerate(checks.get_status()):
            if not checked:
                checks.set_active(index)

    checks.on_clicked(toggle)
    reset.on_clicked(restore)
    fig._week7_widgets = (checks, reset)
    CHART_DIR.mkdir(parents=True, exist_ok=True)
    default_path = CHART_DIR / "partC_default.png"
    fig.savefig(default_path, dpi=300, bbox_inches="tight", facecolor="white")
    if show:
        plt.show()
    print(f"Static interactive default saved to {default_path}")
    return fig


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interactive", action="store_true", help="open the mode checkboxes and Reset control")
    args = parser.parse_args()
    build_interactive(show=args.interactive)


if __name__ == "__main__":
    main()
