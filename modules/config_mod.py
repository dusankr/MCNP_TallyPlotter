# project global variables shared across all modules

# TODO transfer plot settings in JSON format and RCparams

# main variable for tally values and parameters
tallies = {}
xs_data = {}

# matplotlib variables
canvas_id = None
fig_id = None
ax = None
ax2 = None

# TODO write description
output_files = []
non_output = []

# initial and export settings
plot_settings = dict.fromkeys([
    "work_dir_path",
    "export_dir_path",
    "xs_dir_path",
    "fig_x_dimension",
    "fig_y_dimension",
    "fig_format",
    "fig_dpi",
    "x_title",
    "y_title",
    "ratio",
    "data_var",
    "leg_pos",
    "leg_size",
    "grid_switch",
    "grid_opt",
    "grid_ax",
    "ax_label_size",
    "tics_size",
    "xs_switch",
    "y2_title",
    "save_fig",
    "error_bar",
    "latex",
    "x_lim",
    "x_min",
    "x_max",
    "y_lim",
    "y_min",
    "y_max",
    "y2_lim",
    "y2_min",
    "y2_max",
    "fig_title",
    "fig_title_switch",
    "fig_title_size",
    "first_bin"
])

# second option how to create dict:
#plot_settings = {"work_dir_path":None, "fig_x_dimension":None, "fig_y_dimension":None, "fig_format":None, "fig_dpi":None}

# path to work directory
folder_path = None
