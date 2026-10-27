"""Exercise real Tk callbacks with all test windows withdrawn."""

import copy
from pathlib import Path
import tempfile
import tkinter as tk
from tkinter import ttk
import unittest
from unittest.mock import patch

from modules import axis_titles_mod, config_mod, editor_mod, plot_mod, settings_mod
from modules.tally_data import Tally


def descendants(widget):
    for child in widget.winfo_children():
        yield child
        yield from descendants(child)


class PlotGuiTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(f'Tk display unavailable: {exc}')
        self.root.withdraw()
        self.addCleanup(self.root.destroy)
        self.callback_errors = []
        self.root.report_callback_exception = lambda *error: self.callback_errors.append(error)
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.config_path = Path(temp.name) / 'config.toml'
        self.presets_path = Path(temp.name) / 'axis_titles.toml'
        self.settings = settings_mod.default_plot_settings()
        self.settings.update(data_var=False, error_bar=False, x_scale='linear', y_scale='linear')
        tally = Tally('4', 4, 'neutrons', [0, 1, 2, 3], [0, 2, 4, 8],
                      [0, .1, .1, .1], 0, [0, 2, 4, 8], legend_name='Source')
        reference = copy.deepcopy(tally)
        reference.legend_name = 'Reference'
        self.patch_state = patch.multiple(
            config_mod, plot_settings=self.settings, tallies={'source': tally, 'reference': reference},
            canvas_id=None, fig_id=None, ax=None, ax2=None, xs_data={})
        self.patch_state.start()
        self.addCleanup(self.patch_state.stop)
        real_save = settings_mod.save_config
        self.start_patch(patch.object(settings_mod, 'save_config', side_effect=lambda: real_save(self.config_path)))
        self.start_patch(patch.object(settings_mod, 'CONFIG_FILE', str(self.config_path)))
        self.start_patch(patch.object(settings_mod, 'AXIS_TITLES_FILE', str(self.presets_path)))
        self.start_patch(patch.object(settings_mod, 'readsave_legend'))
        self.errors = self.start_patch(patch.object(tk.messagebox, 'showerror'))
        real_toplevel = tk.Toplevel

        def hidden_toplevel(*args, **kwargs):
            window = real_toplevel(*args, **kwargs)
            window.withdraw()
            return window

        self.start_patch(patch.object(tk, 'Toplevel', side_effect=hidden_toplevel))
        plot_mod.plot_window(self.root, ['source', 'reference'])
        self.plot = self.root.winfo_children()[0]
        self.controls = next(widget for widget in descendants(self.plot)
                             if isinstance(widget, axis_titles_mod.AxisTitleControls))

    def start_patch(self, patcher):
        result = patcher.start()
        self.addCleanup(patcher.stop)
        return result

    def tearDown(self):
        if hasattr(self, 'callback_errors'):
            self.assertEqual(self.callback_errors, [])

    def button(self, text, parent=None):
        return next(widget for widget in descendants(parent or self.plot)
                    if isinstance(widget, (tk.Button, ttk.Button, tk.Checkbutton, ttk.Checkbutton))
                    and widget.cget('text') == text)

    def choose_title(self, axis, mode):
        control = self.controls.controls[axis]
        control['menu'].current(control['ids'].index(mode))
        control['menu'].event_generate('<<ComboboxSelected>>')

    def choose_ratio(self, label):
        menu = next(widget['menu'] for widget in descendants(self.plot)
                    if isinstance(widget, tk.OptionMenu)
                    and widget['menu'].entrycget(0, 'label') == 'no ratio')
        for index in range(menu.index('end') + 1):
            if menu.entrycget(index, 'label') == label:
                menu.invoke(index)
                return
        self.fail('Ratio option not found')

    def test_title_controls_preserve_ordinary_and_ratio_edits(self):
        self.choose_title('y', 'custom')
        self.controls.controls['y']['text'].set('Ordinary flux')
        self.controls._edit('y')
        self.assertEqual(config_mod.ax.get_ylabel(), 'Ordinary flux')
        self.choose_ratio('reference')
        self.assertEqual(config_mod.ax.get_ylabel(), 'Ratio (-)')
        self.choose_title('y', 'custom')
        self.controls.controls['y']['text'].set('My ratio')
        self.controls._edit('y')
        self.assertEqual(config_mod.ax.get_ylabel(), 'My ratio')
        self.choose_ratio('no ratio')
        self.assertEqual(config_mod.ax.get_ylabel(), 'Ordinary flux')
        self.assertEqual(self.controls.controls['y']['text'].get(), 'Ordinary flux')
        self.errors.assert_not_called()

    def test_external_preset_and_config_reload_update_controls_and_average(self):
        self.choose_title('x', 'preset:energy')
        self.presets_path.write_text('[x.energy]\nvalue="Updated energy"\ndescription="Updated"\n', encoding='utf-8')
        self.settings.update(moving_average=True, moving_average_window=3)
        settings_mod.save_config()
        self.button('Reload settings').invoke()
        self.assertEqual(config_mod.ax.get_xlabel(), 'Updated energy')
        self.assertEqual(self.controls.controls['x']['text'].get(), 'Updated energy')
        self.assertTrue(any('moving average' in line.get_label() for line in config_mod.ax.lines))
        self.errors.assert_not_called()

    def test_invalid_reload_keeps_last_working_presets(self):
        self.choose_title('x', 'preset:energy')
        self.presets_path.write_text('[invalid', encoding='utf-8')
        self.button('Reload settings').invoke()
        self.assertEqual(config_mod.ax.get_xlabel(), 'energy (MeV)')
        self.errors.assert_called_once()

    def test_preset_editor_save_refreshes_plot_and_restores_grab(self):
        self.choose_title('x', 'preset:energy')
        self.button('Edit title presets').invoke()
        editor = next(widget for widget in self.plot.winfo_children() if widget.winfo_class() == 'Toplevel')
        text = next(widget for widget in descendants(editor) if isinstance(widget, tk.Text))
        text.delete('1.0', tk.END)
        text.insert('1.0', '[x.energy]\nvalue="From editor"\ndescription="Energy"\n')
        self.button('Save file', editor).invoke()
        self.assertFalse(editor.winfo_exists())
        self.assertEqual(config_mod.ax.get_xlabel(), 'From editor')
        self.assertEqual(self.root.grab_current(), self.plot)
        self.errors.assert_not_called()

    def test_editor_and_plot_window_close_protocols_restore_grabs(self):
        editor = editor_mod.open_lib(self.config_path, self.plot, ['source'], on_save=lambda: True)
        self.assertEqual(editor.master, self.plot)
        self.assertEqual(str(editor.transient()), str(self.plot))
        self.assertEqual(self.root.grab_current(), editor)
        editor.tk.call(editor.protocol('WM_DELETE_WINDOW'))
        self.assertFalse(editor.winfo_exists())
        self.assertEqual(self.root.grab_current(), self.plot)
        self.plot.tk.call(self.plot.protocol('WM_DELETE_WINDOW'))
        self.assertIsNone(self.root.grab_current())

    def test_average_checkbox_and_manual_replot(self):
        self.button('Show moving-average overlay').invoke()
        self.assertTrue(any('moving average' in line.get_label() for line in config_mod.ax.lines))
        self.button('disable instant changes').invoke()
        self.button('Show moving-average overlay').invoke()
        self.assertTrue(any('moving average' in line.get_label() for line in config_mod.ax.lines))
        self.button('Replot').invoke()
        self.assertFalse(any('moving average' in line.get_label() for line in config_mod.ax.lines))
        self.errors.assert_not_called()

    def test_reopening_plot_restores_preset_and_average(self):
        self.choose_title('x', 'preset:energy')
        self.button('Show moving-average overlay').invoke()
        self.button('Quit').invoke()
        self.assertTrue(settings_mod.read_config(self.config_path))
        plot_mod.plot_window(self.root, ['source', 'reference'])
        self.plot = self.root.winfo_children()[0]
        controls = next(widget for widget in descendants(self.plot)
                        if isinstance(widget, axis_titles_mod.AxisTitleControls))
        self.assertEqual(controls.controls['x']['menu'].current(), 1)
        self.assertEqual(config_mod.ax.get_xlabel(), 'energy (MeV)')
        self.assertTrue(any('moving average' in line.get_label() for line in config_mod.ax.lines))
        self.errors.assert_not_called()

    def test_settings_editor_saving_refreshes_config(self):
        self.button('Settings editor').invoke()
        editor = next(widget for widget in self.plot.winfo_children() if widget.winfo_class() == 'Toplevel')
        text = next(widget for widget in descendants(editor) if isinstance(widget, tk.Text))
        text.delete('1.0', tk.END)
        text.insert('1.0', '[axes]\ny_title="Editor title"\ny_scale="linear"\nx_scale="linear"\n'
                          '[plot]\nmoving_average=true\nmoving_average_window=3\n')
        self.button('Save file', editor).invoke()
        self.assertFalse(editor.winfo_exists())
        self.assertEqual(config_mod.ax.get_ylabel(), 'Editor title')
        self.assertEqual(self.controls.controls['y']['text'].get(), 'Editor title')
        self.assertTrue(any('moving average' in line.get_label() for line in config_mod.ax.lines))
        self.errors.assert_not_called()

    def test_invalid_average_input_keeps_last_valid_settings(self):
        spinbox = next(widget for widget in descendants(self.plot)
                       if isinstance(widget, ttk.Spinbox) and widget.cget('increment') == 2)
        spinbox.set('4')
        self.button('Replot').configure(state='normal')
        self.button('Replot').invoke()
        self.assertEqual(config_mod.plot_settings['moving_average_window'], 5)
        self.assertEqual(spinbox.get(), '5')
        self.errors.assert_called_once()


if __name__ == '__main__':
    unittest.main()
