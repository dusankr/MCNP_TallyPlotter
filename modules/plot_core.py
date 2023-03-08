# -*- coding: utf-8 -*-
# TODO_list:
# TODO more options (ax min-max value)

# libraries
from modules import config_mod
import math
import pathlib
import tkinter as tk


def plot_to_canvas(tally_to_plot):
    config_mod.ax.clear()
    if config_mod.ax2 != None:
        config_mod.ax2.remove()     # TODO solve Warning!!! (works now)
        config_mod.ax2 = None

    # read reference data for ratio plot
    if (config_mod.plot_settings["ratio"] != 'no ratio') and (config_mod.plot_settings["data_var"] == 'non'):
        x_ratio, y_ratio, y_err_ratio = config_mod.tallies[config_mod.plot_settings["ratio"]][3], config_mod.tallies[config_mod.plot_settings["ratio"]][4], config_mod.tallies[config_mod.plot_settings["ratio"]][5]
    elif (config_mod.plot_settings["ratio"] != 'no ratio') and (config_mod.plot_settings["data_var"] == 'norm'):
        x_ratio, y_ratio, y_err_ratio = config_mod.tallies[config_mod.plot_settings["ratio"]][3], config_mod.tallies[config_mod.plot_settings["ratio"]][7], config_mod.tallies[config_mod.plot_settings["ratio"]][5]

    # create a new list in case the ratio plot is chosen and delete reference tally
    tally_to_plot_mod = tally_to_plot[:]
    if config_mod.plot_settings["ratio"] in tally_to_plot_mod:
        tally_to_plot_mod.remove(config_mod.plot_settings["ratio"])

    # plot all chosen values
    for name in tally_to_plot_mod:
        if config_mod.plot_settings["data_var"] == 'norm':
            x_data, y_data, y_data_err = config_mod.tallies[name][3], config_mod.tallies[name][7][:], config_mod.tallies[name][5][:]  # normalized data
            y_label = 'Tally / MeV / particle'
        elif config_mod.plot_settings["data_var"] == 'non':
            x_data, y_data, y_data_err = config_mod.tallies[name][3], config_mod.tallies[name][4][:], config_mod.tallies[name][5][:]  # original data
            y_label = 'Tally / particle'

        # take right name for legend
        config_mod.tallies[name][9] = config_mod.tallies[name][10]

        # return ratio values
        if config_mod.plot_settings["ratio"] != 'no ratio':
            y_label = 'Tally to Tally ratio (-)'
            if x_data != x_ratio:
                continue  # skip this cycle step if energy bins in current tally have different step from reference tally

            for i in range(0, len(y_data)):  # calculate ratio values and their errors
                if (y_data[i] != 0) and (y_ratio[i] != 0):  # only for non zero values
                    y_data_err[i] = math.sqrt(y_data_err[i] ** 2 + y_err_ratio[i] ** 2)
                    y_data[i] = y_data[i] / y_ratio[i]
                else:
                    y_data[i] = 0
                    y_data_err[i] = 0
            # return new curve title for ratio plot
            config_mod.tallies[name][9] = name + '/' + config_mod.plot_settings["ratio"]

        # calculate interval centers
        x_data_center = interval_mid(x_data)

        # plots
        p_color = next(config_mod.ax._get_lines.prop_cycler)['color']  # same color for step and errorbar plot
        linestep, = config_mod.ax.step(x_data, y_data, color=p_color, label=config_mod.tallies[name][9])

        if config_mod.plot_settings["error_bar"]:
            err = [a * b for a, b in zip(y_data_err, y_data)]  # abs error
            lineerr = config_mod.ax.errorbar(x_data_center, y_data[1:], yerr=err[1:], xerr=0, color=p_color, marker='None', linestyle='None', capthick=0.7, capsize=2)

    # XS plot (if true, run) -------------------------------------------------------------------------------------------
    if config_mod.plot_settings["xs_switch"]:
        config_mod.ax2 = config_mod.ax.twinx()

        if config_mod.plot_settings["y2_title"] != "None":
            config_mod.ax2.set_ylabel(config_mod.plot_settings["y2_title"],fontsize=config_mod.plot_settings["ax_label_size"])
        else:
            config_mod.plot_settings["y2_title"] = "Cross Section (barns)"
            config_mod.ax2.set_ylabel(config_mod.plot_settings["y2_title"], fontsize=config_mod.plot_settings["ax_label_size"])

        config_mod.ax2.set_yscale("log")
        config_mod.ax2.tick_params(axis='both', labelsize=config_mod.plot_settings["tics_size"])

        for name in config_mod.xs_data.keys():
            config_mod.ax2.plot(config_mod.xs_data[name][0], config_mod.xs_data[name][1], ls="--", label=name)

        config_mod.ax2.legend(loc=config_mod.plot_settings["leg_pos"], fontsize=config_mod.plot_settings["leg_size"])

    # plot settings ----------------------------------------------------------------------------------------------------
    config_mod.ax.legend(loc=config_mod.plot_settings["leg_pos"], fontsize=config_mod.plot_settings["leg_size"])

    if config_mod.plot_settings["xs_switch"]:
        lines, labels = config_mod.ax.get_legend_handles_labels()
        lines2, labels2 = config_mod.ax2.get_legend_handles_labels()
        config_mod.ax2.legend(lines + lines2, labels + labels2, loc=config_mod.plot_settings["leg_pos"], fontsize=config_mod.plot_settings["leg_size"])

    config_mod.ax.set_xscale(config_mod.plot_settings["x_scale"])
    config_mod.ax.set_yscale(config_mod.plot_settings["y_scale"])
    config_mod.ax.grid(visible=config_mod.plot_settings["grid_switch"], which=config_mod.plot_settings["grid_opt"], axis=config_mod.plot_settings["grid_ax"])

    if config_mod.plot_settings["x_title"] != "None":
        config_mod.ax.set_xlabel(config_mod.plot_settings["x_title"], fontsize=config_mod.plot_settings["ax_label_size"])
    else:
        config_mod.ax.set_xlabel('energy (MeV)', fontsize=config_mod.plot_settings["ax_label_size"])

    if config_mod.plot_settings["y_title"] != "None":
        config_mod.ax.set_ylabel(config_mod.plot_settings["y_title"], fontsize=config_mod.plot_settings["ax_label_size"])
    else:
        config_mod.ax.set_ylabel(y_label, fontsize=config_mod.plot_settings["ax_label_size"])

    config_mod.ax.tick_params(axis='both', labelsize=config_mod.plot_settings["tics_size"])

    # workaround, this setting does not work in a log
    if config_mod.plot_settings["y_scale"] == 'linear':
        config_mod.ax.ticklabel_format(style='sci', axis='y', scilimits=(0, 0), useMathText=True)

    # TODO add plot size for export
    # TODO independent path, file name
    if config_mod.plot_settings["save_fig"] is True and config_mod.plot_settings["fig_format"] != "None" and config_mod.plot_settings["fig_dpi"] != "None":
        try:
            config_mod.fig_id.savefig(config_mod.plot_settings["work_dir_path"] / pathlib.Path('fig_exp.' + config_mod.plot_settings["fig_format"]), format=config_mod.plot_settings["fig_format"], dpi=int(config_mod.plot_settings["fig_dpi"]))
        except:
            tk.messagebox.showerror('Read error', 'File is opened, please close it and then xou can continue.')


# calculate a middle of energy intervals
def interval_mid(x):
    x_center = []
    for i in range(0, len(x) - 1):
        x_center.append(x[i] + (x[i + 1] - x[i]) / 2)

    return x_center
