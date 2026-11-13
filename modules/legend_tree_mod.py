"""Edit legend labels directly in the main tally tree."""

import tkinter as tk
from tkinter import messagebox, ttk

from modules import config_mod, settings_mod


def refresh_legend_column(tree: ttk.Treeview) -> None:
    """Refresh loaded legend labels without changing row order or checkbox state."""
    for tally_key in tree.get_children(''):
        tally = config_mod.tallies.get(tally_key)
        if tally is not None:
            tree.set(tally_key, 'Legend', tally.legend_name)


def edit_legend_from_event(event, tree: ttk.Treeview) -> bool:
    """Open an entry over a double-clicked Legend cell; return whether handled."""
    if tree.identify_region(event.x, event.y) != 'cell':
        return False
    tally_key = tree.identify_row(event.y)
    column = tree.identify_column(event.x)
    if tally_key not in config_mod.tallies or not column.startswith('#'):
        return False
    column_index = int(column[1:]) - 1
    columns = tree['columns']
    if not 0 <= column_index < len(columns) or columns[column_index] != 'Legend':
        return False

    bounds = tree.bbox(tally_key, column)
    if not bounds:
        return True

    editor = ttk.Entry(tree)
    editor.insert(0, config_mod.tallies[tally_key].legend_name)
    editor.place(x=bounds[0], y=bounds[1], width=bounds[2], height=bounds[3])
    editor.focus_set()
    editor.select_range(0, tk.END)
    saving = False

    def save(_event=None):
        nonlocal saving
        if saving or not editor.winfo_exists():
            return
        saving = True
        try:
            label = settings_mod.update_tally_legend(tally_key, editor.get())
        except (OSError, ValueError, KeyError) as exc:
            messagebox.showerror('Legend update failed', str(exc), parent=tree.winfo_toplevel())
            editor.after_idle(editor.focus_set)
        else:
            if tree.exists(tally_key):
                tree.set(tally_key, 'Legend', label)
            editor.destroy()
        finally:
            saving = False

    def cancel(_event=None):
        editor.destroy()

    editor.bind('<Return>', save)
    editor.bind('<FocusOut>', save)
    editor.bind('<Escape>', cancel)
    return True
