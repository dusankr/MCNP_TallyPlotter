"""Resolve Tk window ownership when native ttk popups hold the grab."""

import tkinter as tk


def current_grab(owner: tk.Misc) -> tk.Misc | None:
    """Return the grabbed Python widget, ignoring Tcl-only popup windows."""
    try:
        return owner.grab_current()
    except KeyError:
        # ttk creates combobox popdowns in Tcl, outside Tkinter's widget registry.
        return None


def dialog_parent(owner: tk.Misc) -> tk.Misc:
    """Prefer a modal editor, falling back to the owning window for ttk popups."""
    grabbed = current_grab(owner)
    return (grabbed if grabbed is not None else owner).winfo_toplevel()
