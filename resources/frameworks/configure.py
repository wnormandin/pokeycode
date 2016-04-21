#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import sys

# Colorize console output
from pokeyworks import Color, color_wrap
# Configuration base class
from pokeyworks import PokeyConfig


def configure_application():
    # Routine to create or edit configuration files
    # to be saved in JSON or YAML format using the
    # pokeyworks.PokeyConfig() class.
    print_app_header()

    menu_queue = []
    highlight = Color.BLUE
    # Menu option groups :
    submenu_1 = [
            ('View options',['v',highlight],print_config),
            ('Add an option',['a',highlight],add_option),
            ('Edit an option',['e',highlight],edit_option),
            ('Remove an option',['r',highlight],remove_option),
            ('Write Config',['w',highlight],write_config),
            ('Back',['b',Color.RED],None),
            ]
    main_menu = [
            ('Open a file',['o',highlight],file_select,submenu_1),
            ('New config file',['n',highlight],create_config),
            ('Convert a file',['c',highlight],convert_file),
            ('Quit',['q',highlight],sys.exit,0),
            ]

    while True:
        # Main application execution loop
        try:
            
        except SystemExit,KeyboardInterrupt:
            ch = raw_input('Really quit? ')
            if ch.upper()=='Y':
                sys.exit(0)
            else:
                continue

def print_config(cfg):
    print 'Loaded Options :'
    for key in cfg.conf_dict:
        print ' [{}] = {}'.format(key,cfg.conf_dict)

def add_option(cfg):
    key = raw_input('Option : ')
    val = raw_input('Value  : ')
    cfg.conf_dict[key]=val

def edit_option(cfg):
    while True:
        print_config(cfg)
        print '[Edit Option]'
        key = raw_input('Selection (q quits) > ')
        if key.upper() in ['Q','QUIT','EXIT']:
            break
        if key in cfg.conf_dict:
            cfg.conf_dict[key] = raw_input('Value > ')
        else:
            msg = 'Option {} does not exist, create it? '.format(key)
            ch=raw_input(msg)
            if ch.upper() in ['Y','YES']:
                cfg.conf_dict[key]=raw_input('Value > ')

def remove_option(cfg,opt=None):
    if opt is not None and opt in cfg.conf_dict:
        del cfg.conf_dict[opt]
        return
    elif opt is not None:
        print "Option not in list!"
    print_config(cfg)
    key = raw_input('Selection (q quits) > ')
    if key.upper() in ['Q','QUIT','EXIT']:
        return
    elif key in cfg.conf_dict:
        del cfg.conf_dict[key]
        return
    print 'Option not found!'

def write_config(cfg):
    cfg.write_cfg()

def file_select(cfg):
    fname = raw_input("Enter a path : ")
    try:
        finfo = os.stat(fname)
        print fname
        print finfo
        ch = raw_input("Load this config? ")
        if ch.upper() in ['Y','YES']:
            if fname.endswith('.json'):
                cfg = pokeyworks.PokeyConfig(fname)
            elif fname.endswith('.yaml'):
                cfg = pokeyworks.PokeyConfig(fname,2)
            else:
                raise AssertionError("Unknown file type : {}".format(fname))
    except OSError:
        print "File not found! {}".format(fname)

def create_config(cfg,opt):
    fname = raw_input("Config file name : ")
    if fname.endswith(".json"):

    elif fname.endswitch(".yaml"):

    else:
        print "Invalid file type : {}".format(fname)
def convert_file():
def menu(opts):
    # Prints menu options and handles user selections

    while True:
        

if __name__=='__main__':
    configure_application()
