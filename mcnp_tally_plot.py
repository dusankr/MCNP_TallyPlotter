# -*- coding: utf-8 -*-
# TODO_list:

# Libraries
import os
import tkinter
from tkinter import ttk
from tkinter import messagebox
from tkinter import simpledialog
# from tkinter import filedialog
# from pathlib import Path
# import sys

#  FUNCTIONS  ##########################################################################################################


# GUI exit from program
def ask_quit():
    if messagebox.askokcancel('Quit', 'Do you want to quit now?'):
        root.destroy()


#  MAIN CODE  ##########################################################################################################
# TODO vlozit dve okna, do kazdeho framu jedno, přidat posuvniky
# TODO hlavicka tabulky v prvnim okne
# TODO pridat horni listu (hlavne File...)


# Global variables
folder_path = None


root = tkinter.Tk()

# Frames
up_frame = ttk.Frame(root)
down_frame = ttk.Frame(root)

# Main window parameters
root.title('MCNP tally plotting')
# root.minsize(500, 300)
# root.maxsize(1000, 600)
# root.geometry('800x350')
style = ttk.Style()
style.theme_use('vista')


# UP frame in GUI
label_layer_types = ttk.Label(up_frame, text='Nejaky text')


# DOWN frame in GUI
button_solve = ttk.Button(down_frame, text='PLOT', command=lambda: quit(), width=20)

# GRIDs
up_frame.grid(column=0, row=0, sticky='nswe', padx=5, pady=5)     # set the margins between window and content
down_frame.grid(column=0, row=1, sticky='nswe', padx=5, pady=5)

# UP frame widgets grid
label_layer_types.grid(sticky='W', column=0, row=0)
label_layer_types.config(width=20)

# DOWN frame widgets grid
button_solve.grid(sticky='W', column=1, row=0)

root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

up_frame.columnconfigure(0, weight=1)
up_frame.rowconfigure(0, weight=0)

down_frame.columnconfigure(0, weight=1)
down_frame.rowconfigure(1, weight=0)


# program end
root.protocol('WM_DELETE_WINDOW', ask_quit)

# run UI
root.mainloop()