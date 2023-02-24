#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# TODO_list:
# 


# libraries
from modules import config_mod
import pathlib
import os

# GUI libraries
import tkinter as tk

# open library or any ascii file in text editor TODO grab_set() pri zavreni editoru zpet na plot window
def open_lib():
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
    save_button = tk.Button(button_frame, text='Save library', command=lambda: save_lib() )
    save_button.grid(column=0, row=0, sticky='nswe', padx=5, pady=5)
    saveas_button = tk.Button(button_frame, text='Save as library', command=lambda: save_as_lib())
    saveas_button.grid(column=1, row=0, sticky='nswe', padx=5, pady=5)

    file_path = pathlib.Path("config_export")

#    editor_win.protocol('WM_DELETE_WINDOW', editor_win.destroy())  # program end

    def read_lib():
        with open(file_path, 'r') as lib_file:
            text = lib_file.read()
            txt_edit.insert(tk.END, text)

        editor_win.title(f'Library editor - {file_path}')

    read_lib()      # run open lib function

    def save_lib():
        with open(file_path, 'w') as output_file:
            text_s = txt_edit.get(1.0, tk.END)
            output_file.write(text_s)


    def save_as_lib():
        file_path_new = tk.filedialog.asksaveasfilename(
            initialdir=os.getcwd(),
            defaultextension="txt",
            filetypes=[("Library Files", "*.lib"), ("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if not file_path_new:
            return

        with open(file_path_new, 'w') as output_file:
            text_s = txt_edit.get(1.0, tk.END)
            output_file.write(text_s)
