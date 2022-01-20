# -*- coding: utf-8 -*-
# TODO_list:
# TODO vložení canvas pro grafy
# TODO vložení tlačítek pro upravy grafu

# libraries
import matplotlib.pyplot as plt     # ploting in matlab style
from modules import config_mod

# GUI libraries
import tkinter


#  Functions  ##########################################################################################################
# create new Top level window
def plot_window(root):
    new_win = tkinter.Toplevel(root)
    new_win.title('Plotting window')
    new_win.minsize(100, 150)

    plot_frame = tkinter.ttk.Frame(new_win)
    plot_option_frame = tkinter.ttk.Frame(new_win)

    # GRIDs
    # frames in main GRID
    plot_frame.grid(column=0, row=0, sticky='nswe', padx=5, pady=5)  # set the margins between window and content
    plot_option_frame.grid(column=1, row=0, sticky='nswe', padx=5, pady=5)

    # LAYOUTs
    # layout UP frame
    plot_frame.columnconfigure(0, weight=1)
    plot_frame.rowconfigure(0, weight=1)

    # layout DOWN frame
    plot_option_frame.columnconfigure(0, weight=1)
    plot_option_frame.rowconfigure(0, weight=1)

    # layout all of the main containers
    new_win.columnconfigure(0, weight=1)
    new_win.rowconfigure(0, weight=1)
