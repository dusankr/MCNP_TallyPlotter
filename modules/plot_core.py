# -*- coding: utf-8 -*-
# TODO_list:
# TODO turn off user setings? (titles...)
# TODO set automaticaly lin/log based on data scale

# libraries
from modules import config_mod, settings_mod, figure_export_mod, moving_average_mod
import math
import tkinter as tk


def add_ratio_reference_line(axis, settings):
    """Draw the ideal-ratio guide only for an active ratio plot."""
    if settings.get("ratio_reference_line", False) and settings.get("ratio") != "no ratio":
        axis.axhline(1.0, color='black', linestyle='--', linewidth=0.75, zorder=3)


def y_axis_title(settings: dict) -> str:
    """Resolve ordinary and ratio titles independently."""
    if settings.get('ratio', 'no ratio') != 'no ratio':
        return settings.get('y_ratio_title') or 'Ratio (-)'
    return settings.get('y_title') or (
        'Tally / MeV / particle' if settings.get('data_var', True) else 'Tally / particle'
    )


def add_moving_average(axis, centers, values, settings: dict, color, label: str,
                       reference_values=None, line_style='-') -> None:
    """Overlay the mean of displayed bins; undefined ratios remain gaps."""
    mode = settings.get('moving_average_mode', 'original')
    if mode == 'original':
        return
    data = list(values)
    if reference_values is not None:
        data = [value if math.isfinite(reference) and reference != 0 else math.nan
                for value, reference in zip(data, reference_values)]
    window = moving_average_mod.validate_window(settings.get('moving_average_window', 5))
    smoothed = moving_average_mod.centered_moving_average(data, window)
    axis.plot(centers, smoothed, color=color, linestyle=line_style if mode == 'average' else '--',
              linewidth=settings.get('line_width', 1.5), zorder=4,
              label=f'{label} (moving average, {window} bins)')


def plot_to_canvas(tally):

    parent = config_mod.canvas_id.get_tk_widget().winfo_toplevel()
    parent = parent.grab_current() or parent

    # Refresh labels for editor saves, manual updates, and reopened plot windows.
    settings_mod.readsave_legend()

    tally_to_plot = tally[:]

    config_mod.ax.clear()

    if config_mod.ax2 != None:
        config_mod.ax2.remove()
        #config_mod.ax2.clear()
        config_mod.ax2 = None

    # Define line styles for different file groups (solid, dashed, dotted, dashdot)
    available_linestyles = ['-', '--', ':', '-.']
    
    # Extract unique file names from selected tallies and create line style mapping
    # Only if line_style_by_file setting is enabled
    file_to_linestyle = {}
    if config_mod.plot_settings.get("line_style_by_file", True) and config_mod.plot_settings["ratio"] == 'no ratio':
        unique_files = []
        for name in tally_to_plot:
            fname = name.rsplit('_', 1)[0]  # Extract file name from tally key
            if fname not in unique_files:
                unique_files.append(fname)
        
        # Assign line styles to files, or default to solid if too many files
        if len(unique_files) <= len(available_linestyles):
            for i, fname in enumerate(unique_files):
                file_to_linestyle[fname] = available_linestyles[i]
        else:
            # Too many files, use solid for all
            for fname in unique_files:
                file_to_linestyle[fname] = '-'

    # read reference data for ratio plot
    if config_mod.plot_settings["ratio"] != "no ratio":
        key = config_mod.plot_settings["ratio"]
        reference_tally = config_mod.tallies[key]
        
        _, y_ratio, _ = reference_tally.get_data(
            normalized=config_mod.plot_settings["data_var"],
            include_first_bin=config_mod.plot_settings["first_bin"]
        )
        
        tally_to_plot.remove(key)   # remove tally name from the list for ratio plot

    # plot all chosen values
    for name in tally_to_plot:
        tally_obj = config_mod.tallies[name]
        
        # Get data using Tally method
        x_data, y_data, y_data_err = tally_obj.get_data(
            normalized=config_mod.plot_settings["data_var"],
            include_first_bin=config_mod.plot_settings["first_bin"]
        )
        
        # take the correct name for legend
        legend_name = tally_obj.legend_name

        # check if the multiplier is set and multiply the data, if not set to 1.0 and show a warning
        # Skip multiplier for ratio plots
        if config_mod.plot_settings["ratio"] == 'no ratio':
            try:
                float(config_mod.plot_settings["tally_multiplier"])
                multiplier = True
            except ValueError:
                tk.messagebox.showwarning('Warning', 'Tally multiplier is not a number, using default value 1.0', parent=parent)
                config_mod.plot_settings["tally_multiplier"] = 1.0
                multiplier = False

            if multiplier is True and config_mod.plot_settings["tally_multiplier"] != 1.0:
                # multiply the data by the multiplier value
                y_data = [y * config_mod.plot_settings["tally_multiplier"] for y in y_data]
                # legend_name += ' × ' + str(config_mod.plot_settings["tally_multiplier"])

        # return ratio values
        if config_mod.plot_settings["ratio"] != 'no ratio':
            # Use Tally method for ratio calculation
            x_data, y_data, y_data_err, success = tally_obj.calculate_ratio(
                reference_tally=reference_tally,
                normalized=config_mod.plot_settings["data_var"],
                include_first_bin=config_mod.plot_settings["first_bin"]
            )
            
            if not success:
                error_msg = (f"Cannot create ratio plot!\n\n"
                           f"Tallies '{tally_obj.legend_name}' and '{reference_tally.legend_name}' have different energy bins.\n\n"
                           f"Ratio plots require tallies with identical energy binning (same bin count and bin boundaries).")
                config_mod.plot_settings['save_fig'] = False
                tk.messagebox.showerror('Ratio Plot Error', error_msg, parent=parent)
                return  # Stop plotting entirely
            
            # return new curve title for ratio plot
            legend_name = f"{tally_obj.legend_name}/{reference_tally.legend_name}"


        # calculate interval centers
        x_data_center = tally_obj.calculate_interval_centers(
            include_first_bin=config_mod.plot_settings["first_bin"]
        )

        # plots
        p_color = config_mod.ax._get_lines.get_next_color()
        
        # Determine line style based on file name (solid for ratio plots or if disabled)
        if config_mod.plot_settings["ratio"] != 'no ratio' or not config_mod.plot_settings.get("line_style_by_file", True):
            line_style = '-'  # Solid line for ratio plots or if line style by file is disabled
        else:
            fname = name.rsplit('_', 1)[0]  # Extract file name
            line_style = file_to_linestyle.get(fname, '-')  # Default to solid if not found

        # Get line width from settings, default to 1.5 if not set
        line_width = config_mod.plot_settings.get("line_width", 1.5)

        show_original = config_mod.plot_settings.get('moving_average_mode', 'original') != 'average'
        if show_original:
            config_mod.ax.step(x_data, y_data, color=p_color, label=legend_name, linestyle=line_style, linewidth=line_width)

        if show_original and config_mod.plot_settings["error_bar"]:
            err = [a * b for a, b in zip(y_data_err, y_data)]  # abs error
            # Scale error bar thickness and cap size with line width
            err_linewidth = line_width * 0.7  # Error bar lines slightly thinner than main line
            err_capthick = line_width * 0.7   # Cap thickness matches error bar line
            err_capsize = line_width * 1.5    # Cap size scales proportionally
            lineerr = config_mod.ax.errorbar(x_data_center, y_data[1:], yerr=err[1:], xerr=0, color=p_color, marker='None', linestyle='None', linewidth=err_linewidth, capthick=err_capthick, capsize=err_capsize)     

        # Like the error bars, the overlay uses real displayed bins, never the
        # artificial leading cutoff value used to draw the step curve.
        add_moving_average(
            config_mod.ax, x_data_center, y_data[1:], config_mod.plot_settings,
            p_color, legend_name,
            reference_values=y_ratio[1:] if config_mod.plot_settings['ratio'] != 'no ratio' else None,
            line_style=line_style,
        )

    # XS plot (if true, run) -------------------------------------------------------------------------------------------
    if config_mod.plot_settings["xs_switch"]:
        config_mod.ax2 = config_mod.ax.twinx()
        
        # set XS Y axis scale
        config_mod.ax2.set_yscale(config_mod.plot_settings["y2_scale"])
        # workaround, this setting does not work in a log
        if config_mod.plot_settings["y2_scale"] == 'linear':
            config_mod.ax2.ticklabel_format(style='sci', axis='y', scilimits=(0, 0), useMathText=True)

        # XS Y axis label
        if config_mod.plot_settings["y2_title"] is not None:
            config_mod.ax2.set_ylabel(config_mod.plot_settings["y2_title"],fontsize=config_mod.plot_settings["ax_label_size"])
        else:
            config_mod.ax2.set_ylabel("Cross Section (barns)", fontsize=config_mod.plot_settings["ax_label_size"])
        
        # XS tic settings
        config_mod.ax2.tick_params(axis='y', labelsize=config_mod.plot_settings["tics_size"])

        for name in config_mod.xs_data.keys():
            p_color = config_mod.ax._get_lines.get_next_color()
            config_mod.ax2.plot(config_mod.xs_data[name][0], config_mod.xs_data[name][1], ls="--", label=name, color=p_color)

        config_mod.ax2.legend(loc=config_mod.plot_settings["leg_pos"], fontsize=config_mod.plot_settings["leg_size"])

        # Set y2 limits - allow setting just min or max or both
        if config_mod.plot_settings["y2_min"] is not None or config_mod.plot_settings["y2_max"] is not None:
            try:
                config_mod.ax2.set_ylim(bottom=config_mod.plot_settings["y2_min"], top=config_mod.plot_settings["y2_max"])
            except Exception as e:
                tk.messagebox.showerror('Error', 'Something went wrong during setting XS Y limits (usually user\'s value is not a number!). Error: ' + str(e), parent=parent)
    
    # set X and Y axes SCALE -------------------------------------------------------------------------------------------
    config_mod.ax.set_xscale(config_mod.plot_settings["x_scale"])
    config_mod.ax.set_yscale(config_mod.plot_settings["y_scale"])

    # workaround, this setting does not work in a log
    if config_mod.plot_settings["x_scale"] == 'linear':
        config_mod.ax.ticklabel_format(style='sci', axis='x', scilimits=(0, 0), useMathText=True)
    
    if config_mod.plot_settings["y_scale"] == 'linear':
        config_mod.ax.ticklabel_format(style='sci', axis='y', scilimits=(0, 0), useMathText=True)
    
    # axis limits ------------------------------------------------------------------------------------------------------
    
    # get x limits from the plot
    '''
    if config_mod.plot_settings["x_min"] is None or config_mod.plot_settings["x_max"] is None:
        config_mod.plot_settings["x_min"], config_mod.plot_settings["x_max"] = config_mod.ax.get_xlim()
        print(config_mod.plot_settings["x_min"], config_mod.plot_settings["x_max"])
    '''
    # Set x limits - allow setting just min or max or both
    if config_mod.plot_settings["x_min"] is not None or config_mod.plot_settings["x_max"] is not None:
        try:
            config_mod.ax.set_xlim(left=config_mod.plot_settings["x_min"], right=config_mod.plot_settings["x_max"])
        except Exception as e:
            tk.messagebox.showerror('Error', 'Something went wrong during setting X limits (usually user\'s value is not a number!). Error: ' + str(e), parent=parent)

    # Set y limits - allow setting just min or max or both
    if config_mod.plot_settings["y_min"] is not None or config_mod.plot_settings["y_max"] is not None:
        try:
            config_mod.ax.set_ylim(bottom=config_mod.plot_settings["y_min"], top=config_mod.plot_settings["y_max"])
        except Exception as e:
            tk.messagebox.showerror('Error', 'Something went wrong during setting Y limits (usually user\'s value is not a number!). Error: ' + str(e), parent=parent)

    # Add the guide after clipping so it stays visible above tally curves and
    # error bars whenever y = 1 lies within the selected range.
    add_ratio_reference_line(config_mod.ax, config_mod.plot_settings)

    # plot settings ----------------------------------------------------------------------------------------------------
    if config_mod.plot_settings["xs_switch"]:
        lines, labels = config_mod.ax.get_legend_handles_labels()
        lines2, labels2 = config_mod.ax2.get_legend_handles_labels()
        config_mod.ax2.legend(lines + lines2, labels + labels2, loc=config_mod.plot_settings["leg_pos"], fontsize=config_mod.plot_settings["leg_size"])
    else:
        config_mod.ax.legend(loc=config_mod.plot_settings["leg_pos"], fontsize=config_mod.plot_settings["leg_size"])

    # set grid
    config_mod.ax.grid(visible=config_mod.plot_settings["grid_switch"], which=config_mod.plot_settings["grid_opt"], axis=config_mod.plot_settings["grid_ax"])

    if config_mod.plot_settings["x_title"] is not None:
        config_mod.ax.set_xlabel(config_mod.plot_settings["x_title"], fontsize=config_mod.plot_settings["ax_label_size"])
    else:
        config_mod.ax.set_xlabel('energy (MeV)', fontsize=config_mod.plot_settings["ax_label_size"])

    config_mod.ax.set_ylabel(y_axis_title(config_mod.plot_settings), fontsize=config_mod.plot_settings["ax_label_size"])

    config_mod.ax.tick_params(axis='both', labelsize=config_mod.plot_settings["tics_size"])

    if config_mod.plot_settings["fig_title_switch"] is True:
        config_mod.ax.set_title(config_mod.plot_settings["fig_title"], fontsize=int(config_mod.plot_settings["fig_title_size"]))

    # SAVE figure into folder with specific dimensions, DPI and format
    if config_mod.plot_settings["save_fig"] is True:
        figure_export_mod.save_figure(config_mod.fig_id, config_mod.plot_settings, parent)

    # draw the plot        
    config_mod.canvas_id.draw()

# Note: interval_mid() function removed - now use Tally.calculate_interval_centers() method instead
