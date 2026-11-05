"""Independent axis-title controls, including a separate ratio title."""

import tkinter as tk
from tkinter import ttk


TITLE_KEYS = ('x_title', 'y_title', 'y2_title', 'y_ratio_title')


def resolve_title_preset(title, mode: str, presets: dict):
    """Resolve a stored selection; retain its text if a named preset was removed."""
    if mode == 'auto':
        return None, 'auto'
    if mode.startswith('preset:') and mode[7:] in presets:
        return presets[mode[7:]]['value'], mode
    return title, 'custom' if title is not None else 'auto'


class AxisTitleControls(ttk.LabelFrame):
    """Keep title edits local until the owning plot applies its settings."""

    def __init__(self, parent, settings: dict, presets: dict, on_change, on_edit) -> None:
        super().__init__(parent, text='Axis and plot titles', padding=6)
        self.on_change = on_change
        self.presets = presets
        self.titles = {}
        self.modes = {}
        self.ratio = False
        self.controls = {}
        self._updating = False
        self._pending_change = None
        self.columnconfigure(1, weight=1)
        for row, axis in enumerate(('x', 'y', 'y2')):
            label = ttk.Label(self, text={'x': 'X', 'y': 'Y', 'y2': 'XS'}[axis])
            label.grid(row=row * 2, column=0, sticky='w', padx=2, pady=2)
            menu = ttk.Combobox(self, state='readonly', width=16)
            menu.grid(row=row * 2, column=1, sticky='ew', padx=2, pady=2)
            text = tk.StringVar(self)
            entry = ttk.Entry(self, textvariable=text, width=16)
            entry.grid(row=row * 2 + 1, column=1, sticky='ew', padx=2, pady=(0, 5))
            self.controls[axis] = dict(label=label, menu=menu, text=text, entry=entry)
            menu.bind('<<ComboboxSelected>>', lambda event, a=axis: self._select(a))
            entry.bind('<Return>', lambda event, a=axis: self._edit(a))
            entry.bind('<FocusOut>', lambda event, a=axis: self._edit(a))
            text.trace_add('write', lambda *args, a=axis: self._text_changed(a))
        ttk.Label(self, text='Plot').grid(row=6, column=0, sticky='w', padx=2, pady=2)
        plot_menu = ttk.Combobox(self, state='readonly', width=16, values=('No title', 'Custom'))
        plot_menu.grid(row=6, column=1, sticky='ew', padx=2, pady=2)
        plot_text = tk.StringVar(self)
        plot_entry = ttk.Entry(self, textvariable=plot_text, width=16)
        plot_entry.grid(row=7, column=1, sticky='ew', padx=2, pady=(0, 5))
        self.plot_title = dict(menu=plot_menu, text=plot_text, entry=plot_entry)
        self.plot_enabled = False
        self.plot_text = None
        plot_menu.bind('<<ComboboxSelected>>', self._select_plot_title)
        plot_entry.bind('<Return>', self._edit_plot_title)
        plot_entry.bind('<FocusOut>', self._edit_plot_title)
        plot_text.trace_add('write', self._plot_text_changed)
        ttk.Button(self, text='Presets editor', command=on_edit).grid(
            row=8, column=0, columnspan=2, sticky='ew', pady=(5, 0))
        self.sync(settings, presets)

    def _key(self, axis: str) -> str:
        return 'y_ratio_title' if axis == 'y' and self.ratio else axis + '_title'

    def _show(self, axis: str) -> None:
        key = self._key(axis)
        control = self.controls[axis]
        ids = ['auto'] + ['preset:' + name for name in self.presets[axis]] + ['custom']
        labels = ['Auto'] + [entry['description'] for entry in self.presets[axis].values()] + ['Custom']
        control['ids'] = ids
        control['menu']['values'] = labels
        control['menu'].current(ids.index(self.modes[key]))
        previous = self._updating
        self._updating = True
        try:
            control['text'].set(self.titles[key] or '')
        finally:
            self._updating = previous
        control['entry']['state'] = 'normal' if self.modes[key] == 'custom' else 'disabled'
        if axis == 'y':
            control['label']['text'] = 'Y (ratio)' if self.ratio else 'Y'

    def _capture(self, axis: str) -> bool:
        key = self._key(axis)
        if self.modes[key] != 'custom':
            return False
        text = self.controls[axis]['text'].get().strip() or None
        changed = text != self.titles[key]
        self.titles[key] = text
        return changed

    def _select(self, axis: str) -> None:
        self._capture(axis)
        key = self._key(axis)
        control = self.controls[axis]
        mode = control['ids'][control['menu'].current()]
        if mode == 'custom':
            self.modes[key] = mode
        else:
            self.titles[key], self.modes[key] = resolve_title_preset(
                self.titles[key], mode, self.presets[axis])
        self._show(axis)
        self._notify_now()

    def _edit(self, axis: str) -> None:
        if self._capture(axis) or self._pending_change is not None:
            self._notify_now()

    def _text_changed(self, axis: str) -> None:
        if not self._updating and self.modes.get(self._key(axis)) == 'custom':
            self._capture(axis)
            self._queue_change()

    def _queue_change(self) -> None:
        self._cancel_pending()
        self._pending_change = self.after(150, self._deliver_change)

    def _cancel_pending(self) -> None:
        if self._pending_change is not None:
            self.after_cancel(self._pending_change)
            self._pending_change = None

    def _deliver_change(self) -> None:
        self._pending_change = None
        self.on_change()

    def _notify_now(self) -> None:
        self._cancel_pending()
        self.on_change()

    def _capture_plot_title(self) -> bool:
        text = self.plot_title['text'].get().strip() or None
        changed = text != self.plot_text
        self.plot_text = text
        return changed

    def _show_plot_title(self) -> None:
        previous = self._updating
        self._updating = True
        try:
            self.plot_title['menu'].current(1 if self.plot_enabled else 0)
            self.plot_title['text'].set(self.plot_text or '')
            self.plot_title['entry'].configure(state='normal' if self.plot_enabled else 'disabled')
        finally:
            self._updating = previous

    def _select_plot_title(self, event=None) -> None:
        self._capture_plot_title()
        self.plot_enabled = self.plot_title['menu'].current() == 1
        self._show_plot_title()
        self._notify_now()

    def _plot_text_changed(self, *args) -> None:
        if not self._updating and self.plot_enabled:
            self._capture_plot_title()
            self._queue_change()

    def _edit_plot_title(self, event=None) -> None:
        if self._capture_plot_title() or self._pending_change is not None:
            self._notify_now()

    def set_ratio(self, active: bool) -> None:
        if active != self.ratio:
            self._capture('y')
            self.ratio = active
            self._show('y')

    def sync(self, settings: dict, presets: dict) -> None:
        """Replace local state on explicit reload, without firing callbacks."""
        self._cancel_pending()
        self.presets = presets
        self.ratio = settings.get('ratio', 'no ratio') != 'no ratio'
        for key in TITLE_KEYS:
            axis = 'y' if key == 'y_ratio_title' else key[:-6]
            default_mode = 'custom' if settings.get(key) is not None else 'auto'
            self.titles[key], self.modes[key] = resolve_title_preset(
                settings.get(key), settings.get(key + '_preset', default_mode), presets[axis])
        for axis in self.controls:
            self._show(axis)
        self.plot_text = settings.get('fig_title')
        self.plot_enabled = bool(settings.get('fig_title_switch', False))
        self._show_plot_title()

    def apply(self, settings: dict) -> None:
        """Commit all independent labels to the existing settings dictionary."""
        for axis in self.controls:
            self._capture(axis)
        for key in TITLE_KEYS:
            settings[key] = self.titles[key]
            settings[key + '_preset'] = self.modes[key]
        self._capture_plot_title()
        settings['fig_title'] = self.plot_text
        settings['fig_title_switch'] = self.plot_enabled

    def destroy(self) -> None:
        self._cancel_pending()
        super().destroy()
