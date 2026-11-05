"""Regression checks for figure saving, labels, and plot transformations."""

from pathlib import Path
import math
import copy
import tempfile
import unittest
from unittest.mock import patch

from matplotlib.figure import Figure
from numpy.testing import assert_allclose

from modules import (figure_export_mod, plot_core, settings_mod,
                     moving_average_mod, axis_titles_mod, config_mod)
from modules.tally_data import Tally


class FigureSaveTests(unittest.TestCase):
    def setUp(self):
        self.figure = Figure(figsize=(8, 6))
        self.settings = settings_mod.default_plot_settings()
        self.settings['save_fig'] = True
        self.parent = object()

    def assert_restored(self):
        self.assertEqual(tuple(self.figure.get_size_inches()), (8, 6))
        self.assertFalse(self.settings['save_fig'])

    def test_cancel_is_quiet_and_restores_state(self):
        with patch.object(figure_export_mod.filedialog, 'asksaveasfilename', return_value='') as dialog, \
                patch.object(figure_export_mod.messagebox, 'showerror') as error, \
                patch.object(self.figure, 'savefig') as save:
            self.assertFalse(figure_export_mod.save_figure(self.figure, self.settings, self.parent))
        self.assertIs(dialog.call_args.kwargs['parent'], self.parent)
        error.assert_not_called()
        save.assert_not_called()
        self.assert_restored()

    def test_success_writes_picture_without_confirmation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'figure.png'
            with patch.object(figure_export_mod.filedialog, 'asksaveasfilename', return_value=str(path)), \
                    patch.object(figure_export_mod.messagebox, 'showinfo') as info:
                self.assertTrue(figure_export_mod.save_figure(self.figure, self.settings, self.parent))
            self.assertGreater(path.stat().st_size, 0)
            self.assertEqual(self.settings['export_dir_path'], path.parent)
            info.assert_not_called()
        self.assert_restored()

    def test_save_and_dialog_failures_restore_state_and_parent_errors(self):
        for dialog_failure in (False, True):
            with self.subTest(dialog_failure=dialog_failure):
                self.settings['save_fig'] = True
                with patch.object(figure_export_mod.filedialog, 'asksaveasfilename',
                                  return_value='figure.png',
                                  side_effect=RuntimeError('dialog failed') if dialog_failure else None), \
                        patch.object(self.figure, 'savefig', side_effect=PermissionError('locked')), \
                        patch.object(figure_export_mod.messagebox, 'showerror') as error:
                    self.assertFalse(figure_export_mod.save_figure(self.figure, self.settings, self.parent))
                self.assertIs(error.call_args.kwargs['parent'], self.parent)
                self.assert_restored()


class AxisTitleTests(unittest.TestCase):
    def test_ratio_uses_separate_title_and_restores_ordinary_title(self):
        settings = settings_mod.default_plot_settings()
        settings['y_title'] = 'Custom flux'
        self.assertEqual(plot_core.y_axis_title(settings), 'Custom flux')
        settings['ratio'] = 'reference'
        self.assertEqual(plot_core.y_axis_title(settings), 'Ratio (-)')
        settings['y_ratio_title'] = 'Custom ratio'
        self.assertEqual(plot_core.y_axis_title(settings), 'Custom ratio')
        settings['ratio'] = 'no ratio'
        self.assertEqual(plot_core.y_axis_title(settings), 'Custom flux')

    def test_named_preset_reload_and_deleted_preset_keeps_text(self):
        presets = {'flux': {'value': 'New flux', 'description': 'Flux'}}
        self.assertEqual(axis_titles_mod.resolve_title_preset('Old flux', 'preset:flux', presets),
                         ('New flux', 'preset:flux'))
        self.assertEqual(axis_titles_mod.resolve_title_preset('Old flux', 'preset:removed', presets),
                         ('Old flux', 'custom'))

    def test_invalid_preset_file_keeps_last_valid_data(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'titles.toml'
            first = settings_mod.get_axis_title_presets(path)
            path.write_text('[x.energy]\nvalue = "Wavelength"\ndescription = "Wavelength"\n', encoding='utf-8')
            changed = settings_mod.get_axis_title_presets(path)
            self.assertEqual(changed['x']['energy']['value'], 'Wavelength')
            self.assertNotEqual(first, changed)
            for invalid in ('[x', '[x.energy]\nvalue = 123\ndescription = "bad"\n'):
                path.write_text(invalid, encoding='utf-8')
                self.assertEqual(settings_mod.get_axis_title_presets(path), changed)
                self.assertIsNotNone(settings_mod.last_axis_titles_error)
            path.write_text('', encoding='utf-8')
            self.assertEqual(settings_mod.get_axis_title_presets(path), {'x': {}, 'y': {}, 'y2': {}})
            self.assertIsNone(settings_mod.last_axis_titles_error)


class MovingAverageTests(unittest.TestCase):
    def test_centered_average_shortens_edges_and_does_not_mutate_input(self):
        values = [1, 2, 6, 10, 16]
        assert_allclose(moving_average_mod.centered_moving_average(values, 3), [1.5, 3, 6, 32 / 3, 13])
        self.assertEqual(values, [1, 2, 6, 10, 16])

    def test_short_empty_zero_and_identity_windows(self):
        self.assertEqual(moving_average_mod.centered_moving_average([], 5), [])
        self.assertEqual(moving_average_mod.centered_moving_average([0, 0], 5), [0, 0])
        self.assertEqual(moving_average_mod.centered_moving_average([2, 4], 5), [3, 3])
        self.assertEqual(moving_average_mod.centered_moving_average([2, 4], 1), [2, 4])

    def test_gaps_are_preserved_without_averaging_across_them(self):
        result = moving_average_mod.centered_moving_average([2, 4, math.nan, 20, 40, math.inf], 5)
        self.assertEqual(result[:2], [3, 3])
        self.assertTrue(math.isnan(result[2]))
        self.assertEqual(result[3:5], [30, 30])
        self.assertTrue(math.isnan(result[5]))

    def test_invalid_windows(self):
        for value in (0, -1, 2, 2.5, 'invalid', True, math.inf, math.nan):
            with self.subTest(value=value), self.assertRaises(ValueError):
                moving_average_mod.validate_window(value)


class PlotRenderingTests(unittest.TestCase):
    def setUp(self):
        self.settings = settings_mod.default_plot_settings()
        self.settings.update(moving_average_mode='both', moving_average_window=3,
                             data_var=False, error_bar=True, x_scale='linear', y_scale='linear')
        self.tally = Tally('4', 4, 'neutrons', [0, 1, 2, 3, 4], [0, 2, 4, 8, 10],
                           [0, .1, .1, .1, .1], 0, [0, 2, 4, 8, 10], legend_name='Test')
        self.figure = Figure()
        self.axis = self.figure.add_subplot()
        from unittest.mock import Mock
        self.canvas = Mock()
        state = patch.multiple(config_mod, plot_settings=self.settings,
                               tallies={'test': self.tally}, fig_id=self.figure,
                               canvas_id=self.canvas, ax=self.axis, ax2=None)
        state.start()
        self.addCleanup(state.stop)
        legend = patch.object(settings_mod, 'readsave_legend')
        legend.start()
        self.addCleanup(legend.stop)

    def test_average_excludes_placeholder_survives_clipping_and_does_not_change_data(self):
        before = copy.deepcopy(self.tally.__dict__)
        plot_core.plot_to_canvas(['test'])
        overlay = next(line for line in self.axis.lines if 'moving average' in line.get_label())
        self.assertEqual(list(overlay.get_xdata()), [.5, 1.5, 2.5, 3.5])
        first_values = list(overlay.get_ydata())
        assert_allclose(first_values, [3, 14 / 3, 22 / 3, 9])
        self.settings.update(y_min=1, y_max=12)
        plot_core.plot_to_canvas(['test'])
        overlay = next(line for line in self.axis.lines if 'moving average' in line.get_label())
        self.assertEqual(list(overlay.get_ydata()), first_values)
        self.assertEqual(self.tally.__dict__, before)

    def test_average_uses_normalized_and_multiplied_values(self):
        self.tally.flux_normalized = [0, 1, 3, 7, 9]
        self.settings.update(data_var=True, tally_multiplier=2)
        plot_core.plot_to_canvas(['test'])
        overlay = next(line for line in self.axis.lines if 'moving average' in line.get_label())
        assert_allclose(overlay.get_ydata(), [4, 22 / 3, 38 / 3, 16])

    def test_ratio_average_leaves_zero_denominators_as_gaps(self):
        reference = copy.deepcopy(self.tally)
        reference.flux = [0, 1, 0, 2, 2]
        reference.legend_name = 'Reference'
        config_mod.tallies['reference'] = reference
        self.settings.update(ratio='reference', y_title='Ordinary label',
                             ratio_reference_line=True, tally_multiplier=100)
        plot_core.plot_to_canvas(['test', 'reference'])
        overlay = next(line for line in self.axis.lines if 'moving average' in line.get_label())
        values = list(overlay.get_ydata())
        self.assertEqual(values[0], 2)
        self.assertTrue(math.isnan(values[1]))
        self.assertEqual(values[2:], [4.5, 4.5])
        self.assertEqual(self.axis.get_ylabel(), 'Ratio (-)')
        self.assertTrue(any(list(line.get_ydata()) == [1, 1] for line in self.axis.lines))

    def test_hidden_first_bin_keeps_overlay_aligned(self):
        self.settings['first_bin'] = False
        plot_core.plot_to_canvas(['test'])
        overlay = next(line for line in self.axis.lines if 'moving average' in line.get_label())
        self.assertEqual(list(overlay.get_xdata()), [1.5, 2.5, 3.5])
        assert_allclose(overlay.get_ydata(), [6, 22 / 3, 9])

    def test_saved_figure_contains_average_and_restores_display_size(self):
        original_size = tuple(self.figure.get_size_inches())
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'average.svg'
            self.settings['save_fig'] = True
            with patch.object(figure_export_mod.filedialog, 'asksaveasfilename', return_value=str(path)):
                plot_core.plot_to_canvas(['test'])
            self.assertIn('moving average, 3 bins', path.read_text(encoding='utf-8'))
        self.assertEqual(tuple(self.figure.get_size_inches()), original_size)
        self.assertFalse(self.settings['save_fig'])

    def test_display_modes_control_curves_legends_and_errors_in_regular_and_ratio_plots(self):
        config_mod.tallies['reference'] = copy.deepcopy(self.tally)
        for ratio in ('no ratio', 'reference'):
            for mode, curves, errors in (('original', 1, 1), ('both', 2, 1), ('average', 1, 0)):
                with self.subTest(ratio=ratio, mode=mode):
                    self.settings.update(ratio=ratio, moving_average_mode=mode, error_bar=True)
                    plot_core.plot_to_canvas(['test'] if ratio == 'no ratio' else ['test', 'reference'])
                    labels = self.axis.get_legend_handles_labels()[1]
                    self.assertEqual(len(labels), curves)
                    self.assertEqual(len(self.axis.containers), errors)
                    self.assertEqual(sum('moving average' in label for label in labels), mode != 'original')
                    if mode == 'average':
                        self.assertTrue(all('moving average' in label for label in labels))

    def test_average_only_respects_file_styles_and_keeps_xs_and_ratio_guide(self):
        config_mod.tallies['other'] = copy.deepcopy(self.tally)
        self.settings.update(moving_average_mode='average', line_width=2.5)
        plot_core.plot_to_canvas(['test', 'other'])
        self.assertEqual([line.get_linestyle() for line in self.axis.lines], ['-', '--'])
        self.assertTrue(all(line.get_linewidth() == 2.5 for line in self.axis.lines))
        self.settings.update(ratio='other', ratio_reference_line=True, xs_switch=True, y2_scale='linear')
        with patch.object(config_mod, 'xs_data', {'XS': ([1, 2], [3, 4])}):
            plot_core.plot_to_canvas(['test', 'other'])
        self.assertTrue(any(list(line.get_ydata()) == [1, 1] for line in self.axis.lines))
        self.assertEqual(config_mod.ax2.lines[0].get_label(), 'XS')
        self.assertEqual(len(self.axis.containers), 0)

    def test_average_only_preserves_gap_clipping_and_saved_legend(self):
        reference = copy.deepcopy(self.tally)
        reference.flux = [0, 1, 0, 2, 2]
        config_mod.tallies['reference'] = reference
        self.settings.update(ratio='reference', moving_average_mode='average', y_min=0, y_max=10)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'only-average.svg'
            self.settings['save_fig'] = True
            with patch.object(figure_export_mod.filedialog, 'asksaveasfilename', return_value=str(path)):
                plot_core.plot_to_canvas(['test', 'reference'])
            self.assertIn('moving average, 3 bins', path.read_text(encoding='utf-8'))
        self.assertEqual(len(self.axis.lines), 1)
        self.assertTrue(math.isnan(self.axis.lines[0].get_ydata()[1]))
        self.assertEqual(self.axis.get_ylim(), (0, 10))

    def test_cross_section_data_are_never_averaged(self):
        xs_data = {'XS': ([.5, 1, 2, 3], [2, 100, 4, 40])}
        before = copy.deepcopy(xs_data)
        self.settings.update(xs_switch=True, y2_scale='linear')
        with patch.object(config_mod, 'xs_data', xs_data):
            for mode in ('original', 'both', 'average'):
                for window in (3, 5):
                    with self.subTest(mode=mode, window=window):
                        self.settings.update(moving_average_mode=mode, moving_average_window=window)
                        plot_core.plot_to_canvas(['test'])
                        self.assertEqual(len(config_mod.ax2.lines), 1)
                        curve = config_mod.ax2.lines[0]
                        self.assertEqual(list(curve.get_xdata()), before['XS'][0])
                        self.assertEqual(list(curve.get_ydata()), before['XS'][1])
                        self.assertEqual(curve.get_label(), 'XS')
                        self.assertEqual(xs_data, before)


if __name__ == '__main__':
    unittest.main()
