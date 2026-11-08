"""Run the complete Week 7 workflow from raw sources to figures."""

from __future__ import annotations

import argparse

from partA_process import process
from partB_charts import make_charts
from partC_interactive import build_interactive
from partD_screen import make_dashboard


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interactive", action="store_true", help="open Task C's Matplotlib controls after exporting")
    args = parser.parse_args()

    process()
    charts, breaks = make_charts()
    interactive_figure = build_interactive(show=False)
    dashboard = make_dashboard()
    print("\nCompleted Week 7 outputs:")
    for chart in charts:
        print(f"  {chart.name}")
    print(f"  partC_default.png")
    print(f"  {dashboard.name}")
    print("Map class breaks:", ", ".join(f"{value:,.0f}" for value in breaks))
    if args.interactive:
        import matplotlib.pyplot as plt

        plt.show()
    else:
        import matplotlib.pyplot as plt

        plt.close(interactive_figure)


if __name__ == "__main__":
    main()
