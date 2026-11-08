# Task C — Interaction contract

**Default state:** all four modes' monthly blended fares are visible for complete months April 2025–August 2026, measured as PKR revenue per fare-system journey.

**Controls:** each mode checkbox hides or restores that mode's line; it does not change the data, dates, scale, or other modes. The categories are exclusive, but the fares are journeys, not vehicle boardings. **Reset: all modes** restores the initial view. `partC_default.png` is saved before any interaction.

**Wrong conclusion to guard against:** a mode filter might invite the reader to add mode-specific fare measures or compare them to route boardings as if they were the same unit. The view presents only blended PKR per journey, labels the measure and period, and does not provide an additive boarding total. Mode categories are mutually exclusive; the default reset is always available.

Run `python weak-7\partC_interactive.py --interactive` from the repository root in an environment with Matplotlib's Tk backend. The default script run writes a static PNG without opening a window. The full pipeline is `python weak-7\run_week7.py`; append `--interactive` to show the controls after exporting.
