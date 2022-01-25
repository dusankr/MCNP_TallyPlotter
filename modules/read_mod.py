# -*- coding: utf-8 -*-
# TODO_list:
# TODO potencialni problem s ruznymi tally a verzemi mcnp (zkusit jiný typ výstupu nebo mctal)
# TODO problém se jmény, v cut off tabulce jsou jednotná čísla a v tally množná, zatím vyřešeno pomocí odečtení
#  posledního písmene, funguje jen pro některé částice

# libraries
from modules import config_mod

# better and easier work with file and directory paths
from pathlib import Path

import tkinter as tk


#  Functions  ##########################################################################################################
# read outputs from chosen directory
def open_folder(treeview_files):
    config_mod.tallies.clear()      # clear tallies dict before read new directory

    folder_path = Path(tk.filedialog.askdirectory(title='Choose directory with MCNP output files', initialdir=Path.cwd()))

    output_files = []
    for file in Path.iterdir(folder_path):
        output_files.append(Path(file))

    for fname in output_files:
        read_file(folder_path, fname)     # read tallies from output files

    # fill treeview part
    x = treeview_files.get_children()       # get id of all items in treeview
    for i in x:                             # delete all items
        treeview_files.delete(i)

    for i in config_mod.tallies.keys():      # fill treeview with new values
        treeview_files.insert('', index='end', values=[i, config_mod.tallies[i][0], config_mod.tallies[i][1], config_mod.tallies[i][2], len(config_mod.tallies[i][3])-1, config_mod.tallies[i][6], config_mod.tallies[i][3][1], config_mod.tallies[i][3][-1]])


# read data from all tally in one output file
def read_file(f_path ,fname):

    with open(f_path / fname, 'r', encoding='utf-8') as temp_file:  # open MCNP output file
        content = temp_file.readlines()

        cutoff_dict = cutoff_func(content)

        flux = [0]
        error = [0]
        energy = []

        for i in range(0, len(content)):
            line = content[i].split()

            if len(line) != 0:
                if '1tally' == line[0] and line[1].isdigit():
                    tally_num = line[1]
                    line = content[i + 1].split()
                    tally_type = int(line[2])
                    line = content[i + 2].split()
                    tally_ptc = line[1]

                    # different beginning for different tally types
                    if tally_type == 8:
                        data_start = i + 7 + 2  # data beginning in output file for F8,miss first 2 values-F8 parameters
                    else:
                        data_start = i + 10  # data beginning in output file for tally F4 and others

                    y = data_start
                    line = content[y].split()

                    while line[0] != 'total':
                        energy.append(float(line[0]))
                        flux.append(float(line[1]))
                        error.append(float(line[2])*flux[-1])
                        y += 1
                        line = content[y].split()

                    # find correct cut off for every tally
                    for particle in cutoff_dict.keys():
                        if tally_ptc[:-1] == particle:
                            cutoff_en = cutoff_dict[particle]

                    # add first energy
                    energy = [cutoff_en] + energy  # neutron cut off E=1E-9 MeV, default photon and e- cut off 0.001 MeV

                    config_mod.tallies[fname.name + '_' + str(tally_num)] = [tally_num, tally_type, tally_ptc, energy, flux, error, cutoff_en]

                    energy = []
                    flux = []
                    error = []


# return cutoff values from output
def cutoff_func(content):
    cutoff_dict = {}

    for k in range(0, len(content)):
        line = content[k].split()
        if len(line) != 0:
            if line[0] == '1particles':
                y = k + 6
                line = content[y].split()
                while len(line) != 0:
                    cutoff_dict[line[2]] = float(line[3])
                    y += 1
                    line = content[y].split()
                return cutoff_dict
