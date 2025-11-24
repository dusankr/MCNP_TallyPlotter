#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# TODO_list:


# libraries
from modules import config_mod
import pathlib
import tkinter as tk
from modules import settings_mod
from modules import plot_core


# open library or any ascii file in text editor
def open_lib(file_path, plot_win, tally):
    
    file_path = pathlib.Path(file_path)
    
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

    save_button = tk.Button(button_frame, text='Save file', command=lambda: save_lib() )
    save_button.grid(column=0, row=0, sticky='nswe', padx=5, pady=5)

    button_quit = tk.ttk.Button(button_frame, text='Quit', command=lambda: quit_m() )
    button_quit.grid(column=1, row=0, sticky='we', padx=5, pady=5)

    def quit_m():
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
        fname = pathlib.Path(file_path).name
        if fname == "config.toml":
            settings_mod.read_config("config.toml")
        elif fname == "legend.toml":
            settings_mod.readsave_legend("legend.toml")

        try:
            plot_core.plot_to_canvas(tally)
        except Exception as e:
            tk.messagebox.showerror(title='Error', message=f'Error in settings value: {e}' + '\n' + 'Please close editor and update plot manualy.')

        # close an editor window and grab the plot window
        quit_m()

    # open and read file into the editor window
    read_lib()
