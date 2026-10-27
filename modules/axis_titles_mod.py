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
        super().__init__(parent, text='Axis titles', padding=6)
        self.on_change = on_change
        self.presets = presets
        self.titles = {}
        self.modes = {}
        self.ratio = False
        self.controls = {}
        self.columnconfigure(1, weight=1)
        for row, axis in enumerate(('x', 'y', 'y2')):
            label = ttk.Label(self, text={'x': 'X', 'y': 'Y', 'y2': 'Secondary Y'}[axis])
            label.grid(row=row * 2, column=0, sticky='w', padx=2, pady=2)
            menu = ttk.Combobox(self, state='readonly', width=27)
            menu.grid(row=row * 2, column=1, sticky='ew', padx=2, pady=2)
            text = tk.StringVar(self)
            entry = ttk.Entry(self, textvariable=text, width=30)
            entry.grid(row=row * 2 + 1, column=1, sticky='ew', padx=2, pady=(0, 5))
            self.controls[axis] = dict(label=label, menu=menu, text=text, entry=entry)
            menu.bind('<<ComboboxSelected>>', lambda event, a=axis: self._select(a))
            entry.bind('<Return>', lambda event, a=axis: self._edit(a))
            entry.bind('<FocusOut>', lambda event, a=axis: self._edit(a))
        ttk.Button(self, text='Edit title presets', command=on_edit).grid(
            row=6, column=0, columnspan=2, sticky='ew', pady=(5, 0))
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
        control['text'].set(self.titles[key] or '')
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
        self.on_change()

    def _edit(self, axis: str) -> None:
        if self._capture(axis):
            self.on_change()

    def set_ratio(self, active: bool) -> None:
        if active != self.ratio:
            self._capture('y')
            self.ratio = active
            self._show('y')

    def sync(self, settings: dict, presets: dict) -> None:
        """Replace local state on explicit reload, without firing callbacks."""
        self.presets = presets
        self.ratio = settings.get('ratio', 'no ratio') != 'no ratio'
        for key in TITLE_KEYS:
            axis = 'y' if key == 'y_ratio_title' else key[:-6]
            default_mode = 'custom' if settings.get(key) is not None else 'auto'
            self.titles[key], self.modes[key] = resolve_title_preset(
                settings.get(key), settings.get(key + '_preset', default_mode), presets[axis])
        for axis in self.controls:
            self._show(axis)

    def apply(self, settings: dict) -> None:
        """Commit all independent labels to the existing settings dictionary."""
        for axis in self.controls:
            self._capture(axis)
        for key in TITLE_KEYS:
            settings[key] = self.titles[key]
            settings[key + '_preset'] = self.modes[key]
