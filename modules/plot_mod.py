# -*- coding: utf-8 -*-
# TODO_list:
# TODO umisteni do stejneho okna jako je je vyber tally?
# TODO ratio plot -> aktivovat jen když je zvoleno víc tally které mají stejný rozměr!!!
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
    new_win.minsize(150, 200)

    # layout all of the main containers
    new_win.columnconfigure(0, weight=1)
    new_win.rowconfigure(0, weight=1)

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

    replot_var = tk.BooleanVar(value=True)     # check box variable

    # ------------------------------------------------------------------------------------------------------------------
    # MAIN frames
    plot_frame = tk.ttk.Frame(new_win, width=25)
    plot_frame.grid(column=0, row=0, sticky='nswe', padx=5, pady=5)  # set the margins between window and content
    # layout PLOT frame
    plot_frame.columnconfigure(0, weight=1)
    plot_frame.rowconfigure(0, weight=1)

    plot_option_frame = tk.ttk.Frame(new_win)
    plot_option_frame.grid(column=1, row=0, sticky='nswe', padx=5, pady=5)
    # layout PLOT_OPTION frame
    plot_option_frame.columnconfigure(0, weight=1)
    plot_option_frame.rowconfigure(0, weight=0)         # wegiht=0 means no stretching...

    # empty CANVAS definition
    empty_fig = matplotlib.figure.Figure(figsize=(5, 5))
    canvas = FigureCanvasTkAgg(empty_fig, plot_frame)
    canvas.get_tk_widget().grid(column=0, row=0, sticky='nswe')

    # plot tallies from user
    def plot_function():
        fig, ax = plt.subplots()

        for name in config_mod.tallies.keys():
            if name in tally_to_plot:
                if data_var.get() == 'norm':
                    x_data, y_data, y_data_err = config_mod.tallies[name][3], config_mod.tallies[name][7], \
                                                 config_mod.tallies[name][8]  # normalized data
                elif data_var.get() == 'non':
                    x_data, y_data, y_data_err = config_mod.tallies[name][3], config_mod.tallies[name][4], \
                                                 config_mod.tallies[name][5]  # unnormalized date

                # calculate interval centers
                x_data_center = interval_mid(x_data)

                # plots
                p_color = next(ax._get_lines.prop_cycler)['color']
                ax.step(x_data, y_data, color=p_color, label=name)
                ax.errorbar(x_data_center, y_data[1:], yerr=y_data_err[1:], xerr=0, color=p_color, marker='None',
                            linestyle='None', capthick=0.7, capsize=2)

        ax.legend(loc=legend_pos.get())
        ax.set_yscale(y_axis_var.get())
        ax.set_xscale(x_axis_var.get())
        ax.grid()
        ax.set_xlabel('energy (MeV)')
        ax.set_ylabel('average flux in cell per one generated neutron')
        if y_axis_var.get() == 'linear':
            ax.ticklabel_format(style='sci', axis='y', scilimits=(0, 0), useMathText=True)  # does not work in log scale with this setting

        # Canvas for plot
        canvas = FigureCanvasTkAgg(fig, plot_frame)  # add Figure to canvas from plot function
        canvas.draw()
        canvas.get_tk_widget().grid(column=0, row=0, sticky='nswe')

        # Toolbar for plot
        toolbar_frame = tk.ttk.Frame(new_win)
        toolbar_frame.grid(column=0, row=1, sticky='nswe')
        toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
        toolbar.update()

    # insert FIRST plot into empty CANVAS
    plot_function()

    # PLOT OPTION FRAME ------------------------------------------------------------------------------------------------

    # X AXIS Radio Button
    x_axis_frame = tk.LabelFrame(plot_option_frame, text='X axis settings')
    x_axis_frame.grid(column=0, row=0, sticky='nwe', padx=5, pady=5)

    x_lin_radio = tk.Radiobutton(x_axis_frame, text='linear', variable=x_axis_var, value='linear', tristatevalue="x")
    x_lin_radio.grid(column=0, row=0, sticky='nswe', padx=5, pady=5)
    x_log_radio = tk.Radiobutton(x_axis_frame, text='log', variable=x_axis_var, value='log', tristatevalue="x")
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
    data_inp_frame.grid(column=0, row=2, sticky='nswe', padx=5, pady=5)

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

    # replot frame
    replot_frame = tk.LabelFrame(plot_option_frame, text='Replot')
    replot_frame.grid(column=0, row=5, sticky='nswe', padx=5, pady=5)

    chk_replot = tk.Checkbutton(replot_frame, text='disable on change replot', var=replot_var)
    chk_replot.grid(column=0, row=0, sticky='nswe', padx=5, pady=5)

    button_replot = tk.ttk.Button(replot_frame, text='Replot', command=lambda: plot_function())    # add Figure to canvas from plot function
    button_replot.grid(column=0, row=1, sticky='nswe', padx=5, pady=5)

    button_quit = tk.ttk.Button(plot_option_frame, text='Quit', command=lambda: new_win.destroy())
    button_quit.grid(column=0, row=6, sticky='nswe', padx=5, pady=5)

    # call replot when Option Menu are changed
    def my_callback(*args):
        plot_function()

    legend_pos.trace_add('write', my_callback)
    ratio_sel.trace_add('write', my_callback)
    x_axis_var.trace_add('write', my_callback)
    y_axis_var.trace_add('write', my_callback)
    data_var.trace_add('write', my_callback)

    '''
    def online_replot():
        
        if replot_var.get() == True:
            legend_pos.trace_remove()
            ratio_sel.trace_remove()
            x_axis_var.trace_remove()
            y_axis_var.trace_remove()
            data_var.trace_remove()
        

    def my_callback_2():
        if replot_var.get() == False:
            button_replot['state'] = 'disabled'
        else:
            button_replot['state'] = 'normal'

    replot_var.trace('r', my_callback_2)
    '''

# ---------------------------------------------------------------------------------------------------------------------
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
