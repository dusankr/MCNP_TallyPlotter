# -*- coding: utf-8 -*-
# TODO_list:
# TODO turn off user setings? (titles...)
# TODO set automaticaly lin/log based on data scale

# libraries
from modules import config_mod
import math
import pathlib
import tkinter as tk


def plot_to_canvas(tally):

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
        
        x_ratio, y_ratio, y_err_ratio = reference_tally.get_data(
            normalized=config_mod.plot_settings["data_var"],
            include_first_bin=config_mod.plot_settings["first_bin"]
        )
        
        y_label = 'Tally / MeV / particle' if config_mod.plot_settings["data_var"] else 'Tally / particle'

        tally_to_plot.remove(key)   # remove tally name from the list for ratio plot

    # plot all chosen values
    for name in tally_to_plot:
        tally_obj = config_mod.tallies[name]
        
        # Get data using Tally method
        x_data, y_data, y_data_err = tally_obj.get_data(
            normalized=config_mod.plot_settings["data_var"],
            include_first_bin=config_mod.plot_settings["first_bin"]
        )
        
        # Set y_label based on normalization
        y_label = 'Tally / MeV / particle' if config_mod.plot_settings["data_var"] else 'Tally / particle'

        # take the correct name for legend
        legend_name = tally_obj.legend_name

        # check if the multiplier is set and multiply the data, if not set to 1.0 and show a warning
        # Skip multiplier for ratio plots
        if config_mod.plot_settings["ratio"] == 'no ratio':
            try:
                float(config_mod.plot_settings["tally_multiplier"])
                multiplier = True
            except ValueError:
                tk.messagebox.showwarning('Warning', 'Tally multiplier is not a number, using default value 1.0')
                config_mod.plot_settings["tally_multiplier"] = 1.0
                multiplier = False

            if multiplier is True and config_mod.plot_settings["tally_multiplier"] != 1.0:
                # multiply the data by the multiplier value
                y_data = [y * config_mod.plot_settings["tally_multiplier"] for y in y_data]
                # legend_name += ' × ' + str(config_mod.plot_settings["tally_multiplier"])

        # return ratio values
        if config_mod.plot_settings["ratio"] != 'no ratio':
            y_label = 'Tally to Tally ratio (-)'
            
            # Use Tally method for ratio calculation
            x_data, y_data, y_data_err, success = tally_obj.calculate_ratio(
                reference_tally=reference_tally,
                normalized=config_mod.plot_settings["data_var"],
                include_first_bin=config_mod.plot_settings["first_bin"]
            )
            
            if not success:
                print('Energy bins in tallies are not the same, ratio plot is not possible.')
                continue  # skip this cycle step if energy bins don't match
            
            # Use custom y_ratio_title if provided
            if config_mod.plot_settings["y_ratio_title"] is not None:
                y_label = config_mod.plot_settings["y_ratio_title"]
            
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

        linestep, = config_mod.ax.step(x_data, y_data, color=p_color, label=legend_name, linestyle=line_style, linewidth=line_width)

        if config_mod.plot_settings["error_bar"]:
            err = [a * b for a, b in zip(y_data_err, y_data)]  # abs error
            lineerr = config_mod.ax.errorbar(x_data_center, y_data[1:], yerr=err[1:], xerr=0, color=p_color, marker='None', linestyle='None', capthick=0.7, capsize=2)     

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
            config_mod.plot_settings["y2_title"] = "Cross Section (barns)"
            config_mod.ax2.set_ylabel(config_mod.plot_settings["y2_title"], fontsize=config_mod.plot_settings["ax_label_size"])
        
        # XS tic settings
        config_mod.ax2.tick_params(axis='y', labelsize=config_mod.plot_settings["tics_size"])

        for name in config_mod.xs_data.keys():
            p_color = config_mod.ax._get_lines.get_next_color()
            config_mod.ax2.plot(config_mod.xs_data[name][0], config_mod.xs_data[name][1], ls="--", label=name, color=p_color)

        config_mod.ax2.legend(loc=config_mod.plot_settings["leg_pos"], fontsize=config_mod.plot_settings["leg_size"])

        try:
            config_mod.ax2.set_ylim(config_mod.plot_settings["y2_min"], config_mod.plot_settings["y2_max"])
        except Exception as e:
            tk.messagebox.showerror('Error', 'Something went wrong during setting XS Y limits (usually user\'s value is not a number!). Error: ' + str(e))
    
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
    try:
        config_mod.ax.set_xlim(config_mod.plot_settings["x_min"], config_mod.plot_settings["x_max"])
    except Exception as e:
        tk.messagebox.showerror('Error', 'Something went wrong during setting X limits (usually user\'s value is not a number!). Error: ' + str(e))

    try:
        config_mod.ax.set_ylim(config_mod.plot_settings["y_min"], config_mod.plot_settings["y_max"])
    except Exception as e:
        tk.messagebox.showerror('Error', 'Something went wrong during setting Y limits (usually user\'s value is not a number!). Error: ' + str(e))

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

    if config_mod.plot_settings["y_title"] is not None:
        config_mod.ax.set_ylabel(config_mod.plot_settings["y_title"], fontsize=config_mod.plot_settings["ax_label_size"])
    else:
        config_mod.ax.set_ylabel(y_label, fontsize=config_mod.plot_settings["ax_label_size"])

    config_mod.ax.tick_params(axis='both', labelsize=config_mod.plot_settings["tics_size"])

    if config_mod.plot_settings["fig_title_switch"] is True:
        config_mod.ax.set_title(config_mod.plot_settings["fig_title"], fontsize=int(config_mod.plot_settings["fig_title_size"]))

    # SAVE figure into folder with specific dimensions, DPI and format
    if config_mod.plot_settings["save_fig"] is True:
        # store original figure size and reuse it after saving the figure
        x_dim, y_dim = config_mod.fig_id.get_size_inches()
        
        # set the figure size in cm
        config_mod.fig_id.set_size_inches(config_mod.plot_settings["fig_x_dimension"] / 2.54, config_mod.plot_settings["fig_y_dimension"] / 2.54)
        
        # get the export directory path and file format from a file save as dialog, available formats: png, pdf, ps, eps and svg
        picture_path = pathlib.Path(tk.filedialog.asksaveasfilename(initialdir=config_mod.plot_settings["export_dir_path"], title='Choose folder and file name without an extension:', filetypes=[("PNG files", "*.png"), ("PDF files", "*.pdf"), ("SVG files", "*.svg"), ("EPS files", "*.eps"), ("PS files", "*.ps")], defaultextension=".png"))
        
        # check if folder exists
        if not pathlib.Path.exists(picture_path.parent) or str(picture_path) == '.':
            tk.messagebox.showerror('Input error', 'No directory and file were selected.')
            # Reset save_fig flag even if user cancels
            config_mod.plot_settings["save_fig"] = False
            return

        # Update export directory path to remember the last used location
        config_mod.plot_settings["export_dir_path"] = picture_path.parent

        # extract format from the path
        config_mod.plot_settings["fig_format"] = picture_path.suffix[1:]

        # save the figure
        try:
            config_mod.fig_id.savefig(picture_path, format=config_mod.plot_settings["fig_format"], dpi=int(config_mod.plot_settings["fig_dpi"]), bbox_inches='tight')
            tk.messagebox.showinfo('File saved', 'Figure was saved to the export directory:\n' + str(picture_path))

        except PermissionError:
            tk.messagebox.showerror('Read error', 'File might be opened and unavailable for plotter, please close it and then you can continue.')
        except Exception as e:
            tk.messagebox.showerror('Error', 'Something went wrong during saving the figure. Please check the settings and try again. Error: ' + str(e))  

        # set the original figure size
        config_mod.fig_id.set_size_inches(x_dim, y_dim)
        
        # Reset save_fig flag after saving is complete
        config_mod.plot_settings["save_fig"] = False

    # draw the plot        
    config_mod.canvas_id.draw()

# Note: interval_mid() function removed - now use Tally.calculate_interval_centers() method instead
