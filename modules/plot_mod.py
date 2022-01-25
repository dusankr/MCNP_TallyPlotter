# -*- coding: utf-8 -*-
# TODO_list:
# TODO vložení tlačítek pro upravy grafu
# TODO lin-log osa x
# TODO lin-log osa y
# TODO
# TODO
# TODO stejná barva chybových úseček jako schodového grafu
# TODO ošetřit když chybí data

# libraries
import matplotlib.pyplot as plt     # ploting in matlab style
from modules import config_mod
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.figure import Figure

# GUI libraries
import tkinter as tk


#  Functions  ##########################################################################################################
# create new Top level window and plot data
def plot_window(root, treeview_file, selected):
    new_win = tk.Toplevel(root)
    new_win.grab_set()      # the main window is locked until the new window is closed

    new_win.title('Plotting window')
    new_win.minsize(100, 150)

    plot_frame = tk.ttk.Frame(new_win)
    plot_frame.grid(column=0, row=0, sticky='nswe', padx=5, pady=5)  # set the margins between window and content

    plot_option_frame = tk.ttk.Frame(new_win)
    plot_option_frame.grid(column=1, row=0, sticky='nswe', padx=5, pady=5)

    tally_to_plot = get_selected(treeview_file, selected)   # obtain keys from checkedbox treeview

    # Canvas for plot
    canvas = FigureCanvasTkAgg(plot_function(tally_to_plot), plot_frame)    # add Figure to canvas from plot function
    canvas.draw()
    canvas.get_tk_widget().grid(column=0, row=0, sticky='nswe')

    # Toolbar for plot
    toolbar_frame = tk.ttk.Frame(new_win)
    toolbar_frame.grid(column=0, row=1, sticky='nswe')
    toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)

    # PLOT OPTION FRAME

    # X AXIS Radio Button
    x_axis_frame = tk.LabelFrame(plot_option_frame, text='X axis settings')
    x_axis_frame.grid(column=0, row=0, sticky='nwe', padx=5, pady=5)

    x_lin_radio = tk.Radiobutton(x_axis_frame, text='lin')
    x_lin_radio.grid(column=0, row=0, sticky='nswe', padx=5, pady=5)
    x_log_radio = tk.Radiobutton(x_axis_frame, text='log')
    x_log_radio.grid(column=1, row=0, sticky='nswe', padx=5, pady=5)

    # Y AXIS Radio Button
    y_axis_frame = tk.LabelFrame(plot_option_frame, text='Y axis settings')
    y_axis_frame.grid(column=0, row=1, sticky='nwe', padx=5, pady=5)

    y_lin_radio = tk.Radiobutton(y_axis_frame, text='lin')
    y_lin_radio.grid(column=0, row=0, sticky='nswe', padx=5, pady=5)
    y_log_radio = tk.Radiobutton(y_axis_frame, text='log')
    y_log_radio.grid(column=1, row=0, sticky='nswe', padx=5, pady=5)

    # DATA Radio Button
    data_inp_frame = tk.LabelFrame(plot_option_frame, text='Data input')
    data_inp_frame.grid(column=0, row=2, sticky='n', padx=5, pady=5)

    data_inp_radio = tk.Radiobutton(data_inp_frame, text='norm')
    data_inp_radio.grid(column=0, row=0, sticky='nswe', padx=5, pady=5)
    data_inp_radio = tk.Radiobutton(data_inp_frame, text='non')
    data_inp_radio.grid(column=1, row=0, sticky='nswe', padx=5, pady=5)

    # LEGEND position
    legend_frame = tk.LabelFrame(plot_option_frame, text='Legend position')
    legend_frame.grid(column=0, row=3, sticky='nswe', padx=5, pady=5)

    # option menu variables
    legend_options = ['best', 'upper right', 'upper left', 'lower left', 'lower right', 'right', 'center left', 'center right', 'lower center', 'upper center', 'center']
    legend_pos = tk.StringVar(new_win)
    legend_pos.set('best')

    legend_menu = tk.OptionMenu(legend_frame, legend_pos, *legend_options)
    legend_menu.grid(column=0, row=0, sticky='nswe', padx=5, pady=5)

    # GRID on/off ?

    # Buttons
    button_replot = tk.ttk.Button(plot_option_frame, text='Replot', width=20)
    button_replot.grid(column=0, row=4)

    button_export = tk.ttk.Button(plot_option_frame, text='Export to CSV', width=20)
    button_export.grid(column=0, row=5)



    # LAYOUTs
    # layout PLOT frame
    plot_frame.columnconfigure(0, weight=1)
    plot_frame.rowconfigure(0, weight=1)

    # layout PLOT_OPTION frame
    plot_option_frame.columnconfigure(0, weight=1)
    plot_option_frame.rowconfigure(0, weight=1)

    # layout all of the main containers
    new_win.columnconfigure(0, weight=1)
    new_win.rowconfigure(0, weight=1)


# get selected tallies from treeview
def get_selected(treeview_file, selected):
    selection = []

    for row in selected:
        selection.append(treeview_file.item(row)['values'][0])

    return selection


# ----------------------------------------------------------------------------------------------------------------------
# support PLOT functions

# calculate central value for all bins
def interval_mid(x):
    x_center = []
    for i in range(0, len(x) - 1):
        x_center.append(x[i] + (x[i + 1] - x[i]) / 2)

    return x_center


# plot tallies from user
def plot_function(tally_to_plot):
    fig = plt.figure()

    for name in config_mod.tallies.keys():
        if name in tally_to_plot:
            #x_data, y_data, y_data_err = config_mod.tallies[name][3], config_mod.tallies[name][4], config_mod.tallies[name][5]      # unnormalized date
            x_data, y_data, y_data_err = config_mod.tallies[name][3], config_mod.tallies[name][7], config_mod.tallies[name][8]     # normalized data

            # calculate interval centers
            x_data_center = interval_mid(x_data)

            # plots
            plt.step(x_data, y_data, label=name)
            plt.errorbar(x_data_center, y_data[1:], yerr=y_data_err[1:], xerr=0, marker='_', linestyle='None', capthick=0.7, capsize=2)


    # todo zformátovat graf
    plt.legend(loc='upper right')
    plt.grid()
    plt.xlabel('energy (MeV)')
    plt.ylabel('average flux in cell per one generated neutron')
    plt.ticklabel_format(style='sci', axis='y', scilimits=(0,0))

    return fig