# -*- coding: utf-8 -*-
# TODO_list:

# Dlouhodobe:
# TODO nacteni jinych dat na dalsi osy Y (pro mě občas XS hodnoty, např. z Talys nebo ENDF formatu)
# TODO umisteni do stejneho okna jako je je vyber tally?
# TODO excel export
# Provozni/vylepseni kodu
# TODO předělat kreslení grafů na updata podle vzorů na webu...

# TODO přesunout ratio plot do externi fce.
# Nastavení grafu
# TODO nové názvy os
# TODO volba fontu pro export
# TODO scrollbar pro nastaveni grafu
# TODO zabránit neustálým změnám velikosti okna
# tkinter.tix.ScrolledWindow
# https://stackoverflow.com/questions/21255216/python-tkinter-attributeerror-nonetype-object-has-no-attribute-xview
# https://stackoverflow.com/questions/23705043/nonetype-object-has-no-attribute-yview
# https://blog.teclado.com/tkinter-scrollable-frames/

# libraries
import matplotlib
import matplotlib.pyplot as plt     # ploting in matlab style
from modules import config_mod
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
import math

# GUI libraries
import tkinter as tk


#  Functions  ##########################################################################################################
# create new Top level window and plot data
def plot_window(root, tally_to_plot):

    # Tkinter variables
    legend_options = ['best', 'upper right', 'upper left', 'lower left', 'lower right', 'right', 'center left',
                      'center right', 'lower center', 'upper center', 'center']
    legend_pos = tk.StringVar(value='best')  # Option Menu variable

    if len(tally_to_plot) > 1:
        ratio_options = ['no ratio'] + tally_to_plot
    else:
        ratio_options = ['no ratio']

    # radio button variable
    x_axis_var = tk.StringVar(value='linear')
    y_axis_var = tk.StringVar(value='linear')
    data_var = tk.StringVar(value='non')

    ratio_sel = tk.StringVar(value='no ratio')  # Option Menu variable
    replot_var = tk.BooleanVar(value=False)  # Check box variable

    # font size variables
    axis_var = tk.StringVar(value=11)  # SpinBox variable
    leg_var = tk.StringVar(value=8)  # SpinBox variable
    ticks_var = tk.StringVar(value=10)  # SpinBox variable

    # grid variables
    grid_options = ['major', 'minor', 'both']
    grid_axis_options = ['both', 'x', 'y']
    grid_var = tk.StringVar(value='major')  # Option Menu variable
    grid_axis_var = tk.StringVar(value='both')  # Option Menu variable
    grid_on_var = tk.BooleanVar(value=True)  # Check box variable

    # figure size
    xfig_var = tk.StringVar(value=20)  # SpinBox variable
    yfig_var = tk.StringVar(value=15)  # SpinBox variable

    # NEW Window definition---------------------------------------------------------------------------------------------
    new_win = tk.Toplevel(root)
    new_win.grab_set()      # the main window is locked until the new window is closed

    new_win.title('Plotting window')
    new_win.minsize(150, 200)

    # layout all of the main containers
    new_win.columnconfigure(0, weight=1)
    new_win.columnconfigure(1, weight=0)
    new_win.rowconfigure(0, weight=1)

    # MAIN frames ------------------------------------------------------------------------------------------------------
    plot_frame = tk.ttk.Frame(new_win)
    plot_frame.grid(column=0, row=0, sticky='nswe', padx=5, pady=5)  # set the margins between window and content
    plot_frame.grid_propagate(False)
    # layout PLOT frame
    plot_frame.columnconfigure(0, weight=1)
    plot_frame.rowconfigure(0, weight=1)

    plot_option_frame = tk.LabelFrame(new_win, text='Plot settings', width=25)
    plot_option_frame.grid(column=1, columnspan=2, row=0, sticky='nswe', padx=5, pady=5)
    # layout PLOT_OPTION frame
    plot_option_frame.columnconfigure(0, weight=1)
    plot_option_frame.rowconfigure(0, weight=0)         # weight=0 means no stretching...
    ''''
    option_scroll = tk.ttk.Scrollbar(new_win, orient='vertical', command=new_win.yview)
    option_scroll.grid(sticky='wens', column=2, row=0, rowspan=1, padx=5, pady=5)
    new_win.configure(yscrollcommand=option_scroll.set)
    
    option_scroll = tk.ttk.Scrollbar(plot_option_frame, orient='vertical', command=plot_option_frame.yview)
    option_scroll.grid(sticky='wens', column=1, row=0, rowspan=8, padx=5, pady=5)
    plot_option_frame.configure(yscrollcommand=option_scroll.set)
    '''

    # plot tallies from user -------------------------------------------------------------------------------------------
    def plot_function():

        # close previous instance of figure
        if len(plt.get_fignums()) > 1:
            plt.close(plt.gcf().number)

        # delete previous instance of canvas if exists
        if config_mod.canvas_id:
            config_mod.canvas_id.get_tk_widget().destroy()

        fig, ax = plt.subplots()        # figsize=(10,8)
        fig.set_size_inches(float(xfig_var.get()) / 2.54, float(yfig_var.get()) / 2.54)

        # read reference data for ratio plot
        if (ratio_sel.get() != 'no ratio') and (data_var.get() == 'non'):
            x_ratio, y_ratio, y_err_ratio = config_mod.tallies[ratio_sel.get()][3], config_mod.tallies[ratio_sel.get()][4], config_mod.tallies[ratio_sel.get()][5]
        elif (ratio_sel.get() != 'no ratio') and (data_var.get() == 'norm'):
            x_ratio, y_ratio, y_err_ratio = config_mod.tallies[ratio_sel.get()][3], config_mod.tallies[ratio_sel.get()][7], config_mod.tallies[ratio_sel.get()][5]

        # create new list in case the ratio plot is chosen and delete reference tally
        tally_to_plot_mod = tally_to_plot[:]
        if ratio_sel.get() in tally_to_plot_mod:
            tally_to_plot_mod.remove(ratio_sel.get())

        for name in config_mod.tallies.keys():
            if name in tally_to_plot_mod:
                if data_var.get() == 'norm':
                    x_data, y_data, y_data_err = config_mod.tallies[name][3], config_mod.tallies[name][7][:], config_mod.tallies[name][5][:]  # normalized data
                    y_label = 'Tally / MeV / particle'
                elif data_var.get() == 'non':
                    x_data, y_data, y_data_err = config_mod.tallies[name][3], config_mod.tallies[name][4][:], config_mod.tallies[name][5][:]  # original data
                    y_label = 'Tally / particle'

                if ratio_sel.get() != 'no ratio':
                    y_label = 'Tally to Tally ratio (-)'
                    if x_data != x_ratio:   # skip this cycle step if energy bins in current tally have different step from reference tally
                        continue

                    for i in range(0, len(y_data)):     # calculate ratio values and their errors
                        if (y_data[i] != 0) and (y_ratio[i] != 0):      # only for non zero values
                            y_data_err[i] = math.sqrt(y_data_err[i]**2 + y_err_ratio[i]**2)
                            y_data[i] = y_data[i] / y_ratio[i]
                        else:
                            y_data[i] = 0
                            y_data_err[i] = 0

                    name = name + '/' + ratio_sel.get()

                # calculate interval centers
                x_data_center = interval_mid(x_data)

                # plots
                p_color = next(ax._get_lines.prop_cycler)['color']      # same color for step and errorbar plot
                ax.step(x_data, y_data, color=p_color, label=name)

                err = [a*b for a,b in zip(y_data_err, y_data)]          # abs error
                ax.errorbar(x_data_center, y_data[1:], yerr=err[1:], xerr=0, color=p_color, marker='None',  linestyle='None', capthick=0.7, capsize=2)

        # plot settings
        ax.legend(loc=legend_pos.get(), fontsize=leg_var.get())
        ax.set_xscale(x_axis_var.get())
        ax.set_yscale(y_axis_var.get())
        ax.grid(visible=grid_on_var.get(), which=grid_var.get(), axis=grid_axis_var.get())
        ax.set_xlabel('energy (MeV)', fontsize=axis_var.get())
        ax.set_ylabel(y_label, fontsize=axis_var.get())
        ax.tick_params(axis='both', labelsize=ticks_var.get())
        if y_axis_var.get() == 'linear':
            ax.ticklabel_format(style='sci', axis='y', scilimits=(0, 0), useMathText=True)  # does not work in log scale with this setting

        # Canvas for plot
        config_mod.canvas_id = FigureCanvasTkAgg(fig, plot_frame)  # add Figure to canvas from plot function
        config_mod.canvas_id.draw()

        if replot_var.get():
            config_mod.canvas_id.get_tk_widget().grid(column=0, row=0)
        else:
            config_mod.canvas_id.get_tk_widget().grid(column=0, row=0, sticky='nswe')

        # Toolbar for plot
        toolbar_frame = tk.ttk.Frame(plot_frame)
        toolbar_frame.grid(column=0, row=1, sticky='nswe')
        toolbar = NavigationToolbar2Tk(config_mod.canvas_id, toolbar_frame)
        toolbar.update()

    # insert FIRST plot CANVAS
    plot_function()

    # region Description: all Tkinter Widgets used for plot settings
    # PLOT OPTION FRAME ------------------------------------------------------------------------------------------------

    # X AXIS Radio Button ----------------------------------------------------------------------------------------------
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

    # DATA Radio Button ------------------------------------------------------------------------------------------------
    data_inp_frame = tk.LabelFrame(plot_option_frame, text='Data input')
    data_inp_frame.grid(column=0, row=2, sticky='nswe', padx=5, pady=5)

    data_inp_radio = tk.Radiobutton(data_inp_frame, text='norm', variable=data_var, value='norm', tristatevalue="z")
    data_inp_radio.grid(column=0, row=0, sticky='nswe', padx=5, pady=5)
    data_inp_radio = tk.Radiobutton(data_inp_frame, text='non', variable=data_var, value='non', tristatevalue="z")
    data_inp_radio.grid(column=1, row=0, sticky='nswe', padx=5, pady=5)

    # LEGEND settings --------------------------------------------------------------------------------------------------
    legend_frame = tk.LabelFrame(plot_option_frame, text='Legend settings')
    legend_frame.grid(column=0, row=3, sticky='nswe', padx=5, pady=5)
    legend_frame.columnconfigure(0, weight=1)
    legend_frame.rowconfigure(0, weight=1)

    legend_menu = tk.OptionMenu(legend_frame, legend_pos, *legend_options)   # plot_window(root, treeview_files, treeview_files.get_checked()
    legend_menu.grid(column=0, row=0, sticky='nswe', padx=5, pady=5)

    leg_spinbox = tk.ttk.Spinbox(legend_frame, from_=5, to=20, textvariable=leg_var, wrap=True, width=4)
    leg_spinbox.grid(column=1, row=0, sticky='e', padx=5, pady=5)

    # Plot TO Plot ratio -----------------------------------------------------------------------------------------------
    ratio_frame = tk.LabelFrame(plot_option_frame, text='Ratio plot')
    ratio_frame.grid(column=0, row=4, sticky='nswe', padx=5, pady=5)

    ratio_menu = tk.OptionMenu(ratio_frame, ratio_sel, *ratio_options)  # plot_window(root, treeview_files, treeview_files.get_checked()
    ratio_menu.grid(column=0, row=0, sticky='nswe', padx=5, pady=5)

    # text size frame --------------------------------------------------------------------------------------------------
    size_frame = tk.LabelFrame(plot_option_frame, text='Font size')
    size_frame.grid(column=0, row=5, sticky='nswe', padx=5, pady=5)
    size_frame.columnconfigure(0, weight=1)
    size_frame.rowconfigure(0, weight=1)

    axis_title = tk.Label(size_frame, text='Axis title size')
    axis_title.grid(column=0, row=0, sticky='nw', padx=5, pady=5)
    axis_spinbox = tk.ttk.Spinbox(size_frame, from_=5, to=20, textvariable=axis_var, wrap=True, width=4)
    axis_spinbox.grid(column=1, row=0, sticky='sne', padx=5, pady=5)

    ticks_title = tk.Label(size_frame, text='Ticks title size')
    ticks_title.grid(column=0, row=1, sticky='nw', padx=5, pady=5)
    ticks_spinbox = tk.ttk.Spinbox(size_frame, from_=5, to=20, textvariable=ticks_var, wrap=True, width=4)
    ticks_spinbox.grid(column=1, row=1, sticky='sne', padx=5, pady=5)

    # GRID settings ----------------------------------------------------------------------------------------------------
    grid_frame = tk.LabelFrame(plot_option_frame, text='Grid settings')
    grid_frame.grid(column=0, row=6, sticky='nswe', padx=5, pady=5)

    grid_chk = tk.Checkbutton(grid_frame, text='Grid ON', var=grid_on_var, command=lambda: change_state())
    grid_chk.grid(column=0, row=0, sticky='nswe', padx=5, pady=5)

    grid_menu = tk.OptionMenu(grid_frame, grid_var, *grid_options)
    grid_menu.grid(column=0, row=1, sticky='nswe', padx=5, pady=5)

    grid_axis_menu = tk.OptionMenu(grid_frame, grid_axis_var, *grid_axis_options)
    grid_axis_menu.grid(column=1, row=1, sticky='nswe', padx=5, pady=5)

    # replot frame -----------------------------------------------------------------------------------------------------
    replot_frame = tk.LabelFrame(plot_option_frame, text='Replot')
    replot_frame.grid(column=0, row=7, sticky='nswe', padx=5, pady=5)
    #replot_frame.columnconfigure(0, weight=0)
    #replot_frame.rowconfigure(0, weight=0)

    chk_replot = tk.Checkbutton(replot_frame, text='disable on change replot', var=replot_var, command=lambda: turn_off_replot())
    chk_replot.grid(column=0, columnspan=2, row=0, sticky='nswe', padx=5, pady=5)

    width_title = tk.Label(replot_frame, text='Width (cm)')
    width_title.grid(column=0, row=1, sticky='nw', padx=5, pady=5)
    height_title = tk.Label(replot_frame, text='Height (cm)')
    height_title.grid(column=1, row=1, sticky='nw', padx=5, pady=5)

    width_spinbox = tk.ttk.Spinbox(replot_frame, from_=5, to=30, increment=.1, state='readonly', textvariable=xfig_var, wrap=True, width=4)
    width_spinbox.grid(column=0, row=2, sticky='sn', padx=5, pady=5)
    height_spinbox = tk.ttk.Spinbox(replot_frame, from_=5, to=30, increment=.1, state='readonly', textvariable=yfig_var, wrap=True, width=4)
    height_spinbox.grid(column=1, row=2, sticky='sn', padx=5, pady=5)

    button_replot = tk.ttk.Button(replot_frame, text='Replot', command=lambda: plot_function())    # add Figure to canvas from plot function
    button_replot['state'] = 'disabled'
    button_replot.grid(column=0, columnspan=2, row=3, sticky='nswe', padx=5, pady=5)

    # TODO opravit: havaruje pri zavreni grafu a jeho znovuotvreni
    '''
    button_quit = tk.ttk.Button(plot_option_frame, text='Quit', command=new_win.quit)
    button_quit.grid(column=0, row=6, sticky='nswe', padx=5, pady=5)
    '''
    # endregion all tkinter widgets for

    # FUNCTIONS conected to MAIN function ------------------------------------------------------------------------------

    # call replot when Option Menu are changed
    def my_callback(*args):
        plot_function()

    # first definition of Tkinter Variables tracing
    legend_pos.trace_add('write', my_callback)
    ratio_sel.trace_add('write', my_callback)
    x_axis_var.trace_add('write', my_callback)
    y_axis_var.trace_add('write', my_callback)
    data_var.trace_add('write', my_callback)
    axis_var.trace_add('write', my_callback)
    leg_var.trace_add('write', my_callback)
    grid_on_var.trace_add('write', my_callback)
    grid_var.trace_add('write', my_callback)
    grid_axis_var.trace_add('write', my_callback)
    ticks_var.trace_add('write', my_callback)

    # turn on-off online replot
    def turn_off_replot():
        if replot_var.get() == True:
            button_replot['state'] = 'normal'
            width_spinbox['state'] = 'normal'
            height_spinbox['state'] = 'normal'

            legend_pos.trace_remove('write', legend_pos.trace_info()[0][1])
            ratio_sel.trace_remove('write', ratio_sel.trace_info()[0][1])
            x_axis_var.trace_remove('write', x_axis_var.trace_info()[0][1])
            y_axis_var.trace_remove('write', y_axis_var.trace_info()[0][1])
            data_var.trace_remove('write', data_var.trace_info()[0][1])
            axis_var.trace_remove('write', axis_var.trace_info()[0][1])
            leg_var.trace_remove('write', leg_var.trace_info()[0][1])
            grid_on_var.trace_remove('write', grid_on_var.trace_info()[0][1])
            grid_var.trace_remove('write', grid_var.trace_info()[0][1])
            grid_axis_var.trace_remove('write', grid_axis_var.trace_info()[0][1])
            ticks_var.trace_remove('write', ticks_var.trace_info()[0][1])
        else:
            button_replot['state'] = 'disabled'
            width_spinbox['state'] = 'readonly'
            height_spinbox['state'] = 'readonly'

            legend_pos.trace_add('write', my_callback)
            ratio_sel.trace_add('write', my_callback)
            x_axis_var.trace_add('write', my_callback)
            y_axis_var.trace_add('write', my_callback)
            data_var.trace_add('write', my_callback)
            axis_var.trace_add('write', my_callback)
            leg_var.trace_add('write', my_callback)
            grid_on_var.trace_add('write', my_callback)
            grid_var.trace_add('write', my_callback)
            grid_axis_var.trace_add('write', my_callback)
            ticks_var.trace_add('write', my_callback)

    def change_state():
        if grid_on_var.get():
            grid_menu['state'] = 'normal'
            grid_axis_menu['state'] = 'normal'
        else:
            grid_menu['state'] = 'disabled'
            grid_axis_menu['state'] = 'disabled'


# OUTSIDE functions ----------------------------------------------------------------------------------------------------
# calculate central value for all bins
def interval_mid(x):
    x_center = []
    for i in range(0, len(x) - 1):
        x_center.append(x[i] + (x[i + 1] - x[i]) / 2)

    return x_center
