# -*- coding: utf-8 -*-
# TODO_list:
# TODO umisteni do stejneho okna jako je je vyber tally?
# TODO ošetřit když chybí data přes try+except
# TODO ratio plot -> aktivovat jen když je zvoleno víc tally které mají stejný rozměr!!!
# TODO vyresit že jsou prvky rozhazene po okne...
# TODO nacteni jinych dat na dalsi osy Y (pro mě občas XS hodnoty, např. z Talys nebo ENDF formatu)
# TODO nacitani dalsich grafu, viz Pepovi potreby

# libraries
import matplotlib.figure
import matplotlib.pyplot as plt     # ploting in matlab style
from modules import config_mod
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)

# GUI libraries
import tkinter as tk


#  Functions  ##########################################################################################################
# create new Top level window and plot data
def plot_window(root, treeview_file, selected):
    new_win = tk.Toplevel(root)
    new_win.grab_set()      # the main window is locked until the new window is closed

    new_win.title('Plotting window')
    new_win.minsize(100, 150)

    # Tkinter variables ------------------------------------------------------------------------------------------------
    legend_options = ['best', 'upper right', 'upper left', 'lower left', 'lower right', 'right', 'center left', 'center right', 'lower center', 'upper center', 'center']
    legend_pos = tk.StringVar()      # Option Menu variable
    legend_pos.set(legend_options[0])

    tally_to_plot = get_selected(treeview_file, selected)  # obtain keys from checkedbox treeview

    if len(tally_to_plot) > 1:
        ratio_options = ['no ratio'] + tally_to_plot
    else:
        ratio_options = ['no ratio']

    # radio button variable
    x_axis_var = tk.StringVar(value='linear')
    y_axis_var = tk.StringVar(value='linear')
    data_var = tk.StringVar(value='non')

    ratio_sel = tk.StringVar(value='no ratio')       # Option Menu variable

    # ------------------------------------------------------------------------------------------------------------------

    plot_frame = tk.ttk.Frame(new_win)
    plot_frame.grid(column=0, row=0, sticky='nswe', padx=5, pady=5)  # set the margins between window and content

    plot_option_frame = tk.ttk.Frame(new_win)
    plot_option_frame.grid(column=1, row=0, sticky='nswe', padx=5, pady=5)

    # empty CANVAS definition
    empty_fig = matplotlib.figure.Figure(figsize=(5, 5))
    canvas = FigureCanvasTkAgg(empty_fig, plot_frame)
    canvas.get_tk_widget().grid(column=0, row=0, sticky='nswe')

    # plot tallies from user
    def plot_function(tally_to_plot, leg, x_scale, y_scale, data_inp, ratio_plot):
        fig, ax = plt.subplots()

        for name in config_mod.tallies.keys():
            if name in tally_to_plot:
                if data_inp == 'norm':
                    x_data, y_data, y_data_err = config_mod.tallies[name][3], config_mod.tallies[name][7], \
                                                 config_mod.tallies[name][8]  # normalized data
                elif data_inp == 'non':
                    x_data, y_data, y_data_err = config_mod.tallies[name][3], config_mod.tallies[name][4], \
                                                 config_mod.tallies[name][5]  # unnormalized date

                # calculate interval centers
                x_data_center = interval_mid(x_data)

                # plots
                p_color = next(ax._get_lines.prop_cycler)['color']
                ax.step(x_data, y_data, color=p_color, label=name)
                ax.errorbar(x_data_center, y_data[1:], yerr=y_data_err[1:], xerr=0, color=p_color, marker='None',
                            linestyle='None', capthick=0.7, capsize=2)

        ax.legend(loc=leg)
        ax.set_yscale(y_scale)
        ax.set_xscale(x_scale)
        ax.grid()
        ax.set_xlabel('energy (MeV)')
        ax.set_ylabel('average flux in cell per one generated neutron')
        #ax.ticklabel_format(style='sci', axis='y', scilimits=(0, 0))  # does not work in log scale with this setting

        # Canvas for plot
        canvas = FigureCanvasTkAgg(fig, plot_frame)  # add Figure to canvas from plot function
        canvas.draw()
        canvas.get_tk_widget().grid(column=0, row=0, sticky='nswe')

        # Toolbar for plot
        toolbar_frame = tk.ttk.Frame(new_win)
        toolbar_frame.grid(column=0, row=1, sticky='nswe')
        toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
        toolbar.update()



    plot_function(tally_to_plot, legend_pos.get(), x_axis_var.get(), y_axis_var.get(), data_var.get(), ratio_sel.get())

    # PLOT OPTION FRAME ------------------------------------------------------------------------------------------------

    # X AXIS Radio Button
    x_axis_frame = tk.LabelFrame(plot_option_frame, text='X axis settings')
    x_axis_frame.grid(column=0, row=0, sticky='nwe', padx=5, pady=5)

    x_lin_radio = tk.Radiobutton(x_axis_frame, text='linear', variable=x_axis_var, value='linear', tristatevalue="x", command=None)
    x_lin_radio.grid(column=0, row=0, sticky='nswe', padx=5, pady=5)
    x_log_radio = tk.Radiobutton(x_axis_frame, text='log', variable=x_axis_var, value='log', tristatevalue="x", command=None)
    x_log_radio.grid(column=1, row=0, sticky='nswe', padx=5, pady=5)

    # Y AXIS Radio Button
    y_axis_frame = tk.LabelFrame(plot_option_frame, text='Y axis settings')
    y_axis_frame.grid(column=0, row=1, sticky='nwe', padx=5, pady=5)

    y_lin_radio = tk.Radiobutton(y_axis_frame, text='linear', variable=y_axis_var, value='linear', tristatevalue="y")
    y_lin_radio.grid(column=0, row=0, sticky='nswe', padx=5, pady=5)
    y_log_radio = tk.Radiobutton(y_axis_frame, text='log', variable=y_axis_var, value='log', tristatevalue="y")
    y_log_radio.grid(column=1, row=0, sticky='nswe', padx=5, pady=5)

    # DATA Radio Button
    data_inp_frame = tk.LabelFrame(plot_option_frame, text='Data input')
    data_inp_frame.grid(column=0, row=2, sticky='n', padx=5, pady=5)

    data_inp_radio = tk.Radiobutton(data_inp_frame, text='norm', variable=data_var, value='norm', tristatevalue="z")
    data_inp_radio.grid(column=0, row=0, sticky='nswe', padx=5, pady=5)
    data_inp_radio = tk.Radiobutton(data_inp_frame, text='non', variable=data_var, value='non', tristatevalue="z")
    data_inp_radio.grid(column=1, row=0, sticky='nswe', padx=5, pady=5)

    # LEGEND position
    legend_frame = tk.LabelFrame(plot_option_frame, text='Legend position')
    legend_frame.grid(column=0, row=3, sticky='nswe', padx=5, pady=5)

    legend_menu = tk.ttk.OptionMenu(legend_frame, legend_pos, legend_options[0], *legend_options)   # plot_window(root, treeview_files, treeview_files.get_checked()
    legend_menu.grid(column=0, row=0, sticky='nswe', padx=5, pady=5)

    # Plot TO Plot ratio
    ratio_frame = tk.LabelFrame(plot_option_frame, text='Ratio plot')
    ratio_frame.grid(column=0, row=4, sticky='nswe', padx=5, pady=5)

    ratio_menu = tk.ttk.OptionMenu(ratio_frame, ratio_sel, ratio_options[0], *ratio_options)  # plot_window(root, treeview_files, treeview_files.get_checked()
    ratio_menu.grid(column=0, row=0, sticky='nswe', padx=5, pady=5)

    # Buttons
    button_replot = tk.ttk.Button(plot_option_frame, text='Replot', width=20, command=lambda: plot_function(tally_to_plot, legend_pos.get(), x_axis_var.get(), y_axis_var.get(), data_var.get(), ratio_sel.get()))    # add Figure to canvas from plot function
    button_replot.grid(column=0, row=5)

    # button_test = tk.ttk.Button(plot_option_frame, text='test', width=20, command=lambda: test_func(canvas))
    # button_test.grid(column=0, row=5)

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

'''
# plot tallies from user
def plot_function(tally_to_plot, leg, x_scale, y_scale, data_inp, ratio_plot):
    fig, ax = plt.subplots()

    for name in config_mod.tallies.keys():
        if name in tally_to_plot:
            if data_inp == 'norm':
                x_data, y_data, y_data_err = config_mod.tallies[name][3], config_mod.tallies[name][7], \
                                             config_mod.tallies[name][8]  # normalized data
            elif data_inp == 'non':
                x_data, y_data, y_data_err = config_mod.tallies[name][3], config_mod.tallies[name][4], \
                                             config_mod.tallies[name][5]  # unnormalized date

            # calculate interval centers
            x_data_center = interval_mid(x_data)

            # plots
            p_color = next(ax._get_lines.prop_cycler)['color']
            ax.step(x_data, y_data, color=p_color, label=name)
            ax.errorbar(x_data_center, y_data[1:], yerr=y_data_err[1:], xerr=0, color=p_color, marker='None', linestyle='None', capthick=0.7, capsize=2)


    ax.legend(loc=leg)
    ax.set_yscale(y_scale)
    ax.set_xscale(x_scale)
    ax.grid()
    ax.set_xlabel('energy (MeV)')
    ax.set_ylabel('average flux in cell per one generated neutron')
    ax.ticklabel_format(style='sci', axis='y', scilimits=(0,0))   # does not work in log scale with this setting

    return fig
'''