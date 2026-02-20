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


# save selected tallies to separate xlsx files, one per source output file
def save_to_xlsx_separate(sel_tally):
    # return to the main window if no tally is selected
    if sel_tally is None:
        return

    export_dir_str = tk.filedialog.askdirectory(
        title='Choose directory for separate xlsx export',
        initialdir=config_mod.plot_settings["export_dir_path"]
    )

    if not export_dir_str:
        tk.messagebox.showerror('Input error', 'No directory was selected.')
        return

    export_dir = pathlib.Path(export_dir_str)
    config_mod.plot_settings["export_dir_path"] = export_dir

    # group tallies by source output file (strip the trailing _<tallynumber>)
    groups = {}
    for tally in sel_tally:
        src_file = tally.rsplit('_', 1)[0]
        groups.setdefault(src_file, []).append(tally)

    # create one xlsx per source file, named after the original output
    for src_file, tallies_list in groups.items():
        export_path = export_dir / (src_file + '.xlsx')

        merged_df = pd.DataFrame()
        for tally in tallies_list:
            fname = tally.rsplit('_', 1)[0]

            df_info = pd.DataFrame({
                'information': ['Filename', fname, 'Tally number', config_mod.tallies[tally][0], 'Tally type', config_mod.tallies[tally][1], 'Tally particle', config_mod.tallies[tally][2], 'Comment', config_mod.tallies[tally][8]]
            })

            df_data = pd.DataFrame({
                'energy (MeV)': config_mod.tallies[tally][3],
                'flux': config_mod.tallies[tally][4],
                'flux norm. per MeV': config_mod.tallies[tally][7],
                'error': config_mod.tallies[tally][5],
            })

            # add empty separator column
            df_data[' '] = ''

            merged_df = pd.concat([merged_df, df_info, df_data], axis=1)

        merged_df.to_excel(export_path, index=False)

    tk.messagebox.showinfo(
        title='Export to XLSX (separate)',
        message=f'Export completed: {len(groups)} file(s) created in\n{export_dir}'
    )
