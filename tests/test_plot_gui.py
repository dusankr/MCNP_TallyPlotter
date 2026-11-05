"""Exercise real Tk callbacks with all test windows withdrawn."""

import copy
from pathlib import Path
import tempfile
import tkinter as tk
from tkinter import ttk
import unittest
from unittest.mock import patch
from matplotlib.backend_bases import MouseEvent, MouseButton
from numpy.testing import assert_allclose

from modules import axis_titles_mod, config_mod, editor_mod, plot_mod, settings_mod
from modules import read_mod, window_mod
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
        self.multiplier_path = Path(temp.name) / 'multipliers.toml'
        self.multiplier_path.write_text('[multipliers.double]\nvalue=2.0\ndescription="Double"\n', encoding='utf-8')
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
        self.start_patch(patch.object(settings_mod, 'MULTIPLIERS_FILE', str(self.multiplier_path)))
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

    def average_selector(self):
        return next(widget for widget in descendants(self.plot)
                    if isinstance(widget, ttk.Combobox) and tuple(widget.cget('values')) ==
                    ('Original only', 'Original + average', 'Average only'))

    def choose_average(self, label):
        self.average_selector().set(label)

    def choose_ratio(self, label):
        menu = next(widget for widget in descendants(self.plot)
                    if isinstance(widget, ttk.Combobox) and widget.cget('values')[0] == 'no ratio')
        self.assertIn(label, menu.cget('values'))
        menu.set(label)

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
        self.settings.update(moving_average_mode='average', moving_average_window=3)
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
        self.button('Presets editor', self.controls).invoke()
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

    def test_average_selector_and_manual_replot(self):
        self.choose_average('Original + average')
        self.assertTrue(any('moving average' in line.get_label() for line in config_mod.ax.lines))
        self.button('disable instant changes').invoke()
        self.choose_average('Original only')
        self.assertTrue(any('moving average' in line.get_label() for line in config_mod.ax.lines))
        self.button('Replot').invoke()
        self.assertFalse(any('moving average' in line.get_label() for line in config_mod.ax.lines))
        self.errors.assert_not_called()

    def test_reopening_plot_restores_preset_and_average(self):
        self.choose_title('x', 'preset:energy')
        self.choose_average('Average only')
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
        self.choose_average('Original + average')
        spinbox = next(widget for widget in descendants(self.plot)
                       if isinstance(widget, ttk.Spinbox) and widget.cget('increment') == 2)
        spinbox.set('4')
        self.button('Replot').configure(state='normal')
        self.button('Replot').invoke()
        self.assertEqual(config_mod.plot_settings['moving_average_window'], 5)
        self.assertEqual(spinbox.get(), '5')
        self.errors.assert_called_once()

    def test_mode_switches_control_states_and_preserve_error_bar_preference(self):
        errors = self.button('show/hide error bars')
        spinbox = next(widget for widget in descendants(self.plot)
                       if isinstance(widget, ttk.Spinbox) and widget.cget('increment') == 2)
        self.assertEqual(str(spinbox.cget('state')), 'disabled')
        errors.invoke()
        self.assertTrue(self.settings['error_bar'])
        self.choose_average('Average only')
        self.assertEqual(str(errors.cget('state')), 'disabled')
        self.assertEqual(str(spinbox.cget('state')), 'normal')
        self.assertTrue(self.settings['error_bar'])
        self.assertEqual(len(config_mod.ax.containers), 0)
        self.button('disable instant changes').invoke()
        self.choose_average('Original only')
        self.assertEqual(str(errors.cget('state')), 'normal')
        self.assertEqual(str(spinbox.cget('state')), 'disabled')
        self.assertEqual(len(config_mod.ax.containers), 0)
        self.button('Replot').invoke()
        self.assertEqual(len(config_mod.ax.containers), 2)
        self.assertTrue(self.settings['error_bar'])

    def test_original_two_tab_layout_and_replot_footer(self):
        self.plot.transient('')
        self.plot.overrideredirect(True)
        self.plot.geometry('1200x700-20000-20000')
        self.plot.deiconify()
        self.plot.update()
        notebook = next(widget for widget in descendants(self.plot) if isinstance(widget, ttk.Notebook))
        names = [notebook.tab(tab, 'text') for tab in notebook.tabs()]
        self.assertEqual(names, ['Plot settings', 'Average'])
        first_tab, second_tab = [notebook.nametowidget(tab) for tab in notebook.tabs()]
        self.assertTrue(str(self.controls).startswith(str(first_tab) + '.'))
        self.assertEqual(self.controls.cget('text'), 'Axis and plot titles')
        self.assertTrue(str(self.average_selector()).startswith(str(second_tab) + '.'))
        for label in ('Save figure', 'Settings editor', 'Reload settings'):
            self.assertTrue(str(self.button(label)).startswith(str(first_tab) + '.'))
        groups = [widget.cget('text') for widget in first_tab.winfo_children()]
        self.assertEqual(groups, ['Plot settings I', 'Plot settings II'])
        for tab in (first_tab, second_tab):
            notebook.select(tab)
            self.plot.update()
            for label in ('Replot', 'Quit', 'disable instant changes'):
                button = self.button(label)
                self.assertTrue(button.winfo_ismapped())
                self.assertLessEqual(button.winfo_rooty() + button.winfo_height(),
                                     self.plot.winfo_rooty() + self.plot.winfo_height())
        self.errors.assert_not_called()

    def wait_for_title_edit(self):
        done = tk.BooleanVar(self.root, value=False)
        self.root.after(220, lambda: done.set(True))
        self.root.wait_variable(done)

    def test_custom_title_typing_redraws_once_with_latest_text(self):
        self.choose_title('x', 'custom')
        with patch.object(plot_mod.plot_core, 'plot_to_canvas', wraps=plot_mod.plot_core.plot_to_canvas) as draw:
            self.controls.controls['x']['text'].set('First')
            self.controls.controls['x']['text'].set('Latest axis title')
            self.wait_for_title_edit()
            self.assertEqual(config_mod.ax.get_xlabel(), 'Latest axis title')
            draw.assert_called_once()

    def test_title_focus_out_redraws_even_when_settings_already_captured_edit(self):
        self.choose_title('y', 'custom')
        self.controls.controls['y']['text'].set('Updated Y title')
        # Other controls can save variables before the title's FocusOut callback.
        self.controls.apply(self.settings)
        self.controls._edit('y')
        self.assertEqual(config_mod.ax.get_ylabel(), 'Updated Y title')

    def test_plot_title_no_title_and_custom_preserve_text_and_reload(self):
        control = self.controls.plot_title
        self.assertEqual(control['menu'].get(), 'No title')
        control['menu'].current(1)
        control['menu'].event_generate('<<ComboboxSelected>>')
        control['text'].set('My plot title')
        self.controls._edit_plot_title()
        self.assertEqual(config_mod.ax.get_title(), 'My plot title')
        control['menu'].current(0)
        control['menu'].event_generate('<<ComboboxSelected>>')
        self.assertEqual(config_mod.ax.get_title(), '')
        self.assertEqual(self.settings['fig_title'], 'My plot title')
        self.assertFalse(self.settings['fig_title_switch'])
        self.button('Reload settings').invoke()
        self.assertEqual(control['menu'].get(), 'No title')
        self.assertEqual(control['text'].get(), 'My plot title')
        control['menu'].current(1)
        control['menu'].event_generate('<<ComboboxSelected>>')
        self.assertEqual(config_mod.ax.get_title(), 'My plot title')
        self.assertFalse(any(isinstance(widget, tk.Checkbutton) and
                             widget.cget('text') == 'On/Off figure title'
                             for widget in descendants(self.plot)))

    def test_title_manual_replot_and_config_reload_cancel_pending_edits(self):
        self.button('disable instant changes').invoke()
        self.choose_title('x', 'custom')
        self.controls.controls['x']['text'].set('Pending title')
        self.wait_for_title_edit()
        self.assertNotEqual(config_mod.ax.get_xlabel(), 'Pending title')
        self.button('Replot').invoke()
        self.assertEqual(config_mod.ax.get_xlabel(), 'Pending title')
        self.controls.controls['x']['text'].set('Stale title')
        self.button('Reload settings').invoke()
        self.wait_for_title_edit()
        self.assertEqual(config_mod.ax.get_xlabel(), 'Pending title')

    def test_axes_separator_spans_auto_controls_and_titles_are_in_settings_ii(self):
        frame = self.button('Auto X').master
        separator = next(widget for widget in frame.winfo_children() if isinstance(widget, ttk.Separator))
        self.assertEqual(separator.grid_info()['columnspan'], 5)
        ancestor = self.controls.master
        while ancestor is not self.plot:
            if isinstance(ancestor, tk.LabelFrame) and ancestor.cget('text') == 'Plot settings II':
                break
            ancestor = ancestor.master
        self.assertIsNot(ancestor, self.plot)

    def write_xs(self, filename='cross-sections.txt', name='Al-27 total'):
        path = self.config_path.parent / filename
        path.write_text(f'name: {name}\n' + '# metadata\n' * 7 + '1 2\n2 4\n//\n', encoding='utf-8')
        return path

    def test_saved_xs_is_loaded_and_plotted_after_restart(self):
        path = self.write_xs()
        self.settings.update(xs_dir_path=path, xs_switch=True)
        settings_mod.save_config()
        self.button('Quit').invoke()
        config_mod.xs_data.clear()
        self.assertTrue(settings_mod.read_config(self.config_path))
        with patch.object(read_mod.filedialog, 'askopenfilename') as picker:
            plot_mod.plot_window(self.root, ['source', 'reference'])
        self.plot = self.root.winfo_children()[0]
        picker.assert_not_called()
        self.assertEqual(config_mod.ax2.lines[0].get_label(), 'Al-27 total')
        self.assertEqual(str(self.button('show/hide XS Y axis').cget('state')), 'normal')
        self.assertTrue(any(isinstance(widget, tk.Label) and widget.cget('text') == path.name
                            for widget in descendants(self.plot)))
        self.errors.assert_not_called()

    def test_fresh_plot_does_not_load_saved_or_cached_xs_but_reload_can(self):
        path = self.write_xs()
        self.settings.update(xs_dir_path=path, xs_switch=True)
        self.button('Quit').invoke()
        settings_mod.reset_plot_settings_to_defaults()
        config_mod.xs_data['Stale'] = [[1], [2]]
        with patch.object(read_mod, 'load_xs_file', wraps=read_mod.load_xs_file) as loader:
            plot_mod.plot_window(self.root, ['source', 'reference'], use_saved_config=False)
            self.plot = self.root.winfo_children()[0]
            loader.assert_not_called()
            self.assertFalse(config_mod.xs_data)
            self.assertFalse(self.settings['xs_switch'])
            self.assertIsNone(config_mod.ax2)
            self.assertEqual(str(self.button('show/hide XS Y axis').cget('state')), 'disabled')
            self.button('Reload settings').invoke()
            loader.assert_called_once_with(path)
        self.assertEqual(str(self.button('show/hide XS Y axis').cget('state')), 'normal')
        self.button('show/hide XS Y axis').invoke()
        self.assertEqual(config_mod.ax2.lines[0].get_label(), 'Al-27 total')
        self.errors.assert_not_called()

    def test_reload_replaces_xs_file_and_hidden_data_can_be_shown(self):
        self.settings.update(xs_dir_path=self.write_xs(), xs_switch=False)
        settings_mod.save_config()
        self.button('Reload settings').invoke()
        self.assertIsNone(config_mod.ax2)
        self.assertEqual(str(self.button('show/hide XS Y axis').cget('state')), 'normal')
        self.button('show/hide XS Y axis').invoke()
        self.assertEqual(config_mod.ax2.lines[0].get_label(), 'Al-27 total')
        self.settings['xs_dir_path'] = self.write_xs('replacement.txt', 'Fe-56 total')
        settings_mod.save_config()
        self.button('Reload settings').invoke()
        self.assertEqual(config_mod.ax2.lines[0].get_label(), 'Fe-56 total')
        self.assertNotIn('Al-27 total', config_mod.xs_data)
        self.errors.assert_not_called()

    def test_unavailable_saved_xs_does_not_leave_checked_empty_axis(self):
        for missing in (False, True):
            path = self.config_path.parent / 'missing.txt' if missing else self.config_path.parent
            self.settings.update(xs_dir_path=path, xs_switch=True)
            config_mod.xs_data['Stale'] = [[1], [2]]
            settings_mod.save_config()
            with self.assertLogs(plot_mod.__name__, level='WARNING'):
                self.button('Reload settings').invoke()
            self.assertIsNone(config_mod.ax2)
            self.assertFalse(config_mod.xs_data)
            self.assertFalse(self.settings['xs_switch'])
            self.assertEqual(str(self.button('show/hide XS Y axis').cget('state')), 'disabled')
        self.assertEqual(self.errors.call_count, 2)

    def test_read_xs_remembers_selection_before_checkbox_is_toggled(self):
        path = self.write_xs()
        with patch.object(read_mod.filedialog, 'askopenfilename', return_value=str(path)):
            self.button('Read XS').invoke()
        self.assertIsNone(config_mod.ax2)
        self.assertEqual(str(self.button('show/hide XS Y axis').cget('state')), 'normal')
        self.assertTrue(settings_mod.read_config(self.config_path))
        self.assertEqual(self.settings['xs_dir_path'], path)
        self.errors.assert_not_called()

    def test_average_and_preset_changes_work_while_tcl_popdown_holds_grab(self):
        selector = self.average_selector()
        popdown = str(selector.tk.call('ttk::combobox::PopdownWindow', str(selector)))
        self.plot.tk.call('grab', 'set', popdown)
        try:
            # Reproduce the widget-registry lookup failure reported by the user.
            with self.assertRaises(KeyError):
                self.plot.grab_current()
            self.assertEqual(window_mod.dialog_parent(self.plot), self.plot)
            for label, mode in (('Original + average', 'both'), ('Average only', 'average'),
                                ('Original only', 'original')):
                self.choose_average(label)
                self.assertEqual(self.settings['moving_average_mode'], mode)
                self.assertEqual(str(self.plot.tk.call('grab', 'current', self.plot)), popdown)
            self.choose_title('x', 'preset:energy')
            self.assertEqual(config_mod.ax.get_xlabel(), 'energy (MeV)')
            self.assertEqual(self.callback_errors, [])
        finally:
            self.plot.tk.call('grab', 'release', popdown)
            self.plot.grab_set()
        self.errors.assert_not_called()

    def test_dialog_parent_prefers_active_editor(self):
        editor = editor_mod.open_lib(self.config_path, self.plot, ['source'], on_save=lambda: True)
        self.assertEqual(window_mod.dialog_parent(self.plot), editor)
        self.button('Quit', editor).invoke()
        self.assertEqual(window_mod.dialog_parent(self.plot), self.plot)

    def zoom_rectangle(self):
        canvas = config_mod.canvas_id
        toolbar = canvas.toolbar
        start = config_mod.ax.transAxes.transform((.2, .25))
        end = config_mod.ax.transAxes.transform((.7, .75))
        toolbar.zoom()
        try:
            toolbar.press_zoom(MouseEvent('button_press_event', canvas, *start, button=MouseButton.LEFT))
            toolbar.release_zoom(MouseEvent('button_release_event', canvas, *end, button=MouseButton.LEFT))
        finally:
            toolbar.zoom()

    def limit_entry(self, axis, side):
        label = next(widget for widget in descendants(self.plot)
                     if isinstance(widget, tk.Label) and widget.cget('text') == f'{axis.upper()} {side}')
        return next(widget for widget in label.master.winfo_children()
                    if isinstance(widget, tk.Entry)
                    and widget.grid_info()['row'] == label.grid_info()['row']
                    and widget.grid_info()['column'] == (1 if side == 'min' else 3))

    def assert_toolbar_limits_match_controls(self):
        for axis, bounds in (('x', config_mod.ax.get_xlim()), ('y', config_mod.ax.get_ylim())):
            for side, value in zip(('min', 'max'), bounds):
                self.assertEqual(self.settings[f'{axis}_{side}'], float(value))
                self.assertEqual(float(self.limit_entry(axis, side).get()), float(value))

    def test_rectangle_zoom_updates_limits_and_survives_average_redraw(self):
        self.assertIsNone(self.settings['x_min'])
        self.zoom_rectangle()
        self.assert_toolbar_limits_match_controls()
        xlim, ylim = config_mod.ax.get_xlim(), config_mod.ax.get_ylim()
        self.choose_average('Original + average')
        assert_allclose(config_mod.ax.get_xlim(), xlim)
        assert_allclose(config_mod.ax.get_ylim(), ylim)
        self.assertTrue(settings_mod.read_config(self.config_path))
        self.assertEqual((self.settings['x_min'], self.settings['x_max']), xlim)
        self.assertEqual((self.settings['y_min'], self.settings['y_max']), ylim)

    def test_toolbar_history_and_pan_update_controls(self):
        initial_x, initial_y = config_mod.ax.get_xlim(), config_mod.ax.get_ylim()
        self.zoom_rectangle()
        zoom_x, zoom_y = config_mod.ax.get_xlim(), config_mod.ax.get_ylim()
        toolbar = config_mod.canvas_id.toolbar
        toolbar.back()
        assert_allclose(config_mod.ax.get_xlim(), initial_x)
        self.assert_toolbar_limits_match_controls()
        toolbar.forward()
        assert_allclose(config_mod.ax.get_xlim(), zoom_x)
        assert_allclose(config_mod.ax.get_ylim(), zoom_y)
        self.assert_toolbar_limits_match_controls()
        toolbar.home()
        assert_allclose(config_mod.ax.get_xlim(), initial_x)
        assert_allclose(config_mod.ax.get_ylim(), initial_y)
        self.assert_toolbar_limits_match_controls()
        start = config_mod.ax.transAxes.transform((.5, .5))
        end = start + (20, 15)
        canvas = config_mod.canvas_id
        toolbar.pan()
        try:
            toolbar.press_pan(MouseEvent('button_press_event', canvas, *start, button=MouseButton.LEFT))
            toolbar.drag_pan(MouseEvent('motion_notify_event', canvas, *end, button=MouseButton.LEFT))
            toolbar.release_pan(MouseEvent('button_release_event', canvas, *end, button=MouseButton.LEFT))
        finally:
            toolbar.pan()
        self.assertNotEqual(config_mod.ax.get_xlim(), initial_x)
        self.assert_toolbar_limits_match_controls()

    def test_cancelled_zoom_keeps_automatic_limits(self):
        canvas = config_mod.canvas_id
        point = config_mod.ax.transAxes.transform((.5, .5))
        toolbar = canvas.toolbar
        toolbar.zoom()
        try:
            toolbar.press_zoom(MouseEvent('button_press_event', canvas, *point, button=MouseButton.LEFT))
            toolbar.release_zoom(MouseEvent('button_release_event', canvas, *point, button=MouseButton.LEFT))
        finally:
            toolbar.zoom()
        self.assertIsNone(self.settings['x_min'])
        self.assertIsNone(self.settings['y_min'])

    def test_axis_reset_clears_only_selected_range(self):
        initial_x = config_mod.ax.get_xlim()
        self.zoom_rectangle()
        zoom_y = config_mod.ax.get_ylim()
        self.button('Auto X').invoke()
        self.assertIsNone(self.settings['x_min'])
        self.assertIsNone(self.settings['x_max'])
        self.assertEqual(self.limit_entry('x', 'min').get(), 'None')
        assert_allclose(config_mod.ax.get_xlim(), initial_x)
        assert_allclose(config_mod.ax.get_ylim(), zoom_y)
        self.button('Auto X').invoke()
        self.assertEqual((self.settings['x_min'], self.settings['x_max']), config_mod.ax.get_xlim())
        self.button('disable instant changes').invoke()
        self.button('Auto Y').invoke()
        self.assertIsNone(self.settings['y_min'])
        self.assertIsNone(self.settings['y_max'])
        assert_allclose(config_mod.ax.get_ylim(), zoom_y)
        self.button('Replot').invoke()
        self.assertNotEqual(config_mod.ax.get_ylim(), zoom_y)

    def test_toolbar_captures_log_axes_and_xs_range(self):
        self.settings.update(xs_dir_path=self.write_xs(), xs_switch=True,
                             x_scale='log', y_scale='log', y2_scale='log')
        settings_mod.save_config()
        self.button('Reload settings').invoke()
        self.zoom_rectangle()
        self.assert_toolbar_limits_match_controls()
        xs_limits = config_mod.ax2.get_ylim()
        self.assertEqual((self.settings['y2_min'], self.settings['y2_max']), xs_limits)
        self.choose_average('Average only')
        assert_allclose(config_mod.ax2.get_ylim(), xs_limits)
        self.button('Auto Y2').invoke()
        self.assertIsNone(self.settings['y2_min'])
        self.assertIsNone(self.settings['y2_max'])
        self.assertEqual(str(self.button('Auto Y2').cget('state')), 'normal')
        self.errors.assert_not_called()

    def multiplier_controls(self):
        frame = next(widget for widget in descendants(self.plot)
                     if isinstance(widget, tk.LabelFrame) and widget.cget('text') == 'Tally multiplier')
        menu = next(widget for widget in frame.winfo_children() if isinstance(widget, ttk.Combobox))
        entry = next(widget for widget in frame.winfo_children()
                     if isinstance(widget, ttk.Entry) and not isinstance(widget, ttk.Combobox))
        return frame, menu, entry

    def test_multiplier_editor_reloads_active_value_and_new_choices(self):
        frame, menu, entry = self.multiplier_controls()
        menu.current(1)
        menu.event_generate('<<ComboboxSelected>>')
        self.assertEqual(self.settings['tally_multiplier'], 2)
        self.button('Presets editor', frame).invoke()
        editor = next(widget for widget in self.plot.winfo_children() if widget.winfo_class() == 'Toplevel')
        text = next(widget for widget in descendants(editor) if isinstance(widget, tk.Text))
        text.delete('1.0', tk.END)
        text.insert('1.0', '[multipliers.double]\nvalue=3.0\ndescription="Tripled"\n'
                          '[multipliers.four]\nvalue=4.0\ndescription="Four"\n')
        self.button('Save file', editor).invoke()
        self.assertFalse(editor.winfo_exists())
        self.assertEqual(menu.get(), 'Tripled')
        self.assertIn('Four', menu.cget('values'))
        self.assertEqual(float(entry.get()), 3)
        self.assertEqual(self.settings['tally_multiplier'], 3)
        assert_allclose(config_mod.ax.lines[0].get_ydata(), [0, 6, 12, 24])
        self.errors.assert_not_called()

    def test_invalid_multiplier_editor_save_keeps_working_presets(self):
        frame, menu, entry = self.multiplier_controls()
        menu.current(1)
        menu.event_generate('<<ComboboxSelected>>')
        self.button('Presets editor', frame).invoke()
        editor = next(widget for widget in self.plot.winfo_children() if widget.winfo_class() == 'Toplevel')
        text = next(widget for widget in descendants(editor) if isinstance(widget, tk.Text))
        text.delete('1.0', tk.END)
        text.insert('1.0', '[invalid')
        with self.assertLogs(settings_mod.__name__, level='WARNING'):
            self.button('Save file', editor).invoke()
        self.assertTrue(editor.winfo_exists())
        self.assertEqual(menu.get(), 'Double')
        self.assertEqual(self.settings['tally_multiplier'], 2)
        self.errors.assert_called_once()

    def test_deleted_multiplier_preset_retains_value_as_custom(self):
        frame, menu, entry = self.multiplier_controls()
        menu.current(1)
        menu.event_generate('<<ComboboxSelected>>')
        self.button('Presets editor', frame).invoke()
        editor = next(widget for widget in self.plot.winfo_children() if widget.winfo_class() == 'Toplevel')
        text = next(widget for widget in descendants(editor) if isinstance(widget, tk.Text))
        text.delete('1.0', tk.END)
        text.insert('1.0', '[multipliers]\n')
        self.button('Save file', editor).invoke()
        self.assertEqual(menu.get(), 'Custom value')
        self.assertEqual(str(entry.cget('state')), 'normal')
        self.assertEqual(self.settings['tally_multiplier'], 2)

    def test_comboboxes_and_stacked_fields_fit_their_frames(self):
        self.plot.transient('')
        self.plot.overrideredirect(True)
        self.plot.geometry('1200x700-20000-20000')
        self.plot.deiconify()
        self.plot.update()
        self.assertFalse(any(isinstance(widget, tk.OptionMenu) for widget in descendants(self.plot)))
        frame, menu, entry = self.multiplier_controls()
        self.assertEqual(menu.winfo_width(), entry.winfo_width())
        self.assertGreaterEqual(entry.winfo_width(), frame.winfo_width() - 12)
        for control in list(self.controls.controls.values()) + [self.controls.plot_title]:
            self.assertGreaterEqual(control['entry'].winfo_y(),
                                    control['menu'].winfo_y() + control['menu'].winfo_height())
            self.assertEqual(control['entry'].winfo_width(), control['menu'].winfo_width())
        grid_frame = self.button('show/hide grid').master
        grid_menus = [widget for widget in grid_frame.winfo_children() if isinstance(widget, ttk.Combobox)]
        self.assertTrue(all(str(widget.cget('state')) == 'readonly' for widget in grid_menus))
        self.button('show/hide grid').invoke()
        self.assertTrue(all(str(widget.cget('state')) == 'disabled' for widget in grid_menus))
        self.button('show/hide grid').invoke()
        self.assertTrue(all(str(widget.cget('state')) == 'readonly' for widget in grid_menus))


if __name__ == '__main__':
    unittest.main()
