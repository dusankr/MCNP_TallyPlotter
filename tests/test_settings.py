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


if __name__ == "__main__":
    unittest.main()
