"""Cross-section loading must also work without opening a file picker."""

from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from modules import config_mod, read_mod, settings_mod


def xs_export(name='Al-27 total', values='1 2\n2 4\n'):
    return f'name: {name}\n' + '# metadata\n' * 7 + values + '//\n'


class CrossSectionReadTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.path = Path(temp.name) / 'xs.txt'
        self.path.write_text(xs_export(), encoding='utf-8')
        state = patch.multiple(config_mod, xs_data={'Previous': [[1], [2]]},
                               plot_settings=settings_mod.default_plot_settings())
        state.start()
        self.addCleanup(state.stop)

    def test_load_multiple_active_curves_without_touching_runtime_state(self):
        self.path.write_text(xs_export() + '#name: skipped curve\n' + xs_export('Fe-56 total'), encoding='utf-8')
        self.assertEqual(read_mod.load_xs_file(self.path), {
            'Al-27 total': [[1.0, 2.0], [2.0, 4.0]],
            'Fe-56 total': [[1.0, 2.0], [2.0, 4.0]],
        })
        self.assertEqual(config_mod.xs_data, {'Previous': [[1], [2]]})

    def test_invalid_or_empty_input_reports_failure(self):
        for content in ('', xs_export().replace('//\n', ''), xs_export(values='bad row\n')):
            with self.subTest(content=content):
                self.path.write_text(content, encoding='utf-8')
                with self.assertRaises(ValueError):
                    read_mod.load_xs_file(self.path)

    def test_cancel_and_bad_selection_preserve_previous_file_and_data(self):
        label = MagicMock()
        previous_path = config_mod.plot_settings['xs_dir_path']
        self.path.write_text('not an XS file', encoding='utf-8')
        with patch.object(read_mod.filedialog, 'askopenfilename', return_value=''), \
                patch.object(read_mod.messagebox, 'showerror') as error:
            self.assertFalse(read_mod.read_xs(label))
            error.assert_not_called()
        with patch.object(read_mod.filedialog, 'askopenfilename', return_value=str(self.path)), \
                patch.object(read_mod.messagebox, 'showerror') as error, \
                self.assertLogs(read_mod.__name__, level='WARNING'):
            self.assertFalse(read_mod.read_xs(label))
            self.assertIs(error.call_args.kwargs['parent'], label.winfo_toplevel())
        self.assertEqual(config_mod.plot_settings['xs_dir_path'], previous_path)
        self.assertEqual(config_mod.xs_data, {'Previous': [[1], [2]]})

    def test_successful_selection_remembers_absolute_file_path(self):
        label = MagicMock()
        with patch.object(read_mod.filedialog, 'askopenfilename', return_value=str(self.path)) as dialog:
            self.assertTrue(read_mod.read_xs(label))
        self.assertEqual(config_mod.plot_settings['xs_dir_path'], self.path.resolve())
        self.assertIs(dialog.call_args.kwargs['parent'], label.winfo_toplevel())
        self.assertEqual(config_mod.xs_data, {'Al-27 total': [[1.0, 2.0], [2.0, 4.0]]})


if __name__ == '__main__':
    unittest.main()
