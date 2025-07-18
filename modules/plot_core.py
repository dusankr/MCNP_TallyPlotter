# -*- coding: utf-8 -*-
# TODO_list:
# TODO turn off user setings? (titles...)

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

    # read reference data for ratio plot
    if config_mod.plot_settings["ratio"] != "no ratio":
        key = config_mod.plot_settings["ratio"]   # not necessary do like this...

        if config_mod.plot_settings["data_var"] is True and config_mod.plot_settings["first_bin"] is True:
            x_ratio, y_ratio, y_err_ratio = config_mod.tallies[key][3], config_mod.tallies[key][7][:], config_mod.tallies[key][5][:]  # normalized data
            y_label = 'Tally / MeV / particle'
        elif config_mod.plot_settings["data_var"] is True and config_mod.plot_settings["first_bin"] is False:
            x_ratio, y_ratio, y_err_ratio = config_mod.tallies[key][3][1:], config_mod.tallies[key][7][1:], config_mod.tallies[key][5][1:]  # normalized data, without first bin
            y_label = 'Tally / MeV / particle'
        elif config_mod.plot_settings["data_var"] is False and config_mod.plot_settings["first_bin"] is True:
            x_ratio, y_ratio, y_err_ratio = config_mod.tallies[key][3], config_mod.tallies[key][4][:], config_mod.tallies[key][5][:]  # original data
            y_label = 'Tally / particle'
        elif config_mod.plot_settings["data_var"] is False and config_mod.plot_settings["first_bin"] is False:
            x_ratio, y_ratio, y_err_ratio = config_mod.tallies[key][3][1:], config_mod.tallies[key][4][1:], config_mod.tallies[key][5][1:] # original data, without first bin

        tally_to_plot.remove(key)   # remove tally name from the list for ratio plot

    # plot all chosen values
    for name in tally_to_plot:
        if config_mod.plot_settings["data_var"] is True and config_mod.plot_settings["first_bin"] is True:
            x_data, y_data, y_data_err = config_mod.tallies[name][3], config_mod.tallies[name][7][:], config_mod.tallies[name][5][:]  # normalized data
            y_label = 'Tally / MeV / particle'
        elif config_mod.plot_settings["data_var"] is True and config_mod.plot_settings["first_bin"] is False:
            x_data, y_data, y_data_err = config_mod.tallies[name][3][1:], config_mod.tallies[name][7][1:], config_mod.tallies[name][5][1:]  # normalized data, without first bin
            y_label = 'Tally / MeV / particle'
        elif config_mod.plot_settings["data_var"] is False and config_mod.plot_settings["first_bin"] is True:
            x_data, y_data, y_data_err = config_mod.tallies[name][3], config_mod.tallies[name][4][:], config_mod.tallies[name][5][:]  # original data
            y_label = 'Tally / particle'
        elif config_mod.plot_settings["data_var"] is False and config_mod.plot_settings["first_bin"] is False:
            x_data, y_data, y_data_err = config_mod.tallies[name][3][1:], config_mod.tallies[name][4][1:], config_mod.tallies[name][5][1:] # original data, without first bin

        # take the correct name for legend
        legend_name = config_mod.tallies[name][10]

        # return ratio values
        if config_mod.plot_settings["ratio"] != 'no ratio':
            y_label = 'Tally to Tally ratio (-)'
            if x_data != x_ratio:
                print('Energy bins in tallies are not the same, ratio plot is not possible.')
                continue  # skip this cycle step if energy bins in current tally have different step from reference tally

            for i in range(0, len(y_data)):  # calculate ratio values and their errors
                if (y_data[i] != 0) and (y_ratio[i] != 0):  # only for non zero values
                    y_data_err[i] = math.sqrt(y_data_err[i] ** 2 + y_err_ratio[i] ** 2)
                    y_data[i] = y_data[i] / y_ratio[i]
                else:
                    y_data[i] = 0
                    y_data_err[i] = 0
            # return new curve title for ratio plot
            legend_name = config_mod.tallies[name][10] + '/' + config_mod.tallies[config_mod.plot_settings["ratio"]][10]


        # calculate interval centers
        x_data_center = interval_mid(x_data)

        # plots
        # p_color = next(config_mod.ax._get_lines.prop_cycler)['color']  # same color for step and errorbar plot
        p_color = config_mod.ax._get_lines.get_next_color()

        linestep, = config_mod.ax.step(x_data, y_data, color=p_color, label=legend_name)

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
            p_color = next(config_mod.ax._get_lines.prop_cycler)['color']  # same color
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
        
        # get the work directory path and file format from a file save as dialog, available formats: png, pdf, ps, eps and svg
        picture_path = pathlib.Path(tk.filedialog.asksaveasfilename(initialdir=config_mod.plot_settings["work_dir_path"], title='Choose folder and file name without an extension:', filetypes=[("PNG files", "*.png"), ("PDF files", "*.pdf"), ("SVG files", "*.svg"), ("EPS files", "*.eps"), ("PS files", "*.ps")], defaultextension=".png"))
        
        # check if folder exists
        if not pathlib.Path.exists(picture_path.parent) or str(picture_path) == '.':
            tk.messagebox.showerror('Input error', 'No directory and file were selected.')
            return

        # extract format from the path
        config_mod.plot_settings["fig_format"] = picture_path.suffix[1:]

        # save the figure
        try:
            config_mod.fig_id.savefig(picture_path, format=config_mod.plot_settings["fig_format"], dpi=int(config_mod.plot_settings["fig_dpi"]), bbox_inches='tight')
            tk.messagebox.showinfo('File saved', 'Figure was saved to the work directory:\n' + str(picture_path))

        except PermissionError:
            tk.messagebox.showerror('Read error', 'File might be opened and unavailable for plotter, please close it and then you can continue.')
        except Exception as e:
            tk.messagebox.showerror('Error', 'Something went wrong during saving the figure. Please check the settings and try again. Error: ' + str(e))  

        # set the original figure size
        config_mod.fig_id.set_size_inches(x_dim, y_dim)

    # draw the plot        
    config_mod.canvas_id.draw()

# calculate a middle of energy intervals
def interval_mid(x):
    x_center = []
    for i in range(0, len(x) - 1):
        x_center.append(x[i] + (x[i + 1] - x[i]) / 2)

    return x_center
