#!/usr/bin/env python3

"""Display the numeric values of a tally in a separate window."""

import tkinter as tk
from tkinter import ttk

from modules import config_mod


def tally_value_rows(tally):
    """Return the real energy-bin rows, followed by the reported total."""
    rows = list(
        zip(
            tally.energy[1:],
            tally.flux[1:],
            tally.error[1:],
            tally.flux_normalized[1:],
        )
    )

    if tally.total is not None:
        rows.append(("Total", tally.total, tally.total_error, None))

    return rows


def _format_number(value):
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return f"{value:.8E}"


def open_tally_values_window(parent, tally_key, tally):
    """Open a scrollable table containing one tally's values."""
    window = tk.Toplevel(parent)
    window.title(f"Tally values - {tally_key}")
    window.geometry("760x400")
    window.minsize(560, 260)
    window.transient(parent)
    window.columnconfigure(0, weight=1)
    window.rowconfigure(1, weight=1)

    particle = getattr(tally, "particle", "") or "unknown"
    tally_number = getattr(tally, "tally_num", "") or tally_key
    ttk.Label(
        window,
        text=f"Tally {tally_number}   Particle: {particle}",
        padding=(10, 8),
    ).grid(row=0, column=0, sticky="w")

    table_frame = ttk.Frame(window, padding=(10, 0, 10, 8))
    table_frame.grid(row=1, column=0, sticky="nsew")
    table_frame.columnconfigure(0, weight=1)
    table_frame.rowconfigure(0, weight=1)

    columns = ("bin", "energy", "value", "error", "normalized")
    table = ttk.Treeview(table_frame, columns=columns, show="headings")
    headings = {
        "bin": "Bin",
        "energy": "Energy upper bound (MeV)",
        "value": "Tally value",
        "error": "Relative error",
        "normalized": "Value / MeV",
    }
    widths = {"bin": 55, "energy": 180, "value": 155, "error": 130, "normalized": 155}

    for column in columns:
        table.heading(column, text=headings[column])
        table.column(
            column,
            width=widths[column],
            minwidth=50,
            anchor="center" if column == "bin" else "e",
            stretch=column != "bin",
        )

    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=table.yview)
    table.configure(yscrollcommand=scrollbar.set)
    table.grid(row=0, column=0, sticky="nsew")
    scrollbar.grid(row=0, column=1, sticky="ns")

    bin_number = 0
    for energy, value, error, normalized in tally_value_rows(tally):
        if energy == "Total":
            displayed = ("", "Total", _format_number(value), _format_number(error), "")
            table.insert("", "end", values=displayed, tags=("total",))
        else:
            bin_number += 1
            displayed = (
                bin_number,
                _format_number(energy),
                _format_number(value),
                _format_number(error),
                _format_number(normalized),
            )
            table.insert("", "end", values=displayed)

    table.tag_configure("total", font=("TkDefaultFont", 9, "bold"))

    ttk.Button(window, text="Close", command=window.destroy).grid(
        row=2, column=0, sticky="e", padx=10, pady=(0, 10)
    )
    return window


def open_tally_table_from_event(event, treeview, parent):
    """Open the tally represented by the row under a double-click event."""
    if treeview.identify_region(event.x, event.y) not in ("tree", "cell"):
        return None

    tally_key = treeview.identify_row(event.y)
    tally = config_mod.tallies.get(tally_key)
    if tally is None:
        return None

    return open_tally_values_window(parent, tally_key, tally)
