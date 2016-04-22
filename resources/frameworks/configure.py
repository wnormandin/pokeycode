#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import sys
import time

# Colorize console output
from pokeyworks import Color, color_wrap
# Configuration base class
from pokeyworks import PokeyConfig


class AppConfig():

    def __init__(self):
        self.print_app_headers()

        self.cfg = None
        menu_queue = []
        highlight = Color.BLUE
        # Menu option groups :
        submenu_1 = [
                ('View options',['v',highlight],self.print_config,[self.cfg]),
                ('Add an option',['a',highlight],self.add_option,[self.cfg]),
                ('Edit an option',['e',highlight],self.edit_option,[self.cfg]),
                ('Remove an option',['r',highlight],self.remove_option,[self.cfg]),
                ('Write Config',['w',highlight],self.write_config,[self.cfg]),
                ('Back',['b',Color.RED],None),
                ]
        main_menu = [
                ('Open a file',['o',highlight],self.file_select,[submenu_1]),
                ('New config file',['n',highlight],self.create_config,[self.cfg]),
                ('Convert a file',['c',highlight],self.convert_file,[]),
                ('Quit',['q',highlight],sys.exit,[0]),
                ]

        while True:
            # Main application execution loop
            try:
                pass
            except SystemExit,KeyboardInterrupt:
                ch = raw_input('Really quit? ')
                if ch.upper()=='Y':
                    sys.exit(0)
                else:
                    continue

    def print_app_headers(self):
        header_path = 'app_header.txt'
        with open(header_path, 'r') as f:
            data = f.readlines()

        for row in data:
            time.sleep(0.05)
            print row.rstrip()

    def print_config(self):
        print 'Loaded Options :'
        for key in self.self.cfg.conf_dict:
            print ' [{}] = {}'.format(key,self.cfg.conf_dict)

    def add_option(self):
        key = raw_input('Option : ')
        val = raw_input('Value  : ')
        self.cfg.conf_dict[key]=val

    def edit_option(self):
        while True:
            print_config(self.cfg)
            print '[Edit Option]'
            key = raw_input('Selection (q quits) > ')
            if key.upper() in ['Q','QUIT','EXIT']:
                break
            if key in self.cfg.conf_dict:
                self.cfg.conf_dict[key] = raw_input('Value > ')
            else:
                msg = 'Option {} does not exist, create it? '.format(key)
                ch=raw_input(msg)
                if ch.upper() in ['Y','YES']:
                    self.cfg.conf_dict[key]=raw_input('Value > ')

    def remove_option(self,opt=None):
        if opt is not None and opt in self.cfg.conf_dict:
            del self.cfg.conf_dict[opt]
            return
        elif opt is not None:
            print "Option not in list!"
        self.print_config(cfg)
        key = raw_input('Selection (q quits) > ')
        if key.upper() in ['Q','QUIT','EXIT']:
            return
        elif key in self.cfg.conf_dict:
            del self.cfg.conf_dict[key]
            return
        print 'Option not found!'

    def write_config(self):
        self.cfg.write_cfg()

    def file_select(self):
        fname = raw_input("Enter a path : ")
        try:
            finfo = os.stat(fname)
            print fname
            print finfo
            ch = raw_input("Load this config? ")
            if ch.upper() in ['Y','YES']:
                if fname.endswith('.json'):
                    self.cfg = pokeyworks.PokeyConfig(fname)
                elif fname.endswith('.yaml'):
                    self.cfg = pokeyworks.PokeyConfig(fname,2)
                else:
                    raise AssertionError("Unknown file type : {}".format(fname))
        except OSError:
            print "File not found! {}".format(fname)

    def create_config(self):
        fname = raw_input("Config file name : ")
        if fname.endswith(".json"):
            args = [fname]
        elif fname.endswitch(".yaml"):
            args = [fname,2]
        else:
            print "Invalid file type : {}".format(fname)
            return False
        try:
            with open(fname,'x') as touchfile:
                #Touch!
                pass
        except IOError:
            print "Unable to stat file : {} - check your permissions foo!".format(fname)
            return False
        self.cfg = PokeyConfig(*args)
        ch = raw_input("Config file created!  Add options? ")
        if ch.upper() in ['Y','YES']:
            return 1    # Need to catch this and move to submenu 1
        else:
            return 0

    def convert_file(self,fpath):
        if self.cfg.loaded_type == PokeyConfig.json:
            self.cfg.fpath = self.cfg.convert_file_path(fpath,'.yaml')
            self.cfg.save_yaml(self.cfg.fpath,self.cfg.conf_dict)
            self.cfg.loaded_type = PokeyConfig.yaml
        elif self.cfg.loaded_type == PokeyConfig.yaml:
            self.cfg.fpath = self.cfg.convert_file_path(fpath,'.json')
            self.cfg.save_json(self.cfg.fpath,self.cfg.conf_dict)
            self.cfg.loaded_type = PokeyConfig.json
        else:
            raise AssertionError("Unknown type : {}".format(self.self.cfg.loaded_type))

        print "{} converted to {}".format(fpath,self.cfg.fpath)
    def menu(opts):
        # Prints menu options and handles user selections

        while True:
            break 

if __name__=='__main__':
    AppConfig()
