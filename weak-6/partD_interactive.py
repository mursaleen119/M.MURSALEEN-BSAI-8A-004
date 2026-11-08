"""Build the Week 6 optional interactive meter-energy view."""

from __future__ import annotations

import plotly.graph_objects as go

from week6_common import CHART_DIR, load_clean, month_boundary_energy


def make_interactive() -> str:
    """Export a mode-filterable monthly energy chart as a self-contained HTML file."""
    data = load_clean()
    fig = go.Figure()
    for zone in sorted(data["daily"]["zone"].unique()):
        monthly = month_boundary_energy(data["daily"], zone)
        fig.add_trace(
            go.Scatter(
                x=[period.to_timestamp() for period in monthly.index],
                y=monthly.values,
                mode="lines+markers",
                name=zone,
                connectgaps=False,
                hovertemplate="%{x|%b %Y}<br>%{y:,.0f} MWh<extra>%{fullData.name}</extra>",
            )
        )
    fig.update_layout(
        title={
            "text": "Monthly energy delivered by supply zone (meter differences)",
            "x": 0.02,
            "xanchor": "left",
        },
        xaxis_title="Month",
        yaxis_title="Energy delivered (MWh)",
        hovermode="x unified",
        legend_title="Zone (click to filter)",
        template="plotly_white",
        annotations=[
            {
                "text": (
                    "Monthly change from the first-day meter reading to the next month's first-day reading; "
                    "missing boundary readings are not estimated. Complete months Apr 2025–Aug 2026. "
                    "Source: synthetic Week 6 grid_daily.csv."
                ),
                "xref": "paper",
                "yref": "paper",
                "x": 0,
                "y": -0.22,
                "showarrow": False,
                "xanchor": "left",
                "font": {"size": 10},
            }
        ],
        margin={"b": 105},
    )
    CHART_DIR.mkdir(parents=True, exist_ok=True)
    destination = CHART_DIR / "partD_interactive.html"
    fig.write_html(destination, include_plotlyjs=True, full_html=True)
    html = destination.read_text(encoding="utf-8")
    destination.write_text(
        "\n".join(line.rstrip() for line in html.splitlines()) + "\n",
        encoding="utf-8",
    )
    return str(destination)


if __name__ == "__main__":
    print(f"Wrote {make_interactive()}")
