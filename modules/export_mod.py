#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# TODO_list:

# libraries
from modules import config_mod
import tkinter as tk
import pathlib
import pandas as pd


# save selected tallies
def save_to_xlsx(sel_tally):
    # return to the main window if no tally is selected
    if sel_tally == None:
        return

    export_path = pathlib.Path(tk.filedialog.asksaveasfilename(title='Choose directory and file name without an extension:', initialdir=config_mod.plot_settings["export_dir_path"], defaultextension=".xlsx", filetypes=[("export", "*.xlsx"), ("all files", "*.*")]))
    config_mod.plot_settings["export_dir_path"] = export_path.parent

    if str(export_path) == '.':
        tk.messagebox.showerror('Input error', 'No directory and file were selected.')
        return

    # create a new directory if it doesn't exist
    # result_path = config_mod.plot_settings["work_dir_path"] / 'export'
    # result_path.mkdir(parents=True, exist_ok=True)

    # create an empty Dataframe for final export to Excel
    merged_df = pd.DataFrame()
    # create new sheets
    for tally in sel_tally:
        fname = tally.rsplit('_', 1)[0]  # get file name from tally name

        df_info = pd.DataFrame({
            'information': ['Filename', fname, 'Tally number', config_mod.tallies[tally][0], 'Tally type', config_mod.tallies[tally][1], 'Tally particle', config_mod.tallies[tally][2], 'Comment', config_mod.tallies[tally][8]]
        })

        df_data = pd.DataFrame({
            'energy (MeV)': config_mod.tallies[tally][3],
            'flux': config_mod.tallies[tally][4],
            'flux norm. per MeV': config_mod.tallies[tally][7],
            'error': config_mod.tallies[tally][5],
        })

        # add empty column
        df_data[' '] = ''

        merged_df = pd.concat([merged_df, df_info, df_data], axis=1)

    # export to excel without index at every row
    merged_df.to_excel(export_path, index=False)

    tk.messagebox.showinfo(title='Export to XLSX', message='Tally export has been completed.')
