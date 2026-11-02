import copy
import pathlib
import tempfile
import unittest

import tomli_w

from modules import config_mod, settings_mod


class ConfigReloadTests(unittest.TestCase):
    def setUp(self):
        self.original_settings = copy.deepcopy(config_mod.plot_settings)
        self.temp_directory = tempfile.TemporaryDirectory()
        self.config_path = pathlib.Path(self.temp_directory.name) / "config.toml"

    def tearDown(self):
        config_mod.plot_settings.clear()
        config_mod.plot_settings.update(self.original_settings)
        settings_mod.last_config_error = None
        self.temp_directory.cleanup()

    def write_config(self, data):
        with self.config_path.open("wb") as config_file:
            tomli_w.dump(data, config_file)

    def test_created_config_loads_complete_typed_defaults(self):
        settings_mod.create_config(self.config_path)

        self.assertTrue(settings_mod.read_config(self.config_path))

        self.assertEqual(set(config_mod.plot_settings), set(settings_mod.default_plot_settings()))
        self.assertIsInstance(config_mod.plot_settings["work_dir_path"], pathlib.Path)
        self.assertIsInstance(config_mod.plot_settings["fig_dpi"], float)
        self.assertIsInstance(config_mod.plot_settings["leg_size"], int)
        self.assertIs(config_mod.plot_settings["x_min"], None)

    def test_reload_clears_explicit_none_and_resets_omitted_values(self):
        config_mod.plot_settings.clear()
        config_mod.plot_settings.update(settings_mod.default_plot_settings())
        config_mod.plot_settings["x_title"] = "Old title"
        config_mod.plot_settings["x_min"] = 3.0
        config_mod.plot_settings["line_width"] = 4.0
        self.write_config({"axes": {"x_title": "None", "limits": {"x_min": "None"}}})

        self.assertTrue(settings_mod.read_config(self.config_path))

        self.assertIsNone(config_mod.plot_settings["x_title"])
        self.assertIsNone(config_mod.plot_settings["x_min"])
        self.assertEqual(config_mod.plot_settings["line_width"], 1.5)

    def test_legacy_numeric_strings_are_coerced_by_setting_type(self):
        self.write_config({
            "figure": {"dpi": "2.5e2"},
            "fonts": {"tics_size": "11"},
            "axes": {"x_title": "123", "limits": {"x_max": "1e4"}},
        })

        self.assertTrue(settings_mod.read_config(self.config_path))

        self.assertEqual(config_mod.plot_settings["fig_dpi"], 250.0)
        self.assertEqual(config_mod.plot_settings["tics_size"], 11)
        self.assertEqual(config_mod.plot_settings["x_title"], "123")
        self.assertEqual(config_mod.plot_settings["x_max"], 10000.0)

    def test_legacy_none_for_nonoptional_value_uses_default(self):
        self.write_config({"title": {"fig_title_size": "None"}})

        self.assertTrue(settings_mod.read_config(self.config_path))

        self.assertEqual(config_mod.plot_settings["fig_title_size"], 14)

    def test_nonexistent_configured_path_is_preserved(self):
        missing_path = pathlib.Path(self.temp_directory.name) / "not-created"
        self.write_config({"paths": {"work_dir_path": str(missing_path)}})

        self.assertTrue(settings_mod.read_config(self.config_path))

        self.assertEqual(config_mod.plot_settings["work_dir_path"], missing_path)

    def test_invalid_toml_keeps_last_working_settings(self):
        previous = settings_mod.default_plot_settings()
        previous["line_width"] = 2.25
        config_mod.plot_settings.clear()
        config_mod.plot_settings.update(previous)
        self.config_path.write_text("[figure\ndpi = 300", encoding="utf-8")

        self.assertFalse(settings_mod.read_config(self.config_path))

        self.assertEqual(config_mod.plot_settings, previous)
        self.assertIn("Could not load", settings_mod.last_config_error)

    def test_invalid_setting_type_keeps_last_working_settings(self):
        previous = settings_mod.default_plot_settings()
        previous["grid_switch"] = False
        config_mod.plot_settings.clear()
        config_mod.plot_settings.update(previous)
        self.write_config({"grid": {"switch": "yes"}})

        self.assertFalse(settings_mod.read_config(self.config_path))

        self.assertEqual(config_mod.plot_settings, previous)
        self.assertIn("grid.switch", settings_mod.last_config_error)

    def test_save_and_reload_round_trip_uses_atomic_temporary_file(self):
        expected = settings_mod.default_plot_settings()
        expected["x_min"] = -1.25
        expected["fig_title"] = None
        expected["work_dir_path"] = pathlib.Path(self.temp_directory.name) / "workspace"
        config_mod.plot_settings.clear()
        config_mod.plot_settings.update(expected)

        settings_mod.save_config(self.config_path)
        config_mod.plot_settings.clear()
        self.assertTrue(settings_mod.read_config(self.config_path))

        self.assertEqual(config_mod.plot_settings, expected)
        self.assertFalse(self.config_path.with_name("config.toml.tmp").exists())

    def test_failed_save_does_not_replace_existing_config(self):
        original_text = "[figure]\ndpi = 150.0\n"
        self.config_path.write_text(original_text, encoding="utf-8")
        config_mod.plot_settings.clear()
        config_mod.plot_settings.update(settings_mod.default_plot_settings())
        config_mod.plot_settings["x_title"] = object()

        with self.assertRaises(Exception):
            settings_mod.save_config(self.config_path)

        self.assertEqual(self.config_path.read_text(encoding="utf-8"), original_text)
        self.assertFalse(self.config_path.with_name("config.toml.tmp").exists())

    def test_legacy_titles_become_custom_and_new_features_default_off(self):
        self.write_config({'axes': {'y_title': 'Existing title'}})
        self.assertTrue(settings_mod.read_config(self.config_path))
        self.assertEqual(config_mod.plot_settings['y_title_preset'], 'custom')
        self.assertEqual(config_mod.plot_settings['x_title_preset'], 'auto')
        self.assertEqual(config_mod.plot_settings['moving_average_mode'], 'original')
        self.assertEqual(config_mod.plot_settings['moving_average_window'], 5)

    def test_external_title_override_works_with_auto_mode(self):
        self.write_config({'axes': {'y_title': 'Edited label', 'y_title_preset': 'auto'}})
        self.assertTrue(settings_mod.read_config(self.config_path))
        self.assertEqual(config_mod.plot_settings['y_title'], 'Edited label')
        self.assertEqual(config_mod.plot_settings['y_title_preset'], 'custom')

    def test_new_features_round_trip_and_invalid_window_does_not_replace_settings(self):
        expected = settings_mod.default_plot_settings()
        expected.update(moving_average_mode='average', moving_average_window=7,
                        x_title='energy (MeV)', x_title_preset='preset:energy',
                        y_title='Flux', y_title_preset='custom',
                        y_ratio_title='Custom ratio', y_ratio_title_preset='custom')
        config_mod.plot_settings.clear()
        config_mod.plot_settings.update(expected)
        settings_mod.save_config(self.config_path)
        self.assertTrue(settings_mod.read_config(self.config_path))
        self.assertEqual(config_mod.plot_settings, expected)
        self.write_config({'plot': {'moving_average_window': 4}})
        self.assertFalse(settings_mod.read_config(self.config_path))
        self.assertEqual(config_mod.plot_settings, expected)


    def test_average_mode_migrates_legacy_config_and_saves_only_new_key(self):
        for legacy, expected in ((False, 'original'), (True, 'both')):
            with self.subTest(legacy=legacy):
                self.write_config({'plot': {'moving_average': legacy}})
                self.assertTrue(settings_mod.read_config(self.config_path))
                self.assertEqual(config_mod.plot_settings['moving_average_mode'], expected)
                settings_mod.save_config(self.config_path)
                import tomllib
                saved = tomllib.loads(self.config_path.read_text(encoding='utf-8'))
                self.assertNotIn('moving_average', saved['plot'])
                self.assertEqual(saved['plot']['moving_average_mode'], expected)

    def test_explicit_average_mode_takes_precedence_over_legacy_value(self):
        for mode in ('original', 'both', 'average'):
            self.write_config({'plot': {'moving_average': 'ignored legacy value', 'moving_average_mode': mode}})
            self.assertTrue(settings_mod.read_config(self.config_path))
            self.assertEqual(config_mod.plot_settings['moving_average_mode'], mode)

    def test_invalid_average_mode_preserves_working_configuration(self):
        previous = settings_mod.default_plot_settings()
        config_mod.plot_settings.clear()
        config_mod.plot_settings.update(previous)
        for invalid in ('unknown', '', 'None', True):
            with self.subTest(invalid=invalid):
                self.write_config({'plot': {'moving_average_mode': invalid}})
                self.assertFalse(settings_mod.read_config(self.config_path))
                self.assertEqual(config_mod.plot_settings, previous)


if __name__ == "__main__":
    unittest.main()
