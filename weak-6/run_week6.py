"""Run the Week 6 audit, charts, board figure, and optional interactive view."""

from partA_process import process
from partB_charts import make_charts
from partC_figure import make_figure
from partD_interactive import make_interactive


def main() -> None:
    process()
    for chart in make_charts():
        print(f"Wrote weak-6/charts/{chart}")
    path, metrics = make_figure()
    print(f"Wrote {path}")
    print(f"Board figure metrics: {metrics}")
    print(f"Wrote {make_interactive()}")


if __name__ == "__main__":
    main()
