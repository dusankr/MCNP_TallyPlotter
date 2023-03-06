# project global variables shared across all modules

# main variable for tally values and parameters
tallies = {}

# matplotlib variables
canvas_id = None
fig_id = None
ax = None

# TODO write description
output_files = []
non_output = []

# initial and export settings
plot_settings = dict.fromkeys([
    "work_dir_path",
    "export_dir_path",
    "fig_x_dimension",
    "fig_y_dimension",
    "fig_format",
    "fig_dpi",
    "x_title",
    "y_title"
])

# second option how to create dict:
#plot_settings = {"work_dir_path":None, "fig_x_dimension":None, "fig_y_dimension":None, "fig_format":None, "fig_dpi":None}

# path to work directory
folder_path = None
