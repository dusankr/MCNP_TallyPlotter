#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# TODO_list:
# 


# libraries
from modules import config_mod
import pathlib


# functions

# on start up will check if config file exists, if not, it will create new one
# with defaul values
def config_file():
    if pathlib.Path("config_export").is_file():
        read_config()
    else:
        create_config()
        read_config()


# create new config file if someone deleted it
def create_config():
    with open("config_export", "w", encoding='utf-8') as temp_file:
        temp_file.write("# export and import setting for STEP plot SW\n")
        temp_file.write("# hashtag is used for commenting\n")
        temp_file.write("# = is used as separator, spaces are not allowed between setting and value!\n")
        temp_file.write("#\n")
        temp_file.write("# initial directory\n")
        temp_file.write("work_dir_path=none\n")


# read values from config file to program variables
def read_config():
    # read values from config file
    with open("config_export","r", encoding='utf-8') as temp_file:
        content = temp_file.readlines()
                
        
        for lines in content:
            if lines[0] != '#':
                line = lines.split("=", 1)
                if line[0] in config_mod.plot_settings.keys():
                    config_mod.plot_settings[line[0]] = line[1].rstrip()
                
    if config_mod.plot_settings["work_dir_path"]  == "none":
        config_mod.folder_path = pathlib.Path.cwd()
    else:
        config_mod.folder_path = pathlib.Path(config_mod.plot_settings["work_dir_path"])
    
    print("Work directory from config file is: " ,config_mod.folder_path)


# save config values
def save_config():
    with open("config_export", "rw", encoding='utf-8') as temp_file:
        content = temp_file.readlines()
        
        for lines in content:
            if lines[0] != "#":
                line = lines.split("=", 1)
                
        
        