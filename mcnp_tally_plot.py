# -*- coding: utf-8 -*-
# TODO_list:

# Libraries
import os, sys

from modules import config_mod, mcnp_read

import tkinter as tk
from ttkwidgets import CheckboxTreeview

from pathlib import Path


#  FUNCTIONS  ##########################################################################################################
def open_folder():
    folder_path = Path(tk.filedialog.askdirectory(title='Choose directory with input files', initialdir=Path.cwd()))

    output_files = []
    for file in os.listdir(folder_path):
        output_files.append(Path(file))

    for fname in output_files:
        mcnp_read.read_file(folder_path, fname)

    treeview_fill()


# TODO zmenit treeview na CheckboxTreeview
# TODO vypnout rozsireni okna po nacteni hodnot do treeview
# TODO u treeView chybí posuvniky
# fill treeview in window
def treeview_fill():
    treeview_files['columns'] = ['File', 'Tally number', 'Tally type', 'Particle', 'Number of values', 'E_min (MeV)', 'E_max (MeV)', 'E_cut-off (MeV)']

    for col_name in ['File', 'Tally number', 'Tally type', 'Particle', 'Number of values', 'E_min (MeV)', 'E_max (MeV)', 'E_cut-off (MeV)']:
        treeview_files.column(col_name, width=100, stretch=False)
        treeview_files.heading(col_name, text=col_name)

    x = treeview_files.get_children()       # get id of all items in treeview
    for i in x:                             # delete all items
        treeview_files.delete(i)

    for i in config_mod.tallies.keys():      # fill treeview with new values
        treeview_files.insert('', index='end', values=[i, config_mod.tallies[i][0], config_mod.tallies[i][1], config_mod.tallies[i][2], len(config_mod.tallies[i][3]), config_mod.tallies[i][3][0], config_mod.tallies[i][3][-1], config_mod.tallies[i][6]])


# GUI exit from program
def ask_quit():
    if tk.messagebox.askokcancel('Quit', 'Do you want to quit now?'):
        root.destroy()


#  MAIN CODE  ##########################################################################################################
# TODO vlozit okno pro log
# TODO vytvořit novy branch a v nem novou tridu pro praci s tallies
#
# ----------------------------------------------------------------------------------------------------------------------
# main window creation
root = tk.Tk()

# Frames
up_frame = tk.ttk.Frame(root)
down_frame = tk.ttk.Frame(root)

# Main window parameters
root.title('MCNP tally plotting')
root.minsize(500, 300)
# root.maxsize(1000, 600)
# root.geometry('800x350')
style = tk.ttk.Style()
style.theme_use('vista')
root.protocol('WM_DELETE_WINDOW', ask_quit)  # program end

# ----------------------------------------------------------------------------------------------------------------------
# treeview
treeview_files = tk.ttk.Treeview(up_frame)
treeview_files['show'] = 'headings'

# Treeview X-scrollbar
tree_x_scroll = tk.ttk.Scrollbar(root, orient='horizontal')
tree_x_scroll.configure(command=treeview_files.xview)
treeview_files.configure(xscrollcommand=tree_x_scroll.set)
# Treeview Y-scrollbar
tree_y_scroll = tk.ttk.Scrollbar(root, orient='vertical', command=treeview_files.yview)
treeview_files.configure(yscrollcommand=tree_y_scroll.set)

# ----------------------------------------------------------------------------------------------------------------------
# widget MENU
# widget definition
menu_bar = tk.Menu(root)
root.config(menu=menu_bar)

# File in MENU definition
file_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label='File', menu=file_menu)
file_menu.add_command(label='Open work directory', underline=0, command=lambda: open_folder())

# ----------------------------------------------------------------------------------------------------------------------
# widgets in FRAMEs
# widgets in UP frame in GUI
label_layer_types = tk.ttk.Label(up_frame, text='Nejaky text')

# widgets DOWN frame in GUI
button_solve = tk.ttk.Button(down_frame, text='Close', command=ask_quit, width=20)

# ----------------------------------------------------------------------------------------------------------------------
# GRIDs
# frames in main GRID
up_frame.grid(column=0, row=0, sticky='nswe', padx=5, pady=5)     # set the margins between window and content
down_frame.grid(column=0, row=1, sticky='nswe', padx=5, pady=5)

# UP frame widgets grid
treeview_files.grid(sticky='wens', column=0, columnspan=5, row=0, rowspan=5)


# DOWN frame widgets grid
button_solve.grid(sticky='W', column=0, row=0)

# ----------------------------------------------------------------------------------------------------------------------
# LAYOUTs
# layout UP frame
up_frame.columnconfigure(0, weight=1)
up_frame.rowconfigure(0, weight=1)

# layout DOWN frame
down_frame.columnconfigure(0, weight=1)
down_frame.rowconfigure(0, weight=1)

# layout all of the main containers
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

# ----------------------------------------------------------------------------------------------------------------------
# run UI
root.mainloop()