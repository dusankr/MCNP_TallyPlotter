# -*- coding: utf-8 -*-
# TODO_list:
# comments
# comments

# LIBRARIES
from modules import read_mod, plot_mod, config_mod
# GUI libraries
import tkinter as tk
import ttkwidgets

import openpyxl
import pathlib


#  FUNCTIONS  ##########################################################################################################
# GUI exit from program
def ask_quit():
    if tk.messagebox.askokcancel('Quit', 'Do you want to quit now?'):
        root.destroy()


# return selected tallies
def selected_tally():
    if len(treeview_files.get_checked()) != 0:

        # send selected tallies to plot_mod function
        selection = []
        for row in treeview_files.get_checked():
            selection.append(treeview_files.item(row)['values'][0])
    else:
        tk.messagebox.showerror('Input error', 'Please choose tally for plotting.')

    return selection


# save selected tallies
def save_to_xlsx():
    # create new directory if doesn't exist
    result_path = config_mod.folder_path / 'export'
    result_path.mkdir(parents=True, exist_ok=True)

    # ask xlsx file name
    filename = tk.simpledialog.askstring(title='Export to XLSX', prompt='Choose a name for export without extension:')

    wb = openpyxl.Workbook()
    del wb['Sheet']

    # create new sheets
    for tally in selected_tally():
        wb.create_sheet(tally)
        wb[tally].append(['Tally number', config_mod.tallies[tally][0]])
        wb[tally].append(['Tally type', config_mod.tallies[tally][1]])
        wb[tally].append(['Tally particle', config_mod.tallies[tally][2]])
        wb[tally].append(['Comment', config_mod.tallies[tally][8]])
        wb[tally].append(['energy', 'flux', 'flux normalized per 1 MeV','error'])
        for i in range(0, len(config_mod.tallies[tally][3])):
            wb[tally].append((config_mod.tallies[tally][3][i], config_mod.tallies[tally][4][i], config_mod.tallies[tally][7][i], config_mod.tallies[tally][5][i]))

    wb.save(filename= str(result_path / pathlib.Path(filename)) + '.xlsx')
    tk.messagebox.showinfo(title='Export to XLSX', message='Tally export has been completed.')

#  MAIN CODE  ##########################################################################################################

# main window creation
root = tk.Tk()

# Main window parameters
root.title('MCNP tally plotting')
# root.minsize(500, 300)
# root.maxsize(1000, 600)
# root.geometry('800x350')
style = tk.ttk.Style()
# style.theme_use('vista')

root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

root.protocol('WM_DELETE_WINDOW', ask_quit)  # program end TODO cause kernel crash at Mac

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

# somehow hide first ghost column
treeview_files['show'] = 'headings', 'tree'

treeview_files['columns'] = ('File', 'Tally number', 'Tally type', 'Particle', 'Number of values', 'E_cut-off (MeV)', 'E_min (MeV)', 'E_max (MeV)', 'comment')


for col_name in ['File', 'Tally number', 'Tally type', 'Particle', 'Number of values', 'E_min (MeV)', 'E_max (MeV)',
                 'E_cut-off (MeV)', "comment"]:
    treeview_files.column(col_name, width=100, stretch=True)
    treeview_files.heading(col_name, text=col_name)

treeview_files.column('#0',anchor='w', width=40, stretch=False)
treeview_files.column('File', width=150, stretch=False)

# Treeview X-scrollbar
tree_x_scroll = tk.ttk.Scrollbar(up_frame, orient='horizontal', command=treeview_files.xview)
tree_x_scroll.grid(sticky='wens', column=0, row=5, columnspan=5, padx=5, pady=5)

# Treeview Y-scrollbar
tree_y_scroll = tk.ttk.Scrollbar(up_frame, orient='vertical', command=treeview_files.yview)
tree_y_scroll.grid(sticky='wens', column=5, row=0, rowspan=5, padx=5, pady=5)

treeview_files.configure(xscrollcommand=tree_x_scroll.set)
treeview_files.configure(yscrollcommand=tree_y_scroll.set)

# widgets in DOWN frame in GUI -----------------------------------------------------------------------------------------
button_frame = tk.Frame(down_frame)
button_frame.grid(column=0, row=0, sticky='ws')

button_file = tk.ttk.Button(button_frame, text='Chose directory', command=lambda: read_mod.open_folder(treeview_files, workdir_label, button_update), width=20)
button_file.grid(column=0, row=0, sticky='ws')

button_update = tk.ttk.Button(button_frame, text='Update directory', state='disabled', command=lambda: read_mod.read_folder(treeview_files), width=20)
button_update.grid(column=1, row=0, sticky='ws')

button_solve = tk.ttk.Button(button_frame, text='Plot data', command=lambda: plot_mod.plot_window(root, selected_tally()), width=20)
button_solve.grid(column=2, row=0, sticky='ws')

button_export = tk.ttk.Button(button_frame, text='Export tally to xlsx', command=lambda: save_to_xlsx(), width=20)
button_export.grid(column=3, row=0, sticky='ws')

# -----------------------------------
workdir_label = tk.Label(down_frame, text='Work directory: ')
workdir_label.grid(column=0, row=1, sticky='ws')

# ----------------------------------------------------------------------------------------------------------------------
# run UI
root.mainloop()