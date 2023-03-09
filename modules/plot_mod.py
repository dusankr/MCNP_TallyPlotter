# -*- coding: utf-8 -*-
# TODO_list:
# TODO bug - option menu for ratio plot is more complicated
# https://stackoverflow.com/questions/17580218/changing-the-options-of-a-optionmenu-when-clicking-a-button
# TODO change whole structure
# https://stackoverflow.com/questions/11154634/call-nested-function-in-python
# TODO reread some settings?
# far future:
# TODO change font in export settings window
# TODO turn on/off LaTeX in the export settings window

# libraries
import matplotlib
from modules import config_mod, editor_mod, plot_core, read_mod
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
import matplotlib.pyplot as plt     # MUST stay here!!!
import tkinter as tk
import pathlib


#  Functions  ##########################################################################################################
# create new Top level window and plot data
def plot_window(root, tally_to_plot):
    # close plot window if there are no tallies
    if tally_to_plot == None:
        return

    # region Tkinter local variables
    legend_options = ['best', 'upper right', 'upper left', 'lower left', 'lower right', 'right', 'center left',
                      'center right', 'lower center', 'upper center', 'center']
    legend_pos = tk.StringVar(value='best')  # Option Menu variable

    edit_options = ["config_export", "config_legend"]
    edit_var = tk.StringVar(value='config_export')

    def legend_opt():
        global ratio_options
        if len(tally_to_plot) > 1:
            ratio_options = ['no ratio']
            for key in config_mod.tallies.keys():
                if key in tally_to_plot:
                    ratio_options.append(config_mod.tallies[key][10])
        else:
            ratio_options = ['no ratio']

        #return ratio_options

    # first read of an option menu
    legend_opt()

    # radio button variable
    x_axis_var = tk.StringVar(value='linear')
    y_axis_var = tk.StringVar(value='linear')
    data_var = tk.StringVar(value='non')

    ratio_sel = tk.StringVar(value='no ratio')  # Option Menu variable
    replot_var = tk.BooleanVar(value=False)  # Check box variable

    # font size variables
    axis_var = tk.StringVar(value=12)  # SpinBox variable
    leg_var = tk.StringVar(value=10)  # SpinBox variable
    ticks_var = tk.StringVar(value=10)  # SpinBox variable

    # grid variables
    grid_options = ['major', 'minor', 'both']
    grid_axis_options = ['both', 'x', 'y']
    grid_var = tk.StringVar(value='major')  # Option Menu variable
    grid_axis_var = tk.StringVar(value='both')  # Option Menu variable
    grid_on_var = tk.BooleanVar(value=True)  # Check box variable
    save_var = tk.BooleanVar(value=False)  # Check box variable - save figure
    error_var = tk.BooleanVar(value=True)  # Turn on error bars

    xs_var = tk.BooleanVar(value=False)  # Check box variable - show XS data
    """ This is not more used - make problems if replot button is activated
    # figure size
    xfig_var = tk.StringVar(value=20)  # SpinBox variable
    yfig_var = tk.StringVar(value=15)  # SpinBox variable
    """

    # endregion

    # NEW Window definition---------------------------------------------------------------------------------------------
    plot_win = tk.Toplevel(root)
    plot_win.grab_set()      # the main window is locked until the new window is closed
    plot_win.geometry('1200x850')

    plot_win.title('Plotting window')

    # layout FOR all the main containers
    plot_win.columnconfigure(0, weight=1)
    plot_win.columnconfigure(1, weight=0)
    plot_win.rowconfigure(0, weight=1)

    # MAIN frames ------------------------------------------------------------------------------------------------------
    plot_frame = tk.ttk.Frame(plot_win)
    plot_frame.grid(column=0, row=0, sticky='nswe', padx=5, pady=5)  # set the margins between window and content

    # plot_frame.grid_propagate(False)      # Turn of auto resize of plot frame

    # layout PLOT frame
    plot_frame.columnconfigure(0, weight=1)
    plot_frame.rowconfigure(0, weight=1)

    plot_option_frame = tk.LabelFrame(plot_win, text='Plot settings', width=25)
    plot_option_frame.grid(column=1, row=0, sticky='nswe', padx=5, pady=5)
    # layout PLOT_OPTION frame
    plot_option_frame.columnconfigure(0, weight=1)
    plot_option_frame.rowconfigure(0, weight=0)         # weight=0 means no stretching...

    # Srollbar cannot work in window or frame -> canvas
    # https://riptutorial.com/tkinter/example/30942/scrolling-a-group-of-widgets
    # win_scroll = tk.Scrollbar(new_win, orient='vertical')
    # win_scroll.grid(sticky='ns', column=2, row=0)

    # Canvas definition
    config_mod.fig_id = matplotlib.figure.Figure()  # TODO looks like a very old matplotlib commands
    config_mod.ax = config_mod.fig_id.add_subplot()

    config_mod.canvas_id = FigureCanvasTkAgg(config_mod.fig_id, plot_frame)  # add Figure to canvas from plot function
    config_mod.canvas_id.get_tk_widget().grid(column=0, row=0, sticky='nswe')
    config_mod.canvas_id.draw()

    # Toolbar for plot
    toolbar_frame = tk.ttk.Frame(plot_frame)
    toolbar_frame.grid(column=0, row=1, sticky='nswe')
    toolbar = NavigationToolbar2Tk(config_mod.canvas_id, toolbar_frame)
    toolbar.update()

    # plot tallies from user -------------------------------------------------------------------------------------------
    def plot_function(tally):
        legend_opt()    # update option menu
        print(ratio_options)

        config_mod.plot_settings["ratio"] = ratio_sel.get()
        config_mod.plot_settings["data_var"] = data_var.get()
        config_mod.plot_settings["leg_pos"] = legend_pos.get()
        config_mod.plot_settings["leg_size"] = leg_var.get()
        config_mod.plot_settings["x_scale"] = x_axis_var.get()
        config_mod.plot_settings["y_scale"] = y_axis_var.get()
        config_mod.plot_settings["grid_switch"] = grid_on_var.get()
        config_mod.plot_settings["grid_opt"] = grid_var.get()
        config_mod.plot_settings["grid_ax"] = grid_axis_var.get()
        config_mod.plot_settings["ax_label_size"] = axis_var.get()
        config_mod.plot_settings["tics_size"] = ticks_var.get()
        config_mod.plot_settings["xs_switch"] = xs_var.get()
        config_mod.plot_settings["save_fig"] = save_var.get()
        config_mod.plot_settings["error_bar"] = error_var.get()

        # fill ax and fig with all curves and return it to the canvas
        plot_core.plot_to_canvas(tally)

        # Canvas for plot
        config_mod.canvas_id.draw()

    # insert FIRST plot CANVAS
    plot_function(tally_to_plot)

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

    chk_replot = tk.Checkbutton(data_inp_frame, text='error bars', var=error_var)
    chk_replot.grid(column=0, row=1, sticky='nswe', padx=5, pady=5)

    # plot_window(root, treeview_files, treeview_files.get_checked()
    ratio_menu = tk.OptionMenu(data_inp_frame, ratio_sel, *ratio_options)
    ratio_menu.grid(column=0, columnspan=2, row=2, sticky='nswe', padx=5, pady=5)

    # LEGEND settings --------------------------------------------------------------------------------------------------
    legend_frame = tk.LabelFrame(plot_option_frame, text='Legend settings')
    legend_frame.grid(column=0, row=3, sticky='nswe', padx=5, pady=5)
    legend_frame.columnconfigure(0, weight=1)
    legend_frame.rowconfigure(0, weight=1)

    # plot_window(root, treeview_files, treeview_files.get_checked()
    legend_menu = tk.OptionMenu(legend_frame, legend_pos, *legend_options)
    legend_menu.grid(column=0, row=0, sticky='nswe', padx=5, pady=5)

    leg_spinbox = tk.ttk.Spinbox(legend_frame, from_=5, to=20, textvariable=leg_var, wrap=True, width=4)
    leg_spinbox.grid(column=1, row=0, sticky='e', padx=5, pady=5)

    # text size frame --------------------------------------------------------------------------------------------------
    size_frame = tk.LabelFrame(plot_option_frame, text='Font size')
    size_frame.grid(column=0, row=5, sticky='nswe', padx=5, pady=5)
    size_frame.columnconfigure(0, weight=1)
    size_frame.rowconfigure(0, weight=1)

    axis_title = tk.Label(size_frame, text='Axis/Tics')
    axis_title.grid(column=0, row=0, sticky='nw', padx=5, pady=5)
    axis_spinbox = tk.ttk.Spinbox(size_frame, from_=5, to=20, textvariable=axis_var, wrap=True, width=4)
    axis_spinbox.grid(column=1, row=0, sticky='sne', padx=5, pady=5)

    ticks_spinbox = tk.ttk.Spinbox(size_frame, from_=5, to=20, textvariable=ticks_var, wrap=True, width=4)
    ticks_spinbox.grid(column=2, row=0, sticky='sne', padx=5, pady=5)

    # GRID settings ----------------------------------------------------------------------------------------------------
    grid_frame = tk.LabelFrame(plot_option_frame, text='Grid settings')
    grid_frame.grid(column=0, row=6, sticky='nswe', padx=5, pady=5)

    grid_chk = tk.Checkbutton(grid_frame, text='Grid ON', var=grid_on_var, command=lambda: change_state())
    grid_chk.grid(column=0, row=0, sticky='nswe', padx=5, pady=5)

    grid_menu = tk.OptionMenu(grid_frame, grid_var, *grid_options)
    grid_menu.grid(column=0, row=1, sticky='nswe', padx=5, pady=5)

    grid_axis_menu = tk.OptionMenu(grid_frame, grid_axis_var, *grid_axis_options)
    grid_axis_menu.grid(column=1, row=1, sticky='nswe', padx=5, pady=5)

    # cross sections frame ---------------------------------------------------------------------------------------------
    # TODO data source: ENDF, ACE, Talys
    # TODO choose XS data for plotting (more complicated)
    # TODO step vs. point plot
    xs_frame = tk.LabelFrame(plot_option_frame, text='Cross Section')
    xs_frame.grid(column=0, row=7, sticky='nswe', padx=5, pady=5)

    chk_xs = tk.Checkbutton(xs_frame, text='turn on a second Y axis', var=xs_var)
    chk_xs.grid(column=0, row=0, sticky='nswe', padx=5, pady=5)

    button_xs = tk.ttk.Button(xs_frame, text='Read XS', command=lambda: read_mod.read_xs())
    button_xs.grid(column=0, columnspan=2, row=1, sticky='nswe', padx=5, pady=5)

    # config (save, editor) --------------------------------------------------------------------------------------------
    save_frame = tk.LabelFrame(plot_option_frame, text='Export')
    save_frame.grid(column=0, row=8, sticky='nswe', padx=5, pady=5)

    legend_menu = tk.OptionMenu(save_frame, edit_var, *edit_options)
    legend_menu.grid(column=0, row=0, sticky='nswe', padx=5, pady=5)

    button_settings = tk.ttk.Button(save_frame, text='Editor settings/legend', command=lambda: editor_mod.open_lib(pathlib.Path(edit_var.get()), tally_to_plot, plot_win))
    button_settings.grid(column=0, columnspan=2, row=1, sticky='nswe', padx=5, pady=5)

    chk_replot = tk.Checkbutton(save_frame, text='On/Off save figure', var=save_var)
    chk_replot.grid(column=0, row=2, sticky='nswe', padx=5, pady=5)

    # replot frame -----------------------------------------------------------------------------------------------------
    replot_frame = tk.LabelFrame(plot_option_frame, text='Replot')
    replot_frame.grid(column=0, row=9, sticky='nswe', padx=5, pady=5)

    chk_replot = tk.Checkbutton(replot_frame, text='disable immediate changes', var=replot_var, command=lambda: turn_off_replot())
    chk_replot.grid(column=0, columnspan=2, row=0, sticky='nswe', padx=5, pady=5)

    button_replot = tk.ttk.Button(replot_frame, text='Replot', command=lambda: plot_function(), state='disabled')
    button_replot.grid(column=0, columnspan=2, row=1, sticky='nswe', padx=5, pady=5)

    # quit -------------------------------------------------------------------------------------------------------------
    button_quit = tk.ttk.Button(plot_option_frame, text='Quit', command=plot_win.destroy)
    button_quit.grid(column=0, row=10, sticky='we', padx=5, pady=5)

    # endregion all tkinter widgets for

    # FUNCTIONS conected to MAIN function ------------------------------------------------------------------------------

    # call replot when Option Menu is changed
    def my_callback(*args):
        plot_function(tally_to_plot)

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
    xs_var.trace_add('write', my_callback)
    save_var.trace_add('write', my_callback)
    error_var.trace_add('write', my_callback)

    # turn on-off online replot
    def turn_off_replot():
        if replot_var.get() == True:
            button_replot['state'] = 'normal'

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
            xs_var.trace_remove('write', xs_var.trace_info()[0][1])
            save_var.trace_remove('write', save_var.trace_info()[0][1])
            error_var.trace_remove('write', error_var.trace_info()[0][1])
        else:
            button_replot['state'] = 'disabled'

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
            xs_var.trace_add('write', my_callback)
            save_var.trace_add('write', my_callback)
            error_var.trace_add('write', my_callback)

    def change_state():
        if grid_on_var.get():
            grid_menu['state'] = 'normal'
            grid_axis_menu['state'] = 'normal'
        else:
            grid_menu['state'] = 'disabled'
            grid_axis_menu['state'] = 'disabled'
