#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# TODO_list:


# libraries
from modules import config_mod
import pathlib
import tkinter as tk
from modules import settings_mod

# open library or any ascii file in text editor
def open_lib(file_path, tally_to_plot, plot_win):
    editor_win = tk.Toplevel()
    editor_win.grab_set()
    editor_win.minsize(500, 300)
    editor_win.title('Library editor')
    editor_win.rowconfigure(0, weight=1)
    editor_win.rowconfigure(0, weight=1)
    editor_win.columnconfigure(0, weight=1)

    txt_edit = tk.Text(editor_win, bg='white')
    txt_edit.grid(column=0, row=0, sticky='nswe', padx=5, pady=5)

    button_frame = tk.Frame(editor_win)
    button_frame.grid(column=0, row=1, sticky='nswe', padx=5, pady=5)

    # read_button = tk.Button(button_frame, text='Open file', command=lambda: read_lib())
    # read_button.grid(column=0, row=0, sticky='nswe', padx=5, pady=5)

    save_button = tk.Button(button_frame, text='Save file', command=lambda: save_lib() )
    save_button.grid(column=0, row=0, sticky='nswe', padx=5, pady=5)

    #saveas_button = tk.Button(button_frame, text='Save as library', command=lambda: save_as_lib())
    #saveas_button.grid(column=1, row=0, sticky='nswe', padx=5, pady=5)
    button_quit = tk.ttk.Button(button_frame, text='Quit', command=lambda: quit() )
    button_quit.grid(column=1, row=0, sticky='we', padx=5, pady=5)

    def quit():
        # close the editor window and grab the plot window
        plot_win.grab_set()
        editor_win.destroy()

    def read_lib():
        with open(file_path, 'r') as lib_file:
            text = lib_file.read()
            txt_edit.insert(tk.END, text)

        editor_win.title(f'Library editor - {file_path}')

    def save_lib():
        with open(file_path, 'w') as output_file:
            text_s = txt_edit.get(1.0, tk.END)
            output_file.write(text_s)
        
        # tk.messagebox.showinfo(title='Config file', message='Config file was modified and saved.')

        # read again config file
        if pathlib.Path(file_path).name == "config_export":
            settings_mod.read_config("config_export")
        elif pathlib.Path(file_path).name == "config_legend":
            settings_mod.readsave_legend("config_legend")

        # close an editor window and grab plot window
        quit()

    # open and read file into the editor window
    read_lib()
