# -*- coding: utf-8 -*-
# TODO_list:

# LIBRARIES
from modules import read_mod, plot_mod, settings_mod, export_mod, config_mod
# GUI libraries
import tkinter as tk
import ttkwidgets


#  FUNCTIONS  ##########################################################################################################
# GUI exit from program
def ask_quit():
    if tk.messagebox.askokcancel('Quit', 'Do you want to quit now?'):
        # settings_mod.save_config()
        root.quit()     # stops mainloop
        root.destroy()  # this is necessary on Windows to prevent Fatal Python Error: PyEval_RestoreThread: NULL tstate


# return selected tallies
def selected_tally():
    if len(treeview_files.get_checked()) != 0:
        # send selected tallies to plot_mod function
        selection = []
        for row in treeview_files.get_checked():
            key = treeview_files.item(row)['values'][0] + '_' + str(treeview_files.item(row)['values'][1])  # get file name and tally number
            selection.append(key)
    else:
        tk.messagebox.showerror('Input error', 'Please choose tally for plotting.')
        return None
    
    return selection


def select_all_click():
    global check_on_click
    if check_on_click:
        for item in treeview_files.get_children():
            treeview_files.change_state(item, state="checked")
        check_on_click = False
    else:
        for item in treeview_files.get_children():
            treeview_files.change_state(item, state="unchecked")
        check_on_click = True


# sort data in columns in treeview
def treeview_sort_column(tree, col, reverse):
    data = [(tree.set(child, col), child) for child in tree.get_children('')]
    data.sort(reverse=reverse)

    # rearrange items in sorted positions
    for index, (val, child) in enumerate(data):
        tree.move(child, '', index)

    # Re-apply alternating row colors after sorting while preserving checkbox state
    for index, (val, child) in enumerate(data):
        row_tag = "oddrow" if index % 2 == 0 else "evenrow"
        # Get current tags (checkbox state: "checked" or "unchecked")
        current_tags = tree.item(child, 'tags')
        # Preserve the checkbox state tag and add the color tag
        checkbox_state = [tag for tag in current_tags if tag in ("checked", "unchecked")]
        # Set tags with both checkbox state and color tag
        new_tags = tuple(checkbox_state) + (row_tag,)
        tree.item(child, tags=new_tags)

    # rearrange items in sorted positions
    tree.heading(col, command=lambda: treeview_sort_column(tree, col, not reverse))


#  MAIN CODE  ##########################################################################################################

# main window creation
root = tk.Tk()

# variable
check_var = tk.BooleanVar(value=False)  # unchecked unchecked
check_on_click = True

# Main window parameters
root.title('MCNP 2D tally plotter')
# root.minsize(500, 300)
# root.maxsize(1000, 600)
# root.geometry('800x350')
style = tk.ttk.Style()
# style.theme_use('vista')

# Configure treeview with row borders/gridlines
style.configure("Treeview", rowheight=25, background="#ffffff", fieldbackground="#ffffff", relief="solid", borderwidth=1)
style.configure("Treeview.Heading", background="#d0d0d0", foreground="black", borderwidth=1, relief="raised")

# Configure selection colors
style.map('Treeview', 
          background=[('selected', '#0078d7')], 
          foreground=[('selected', 'white')])

root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

root.protocol('WM_DELETE_WINDOW', ask_quit)  # program end
# ----------------------------------------------------------------------------------------------------------------------
# modules executed at startup
settings_mod.read_config("config.toml")   # read settings from config file

# Checkbox variable for using saved config
use_saved_config_var = tk.BooleanVar(value=False)

# Function to open plot window with config handling
def open_plot_window():
    """Open plot window, resetting settings to defaults if checkbox is unchecked."""
    if not use_saved_config_var.get():
        settings_mod.reset_plot_settings_to_defaults()
    plot_mod.plot_window(root, selected_tally())

# MENU (not used due to problems on Mac devices) -----------------------------------------------------------------------
# does NOT work at MAC devices...

# FRAMES ---------------------------------------------------------------------------------------------------------------
up_frame = tk.ttk.Frame(root)
up_frame.grid(column=0, row=0, sticky='nswe', padx=5, pady=5)     # set the margins between window and content
up_frame.columnconfigure(0, weight=1)
up_frame.rowconfigure(0, weight=1)


down_frame = tk.ttk.Frame(root)
down_frame.grid(column=0, row=1, sticky='nswe', padx=5, pady=5)
down_frame.columnconfigure(0, weight=0)
down_frame.rowconfigure(0, weight=0)


# widgets in UP frame in GUI -------------------------------------------------------------------------------------------

# TREEVIEW
treeview_files = ttkwidgets.CheckboxTreeview(up_frame)
treeview_files.grid(sticky='wens', column=0, columnspan=5, row=0, rowspan=5)

# somehow hide the first ghost column
treeview_files['show'] = 'headings', 'tree'

treeview_files['columns'] = ('File', 'Tally number', 'Tally type', 'Particle', 'Number of values', 'E_cut-off (MeV)', 'E_min (MeV)', 'E_max (MeV)', 'comment')

for col_name in ['File', 'Tally number', 'Tally type', 'Particle', 'Number of values', 'E_min (MeV)', 'E_max (MeV)', 'E_cut-off (MeV)', "comment"]:
    treeview_files.column(col_name, width=100, stretch=True)
    treeview_files.heading(col_name, text=col_name, command=lambda _col=col_name: treeview_sort_column(treeview_files, _col, False))

# allows chose all items in the treeview by clicking on the heading
treeview_files.heading('#0', text='(un)check all', anchor='w', command=lambda: select_all_click())

treeview_files.column('#0',anchor='w', width=75, stretch=False)
treeview_files.column('File', width=150, stretch=False)

# Treeview X-scrollbar
tree_x_scroll = tk.ttk.Scrollbar(up_frame, orient='horizontal', command=treeview_files.xview)
tree_x_scroll.grid(sticky='wens', column=0, row=5, columnspan=5, padx=5, pady=5)

# Treeview Y-scrollbar
tree_y_scroll = tk.ttk.Scrollbar(up_frame, orient='vertical', command=treeview_files.yview)
tree_y_scroll.grid(sticky='wens', column=5, row=0, rowspan=5, padx=5, pady=5)

treeview_files.configure(xscrollcommand=tree_x_scroll.set)
treeview_files.configure(yscrollcommand=tree_y_scroll.set)

# Enable grid lines to separate rows
# Note: gridlines parameter may not work on all ttk themes
try:
    treeview_files.configure(show='tree headings')
except:
    pass

# Configure tag colors for alternating rows with higher contrast
treeview_files.tag_configure("oddrow", background="#ffffff", foreground="#000000")
treeview_files.tag_configure("evenrow", background="#d9e8f5", foreground="#000000")

# widgets in DOWN frame in GUI -----------------------------------------------------------------------------------------
button_frame = tk.Frame(down_frame)
button_frame.grid(column=0, row=0, sticky='ws')

button_file = tk.ttk.Button(button_frame, text='Chose directory', command=lambda: read_mod.open_folder(treeview_files, workdir_label, button_update), width=20)
button_file.grid(column=0, row=0, sticky='ws')

button_update = tk.ttk.Button(button_frame, text='Update directory', state='disabled', command=lambda: read_mod.read_folder(treeview_files), width=20)
button_update.grid(column=1, row=0, sticky='ws')

button_plot = tk.ttk.Button(button_frame, text='Plot data', command=open_plot_window, width=20)
button_plot.grid(column=2, row=0, sticky='ws')

# Checkbox for using saved config
chk_use_config = tk.Checkbutton(button_frame, text='Use saved config', var=use_saved_config_var)
chk_use_config.grid(column=4, row=0, sticky='ws', padx=10)

button_export = tk.ttk.Button(button_frame, text='Export tally to xlsx', command=lambda: export_mod.save_to_xlsx(selected_tally()), width=20)
button_export.grid(column=3, row=0, sticky='ws')

# -----------------------------------
workdir_label = tk.Label(down_frame, text='Work directory: ')
workdir_label.grid(column=0, row=1, sticky='ws')

# ----------------------------------------------------------------------------------------------------------------------
# run UI
root.mainloop()