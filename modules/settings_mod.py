#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# TOML-based configuration management

# libraries
from modules import config_mod
import pathlib
import tomllib
import tomli_w


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
    ("plot", "error_bar"): "error_bar",
    ("plot", "first_bin"): "first_bin",
    ("plot", "latex"): "latex",
    # Axes
    ("axes", "x_scale"): "x_scale",
    ("axes", "y_scale"): "y_scale",
    ("axes", "y2_scale"): "y2_scale",
    ("axes", "x_title"): "x_title",
    ("axes", "y_title"): "y_title",
    ("axes", "y2_title"): "y2_title",
    ("axes", "y_ratio_title"): "y_ratio_title",
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


def get_nested_value(data, keys):
    """Get value from nested dictionary using tuple of keys."""
    value = data
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return None
    return value


def set_nested_value(data, keys, value):
    """Set value in nested dictionary using tuple of keys."""
    for key in keys[:-1]:
        if key not in data:
            data[key] = {}
        data = data[key]
    data[keys[-1]] = value


def create_config(fname="config.toml"):
    """Create a new TOML config file with default values."""
    default_config = {
        "paths": {
            "work_dir_path": str(pathlib.Path.cwd()),
            "export_dir_path": str(pathlib.Path.cwd()),
            "xs_dir_path": str(pathlib.Path.cwd()),
        },
        "figure": {
            "x_dimension": 20.0,
            "y_dimension": 15.0,
            "format": "png",
            "dpi": 150.0,
        },
        "plot": {
            "data_var": True,
            "ratio": "no ratio",
            "error_bar": True,
            "first_bin": True,
            "latex": False,
        },
        "axes": {
            "x_scale": "log",
            "y_scale": "log",
            "y2_scale": "log",
            # Optional title fields as string "None"
            "x_title": "None",
            "y_title": "None",
            "y2_title": "None",
            "y_ratio_title": "None",
            "limits": {
                # Optional limit fields as string "None"
                "x_min": "None",
                "x_max": "None",
                "y_min": "None",
                "y_max": "None",
                "y2_min": "None",
                "y2_max": "None",
            },
        },
        "legend": {
            "position": "best",
            "size": 10,
        },
        "grid": {
            "switch": True,
            "option": "major",
            "axis": "both",
        },
        "fonts": {
            "ax_label_size": 12,
            "tics_size": 10,
        },
        "title": {
            # Optional title fields as string "None"
            "fig_title": "None",
            "fig_title_switch": False,
            "fig_title_size": "None",
        },
        "cross_section": {
            "xs_switch": False,
        },
        "line": {
            "style_by_file": True,
            "width": 1.5,
        },
        "advanced": {
            "tally_multiplier": 1.0,
        },
    }
    
    with open(fname, "wb") as f:
        tomli_w.dump(default_config, f)


def reset_plot_settings_to_defaults():
    """Reset all plot settings to default values (None for limits, defaults for others)."""
    config_mod.plot_settings['x_scale'] = 'log'
    config_mod.plot_settings['y_scale'] = 'log'
    config_mod.plot_settings['y2_scale'] = 'log'
    config_mod.plot_settings['data_var'] = True
    config_mod.plot_settings['ratio'] = 'no ratio'
    config_mod.plot_settings['error_bar'] = True
    config_mod.plot_settings['first_bin'] = True
    config_mod.plot_settings['latex'] = False
    config_mod.plot_settings['leg_pos'] = 'best'
    config_mod.plot_settings['leg_size'] = 10
    config_mod.plot_settings['grid_switch'] = True
    config_mod.plot_settings['grid_opt'] = 'major'
    config_mod.plot_settings['grid_ax'] = 'both'
    config_mod.plot_settings['ax_label_size'] = 12
    config_mod.plot_settings['tics_size'] = 10
    config_mod.plot_settings['xs_switch'] = False
    config_mod.plot_settings['fig_title_switch'] = False
    config_mod.plot_settings['line_style_by_file'] = True
    config_mod.plot_settings['line_width'] = 1.4
    config_mod.plot_settings['tally_multiplier'] = 1.0
    # Reset all limits to None (auto)
    config_mod.plot_settings['x_min'] = None
    config_mod.plot_settings['x_max'] = None
    config_mod.plot_settings['y_min'] = None
    config_mod.plot_settings['y_max'] = None
    config_mod.plot_settings['y2_min'] = None
    config_mod.plot_settings['y2_max'] = None
    config_mod.plot_settings['x_title'] = None
    config_mod.plot_settings['y_title'] = None
    config_mod.plot_settings['y2_title'] = None
    config_mod.plot_settings['y_ratio_title'] = None
    config_mod.plot_settings['fig_title'] = None
    config_mod.plot_settings['fig_title_size'] = 14


def read_config(fname="config.toml"):
    """Read configuration from TOML file."""
    if not pathlib.Path(fname).is_file():
        print(f"Creating new config file: {fname}")
        create_config(fname)
    
    # Read TOML file with error handling
    try:
        with open(fname, "rb") as f:
            toml_data = tomllib.load(f)
    except Exception as e:
        print(f"Error reading config file: {e}")
        print(f"Creating new config file: {fname}")
        create_config(fname)
        with open(fname, "rb") as f:
            toml_data = tomllib.load(f)
    
    # Map TOML structure to flat plot_settings dictionary
    for toml_keys, settings_key in TOML_TO_SETTINGS.items():
        value = get_nested_value(toml_data, toml_keys)
        if value is not None:
            # Convert string "None" to actual None (for legacy compatibility)
            if isinstance(value, str):
                if value.strip().lower() in ('none', ''):
                    value = None
                else:
                    # Try to convert to float/int if it's a numeric string
                    try:
                        if '.' in value:
                            value = float(value)
                        else:
                            # Could be int or just a string - try int first
                            try:
                                value = int(value)
                            except ValueError:
                                pass  # Keep as string
                    except (ValueError, AttributeError):
                        pass  # Keep as string
        
        # Set the value (could be None now after conversion)
        if value is not None:
            config_mod.plot_settings[settings_key] = value
    
    # Convert path strings to Path objects
    for path_key in ["work_dir_path", "export_dir_path", "xs_dir_path"]:
        if config_mod.plot_settings[path_key] is not None:
            try:
                path = pathlib.Path(config_mod.plot_settings[path_key])
                if path.is_file():
                    # If it's a file, use parent directory
                    config_mod.plot_settings[path_key] = path.parent
                elif path.is_dir():
                    config_mod.plot_settings[path_key] = path
                else:
                    # Path doesn't exist, use current directory
                    config_mod.plot_settings[path_key] = pathlib.Path.cwd()
            except Exception:
                config_mod.plot_settings[path_key] = pathlib.Path.cwd()
        else:
            config_mod.plot_settings[path_key] = pathlib.Path.cwd()


def save_config(fname="config.toml"):
    """Save configuration to TOML file."""
    # List of settings that should NOT be saved (transient flags)
    exclude_from_save = ['save_fig']
    
    # Build TOML structure from flat plot_settings
    toml_data = {}
    
    for toml_keys, settings_key in TOML_TO_SETTINGS.items():
        # Skip excluded settings
        if settings_key in exclude_from_save:
            continue
        
        value = config_mod.plot_settings.get(settings_key)
        
        # Convert None to string "None" so it's stored in TOML
        if value is None:
            value = "None"
        
        # Convert Path objects to strings
        if isinstance(value, pathlib.Path):
            value = str(value)
        
        # Set the value in nested structure
        set_nested_value(toml_data, toml_keys, value)
    
    # Write TOML file
    with open(fname, "wb") as f:
        tomli_w.dump(toml_data, f)


def create_legend_config(fname="legend.toml"):
    """Create a new legend config file."""
    with open(fname, "w", encoding='utf-8') as f:
        f.write("# Legend name mappings for tallies\n")
        f.write("# Format: tally_key = \"Display Name\"\n")
        f.write("#\n")
        f.write("[legend]\n")


def readsave_legend(fname="legend.toml"):
    """Read and save tally names to the legend config file (TOML format)."""
    if not pathlib.Path(fname).is_file():
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


