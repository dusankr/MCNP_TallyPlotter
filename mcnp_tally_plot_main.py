# -*- coding: utf-8 -*-
# TODO_list:

# LIBRARIES
from modules import read_mod, plot_mod
# GUI libraries
import tkinter as tk
import ttkwidgets


#  FUNCTIONS  ##########################################################################################################
# GUI exit from program
def ask_quit():
    if tk.messagebox.askokcancel('Quit', 'Do you want to quit now?'):
        root.destroy()


def open_plot_win():
    if len(treeview_files.get_checked()) != 0:

        # send selected tallies to plot_mod function
        selection = []
        for row in treeview_files.get_checked():
            selection.append(treeview_files.item(row)['values'][0])

        plot_mod.plot_window(root, selection)
    else:
        tk.messagebox.showerror('Input error', 'Please choose tally for plotting.')


#  MAIN CODE  ##########################################################################################################

# main window creation
root = tk.Tk()

# Main window parameters
root.title('MCNP tally plotting')
root.minsize(500, 300)
# root.maxsize(1000, 600)
# root.geometry('800x350')
style = tk.ttk.Style()
# style.theme_use('vista')

root.protocol('WM_DELETE_WINDOW', ask_quit)  # program end

# ----------------------------------------------------------------------------------------------------------------------
'''
# widget MENU

# widget definition
menu_bar = tk.Menu(root)
root.config(menu=menu_bar)

# File in MENU definition
file_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label='File', menu=file_menu)
file_menu.add_command(label='Work directory', underline=0, command=lambda: read_mod.open_folder(treeview_files))
'''

# FRAMES ---------------------------------------------------------------------------------------------------------------
up_frame = tk.ttk.Frame(root)
up_frame.grid(column=0, row=0, sticky='nswe', padx=5, pady=5)     # set the margins between window and content

down_frame = tk.ttk.Frame(root)
down_frame.grid(column=0, row=1, sticky='nswe', padx=5, pady=5)

# widgets in UP frame in GUI -------------------------------------------------------------------------------------------
treeview_files = ttkwidgets.CheckboxTreeview(up_frame)
treeview_files.grid(sticky='wens', column=0, columnspan=5, row=0, rowspan=5)

# somehow hide first ghost column
treeview_files['show'] = 'headings', 'tree'

treeview_files['columns'] = ('File', 'Tally number', 'Tally type', 'Particle', 'Number of values', 'E_cut-off (MeV)', 'E_min (MeV)', 'E_max (MeV)', 'comment')


for col_name in ['File', 'Tally number', 'Tally type', 'Particle', 'Number of values', 'E_min (MeV)', 'E_max (MeV)',
                 'E_cut-off (MeV)', "comment"]:
    treeview_files.column(col_name, width=100, stretch=True)
    treeview_files.heading(col_name, text=col_name)

treeview_files.column('#0',anchor='w', width=40, stretch=False)
treeview_files.column('File', width=150, stretch=False)

# TREEVIEW
# Treeview X-scrollbar
tree_x_scroll = tk.ttk.Scrollbar(up_frame, orient='horizontal', command=treeview_files.xview)
tree_x_scroll.grid(sticky='wens', column=0, row=5, columnspan=5, padx=5, pady=5)

# Treeview Y-scrollbar
tree_y_scroll = tk.ttk.Scrollbar(up_frame, orient='vertical', command=treeview_files.yview)
tree_y_scroll.grid(sticky='wens', column=5, row=0, rowspan=5, padx=5, pady=5)

treeview_files.configure(xscrollcommand=tree_x_scroll.set)
treeview_files.configure(yscrollcommand=tree_y_scroll.set)


# widgets in DOWN frame in GUI -----------------------------------------------------------------------------------------
button_file = tk.ttk.Button(down_frame, text='Work directory', command=lambda: read_mod.open_folder(treeview_files), width=20)
button_file.grid(column=0, row=0, sticky='ws')

button_solve = tk.ttk.Button(down_frame, text='Plot data', command=lambda: open_plot_win(), width=20)
button_solve.grid(column=1, row=0, sticky='ws')

button_export = tk.ttk.Button(down_frame, text='Export tally to CSV', width=20)     # TODO write function for tally export to CSV/Excel/etc.
button_export.grid(column=2, row=0, sticky='ws')

# ----------------------------------------------------------------------------------------------------------------------
# LAYOUTs

# layout UP frame
up_frame.columnconfigure(0, weight=1)
up_frame.rowconfigure(0, weight=1)

# layout DOWN frame
down_frame.columnconfigure(0, weight=0)
down_frame.rowconfigure(0, weight=0)

# layout all of the main containers
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

# ----------------------------------------------------------------------------------------------------------------------
# run UI
root.mainloop()