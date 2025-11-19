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
        tally_obj = config_mod.tallies[tally]

        df_info = pd.DataFrame({
            'information': ['Filename', fname, 'Tally number', tally_obj.tally_num, 'Tally type', tally_obj.tally_type, 'Tally particle', tally_obj.particle, 'Comment', tally_obj.comment]
        })

        df_data = pd.DataFrame({
            'energy (MeV)': tally_obj.energy,
            'flux': tally_obj.flux,
            'flux norm. per MeV': tally_obj.flux_normalized,
            'error': tally_obj.error,
        })

        # add empty column
        df_data[' '] = ''

        merged_df = pd.concat([merged_df, df_info, df_data], axis=1)

    # export to excel without index at every row
    merged_df.to_excel(export_path, index=False)

    tk.messagebox.showinfo(title='Export to XLSX', message='Tally export has been completed.')
