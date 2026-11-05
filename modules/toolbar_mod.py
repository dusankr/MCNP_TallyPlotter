"""Notify plot controls when toolbar navigation changes the visible ranges."""

from collections.abc import Callable

from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk


class SyncedNavigationToolbar(NavigationToolbar2Tk):
    """Publish completed zoom, pan, and history actions without tracking redraws."""

    def __init__(self, canvas, parent, on_view_changed: Callable[[], None]) -> None:
        self._on_view_changed = on_view_changed
        self._pan_start_view = None
        super().__init__(canvas, parent)

    def _view(self) -> tuple:
        return tuple((axis, axis.get_xlim(), axis.get_ylim())
                     for axis in self.canvas.figure.axes)

    def _notify_if_changed(self, before) -> None:
        if before is not None and self._view() != before:
            self._on_view_changed()

    def release_zoom(self, event) -> None:
        before = self._view()
        super().release_zoom(event)
        self._notify_if_changed(before)

    def press_pan(self, event) -> None:
        self._pan_start_view = self._view()
        super().press_pan(event)

    def release_pan(self, event) -> None:
        before = self._pan_start_view
        super().release_pan(event)
        self._pan_start_view = None
        self._notify_if_changed(before)

    def home(self, *args) -> None:
        before = self._view()
        super().home(*args)
        self._notify_if_changed(before)

    def back(self, *args) -> None:
        before = self._view()
        super().back(*args)
        self._notify_if_changed(before)

    def forward(self, *args) -> None:
        before = self._view()
        super().forward(*args)
        self._notify_if_changed(before)

    def destroy(self) -> None:
        # Navigation schedules Tk idle draws; cancel them when closing the plot.
        idle_draw = self.canvas._idle_draw_id
        if idle_draw is not None:
            self.canvas.get_tk_widget().after_cancel(idle_draw)
            self.canvas._idle_draw_id = None
        super().destroy()
