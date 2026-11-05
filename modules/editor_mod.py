#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# TODO_list:


# libraries
from modules import config_mod
import pathlib
import tkinter as tk
from modules import settings_mod
from modules import plot_core, window_mod


# open library or any ascii file in text editor
def open_lib(file_path, plot_win, tally, on_save=None):
    
    file_path = pathlib.Path(file_path)
    
    previous_grab = window_mod.current_grab(plot_win)
    editor_win = tk.Toplevel(plot_win)
    editor_win.transient(plot_win)
    editor_win.grab_set()
    editor_win.minsize(500, 300)
    editor_win.title('Library editor')
    editor_win.rowconfigure(0, weight=1)
    editor_win.rowconfigure(0, weight=1)
    editor_win.columnconfigure(0, weight=1)

    txt_edit = tk.Text(editor_win, bg='white')
    txt_edit.grid(column=0, row=0, sticky='nswe', padx=(5, 0), pady=5)
    text_scrollbar = tk.ttk.Scrollbar(editor_win, orient='vertical', command=txt_edit.yview)
    text_scrollbar.grid(column=1, row=0, sticky='ns', padx=(0, 5), pady=5)
    txt_edit.configure(yscrollcommand=text_scrollbar.set)

    button_frame = tk.Frame(editor_win)
    button_frame.grid(column=0, columnspan=2, row=1, sticky='nswe', padx=5, pady=5)

    save_button = tk.Button(button_frame, text='Save file', command=lambda: save_lib() )
    save_button.grid(column=0, row=0, sticky='nswe', padx=5, pady=5)

    button_quit = tk.ttk.Button(button_frame, text='Quit', command=lambda: quit_m() )
    button_quit.grid(column=1, row=0, sticky='we', padx=5, pady=5)

    def quit_m():
        editor_win.grab_release()
        editor_win.destroy()
        if previous_grab is not None and previous_grab.winfo_exists():
            previous_grab.grab_set()

    editor_win.protocol('WM_DELETE_WINDOW', quit_m)

    def read_lib():
        with open(file_path, 'r', encoding='utf-8') as lib_file:
            text = lib_file.read()
            txt_edit.insert(tk.END, text)

        editor_win.title(f'Library editor - {file_path}')

    def save_lib():
        try:
            with open(file_path, 'w', encoding='utf-8') as output_file:
                text_s = txt_edit.get(1.0, tk.END)
                output_file.write(text_s)
            if on_save is not None:
                # The owning window is responsible for loading the file, updating
                # its controls, and redrawing from one consistent settings state.
                if on_save() is False:
                    return
            else:
                fname = pathlib.Path(file_path).name
                if fname == settings_mod.CONFIG_FILE and not settings_mod.read_config(file_path):
                    tk.messagebox.showerror(
                        title='Config reload failed',
                        message=settings_mod.last_config_error,
                        parent=editor_win,
                    )
                    return
                plot_core.plot_to_canvas(tally)
        except Exception as e:
            tk.messagebox.showerror(
                title='Error',
                message=f'Error in settings value: {e}',
                parent=editor_win,
            )
            return

        # close an editor window and grab the plot window
        quit_m()

    # open and read file into the editor window
    try:
        read_lib()
    except (OSError, UnicodeError) as exc:
        tk.messagebox.showerror('Read error', str(exc), parent=editor_win)
        quit_m()
    return editor_win
