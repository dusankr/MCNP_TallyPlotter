#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# TODO_list:
# 

# libraries
from modules import config_mod
import pathlib


# functions
#
# create a new config file if someone deleted it
def create_config(fname):
    with open(fname, "w", encoding='utf-8') as temp_file:
        if fname == "config_export":
            temp_file.write("# export and import setting for STEP plot SW\n")
            temp_file.write("# hashtag is used for commenting\n")
            temp_file.write("# = is used as separator, spaces are not allowed between setting and value!\n")
            temp_file.write("#\n")
            for key in config_mod.plot_settings.keys():
                temp_file.write(key + "=" + str(config_mod.plot_settings[key]) + "\n")

        elif fname == "config_legend":
            temp_file.write("# list of all loaded tallies through the time\n")
            temp_file.write("# on the left side of = is name from SW\n")
            temp_file.write("# in the right side of = is possible write new name\n")
            temp_file.write("#\n")


def is_float(element):
    try:
        float(element)
        return True
    except ValueError:
        return False


# read values from config file to program variables
def read_config(fname):
    if not pathlib.Path(fname).is_file():
        create_config(fname)

    # read values from config files
    with open(fname,"r", encoding='utf-8') as temp_file:
        content = temp_file.readlines()

        for lines in content:
            if lines[0] != '#':
                line = lines.split("=", 1)
                if line[0] in config_mod.plot_settings.keys():
                    value = line[1].rstrip()    # rstrip remove \n from the end of line
                    if is_float(value):
                        config_mod.plot_settings[line[0]] = float(value)
                    elif value == "None" or value == "none":
                        config_mod.plot_settings[line[0]] = None
                    elif value == "True" or value == "true":
                        config_mod.plot_settings[line[0]] = True
                    elif value == "False" or value == "false":
                        config_mod.plot_settings[line[0]] = False
                    else:
                        config_mod.plot_settings[line[0]] = value

    # conditions for all possibilities
    try:
        if config_mod.plot_settings["work_dir_path"] is None:
            config_mod.plot_settings["work_dir_path"] = pathlib.Path.cwd()
        #elif config_mod.plot_settings["work_dir_path"] is not pathlib.Path(config_mod.plot_settings["work_dir_path"]).is_dir():
            #config_mod.plot_settings["work_dir_path"] = pathlib.Path.cwd()
        else:
            config_mod.plot_settings["work_dir_path"] = pathlib.Path(config_mod.plot_settings["work_dir_path"])
    except:
        config_mod.plot_settings["work_dir_path"] = pathlib.Path.cwd()
        
    try:
        if config_mod.plot_settings["xs_dir_path"] is None:
            config_mod.plot_settings["xs_dir_path"] = pathlib.Path.cwd()
        elif pathlib.Path(config_mod.plot_settings["xs_dir_path"]).is_file():
            config_mod.plot_settings["xs_dir_path"] = pathlib.Path(config_mod.plot_settings["xs_dir_path"]).parent
        elif pathlib.Path(config_mod.plot_settings["xs_dir_path"]).is_dir():
            config_mod.plot_settings["xs_dir_path"] = pathlib.Path(config_mod.plot_settings["xs_dir_path"])
    except:
        config_mod.plot_settings["xs_dir_path"] = pathlib.Path.cwd()
        
    try:
        if config_mod.plot_settings["export_dir_path"] is None:
            config_mod.plot_settings["export_dir_path"] = pathlib.Path.cwd()
        elif pathlib.Path(config_mod.plot_settings["export_dir_path"]).is_file():
            config_mod.plot_settings["export_dir_path"] = pathlib.Path(config_mod.plot_settings["export_dir_path"]).parent
        elif pathlib.Path(config_mod.plot_settings["export_dir_path"]).is_dir():
            config_mod.plot_settings["export_dir_path"] = pathlib.Path(config_mod.plot_settings["export_dir_path"])
    except:
        config_mod.plot_settings["export_dir_path"] = pathlib.Path.cwd()

    print("Old work directory from config file is: " , config_mod.plot_settings["work_dir_path"])
    print("Old XS directory from config file is: ", config_mod.plot_settings["xs_dir_path"])
    print("Old export directory from config file is: ", config_mod.plot_settings["export_dir_path"], "\n")


# save config values
def save_config():
    with open("config_export", "r+", encoding='utf-8') as temp_file:
        content = temp_file.readlines()
        content_n = []

        for key, val in zip(config_mod.plot_settings.keys(), config_mod.plot_settings.values()):
            i = 0
            while i < len(content):
                if (content[i][0] != "#"):
                    line = content[i].split("=")
                    if key == line[0]:
                        content[i] = str(key) + "=" + str(val) + "\n"
                        break
                    else:
                        i += 1
                else:
                    i += 1

                # if there is end of content cycle and key wasn't find, then add it to end of file
                if i == (len(content)):
                    content_n.append(key + '=' + str(val) + '\n')

        # instead of reopen in a writing mode:
        temp_file.seek(0)
        temp_file.truncate()
        temp_file.writelines(content + content_n)


# read and save tally names to the config_legend file
def readsave_legend(fname):
    if not pathlib.Path(fname).is_file():
        create_config(fname)

    # read values from config files
    with open(fname,"r+", encoding='utf-8') as temp_file:
        content = temp_file.readlines()
        content_n = []

        for key in config_mod.tallies.keys():
            for i in range(0,len(content)):
                if content[i][0] != '#':
                    line = content[i].split("=", 1)
                    if line[0] == key:
                        config_mod.tallies[key][10] = line[1].rstrip()
                        break
                if i == len(content) - 1:
                    config_mod.tallies[key][10] = key
                    content_n.append(key + '=' + key + '\n')

        # add new lines to the end of this file:
        temp_file.seek(0)
        temp_file.truncate()
        temp_file.writelines(content + content_n)
