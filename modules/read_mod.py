# -*- coding: utf-8 -*-
# TODO_list:
# TODO problem s ruznymi tally, verzemi mcnp, cut off
# TODO pokud je cut off vetsi nez E_min???
# TODO test MCTAL

# libraries
from modules import config_mod

# better and easier work with file and directory paths
from pathlib import Path

import tkinter as tk


#  Functions  ##########################################################################################################
# read outputs from chosen directory
def open_folder(treeview_files):
    config_mod.tallies.clear()  # clear tallies dict before read new directory

    folder_path = Path(
        tk.filedialog.askdirectory(title='Choose directory with MCNP output files', initialdir=Path.cwd()))

    output_files = []
    for file in Path.iterdir(folder_path):
        output_files.append(Path(file))


    # TODO Dusan - hidden files Windows
    hidden = 0  # You have to set it and test it for windows
    while hidden < len(output_files):

        if "." in str(output_files[hidden].stem)[0]:  # if there is unix hiden file (compare first letter from file name)
            print("Hidden file was skipped ---> " + str(output_files[hidden]))  # file is printed
            del output_files[hidden]  # file is deleted
        else:
            hidden += 1
    '''
    try:
        for fname in output_files:
            read_file(folder_path, fname)  # read tallies from output files
    except:
        tk.messagebox.showerror('Input error', 'No directory was selected.')
        return
    '''
    for fname in output_files:
        read_file(folder_path, fname)  # read tallies from output files

    # fill treeview part
    x = treeview_files.get_children()  # get id of all items in treeview
    for i in x:  # delete all items
        treeview_files.delete(i)

    for i in config_mod.tallies.keys():  # fill treeview with new values
        treeview_files.insert('', index='end',
                              values=[i, config_mod.tallies[i][0], config_mod.tallies[i][1], config_mod.tallies[i][2],
                                      len(config_mod.tallies[i][3]) - 1, config_mod.tallies[i][6],
                                      config_mod.tallies[i][3][1], config_mod.tallies[i][3][-1],
                                      config_mod.tallies[i][9]])


# read data from all tally in one output file
def read_file(f_path, fname):
    with open(f_path / fname, 'r', encoding='utf-8') as temp_file:  # open MCNP output file
        content = temp_file.readlines()

        cutoff_dict = cutoff_func(content)

        energy = []
        flux = [0]
        error = [0]

        i = 0
        while i < len(content):
            line = content[i].split()

            if len(line) != 0:  # skip empty lines (try to find better solution?)
                if '1tally' == line[0] and line[1].isdigit():
                    tally_num = line[1]
                    line = content[i + 1].split()

                    comment_loading = []
                    if line[0] == "+":
                        comment_loading = [line[1]]
                        # print(line[1])
                        for comment in range(2, len(line)):
                            comment_loading.append(line[comment])
                        comment_int = 1
                        com_loaded = " ".join(comment_loading)

                    else:
                        comment_int = 0
                        com_loaded = "---"  # IF TALLY IS COMMENTED IN MCNP, IT WILL BE WRITTEN, OTHER WAY, ONLY "--"
                    line = content[i + 1 + comment_int].split()
                    tally_type = int(line[2])
                    line = content[i + 2 + comment_int].split()
                    tally_ptc = line[1]

                    # different beginning for different tally types
                    walking = 0
                    maxwalking = 50
                    while walking < maxwalking:
                        line = content[i + walking].split()
                        if len(line) != 0:
                            if "energy" == line[0]:
                                data_start = i + walking + 1
                                walking = maxwalking
                            else:
                                walking = walking + 1
                        elif len(line) == 0:
                            walking = walking + 1

                    i = data_start
                    line = content[i].split()

                    while line[0] != 'total':
                        energy.append(float(line[0]))
                        flux.append(float(line[1]))
                        error.append(float(line[2]) * flux[-1])
                        i += 1
                        line = content[i].split()

                    # find correct cut off for every tally
                    for particle in cutoff_dict.keys():
                        if tally_ptc[
                            -1] == "s":  # some tallies are not in plural, do not know why -> cure this difference with "s"
                            if tally_ptc[:-1] == particle:
                                cutoff_en = cutoff_dict[particle]
                        elif tally_ptc == particle:
                            cutoff_en = cutoff_dict[particle]

                    # add first energy
                    energy = [cutoff_en] + energy  # neutron cut off E=1E-9 MeV, default photon and e- cut off 0.001 MeV

                    flux_n, error_n = flux_norm(energy, flux,
                                                error)  # create normalized variables for dictionary instead of rewrite original values

                    config_mod.tallies[fname.name + '_' + str(tally_num)] = [tally_num, tally_type, tally_ptc, energy,
                                                                             flux, error, cutoff_en, flux_n, error_n,
                                                                             com_loaded]

                    energy = []
                    flux = [0]
                    error = [0]
            i += 1


# return cutoff values from output
def cutoff_func(content):
    cutoff_dict = {"neutron": 1e-9, "proton": 1e0, "electron": 1e-3, "photon": 1e-3, "pi_+": 0, "pi_0": 0}

    for k in range(0, len(content)):
        if "print table 101" in str(content[k]):
            y = k + 6
            line = content[y].split()
            while len(line) != 0:
                cutoff_dict[line[2]] = float(line[3])
                y += 1
                line = content[y].split()
            # print(cutoff_dict)    # print cut off dict
            return cutoff_dict
        if k == len(content) - 1:
            # print(cutoff_dict)    # print cut off dict
            return cutoff_dict


# flux bin normalization per 1 MeV
def flux_norm(energy, flux, error):
    fl_n = [0]
    fl_n_err = [0]

    for i in range(1, len(flux)):
        if (energy[i] - energy[i - 1]) == 0:
            fl_n.append(0)
            fl_n_err.append(0)
        else:
            fl_n.append(flux[i] / (energy[i] - energy[i - 1]))
            fl_n_err.append(error[i] / (energy[i] - energy[i - 1]))

    return fl_n, fl_n_err
