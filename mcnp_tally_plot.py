# -*- coding: utf-8 -*-
# TODO_list:
# TODO nahradit treeview za checkboxtreeview
# TODO vypnout rozsireni okna po nacteni hodnot do treeview
# TODO vlozit okno pro log
# TODO vytvořit novy branch a v nem novou tridu pro praci s tallies

# LIBRARIES
# import from our files
from modules import mcnp_read, plot_mod

# GUI libraries
import tkinter as tk
from ttkwidgets import CheckboxTreeview


#  FUNCTIONS  ##########################################################################################################
# GUI exit from program
def ask_quit():
    if tk.messagebox.askokcancel('Quit', 'Do you want to quit now?'):
        root.destroy()


#  MAIN CODE  ##########################################################################################################

# main window creation
root = tk.Tk()

# Main window parameters
root.title('MCNP tally plotting')
root.minsize(500, 300)
# root.maxsize(1000, 600)
# root.geometry('800x350')
style = tk.ttk.Style()
style.theme_use('vista')

root.protocol('WM_DELETE_WINDOW', ask_quit)  # program end

# Frames
up_frame = tk.ttk.Frame(root)
down_frame = tk.ttk.Frame(root)

# ----------------------------------------------------------------------------------------------------------------------
# widget MENU

# widget definition
menu_bar = tk.Menu(root)
root.config(menu=menu_bar)

# File in MENU definition
file_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label='File', menu=file_menu)
file_menu.add_command(label='Work directory', underline=0, command=lambda: mcnp_read.open_folder(treeview_files))

# ----------------------------------------------------------------------------------------------------------------------
# widgets in FRAMEs

# widgets in UP frame in GUI
treeview_files = tk.ttk.Treeview(up_frame)
treeview_files['show'] = 'headings'

# Treeview X-scrollbar
tree_x_scroll = tk.ttk.Scrollbar(up_frame, orient='horizontal')
tree_x_scroll.configure(command=treeview_files.xview)
treeview_files.configure(xscrollcommand=tree_x_scroll.set)
# Treeview Y-scrollbar
tree_y_scroll = tk.ttk.Scrollbar(up_frame, orient='vertical', command=treeview_files.yview)
treeview_files.configure(yscrollcommand=tree_y_scroll.set)


# widgets in DOWN frame in GUI
button_solve = tk.ttk.Button(down_frame, text='Plot data', command=lambda: plot_mod.plot_window(root), width=20)

# ----------------------------------------------------------------------------------------------------------------------
# GRIDs

# frames in main GRID
up_frame.grid(column=0, row=0, sticky='nswe', padx=5, pady=5)     # set the margins between window and content
down_frame.grid(column=0, row=1, sticky='nswe', padx=5, pady=5)

# UP frame widgets grid
treeview_files.grid(sticky='wens', column=0, columnspan=5, row=0, rowspan=5)
tree_x_scroll.grid(sticky='wens', column=0, row=5, columnspan=5, padx=5, pady=5)
tree_y_scroll.grid(sticky='wens', column=5, row=0, rowspan=5, padx=5, pady=5)

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