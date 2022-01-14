# -*- coding: utf-8 -*-
# TODO_list:

# Libraries
import os, sys

from modules import config_mod, mcnp_read

import tkinter
from tkinter import ttk, messagebox, simpledialog, filedialog, Menu
from ttkwidgets import CheckboxTreeview

from pathlib import Path


#  FUNCTIONS  ##########################################################################################################
def open_folder():
    folder_path = Path(filedialog.askdirectory(title='Choose directory with input files', initialdir=Path.cwd()))

    output_files = []
    for file in os.listdir(folder_path):
        output_files.append(Path(file))

    for fname in output_files:
        mcnp_read.read_file(folder_path, fname)

    print(config_mod.tallies.keys())


# GUI exit from program
def ask_quit():
    if messagebox.askokcancel('Quit', 'Do you want to quit now?'):
        root.destroy()


#  MAIN CODE  ##########################################################################################################
# TODO vlozit okno pro log
# TODO hlavicka tabulky v prvnim okne


# ----------------------------------------------------------------------------------------------------------------------
# main window creation
root = tkinter.Tk()

# Frames
up_frame = ttk.Frame(root)
down_frame = ttk.Frame(root)

# Main window parameters
root.title('MCNP tally plotting')
root.minsize(500, 300)
# root.maxsize(1000, 600)
# root.geometry('800x350')
style = ttk.Style()
style.theme_use('vista')
root.protocol('WM_DELETE_WINDOW', ask_quit)  # program end

# ----------------------------------------------------------------------------------------------------------------------
# treeview
treeview_files = ttk.Treeview(up_frame)
treeview_files['show'] = 'headings'

# Treeview X-scrollbar
tree_x_scroll = ttk.Scrollbar(root, orient='horizontal')
tree_x_scroll.configure(command=treeview_files.xview)
treeview_files.configure(xscrollcommand=tree_x_scroll.set)
# Treeview Y-scrollbar
tree_y_scroll = ttk.Scrollbar(root, orient='vertical', command=treeview_files.yview)
treeview_files.configure(yscrollcommand=tree_y_scroll.set)

# ----------------------------------------------------------------------------------------------------------------------
# widget MENU
# widget definition
menu_bar = Menu(root)
root.config(menu=menu_bar)

# File in MENU definition
file_menu = Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label='File', menu=file_menu)
file_menu.add_command(label='Open work directory', underline=0, command=lambda: open_folder())

# ----------------------------------------------------------------------------------------------------------------------
# widgets in FRAMEs
# widgets in UP frame in GUI
label_layer_types = ttk.Label(up_frame, text='Nejaky text')

# widgets DOWN frame in GUI
button_solve = ttk.Button(down_frame, text='Close', command=ask_quit, width=20)

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