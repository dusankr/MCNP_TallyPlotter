"""Save figures through a dialog owned by the plot window."""

from pathlib import Path
from tkinter import filedialog, messagebox


def save_figure(figure, settings: dict, parent) -> bool:
    """Save a figure, restoring its display size and transient save state."""
    original_size = figure.get_size_inches().copy()
    try:
        filename = filedialog.asksaveasfilename(
            parent=parent,
            initialdir=settings["export_dir_path"],
            title="Save figure",
            filetypes=[("PNG files", "*.png"), ("PDF files", "*.pdf"),
                       ("SVG files", "*.svg"), ("EPS files", "*.eps"),
                       ("PS files", "*.ps")],
            defaultextension=".png",
        )
        if not filename:
            return False
        path = Path(filename)
        figure.set_size_inches(
            settings["fig_x_dimension"] / 2.54,
            settings["fig_y_dimension"] / 2.54,
        )
        figure.savefig(path, format=path.suffix[1:],
                       dpi=int(settings["fig_dpi"]), bbox_inches="tight")
        settings["export_dir_path"] = path.parent
        settings["fig_format"] = path.suffix[1:]
        return True
    except PermissionError:
        messagebox.showerror("Save error", "The file cannot be written. Check whether it is open in another application.", parent=parent)
    except Exception as exc:
        # Saving and native dialogs are an application boundary.
        messagebox.showerror("Save error", f"The figure could not be saved: {exc}", parent=parent)
    finally:
        settings["save_fig"] = False
        figure.set_size_inches(original_size)
    return False
