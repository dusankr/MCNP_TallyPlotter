# -*- coding: utf-8 -*-
# TODO_list:
# TODO replace all the functions with classes
# TODO replace variables with dictionary (can I work with widget variables all the time instead current solution?)
# TODO replace tally to plot with config_mod.tally_to_plot
# TODO reload settings from last session
# TODO change font in export settings window
# TODO turn on/off LaTeX in the export settings window
# cross section data
# TODO data source: ACE
# TODO choose XS data for plotting (more complicated)
# TODO step vs. point plot

# libraries
import matplotlib.style
from modules import config_mod, editor_mod, plot_core, read_mod, settings_mod
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
import matplotlib
import matplotlib.pyplot as plt     # MUST stay here!!!
import tkinter as tk


#  Functions  ##########################################################################################################
# create new Top level window and plot data
def plot_window(root, tally_to_plot):
    def quit_m():
        # close the editor window and grab the plot window
        root.grab_set()
        plot_win.destroy()

    # close the plot window if there are no tallies
    if tally_to_plot == None:
        return

    # region Tkinter local variables ----------------------------------------------------------------------------------
    
    legend_options = ['best', 'upper right', 'upper left', 'lower left', 'lower right', 'right', 'center left',
                      'center right', 'lower center', 'upper center', 'center']
    legend_pos = tk.StringVar(value='best')  # Option Menu variable

    # create a list of values for the ratio menu
    if len(tally_to_plot) > 1:
        ratio_options = ['no ratio'] + tally_to_plot
    else:
        ratio_options = ['no ratio']

    # radio button variable
    x_axis_var = tk.StringVar(value='log')
    y_axis_var = tk.StringVar(value='log')
    y2_axis_var = tk.StringVar(value='log')
    data_var = tk.BooleanVar(value=True)

    ratio_sel = tk.StringVar(value='no ratio')  # Option Menu variable
    replot_var = tk.BooleanVar(value=False)

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
    
    # additional data modifiers
    error_var = tk.BooleanVar(value=True)  # Turn on error bars
    bin_var = tk.BooleanVar(value=True)  # Turn on first bin
    fig_title_var = tk.BooleanVar(value=False)  # Check box variable - use figure title
    
    # XS data
    xs_var = tk.BooleanVar(value=False)  # Check box variable - show XS data
    
    # Axes limits
    y_min_var = tk.StringVar(value='None')
    y_max_var = tk.StringVar(value='None')
    x_min_var = tk.StringVar(value='None')
    x_max_var = tk.StringVar(value='None')
    y2_min_var = tk.StringVar(value='None')
    y2_max_var = tk.StringVar(value='None')
    # xlim_var = tk.BooleanVar(value=False)  # Check box variable - use X axis limits

    # Tally multiplier
    multiplier_var = tk.StringVar(value='1.0')  # SpinBox variable
  
    # Line options
    line_style_var = tk.BooleanVar(value=True)  # Check box variable - unique line style by file
    line_width_var = tk.DoubleVar(value=1.4)  # SpinBox variable - line width

    # figure export variables
    x_fig_var = tk.DoubleVar(value=20)  # SpinBox variable
    y_fig_var = tk.DoubleVar(value=15)  # SpinBox variable
    dpi_var = tk.DoubleVar(value=150)  # SpinBox variable
    latex_var = tk.BooleanVar(value=False)   # check box LaTeX

    # endregion

    # ------------------------------------------------------------------------------------------------------------------
    # NEW Window definition---------------------------------------------------------------------------------------------
    plot_win = tk.Toplevel(root)
    plot_win.grab_set()      # the main window is locked until the new window is closed
    plot_win.geometry('1200x700')

    plot_win.title('Plotting window')

    # layout FOR all the main containers
    plot_win.columnconfigure(0, weight=1)
    plot_win.columnconfigure(1, weight=0)
    plot_win.rowconfigure(0, weight=1)

    # MAIN frames ------------------------------------------------------------------------------------------------------
    plot_frame = tk.ttk.Frame(plot_win)
    plot_frame.grid(column=0, row=0, sticky='nswe', padx=2, pady=2)  # set the margins between window and content
    plot_frame.columnconfigure(0, weight=1)
    plot_frame.rowconfigure(0, weight=1)
    # plot_frame.grid_propagate(False)      # Turn of auto resize of plot frame

    # PLOT_OPTION both columns
    option_frame = tk.LabelFrame(plot_win, width=40)
    option_frame.grid(column=1, row=0, sticky='nswe', padx=2, pady=2)
    option_frame.columnconfigure(0, weight=1)
    option_frame.columnconfigure(1, weight=1)
    option_frame.rowconfigure(0, weight=1)  # weight=0 means no stretching...

    # first column
    plot_option_frame = tk.LabelFrame(option_frame, text='Plot settings I', width=20)
    plot_option_frame.grid(column=0, row=0, sticky='nswe', padx=2, pady=2)
    # plot_option_frame.columnconfigure(0, weight=1)
    # plot_option_frame.rowconfigure(0, weight=0)  # weight=0 means no stretching...

    # second column
    plot_option_frame2 = tk.LabelFrame(option_frame,text="Plot settings II", width=20)
    plot_option_frame2.grid(column=1, row=0, sticky='nswe', padx=2, pady=2)
    # plot_option_frame2.columnconfigure(0, weight=1)
    # plot_option_frame2.rowconfigure(0, weight=0)  # weight=0 means no stretching...

    # new row - unused
    # bottom_opt_frame = tk.LabelFrame(option_frame)
    # bottom_opt_frame.grid(column=0, columnspan=2, row=1)

    # Canvas definition     # TODO try to define this only in plot core
    config_mod.fig_id = matplotlib.pyplot.figure()
    config_mod.ax = config_mod.fig_id.add_subplot()

    config_mod.canvas_id = FigureCanvasTkAgg(config_mod.fig_id, plot_frame)  # add Figure to canvas from plot function
    config_mod.canvas_id.get_tk_widget().grid(column=0, row=0, sticky='nswe')

    # Toolbar for plot
    toolbar_frame = tk.ttk.Frame(plot_frame)
    toolbar_frame.grid(column=0, row=1, sticky='nswe')
    toolbar = NavigationToolbar2Tk(config_mod.canvas_id, toolbar_frame)
    toolbar.update()

    # white background in plot on Mac
    matplotlib.rcParams['axes.facecolor'] = 'white'     # set only the background color of the plot
    # matplotlib.style.use('classic')   # set the style of the plot - global setting

    # save values from widgets into dictionary
    def plot_variables(save=False):

        config_mod.plot_settings["ratio"] = ratio_sel.get()
        config_mod.plot_settings["data_var"] = data_var.get()
        config_mod.plot_settings["leg_pos"] = legend_pos.get()
        config_mod.plot_settings["leg_size"] = leg_var.get()
        config_mod.plot_settings["x_scale"] = x_axis_var.get()
        config_mod.plot_settings["y_scale"] = y_axis_var.get()
        config_mod.plot_settings["y2_scale"] = y2_axis_var.get()
        config_mod.plot_settings["grid_switch"] = grid_on_var.get()
        config_mod.plot_settings["grid_opt"] = grid_var.get()
        config_mod.plot_settings["grid_ax"] = grid_axis_var.get()
        config_mod.plot_settings["ax_label_size"] = axis_var.get()
        config_mod.plot_settings["tics_size"] = ticks_var.get()
        config_mod.plot_settings["xs_switch"] = xs_var.get()
        
        config_mod.plot_settings["error_bar"] = error_var.get()
        config_mod.plot_settings["first_bin"] = bin_var.get()
        config_mod.plot_settings["latex"] = latex_var.get()
        
        # limits
        config_mod.plot_settings["x_min"] = x_min_var.get()
        config_mod.plot_settings["x_max"] = x_max_var.get()
        config_mod.plot_settings["y_min"] = y_min_var.get()
        config_mod.plot_settings["y_max"] = y_max_var.get()
        config_mod.plot_settings["y2_min"] = y2_min_var.get()
        config_mod.plot_settings["y2_max"] = y2_max_var.get()
        
        # config_mod.plot_settings["x_lim"] = xlim_var.get()
        config_mod.plot_settings["fig_title_switch"] = fig_title_var.get()
        
        # save figure
        config_mod.plot_settings['fig_x_dimension'] = x_fig_var.get()
        config_mod.plot_settings['fig_y_dimension'] = y_fig_var.get()
        config_mod.plot_settings['save_fig'] = save
        config_mod.plot_settings['fig_dpi'] = dpi_var.get()

        # Tally multiplier
        config_mod.plot_settings['tally_multiplier'] = multiplier_var.get()

        # Line options
        config_mod.plot_settings['line_style_by_file'] = line_style_var.get()
        config_mod.plot_settings['line_width'] = line_width_var.get()

        # save values to the config file
        settings_mod.save_config()
        settings_mod.read_config("config_export")

    # insert FIRST plot CANVAS
    plot_variables()
    plot_core.plot_to_canvas(tally_to_plot)

    # region Description: all Tkinter Widgets used for plot settings
    # PLOT OPTION FRAME ------------------------------------------------------------------------------------------------
    row_c = 0

    # SCALE frame ------------------------------------------------------------------------------------------------------
    scale_frame = tk.LabelFrame(plot_option_frame, text='Axis scale')
    scale_frame.grid(column=0, row=row_c, sticky='nswe', padx=2, pady=2)
    scale_frame.columnconfigure(0, weight=0)
    scale_frame.columnconfigure(0, weight=0)
    scale_frame.columnconfigure(0, weight=0)
    row_c += 1
    row_f = 0

    x_scale_label = tk.Label(scale_frame, text='X axis:')
    x_scale_label.grid(column=0, row=row_f, sticky='nw', padx=2, pady=2)
    x_lin_radio = tk.Radiobutton(scale_frame, text='linear', variable=x_axis_var, value='linear', tristatevalue="x")
    x_lin_radio.grid(column=1, row=row_f, sticky='nw', padx=2, pady=2)
    x_log_radio = tk.Radiobutton(scale_frame, text='log', variable=x_axis_var, value='log', tristatevalue="x")
    x_log_radio.grid(column=2, row=row_f, sticky='nw', padx=2, pady=2)
    row_f += 1

    y_scale_label = tk.Label(scale_frame, text='Y axis:')
    y_scale_label.grid(column=0, row=row_f, sticky='nw', padx=2, pady=2)
    y_lin_radio = tk.Radiobutton(scale_frame, text='linear', variable=y_axis_var, value='linear', tristatevalue="y")
    y_lin_radio.grid(column=1, row=row_f, sticky='nw', padx=2, pady=2)
    y_log_radio = tk.Radiobutton(scale_frame, text='log', variable=y_axis_var, value='log', tristatevalue="y")
    y_log_radio.grid(column=2, row=row_f, sticky='nw', padx=2, pady=2)
    row_f += 1

    y2_scale_label = tk.Label(scale_frame, text='Y2 axis:')
    y2_scale_label.grid(column=0, row=row_f, sticky='nw', padx=2, pady=2)
    y2_lin_radio = tk.Radiobutton(scale_frame, text='linear', variable=y2_axis_var, value='linear', tristatevalue="y2", state='disabled')
    y2_lin_radio.grid(column=1, row=row_f, sticky='nw', padx=2, pady=2)
    y2_log_radio = tk.Radiobutton(scale_frame, text='log', variable=y2_axis_var, value='log', tristatevalue="y2", state='disabled')
    y2_log_radio.grid(column=2, row=row_f, sticky='nw', padx=2, pady=2)
    row_f += 1

    # DATA input ------------------------------------------------------------------------------------------------
    data_inp_frame = tk.LabelFrame(plot_option_frame, text='Data input')
    data_inp_frame.grid(column=0, row=row_c, sticky='nswe', padx=2, pady=2)
    data_inp_frame.columnconfigure(0, weight=1)
    row_c += 1
    row_f = 0

    chk_norm = tk.Checkbutton(data_inp_frame, text='on/off en. normalization', var=data_var)
    chk_norm.grid(column=0, row=row_f, sticky='nw', padx=2, pady=2)
    row_f += 1

    chk_error = tk.Checkbutton(data_inp_frame, text='show/hide error bars', var=error_var)
    chk_error.grid(column=0, row=row_f, sticky='nw', padx=2, pady=2)
    row_f += 1

    chk_bin = tk.Checkbutton(data_inp_frame, text='show/hide first bin', var=bin_var)
    chk_bin.grid(column=0, row=row_f, sticky='nw', padx=2, pady=2)
    row_f += 1

    # plot_window(root, treeview_files, treeview_files.get_checked()
    ratio_menu = tk.OptionMenu(data_inp_frame, ratio_sel, *ratio_options)
    ratio_menu.grid(column=0, row=row_f, sticky='nwe', padx=2, pady=2)
    row_f += 1

    # LEGEND settings --------------------------------------------------------------------------------------------------
    legend_frame = tk.LabelFrame(plot_option_frame, text='Legend settings')
    legend_frame.grid(column=0, row=row_c, sticky='nswe', padx=2, pady=2)
    legend_frame.columnconfigure(0, weight=1)
    legend_frame.columnconfigure(1, weight=0)
    row_c += 1
    row_f = 0

    legend_menu = tk.OptionMenu(legend_frame, legend_pos, *legend_options)
    legend_menu.grid(column=0, columnspan=3, row=row_f, sticky='nwe', padx=2, pady=2)
    leg_spinbox = tk.ttk.Spinbox(legend_frame, from_=5, to=20, textvariable=leg_var, wrap=True, width=4)
    leg_spinbox.grid(column=3, row=row_f, sticky='nwe', padx=2, pady=2)
    row_f += 1

    h_sep3 = tk.ttk.Separator(legend_frame, orient='horizontal')
    h_sep3.grid(column=0, columnspan=4, row=row_f, sticky='nwe', padx=2, pady=2)
    row_f += 1

    button_legend = tk.ttk.Button(legend_frame, text='Legend editor', command=lambda: editor_mod.open_lib('config_legend', plot_win, tally_to_plot))
    button_legend.grid(column=0, columnspan=4, row=row_f, sticky='nswe', padx=2, pady=2)
    row_f += 1  

    # FONT size frame --------------------------------------------------------------------------------------------------
    font_size_frame = tk.LabelFrame(plot_option_frame, text='Axis font size')
    font_size_frame.grid(column=0, row=row_c, sticky='nswe', padx=2, pady=2)
    row_c += 1
    row_f = 0

    axis_title = tk.Label(font_size_frame, text='Label')
    axis_title.grid(column=0, row=row_f, sticky='nw', padx=2, pady=2)
    axis_spinbox = tk.ttk.Spinbox(font_size_frame, from_=5, to=20, textvariable=axis_var, wrap=True, width=4)
    axis_spinbox.grid(column=1, row=row_f, sticky='nw', padx=2, pady=2)
    axis_title = tk.Label(font_size_frame, text='Tics')
    axis_title.grid(column=2, row=row_f, sticky='nw', padx=2, pady=2)
    ticks_spinbox = tk.ttk.Spinbox(font_size_frame, from_=5, to=20, textvariable=ticks_var, wrap=True, width=4)
    ticks_spinbox.grid(column=3, row=row_f, sticky='nw', padx=2, pady=2)
    row_f += 1

    # GRID settings ----------------------------------------------------------------------------------------------------
    grid_frame = tk.LabelFrame(plot_option_frame, text='Grid settings')
    grid_frame.grid(column=0, row=row_c, sticky='nswe', padx=2, pady=2)
    grid_frame.columnconfigure(0, weight=1)
    grid_frame.columnconfigure(1, weight=1)
    row_c += 1
    row_f = 0

    grid_chk = tk.Checkbutton(grid_frame, text='show/hide grid', var=grid_on_var, command=lambda: change_state())
    grid_chk.grid(column=0, columnspan=2, row=row_f, sticky='nw', padx=2, pady=2)
    row_f += 1

    grid_menu = tk.OptionMenu(grid_frame, grid_var, *grid_options)
    grid_menu.grid(column=0, row=row_f, sticky='nsew', padx=2, pady=2)
    grid_axis_menu = tk.OptionMenu(grid_frame, grid_axis_var, *grid_axis_options)
    grid_axis_menu.grid(column=1, row=row_f, sticky='nsew', padx=2, pady=2)
    row_f += 1

    # SAVE figure frame ------------------------------------------------------------------------------------------------
    save_frame = tk.LabelFrame(plot_option_frame, text='Save')
    save_frame.grid(column=0, row=row_c, sticky='nswe', padx=2, pady=2)
    #save_frame.columnconfigure(0, weight=1)
    row_c += 1
    row_f = 0   

    button_save = tk.ttk.Button(save_frame, text='Save figure', command=lambda: (plot_variables(True), plot_core.plot_to_canvas(tally_to_plot)))
    button_save.grid(column=0, columnspan=4, row=row_f, sticky='nwse', padx=2, pady=2)
    row_f += 1

    x_size_label = tk.Label(save_frame, text='X (cm)')
    x_size_label.grid(column=0, row=row_f, sticky='nw', padx=2, pady=2)
    x_size_spinbox = tk.ttk.Spinbox(save_frame, from_=4, to=50, textvariable=x_fig_var , wrap=True, width=4)
    x_size_spinbox.grid(column=1, row=row_f, sticky='nw', padx=2, pady=2)
    y_size_label = tk.Label(save_frame, text='Y (cm)')
    y_size_label.grid(column=2, row=row_f, sticky='nw', padx=2, pady=2)
    y_size_spinbox = tk.ttk.Spinbox(save_frame, from_=4, to=50, textvariable=y_fig_var, wrap=True, width=4)
    y_size_spinbox.grid(column=3, row=row_f, sticky='nw', padx=2, pady=2)
    row_f += 1

    dpi_label = tk.Label(save_frame, text='DPI')
    dpi_label.grid(column=0, row=row_f, sticky='nw', padx=2, pady=2)
    dpi_spinbox = tk.ttk.Spinbox(save_frame, from_=50, to=1000, textvariable=dpi_var , wrap=True, width=4)
    dpi_spinbox.grid(column=1, row=row_f, sticky='nw', padx=2, pady=2)
    chk_latex = tk.Checkbutton(save_frame, text='On/Off LaTeX', var=latex_var, state='disabled')
    chk_latex.grid(column=2, columnspan=2, row=row_f, sticky='nw', padx=2, pady=2)
    row_f += 1

    # NEW COLUMN -------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
    
    # cross sections frame ---------------------------------------------------------------------------------------------
    row_c = 0
    
    xs_frame = tk.LabelFrame(plot_option_frame2, text='Cross Section')
    xs_frame.grid(column=0, row=row_c, sticky='nswe', padx=2, pady=2)
    xs_frame.columnconfigure(0, weight=1)
    row_c += 1
    row_f = 0

    button_xs = tk.ttk.Button(xs_frame, text='Read XS', command=lambda: [read_mod.read_xs(name_label), change_state2()])
    button_xs.grid(column=0, columnspan=4, row=row_f, sticky='nswe', padx=2, pady=2)
    row_f += 1

    file_label = tk.Label(xs_frame, text='File name:')
    file_label.grid(column=0, columnspan=4, row=row_f, sticky='wn')
    row_f += 1

    name_label = tk.Label(xs_frame, text=' ')
    name_label.grid(column=0, columnspan=4, row=2, sticky='wn')
    row_f += 1

    h_sep1 = tk.ttk.Separator(xs_frame, orient='horizontal')
    h_sep1.grid(column=0, columnspan=4, row=row_f, sticky='nswe', padx=2, pady=2)
    row_f += 1

    chk_xs = tk.Checkbutton(xs_frame, text='show/hide XS Y axis', var=xs_var, state="disabled", command=lambda: change_state3())
    chk_xs.grid(column=0, columnspan=4, row=row_f, sticky='nsw', padx=2, pady=2)
    row_f += 1

    # config (editor) --------------------------------------------------------------------------------------------
    config_frame = tk.LabelFrame(plot_option_frame2, text='Settings')
    config_frame.grid(column=0, row=row_c, sticky='nswe', padx=2, pady=2)
    config_frame.columnconfigure(0, weight=1)
    row_c += 1
    row_f = 0   

    button_settings = tk.ttk.Button(config_frame, text='Settings editor', command=lambda: editor_mod.open_lib('config_export', plot_win, tally_to_plot))
    button_settings.grid(column=0, columnspan=4, row=row_f, sticky='nswe', padx=2, pady=2)
    row_f += 1

    button_reload = tk.ttk.Button(config_frame, text='Reload config', command=lambda: settings_mod.read_config("config_export"))
    button_reload.grid(column=0, columnspan=4, row=row_f, sticky='nswe', padx=2, pady=2)
    row_f += 1

    h_sep_4 = tk.ttk.Separator(config_frame, orient='horizontal')
    h_sep_4.grid(column=0, columnspan=4, row=row_f, sticky='nswe', padx=2, pady=2)
    row_f += 1

    chk_title = tk.Checkbutton(config_frame, text="On/Off figure title", var=fig_title_var)
    chk_title.grid(column=0, columnspan=4, row=row_f, sticky='nw', padx=2, pady=2)
    row_f += 1

    # LIMITS frame --------------------------------------------------------------------------------------------
    limits_frame = tk.LabelFrame(plot_option_frame2, text='Axes limits')
    limits_frame.grid(column=0, row=row_c, sticky='nswe', padx=2, pady=2)
    limits_frame.columnconfigure(0, weight=1)
    row_c += 1
    row_f = 0   

    limits1_label = tk.Label(limits_frame, text='Usage:')
    limits1_label.grid(column=0, columnspan=4, row=row_f, sticky='nw', padx=2, pady=2)
    row_f += 1

    limits2_label = tk.Label(limits_frame, text='None = auto')
    limits2_label.grid(column=0, columnspan=4, row=row_f, sticky='nw', padx=2, pady=2)
    row_f += 1
    
    limits3_label = tk.Label(limits_frame, text='apply: active cursor + hit Enter')
    limits3_label.grid(column=0, columnspan=4, row=row_f, sticky='nw', padx=2, pady=2)
    row_f += 1

    h_sep_5 = tk.ttk.Separator(limits_frame, orient='horizontal')
    h_sep_5.grid(column=0, columnspan=4, row=row_f, sticky='nswe', padx=2, pady=2)
    row_f += 1

    x_min_label = tk.Label(limits_frame, text='X min')
    x_min_label.grid(column=0, row=row_f, sticky='nw', padx=2, pady=2)
    x_min_entry = tk.Entry(limits_frame, width=6, textvariable=x_min_var)
    x_min_entry.grid(column=1, row=row_f, sticky='nw', padx=2, pady=2)
    x_min_entry.bind('<Return>', lambda event: (plot_variables(), plot_core.plot_to_canvas(tally_to_plot)))
    x_max_label = tk.Label(limits_frame, text='X max')
    x_max_label.grid(column=2, row=row_f, sticky='nw', padx=2, pady=2)
    x_max_entry = tk.Entry(limits_frame, width=6, textvariable=x_max_var)
    x_max_entry.grid(column=3, row=row_f, sticky='nw', padx=2, pady=2)
    x_max_entry.bind('<Return>', lambda event: (plot_variables(), plot_core.plot_to_canvas(tally_to_plot)))
    row_f += 1

    # chk_xlim = tk.Checkbutton(limits_frame, text='On/Off X axis limits', var=xlim_var)
    # chk_xlim.grid(column=0, columnspan=4, row=row_f, sticky='nw', padx=2, pady=2)
    # row_f += 1

    y_min_label = tk.Label(limits_frame, text='Y min')
    y_min_label.grid(column=0, row=row_f, sticky='nw', padx=2, pady=2)
    y_min_entry = tk.Entry(limits_frame, width=6, textvariable=y_min_var)
    y_min_entry.grid(column=1, row=row_f, sticky='nw', padx=2, pady=2)
    y_min_entry.bind('<Return>', lambda event: (plot_variables(), plot_core.plot_to_canvas(tally_to_plot)))
    y_max_label = tk.Label(limits_frame, text='Y max')
    y_max_label.grid(column=2, row=row_f, sticky='nw', padx=2, pady=2)
    y_max_entry = tk.Entry(limits_frame, width=6, textvariable=y_max_var)
    y_max_entry.bind('<Return>', lambda event: (plot_variables(), plot_core.plot_to_canvas(tally_to_plot)))
    y_max_entry.grid(column=3, row=row_f, sticky='nw', padx=2, pady=2)
    row_f += 1

    xs_min_label = tk.Label(limits_frame, text='Y2 min')
    xs_min_label.grid(column=0, row=row_f, sticky='nw', padx=2, pady=2)
    xs_min_entry = tk.Entry(limits_frame, width=6, textvariable=y2_min_var, state='disabled')
    xs_min_entry.grid(column=1, row=row_f, sticky='nw', padx=2, pady=2)
    xs_min_entry.bind('<Return>', lambda event: (plot_variables(), plot_core.plot_to_canvas(tally_to_plot)))
    xs_max_label = tk.Label(limits_frame, text='Y2 max')
    xs_max_label.grid(column=2, row=row_f, sticky='nw', padx=2, pady=2)
    xs_max_entry = tk.Entry(limits_frame, width=6, textvariable=y2_max_var, state='disabled')
    xs_max_entry.grid(column=3, row=row_f, sticky='nw', padx=2, pady=2)
    xs_max_entry.bind('<Return>', lambda event: (plot_variables(), plot_core.plot_to_canvas(tally_to_plot)))
    row_f += 1

    # tally multiplier frame -----------------------------------------------------------------------------------
    multiplier_frame = tk.LabelFrame(plot_option_frame2, text='Tally multiplier')
    multiplier_frame.grid(column=0, row=row_c, sticky='nswe', padx=2, pady=2)
    multiplier_frame.columnconfigure(0, weight=1)
    row_c += 1
    row_f = 0

    # label with description and entry for multiplier value, default value is 1.0
    # this value is used to multiply the tally values before plotting
    multiplier_entry = tk.Entry(multiplier_frame, width=6, textvariable=multiplier_var, justify="right")
    multiplier_entry.grid(column=0, row=row_f, sticky='nwse', padx=2, pady=2)
    multiplier_entry.bind('<Return>', lambda event: (plot_variables(), plot_core.plot_to_canvas(tally_to_plot)))
    row_f += 1    

    # Line options frame -----------------------------------------------------------------------------------------------
    line_options_frame = tk.LabelFrame(plot_option_frame2, text='Line options')
    line_options_frame.grid(column=0, row=row_c, sticky='nswe', padx=2, pady=2)
    line_options_frame.columnconfigure(0, weight=1)
    row_c += 1
    row_f = 0

    # Checkbox for unique line style based on filename
    chk_line_style = tk.Checkbutton(line_options_frame, text='Unique linestyle by file', var=line_style_var, command=lambda: (plot_variables(), plot_core.plot_to_canvas(tally_to_plot)))
    chk_line_style.grid(column=0, columnspan=2, row=row_f, sticky='w', padx=2, pady=2)
    row_f += 1

    # Line width spinbox on same row as label
    line_width_label = tk.Label(line_options_frame, text='Line width:')
    line_width_label.grid(column=0, row=row_f, sticky='w', padx=2, pady=2)
    
    line_width_spinbox = tk.ttk.Spinbox(line_options_frame, from_=0.2, to=5.0, increment=0.2, textvariable=line_width_var, wrap=True, width=5)
    line_width_spinbox.grid(column=1, row=row_f, sticky='w', padx=2, pady=2)
    line_width_spinbox.bind('<Return>', lambda event: (plot_variables(), plot_core.plot_to_canvas(tally_to_plot)))
    row_f += 1

    # ------------------------------------------------------------------------------------------------------------------
    # replot frame -----------------------------------------------------------------------------------------------------
    replot_frame = tk.LabelFrame(option_frame, text='Replot')
    replot_frame.grid(column=0, columnspan=2, row=1, sticky='swe', padx=2, pady=2)
    replot_frame.columnconfigure(0, weight=1)
    replot_frame.columnconfigure(1, weight=1)

    chk_replot = tk.Checkbutton(replot_frame, text='disable instant changes', var=replot_var, command=lambda: turn_off_replot())
    chk_replot.grid(column=0, row=0, sticky='swe', padx=2, pady=2)

    button_replot = tk.ttk.Button(replot_frame, text='Replot', command=lambda: (plot_variables(), plot_core.plot_to_canvas(tally_to_plot)), state='disabled')
    button_replot.grid(column=0, row=1, sticky='swen', padx=2, pady=2)
    
    button_quit = tk.ttk.Button(replot_frame, width=24, text='Quit', command=lambda: quit_m())
    button_quit.grid(column=1, row=0, rowspan=2, sticky='swen', padx=2, pady=2)
    
    # endregion all tkinter widgets for

    # FUNCTIONS conected to MAIN function ------------------------------------------------------------------------------

    # call replot when Option Menu is changed
    def my_callback(*args):
        plot_variables()
        plot_core.plot_to_canvas(tally_to_plot)

    # first definition of Tkinter Variables tracing
    legend_pos.trace_add('write', my_callback)
    ratio_sel.trace_add('write', my_callback)
    x_axis_var.trace_add('write', my_callback)
    y_axis_var.trace_add('write', my_callback)
    y2_axis_var.trace_add('write', my_callback)
    data_var.trace_add('write', my_callback)
    axis_var.trace_add('write', my_callback)
    leg_var.trace_add('write', my_callback)
    grid_on_var.trace_add('write', my_callback)
    grid_var.trace_add('write', my_callback)
    grid_axis_var.trace_add('write', my_callback)
    ticks_var.trace_add('write', my_callback)
    xs_var.trace_add('write', my_callback)
    error_var.trace_add('write', my_callback)
    bin_var.trace_add('write', my_callback)
    # xlim_var.trace_add('write', my_callback)
    fig_title_var.trace_add('write', my_callback)
    line_style_var.trace_add('write', my_callback)
    line_width_var.trace_add('write', my_callback)

    # turn on-off online replot
    def turn_off_replot():
        if replot_var.get() is True:
            button_replot['state'] = 'normal'

            legend_pos.trace_remove('write', legend_pos.trace_info()[0][1])
            ratio_sel.trace_remove('write', ratio_sel.trace_info()[0][1])
            x_axis_var.trace_remove('write', x_axis_var.trace_info()[0][1])
            y_axis_var.trace_remove('write', y_axis_var.trace_info()[0][1])
            y2_axis_var.trace_remove('write', y2_axis_var.trace_info()[0][1])
            data_var.trace_remove('write', data_var.trace_info()[0][1])
            axis_var.trace_remove('write', axis_var.trace_info()[0][1])
            leg_var.trace_remove('write', leg_var.trace_info()[0][1])
            grid_on_var.trace_remove('write', grid_on_var.trace_info()[0][1])
            grid_var.trace_remove('write', grid_var.trace_info()[0][1])
            grid_axis_var.trace_remove('write', grid_axis_var.trace_info()[0][1])
            ticks_var.trace_remove('write', ticks_var.trace_info()[0][1])
            xs_var.trace_remove('write', xs_var.trace_info()[0][1])
            error_var.trace_remove('write', error_var.trace_info()[0][1])
            bin_var.trace_remove('write', bin_var.trace_info()[0][1])
            # xlim_var.trace_remove('write', xlim_var.trace_info()[0][1])
            fig_title_var.trace_remove('write', fig_title_var.trace_info()[0][1])
            line_style_var.trace_remove('write', line_style_var.trace_info()[0][1])
            line_width_var.trace_remove('write', line_width_var.trace_info()[0][1])
        else:
            button_replot['state'] = 'disabled'

            legend_pos.trace_add('write', my_callback)
            ratio_sel.trace_add('write', my_callback)
            x_axis_var.trace_add('write', my_callback)
            y_axis_var.trace_add('write', my_callback)
            y2_axis_var.trace_add('write', my_callback)
            data_var.trace_add('write', my_callback)
            axis_var.trace_add('write', my_callback)
            leg_var.trace_add('write', my_callback)
            grid_on_var.trace_add('write', my_callback)
            grid_var.trace_add('write', my_callback)
            grid_axis_var.trace_add('write', my_callback)
            ticks_var.trace_add('write', my_callback)
            xs_var.trace_add('write', my_callback)
            error_var.trace_add('write', my_callback)
            bin_var.trace_add('write, my_callback')
            # xlim_var.trace_add('write', my_callback)
            fig_title_var.trace_add('write', my_callback)
            line_style_var.trace_add('write', my_callback)
            line_width_var.trace_add('write', my_callback)


    # enable/disable grid settings
    def change_state():
        if grid_on_var.get():
            grid_menu['state'] = 'normal'
            grid_axis_menu['state'] = 'normal'
        else:
            grid_menu['state'] = 'disabled'
            grid_axis_menu['state'] = 'disabled'


    # enable/disable XS checkbox if XS data are available
    def change_state2():
        if len(config_mod.xs_data.keys()) > 0:
            chk_xs['state'] = 'normal'
        else:
            chk_xs['state'] = 'disabled'
    
    # enable/disable widgets connected to XS data based on
    def change_state3():
        if xs_var.get():
            # active y2 scale, y2 limits
            y2_lin_radio['state'] = 'normal'
            y2_log_radio['state'] = 'normal'
            xs_min_entry['state'] = 'normal'
            xs_max_entry['state'] = 'normal'
        else:
            y2_lin_radio['state'] = 'disabled'
            y2_log_radio['state'] = 'disabled'
            xs_min_entry['state'] = 'disabled'
            xs_max_entry['state'] = 'disabled'
   