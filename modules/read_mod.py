# -*- coding: utf-8 -*-
# TODO_list:
# TODO what happens if cut off is higher than E_min???
# TODO use MCNP Tools
# TODO create own class for tally results?
# TODO create log file!
# https://www.geeksforgeeks.org/how-to-log-a-python-exception/
# https://docs.python.org/3/library/traceback.html
# https://stackoverflow.com/questions/5191830/how-do-i-log-a-python-error-with-debug-information

# libraries
from modules import config_mod, settings_mod
import pathlib  # better and easier work with file and directory paths
import tkinter as tk
import os
import traceback

# lib for Windows API (nt is name for win OS)
if os.name == 'nt':  # return OS system name
    import win32api, win32con


#  Functions  ##########################################################################################################
# return cutoff value from output or use a default value
def cutoff_func(content):
    # default values table 2-2. in MCNP6.2 manual (MeV):
    cutoff_dict = {
        "neutron": 0.0000E+00,
        "photon": 1.0000E-03,
        "electron": 1.0000E-03,
        "mu_minus": 1.1261E-01,
        "Aneutron": 0.0000E+00,
        "nu_e": 0.0000E+00,
        "nu_m": 0.0000E+00,
        "proton": 1.0000E+00,
        "lambda0": 1.0000E+00,
        "sigma+": 1.2676E+00,
        "sigma-": 1.2762E+00,
        "xi0": 1.0000E+00,
        "xi_minus": 1.4082E+00,
        "omega-": 1.7825E+00,
        "mu_plus": 1.1261E-01,
        "Anu_e": 0.0000E+00,
        "Anu_m": 0.0000E+00,
        "Aproton": 1.0000E+00,
        "pi_plus": 1.4875E-01,
        "pi_zero": 0.0000E+00,
        "k_plus": 5.2614E-01,
        "k0_short": 0.0000E+00,
        "k0_long": 0.0000E+00,
        "Alambda0": 1.0000E+00,
        "Asigma+": 1.2676E+00,
        "Asigma-": 1.2762E+00,
        "Axi0": 1.0000E+00,
        "xi_plus": 1.4082E+00,
        "Aomega-": 1.7825E+00,
        "deuteron": 2.0000E+00,
        "triton": 3.0000E+00,
        "helion": 3.0000E+00,
        "alpha": 4.0000E+00,
        "pi_minus": 1.4875E-01,
        "k_minus": 5.2614E-01,
        "heavyion": 5.0000E+00
    }

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


# calculate flux bin normalization per 1 MeV
def flux_norm(energy, flux):
    fl_n = [0]
    for i in range(1, len(flux)):
        if (energy[i] - energy[i - 1]) == 0:
            fl_n.append(0)
        else:
            fl_n.append(flux[i] / (energy[i] - energy[i - 1]))

    return fl_n


# check if file is hidden in Windows folder
def file_is_hidden(p):
    if os.name != 'nt':
        return False
    attribute = win32api.GetFileAttributes(str(p))
    # & - bitwise AND; | - bitwise OR
    if (attribute & (win32con.FILE_ATTRIBUTE_HIDDEN | win32con.FILE_ATTRIBUTE_SYSTEM)) == 2:
        return True


# chose folder with MCNP outputs, read all files
def open_folder(treeview_files, workdir_label, button_update):
    config_mod.plot_settings["work_dir_path"] = pathlib.Path(tk.filedialog.askdirectory(title='Choose a directory with MCNP output files', initialdir=config_mod.plot_settings["work_dir_path"]))

    if str(config_mod.plot_settings["work_dir_path"]) == '.':
        tk.messagebox.showerror('Input error', 'No directory was selected.')
        return

    workdir_label['text'] = 'Work directory: ' + str(config_mod.plot_settings["work_dir_path"])
    button_update['state'] = 'normal'

    read_folder(treeview_files)


# read file names in chosen folder and skip hidden files and subdirectories
# TODO maybe this one could be deleted and work only with try-except...
def read_folder(treeview_files):
    config_mod.tallies.clear()  # clear tallies dict before read new directory

    config_mod.output_files = []
    for file in pathlib.Path.iterdir(config_mod.plot_settings["work_dir_path"]):
        if file.is_dir() or (file.stem[0] == '.') or file_is_hidden(file):  # UNIX/Mac/Windows hidden files and directories are skipped
            config_mod.non_output.append(file.name)
            continue  # skip to the next iteration
        else:
            config_mod.output_files.append(file)

    # run function for separating tally data from output files
    read_tallies(treeview_files)


# read outputs from a directory (go through all relevant outputs and read tallies via the next function)
def read_tallies(treeview_files):

    for fname in config_mod.output_files:
        read_tally(config_mod.plot_settings["work_dir_path"], fname)  # read tallies from output files

    # print list of non MCNP files OR empty outputs
    print('\nList of non MCNP output files OR empty outputs:')
    for file in config_mod.non_output:
        print("\t" + file)

    # read legend names
    settings_mod.readsave_legend("config_legend")

    # fill treeview part
    x = treeview_files.get_children()  # get id of all items in treeview
    for i in x:  # delete all items
        treeview_files.delete(i)

    for i in config_mod.tallies.keys():  # fill treeview with new values
        treeview_files.insert('', index='end',
                              values=[i, config_mod.tallies[i][0], config_mod.tallies[i][1], config_mod.tallies[i][2],
                                      len(config_mod.tallies[i][3]) - 1, config_mod.tallies[i][6],
                                      config_mod.tallies[i][3][1], config_mod.tallies[i][3][-1],
                                      config_mod.tallies[i][8]])


# read data from all tallies in one output file and add them into global dictionary
def read_tally(f_path, fname):
    try:
        with open(f_path / fname, 'r', encoding='utf-8') as temp_file:  # open MCNP output file
            content = temp_file.readlines()

            cutoff_dict = cutoff_func(content)      # read cut-off table from output file, if does not exist then use default values

            # local variables for temporary storing of energy, flux and error from one tally
            energy = []
            flux = [0]
            error = [0]
            # josef20220202-1line
            save_talies = None  # new variable for separate more items(cells or surfaces) in one tally

            # print name of current OUTPUT file
            print("Name off processed file: ", fname.name)

            i = 0
            while i < len(content):
                line = content[i].split()

                if len(line) != 0:  # skip empty lines (try to find a better solution?)
                    if '1tally' == line[0] and line[1].isdigit():
                        tally_num = line[1]
                        line = content[i + 1].split()

                        comment_loading = []
                        if line[0] == "+":
                            comment_loading = [line[1]]
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
                        # josef20220202-start
                        while walking < maxwalking:
                            line = content[i + walking].split()
                            if len(line) != 0 and "energy" == line[0]:
                                surface_or_cell = content[
                                    i + walking - 1].split()  # new variable which takes first item of found tally
                                data_start = i + walking + 1
                                if len(surface_or_cell) == 0:  # some tallies of mcnp version that there is extra empty line between item description and "energy"
                                    surface_or_cell = content[i + walking - 2].split()
                                walking = maxwalking
                            else:
                                walking = walking + 1

                        # find correct cut off for every tally
                        for particle in cutoff_dict.keys():
                            if tally_ptc[-1] == "s":  # some tallies are not in plural, do not know why -> cure this difference with "s"
                                if tally_ptc[:-1] == particle:
                                    cutoff_en = cutoff_dict[particle]
                            elif tally_ptc == particle:
                                cutoff_en = cutoff_dict[particle]

                        # for tally F8 are the first two lines skipped:
                        # first value is a non-analog knock-on e- negativ scores
                        # epsilon bin (more details in manual)
                        if tally_type == 8:
                            i = data_start + 2
                        else:
                            i = data_start

                        line = content[i].split()
                        while line[0] != 'total':
                            energy.append(float(line[0]))
                            flux.append(float(line[1]))
                            error.append(float(line[2]))
                            i += 1
                            line = content[i].split()
                            last = i
                        # add first energy
                        energy = [cutoff_en] + energy  # neutron cut off E=1E-9 MeV, default photon and e- cut off 0.001 MeV
                        # create normalized variables for dictionary instead of rewrite original values
                        flux_n = flux_norm(energy, flux)

                        control_next_tally_connection = content[last + 2].split()
                        #print("control prirazeni", control_next_tally_connection)
                        if len(control_next_tally_connection) != 0 and control_next_tally_connection[0] == surface_or_cell[0] and control_next_tally_connection[1].isdigit():  # second word must be digit, for point detector (tally5) there is dvo data file for one tally - collide and uncolide results, first world is the same, but second is not digit!
                            print(str(surface_or_cell[0]) + str(surface_or_cell[1]) + "  ---  line" + str(last + 2))
                            next_tally = last + 4
                            more_items_in_one_tally = True
                        else:
                            print(str(surface_or_cell[0]) + str(surface_or_cell[1]) + "  ---  line" + str(i + walking - 2))
                            print("---> no more items in this tally !\n")
                            more_items_in_one_tally = False

                        while more_items_in_one_tally == True:
                            config_mod.tallies[fname.stem + '_' + str(tally_num) + "_" + str(surface_or_cell[0]) + "_" + str(surface_or_cell[1])] = [tally_num, tally_type, tally_ptc, energy, flux, error, cutoff_en, flux_n, com_loaded, None, None]

                            energy = []
                            flux = [0]
                            error = [0]
                            surface_or_cell = control_next_tally_connection

                            # for tally F8 are the first two lines skipped:
                            # first value is a non-analog knock-on e- negative scores
                            # epsilon bin (more details in manual)
                            if tally_type == 8:
                                next_tally += 2

                            line = content[next_tally].split()
                            while line[0] != 'total':
                                energy.append(float(line[0]))
                                flux.append(float(line[1]))
                                error.append(float(line[2]))
                                next_tally += 1
                                line = content[next_tally].split()
                                last = next_tally
                            energy = [cutoff_en] + energy
                            flux_n = flux_norm(energy, flux)

                            control_next_tally_connection = content[last + 2].split()

                            # temporary bug fix, solve an empty list if there is not a next tally
                            if not control_next_tally_connection:
                                control_next_tally_connection.extend(["empty", 0])

                            if control_next_tally_connection[0] == surface_or_cell[0]:
                                print("---> next tally included...")
                                print(str(surface_or_cell[0]) + str(surface_or_cell[1]) + "  ---  line" + str(last + 4))
                                next_tally = last + 4
                                save_talies = control_next_tally_connection[1]
                                more_items_in_one_tally = True
                            else:
                                save_talies = control_next_tally_connection[1]
                                more_items_in_one_tally = False

                        else:
                            if len(control_next_tally_connection) > 1 and save_talies == control_next_tally_connection[1]:
                                print("---> next tally included...")
                                print(str(surface_or_cell[0]) + str(surface_or_cell[1]) + "  ---  line" + str(last + 4))
                                config_mod.tallies[fname.stem + '_' + str(tally_num) + "_" + str(surface_or_cell[0]) + "_" + str(surface_or_cell[1])] = [tally_num, tally_type, tally_ptc, energy, flux, error, cutoff_en, flux_n, com_loaded, None, None]
                                # print("last_tallies.....")
                            else:
                                config_mod.tallies[fname.stem + '_' + str(tally_num)] = [tally_num, tally_type, tally_ptc, energy, flux, error, cutoff_en, flux_n, com_loaded, None, None]
                                print("---> This file does not contain more items per tally\n")

                            # josef20220202-end
                            energy = []
                            flux = [0]
                            error = [0]
                i += 1
    except:
        traceback.print_exc()
        config_mod.non_output.append(fname.name)
        print('Read process crash for this file: ' + fname.name)


# read XS data
def read_xs():
    config_mod.plot_settings["xs_dir_path"] = pathlib.Path(tk.filedialog.askopenfilename(title='Choose directory with XS file', initialdir=config_mod.plot_settings["work_dir_path"]))

    try:
        with open(config_mod.plot_settings["xs_dir_path"], 'r', encoding='utf-8') as temp_file:  # open XS file
            content = temp_file.readlines()

            config_mod.xs_data.clear()

            x_dat = []
            y_dat = []

            i = 0
            while i < len(content):
                if content[i][0] != '#':
                    line = content[i].split()
                    if line[0] == "name:":
                        name_xs = line[1] + " " + line[2]

                        i += 8
                        while content[i] != "//\n":
                            line = content[i].split()
                            x_dat.append(float(line[0]))
                            y_dat.append(float(line[1]))
                            i += 1
                        config_mod.xs_data[name_xs] = [x_dat, y_dat]
                        x_dat, y_dat = [], []
                    else:
                        i += 1
                else:
                    i += 1

        # print all XS from file in CMD
        print("All XS from ", config_mod.plot_settings["xs_dir_path"].name, " file:")
        for nam in config_mod.xs_data.keys():
            print(nam)

    except:
        traceback.print_exc()
        print('Read process crash for this file:')
