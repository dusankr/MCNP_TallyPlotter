#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# TOML-based configuration management

# libraries
from modules import config_mod
from modules.moving_average_mod import validate_window
import pathlib
import shutil
import copy
import tomllib
import tomli_w


LEGEND_CONFIG_FILE = "legend.toml"
CONFIG_FILE = "config.toml"
AXIS_TITLES_FILE = "axis_titles.toml"
last_axis_titles_error = None
_axis_title_cache = {}
_MISSING = object()
last_config_error = None


# Mapping between TOML structure and flat plot_settings dictionary
TOML_TO_SETTINGS = {
    # Paths
    ("paths", "work_dir_path"): "work_dir_path",
    ("paths", "export_dir_path"): "export_dir_path",
    ("paths", "xs_dir_path"): "xs_dir_path",
    # Figure
    ("figure", "x_dimension"): "fig_x_dimension",
    ("figure", "y_dimension"): "fig_y_dimension",
    ("figure", "format"): "fig_format",
    ("figure", "dpi"): "fig_dpi",
    # Plot
    ("plot", "data_var"): "data_var",
    ("plot", "ratio"): "ratio",
    ("plot", "ratio_reference_line"): "ratio_reference_line",
    ("plot", "error_bar"): "error_bar",
    ("plot", "first_bin"): "first_bin",
    ("plot", "latex"): "latex",
    ("plot", "moving_average"): "moving_average",
    ("plot", "moving_average_window"): "moving_average_window",
    # Axes
    ("axes", "x_scale"): "x_scale",
    ("axes", "y_scale"): "y_scale",
    ("axes", "y2_scale"): "y2_scale",
    ("axes", "x_title"): "x_title",
    ("axes", "y_title"): "y_title",
    ("axes", "y2_title"): "y2_title",
    ("axes", "y_ratio_title"): "y_ratio_title",
    ("axes", "x_title_preset"): "x_title_preset",
    ("axes", "y_title_preset"): "y_title_preset",
    ("axes", "y2_title_preset"): "y2_title_preset",
    ("axes", "y_ratio_title_preset"): "y_ratio_title_preset",
    # Axes limits
    ("axes", "limits", "x_min"): "x_min",
    ("axes", "limits", "x_max"): "x_max",
    ("axes", "limits", "y_min"): "y_min",
    ("axes", "limits", "y_max"): "y_max",
    ("axes", "limits", "y2_min"): "y2_min",
    ("axes", "limits", "y2_max"): "y2_max",
    # Legend
    ("legend", "position"): "leg_pos",
    ("legend", "size"): "leg_size",
    # Grid
    ("grid", "switch"): "grid_switch",
    ("grid", "option"): "grid_opt",
    ("grid", "axis"): "grid_ax",
    # Fonts
    ("fonts", "ax_label_size"): "ax_label_size",
    ("fonts", "tics_size"): "tics_size",
    # Title
    ("title", "fig_title"): "fig_title",
    ("title", "fig_title_switch"): "fig_title_switch",
    ("title", "fig_title_size"): "fig_title_size",
    # Cross section
    ("cross_section", "xs_switch"): "xs_switch",
    # Line
    ("line", "style_by_file"): "line_style_by_file",
    ("line", "width"): "line_width",
    # Advanced
    ("advanced", "tally_multiplier"): "tally_multiplier",
}


def get_nested_value(data, keys, default=None):
    """Get value from nested dictionary using tuple of keys."""
    value = data
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default
    return value


def set_nested_value(data, keys, value):
    """Set value in nested dictionary using tuple of keys."""
    for key in keys[:-1]:
        if key not in data:
            data[key] = {}
        data = data[key]
    data[keys[-1]] = value


def default_plot_settings():
    """Return a complete, independently mutable set of runtime defaults."""
    current_dir = pathlib.Path.cwd()
    return {
        "work_dir_path": current_dir,
        "export_dir_path": current_dir,
        "xs_dir_path": current_dir,
        "fig_x_dimension": 20.0,
        "fig_y_dimension": 15.0,
        "fig_format": "png",
        "fig_dpi": 150.0,
        "x_title": None,
        "y_title": None,
        "ratio": "no ratio",
        "ratio_reference_line": False,
        "data_var": True,
        "leg_pos": "best",
        "leg_size": 10,
        "grid_switch": True,
        "grid_opt": "major",
        "grid_ax": "both",
        "ax_label_size": 12,
        "tics_size": 10,
        "save_fig": False,
        "error_bar": True,
        "latex": False,
        "x_min": None,
        "x_max": None,
        "y_min": None,
        "y_max": None,
        "y2_min": None,
        "y2_max": None,
        "xs_switch": False,
        "y2_title": None,
        "fig_title": None,
        "fig_title_switch": False,
        "fig_title_size": 14,
        "first_bin": True,
        "y2_scale": "log",
        "y_scale": "log",
        "x_scale": "log",
        "tally_multiplier": 1.0,
        "y_ratio_title": None,
        "line_style_by_file": True,
        "line_width": 1.5,
        "moving_average": False,
        "moving_average_window": 5,
        "x_title_preset": "auto",
        "y_title_preset": "auto",
        "y2_title_preset": "auto",
        "y_ratio_title_preset": "auto",
    }


PATH_SETTINGS = {"work_dir_path", "export_dir_path", "xs_dir_path"}
BOOLEAN_SETTINGS = {
    "data_var", "ratio_reference_line", "error_bar", "first_bin", "latex", "grid_switch",
    "fig_title_switch", "xs_switch", "line_style_by_file", "moving_average",
}
INTEGER_SETTINGS = {"leg_size", "ax_label_size", "tics_size", "fig_title_size"}
FLOAT_SETTINGS = {
    "fig_x_dimension", "fig_y_dimension", "fig_dpi", "x_min", "x_max",
    "y_min", "y_max", "y2_min", "y2_max", "tally_multiplier", "line_width",
}
OPTIONAL_SETTINGS = {
    "x_title", "y_title", "y2_title", "y_ratio_title", "fig_title",
    "x_min", "x_max", "y_min", "y_max", "y2_min", "y2_max",
}
ENUM_SETTINGS = {
    "x_scale": {"linear", "log"},
    "y_scale": {"linear", "log"},
    "y2_scale": {"linear", "log"},
    "grid_opt": {"major", "minor", "both"},
    "grid_ax": {"x", "y", "both"},
    "leg_pos": {
        "best", "upper right", "upper left", "lower left", "lower right", "right",
        "center left", "center right", "lower center", "upper center", "center",
    },
}


def _coerce_setting(settings_key, value, toml_keys):
    """Convert legacy string values using the expected type for each setting."""
    label = ".".join(toml_keys)
    if settings_key == 'moving_average_window':
        return validate_window(value)
    if settings_key in OPTIONAL_SETTINGS and isinstance(value, str) and value.strip().lower() in ('none', ''):
        return None
    if settings_key in PATH_SETTINGS:
        if not isinstance(value, (str, pathlib.Path)):
            raise ValueError(f"{label} must be a path string")
        return pathlib.Path(value)
    if settings_key in BOOLEAN_SETTINGS:
        if not isinstance(value, bool):
            raise ValueError(f"{label} must be true or false")
        return value
    if settings_key in INTEGER_SETTINGS:
        if isinstance(value, bool):
            raise ValueError(f"{label} must be an integer")
        try:
            number = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{label} must be an integer") from exc
        if not number.is_integer():
            raise ValueError(f"{label} must be an integer")
        return int(number)
    if settings_key in FLOAT_SETTINGS:
        if isinstance(value, bool):
            raise ValueError(f"{label} must be a number")
        try:
            return float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{label} must be a number or 'None'") from exc
    if not isinstance(value, str):
        raise ValueError(f"{label} must be a string")
    if settings_key in ENUM_SETTINGS and value not in ENUM_SETTINGS[settings_key]:
        choices = ", ".join(sorted(ENUM_SETTINGS[settings_key]))
        raise ValueError(f"{label} must be one of: {choices}")
    return value


def _settings_to_toml(settings):
    toml_data = {}
    for toml_keys, settings_key in TOML_TO_SETTINGS.items():
        value = settings.get(settings_key)
        if value is None:
            value = "None"
        elif isinstance(value, pathlib.Path):
            value = str(value)
        set_nested_value(toml_data, toml_keys, value)
    return toml_data


def create_config(fname=CONFIG_FILE):
    """Create a new TOML config file with default values."""
    default_config = _settings_to_toml(default_plot_settings())
    with open(fname, "wb") as f:
        tomli_w.dump(default_config, f)


def reset_plot_settings_to_defaults():
    """Reset all plot settings to default values (None for limits, defaults for others)."""
    defaults = default_plot_settings()
    preserved = {key: config_mod.plot_settings.get(key) for key in (
        'work_dir_path', 'export_dir_path', 'xs_dir_path', 'fig_x_dimension',
        'fig_y_dimension', 'fig_format', 'fig_dpi',
    )}
    config_mod.plot_settings.update(defaults)
    config_mod.plot_settings.update({key: value for key, value in preserved.items() if value is not None})


def read_config(fname=CONFIG_FILE):
    """Read a complete, typed configuration and commit it only after validation."""
    global last_config_error
    try:
        if not pathlib.Path(fname).is_file():
            print(f"Creating new config file: {fname}")
            create_config(fname)
        with open(fname, "rb") as f:
            toml_data = tomllib.load(f)
        loaded = default_plot_settings()
        for toml_keys, settings_key in TOML_TO_SETTINGS.items():
            value = get_nested_value(toml_data, toml_keys, _MISSING)
            if value is not _MISSING:
                # Older generated configs used "None" for a few non-optional
                # fields. Treat those entries as omitted and use the default.
                if (settings_key not in OPTIONAL_SETTINGS and isinstance(value, str)
                        and value.strip().lower() in ('none', '')):
                    continue
                loaded[settings_key] = _coerce_setting(settings_key, value, toml_keys)
        # Existing configs store only title strings. Preserve those as custom titles.
        for title in ('x_title', 'y_title', 'y2_title', 'y_ratio_title'):
            mode = title + '_preset'
            if get_nested_value(toml_data, ('axes', mode), _MISSING) is _MISSING:
                loaded[mode] = 'custom' if loaded[title] is not None else 'auto'
            elif loaded[mode] == 'auto' and loaded[title] is not None:
                # Editing an automatic label directly in config.toml must still work.
                loaded[mode] = 'custom'
    except Exception as exc:
        last_config_error = f"Could not load {fname}: {exc}"
        print(last_config_error)
        if not any(value is not None for value in config_mod.plot_settings.values()):
            config_mod.plot_settings.update(default_plot_settings())
        return False

    config_mod.plot_settings.clear()
    config_mod.plot_settings.update(loaded)
    last_config_error = None
    return True


def save_config(fname=CONFIG_FILE):
    """Save configuration to TOML file."""
    toml_data = _settings_to_toml(config_mod.plot_settings)
    target = pathlib.Path(fname)
    temporary = target.with_name(target.name + '.tmp')
    try:
        with open(temporary, "wb") as f:
            tomli_w.dump(toml_data, f)
        temporary.replace(target)
    finally:
        if temporary.exists():
            temporary.unlink()


def default_axis_title_presets() -> dict:
    """Return example presets without coupling labels to data transformations."""
    return {
        'x': {'energy': {'value': 'energy (MeV)', 'description': 'Energy (MeV)'}},
        'y': {
            'per_mev': {'value': 'Tally / MeV / particle', 'description': 'Tally per MeV per particle'},
            'per_particle': {'value': 'Tally / particle', 'description': 'Tally per particle'},
            'ratio': {'value': 'Ratio (-)', 'description': 'Ratio'},
        },
        'y2': {'cross_section': {'value': 'Cross Section (barns)', 'description': 'Cross section (barns)'}},
    }


def get_axis_title_presets(fname=None) -> dict:
    """Load and validate presets, keeping the last valid file on failure."""
    global last_axis_titles_error
    path = pathlib.Path(fname if fname is not None else AXIS_TITLES_FILE)
    cache_key = path.resolve()
    try:
        if not path.exists():
            with path.open('wb') as stream:
                tomli_w.dump(default_axis_title_presets(), stream)
        with path.open('rb') as stream:
            data = tomllib.load(stream)
        presets = {}
        for axis in ('x', 'y', 'y2'):
            entries = data.get(axis, {})
            if not isinstance(entries, dict):
                raise ValueError(f'{axis} must be a table of presets')
            presets[axis] = {}
            for name, entry in entries.items():
                if not isinstance(entry, dict) or any(
                    not isinstance(entry.get(field), str) or not entry[field].strip()
                    for field in ('value', 'description')
                ):
                    raise ValueError(f'{axis}.{name} needs nonempty value and description strings')
                presets[axis][name] = {field: entry[field] for field in ('value', 'description')}
    except (OSError, ValueError) as exc:
        last_axis_titles_error = f'Could not load {path}: {exc}'
        return copy.deepcopy(_axis_title_cache.get(cache_key, default_axis_title_presets()))
    _axis_title_cache[cache_key] = presets
    last_axis_titles_error = None
    return copy.deepcopy(presets)


def create_multipliers_config(fname="multipliers.toml"):
    """Create a new multipliers config file with preset values."""
    default_multipliers = {
        "multipliers": {
            "Lujan-100uA": {"value": 6.2415091E14, "description": "Lujan Center 100 uA"},
            "Lujan-80uA": {"value": 4.9932073E14, "description": "Lujan Center 80 uA"},
        }
    }
    
    with open(fname, "wb") as f:
        tomli_w.dump(default_multipliers, f)


def get_multiplier_presets(fname="multipliers.toml"):
    """Read multiplier presets from multipliers.toml file and return as dictionary.
    Returns dict with format: {key: {'value': float, 'description': str}}
    """
    if not pathlib.Path(fname).is_file():
        create_multipliers_config(fname)
    
    try:
        with open(fname, "rb") as f:
            toml_data = tomllib.load(f)
        
        multipliers = toml_data.get("multipliers", {})
        return multipliers
    except Exception as e:
        print(f"Warning: Could not read multiplier presets: {e}")
        return {}


def create_legend_config(fname=LEGEND_CONFIG_FILE):
    """Create a new legend config file."""
    with open(fname, "w", encoding='utf-8') as f:
        f.write("# Legend name mappings for tallies\n")
        f.write("# Format: tally_key = \"Display Name\"\n")
        f.write("#\n")
        f.write("[legend]\n")


def readsave_legend(fname=LEGEND_CONFIG_FILE):
    """Read and save tally names to the legend config file (TOML format)."""
    if not pathlib.Path(fname).is_file():
        legacy_path = pathlib.Path(fname).with_name("config_legend")
        if pathlib.Path(fname).name == LEGEND_CONFIG_FILE and legacy_path.is_file():
            # Preserve existing mappings when upgrading to the TOML filename.
            shutil.copyfile(legacy_path, fname)
        else:
            create_legend_config(fname)
    
    # Read TOML legend file
    try:
        with open(fname, "rb") as f:
            legend_data = tomllib.load(f)
        
        legend_dict = legend_data.get("legend", {})
        
        # Apply existing mappings and track new tallies
        new_tallies = {}
        for key in config_mod.tallies.keys():
            if key in legend_dict:
                config_mod.tallies[key].legend_name = legend_dict[key]
            else:
                # New tally, use key as default
                config_mod.tallies[key].legend_name = key
                new_tallies[key] = key
        
        # If there are new tallies, save them
        if new_tallies:
            legend_dict.update(new_tallies)
            with open(fname, "wb") as f:
                tomli_w.dump({"legend": legend_dict}, f)
    
    except Exception as e:
        print(f"Warning: Could not read legend config: {e}")
        # Fallback: use keys as names
        for key in config_mod.tallies.keys():
            config_mod.tallies[key].legend_name = key


