#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
#***********************************************************************
#			Essential Framework and Utilities- bill@pokeybill.us
#***********************************************************************
""" This framework is intented to contain miscellaneous utilities for
    python projects.  Includes :

	Logging Utility
	Gtk 3.0 Dialog Windows
	File Path Generators
	Language Functions (pluralization,)
	System Path Editing
	Configuration Objects
	Colorizing Console Output
	Local module installations
    Linux daemon class

    The _flags global dict will contain various boolean values corresponding
    to the presence/absence of certain core modules that are not in the
    standard distribution (ie Gtk, MultiProcessing based on OS)
"""
#****************************** Globals ********************************

import os
import os.path
import subprocess
import logging
import time
import sys
import multiprocessing
import inspect
import base64
from cStringIO import StringIO

# Conditional imports
try:
    import json
except:
    JSON_ENABLED=False
else:
    JSON_ENABLED=True

try:
    import yaml
except:
    YAML_ENABLED=False
else:
    YAML_ENABLED=True

# PATHS
_conf_path = ''		# Optional default path to app configutaion file
_icon_path = ''		# Optional Gtk window icon path
_log_path = ''		# Optional default log path (can also generate path)

# Permissions Constants (used with Linux filesystem operations)
PERM_0777=[0o777,'fd'] # File/Dir
PERM_0755=[0o755,'fd'] # File/Dir
PERM_0700=[0o700,'fd'] # File/Dir
PERM_0666=[0o666,'f']
PERM_0644=[0o644,'f']
PERM_0600=[0o600,'f']
PERM_0000=[0o000,'fd'] # File/Dir

# MODULE FLAGS
_flags = {}			# Miscellaneous module availability flags and etc
flag_list = ['sys','multiprocessing','os','logging','csv',
                     'socket','random','time','subprocess']

for mod in flag_list:
	try:
		exec 'import {}'.format(mod)
	except:
		_flags[mod]=False
		continue
	else:
		_flags[mod]=True

try:
	from gi.repository import Gtk
except:
	_flags['gtk']=False
else:
	_flags['gtk']=True

def chk_deps(mods):
	return all(_flags[mod]==True for mod in mods)

#****************************** Logging ********************************

#***********************************************************************
#		Default logging configuration settings
#		https://docs.python.org/2/library/logging.html#logger-objects
#***********************************************************************

def setup_logger(name, level, lpath='./tmp/last_run.log',fpath=__name__):

	# Get the logger and set the level
	logger = logging.getLogger(name)
	logger.setLevel(level)
	# Create the formatters
	file_formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(module)s >> %(message)s')
	cons_formatter = logging.StreamHandler('%(message)s')
	# Create the handlers
	cons_handler = logging.StreamHandler(sys.stdout)
	cons_handler.setFormatter(cons_formatter)
	logger.addHandler(cons_handler)

	if level==logging.DEBUG:
		# Includes current run information if level = logging.DEBUG
		f=open(resource_path(__file__,lpath),'w+')
		f.close()

		last_run = logging.FileHandler(resource_path(__file__,lpath), 'w')
		last_run.setFormatter(file_formatter)
		logger.addHandler(last_run)

	return logger

#****************************** File Ops *******************************

def read_csv(fpath, delim=',',qchar="'"):
	if chk_deps(['csv']):
		try:
			with open(fpath, 'rb') as f:
				csvobj = csv.reader(f, delimiter=delim, quotechar=qchar)
				return [row for row in csvobj]
		except Exception as e:
			raise

#*************************** Misc Utilities ****************************

# Validates the argument format if date type
def valid_date(s):
	hgt_logger.debug('\tvalid_date args : {}'.format(s))

	try:
		return datetime.strptime(s, "%Y-%m-%d")
	except ValueError:
		return False

# Return path to a resource based on relative path passed
def resource_path(fpath,rel_path):
    dir_of_py_file = os.path.dirname(fpath)
    rel_path_to_resource = os.path.join(dir_of_py_file, rel_path)
    abs_path_to_resource = os.path.abspath(rel_path_to_resource)
    return abs_path_to_resource


# With the Color class, color_wrap provides limited color, underline, and boldface
# type when outputting to consoles or logs
def color_wrap(val, color):
	return '{}{}{}'.format(color, val, '\033[0m')

# Limited selection
# Uses ascii color codes, may not play nicely with all terminals
class Color:
    BLACK_ON_GREEN = '\x1b[1;30;42m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

plurals_list = [
		[['y'],-2,'ies'],
		[['o','ch'],'es'],
		[['us'],-2,'i'],
		[['fe'],-2,'ves'],
		[['f'],-1,'ves'],
		[['on'],-2,'a'],
		]

# Limited Word Pluralization
def plurals(word, qty):

	if qty > 1:
		for grp in plurals_list:
			for suff in grp[0]:
				if word.endswith(suff):
					if len(grp)==3:
						word=word[:grp[1]]
					suffix=grp[-1]

		if not suffix:
			suffix = 's'

		return qty, '{}{}'.format(word, suffix)

	else:
		return qty, word

#*****************************PokeyConfig*******************************

class PokeyConfig(object):

    """ PokeyConfig is a multi-language configuration file class """

    #Supported formats :
    #    Python
    #    JSON
    #    YAML
    #    Delimited

    # Enable delimited mode by passing a delimiter in the type
    pipe = '|'
    tab = '\t'
    semicolon = ';'
    comma = ','
    percent = '%'

    delimiters = [pipe,tab,semicolon,comma]

    # Available formats
    json = 1
    yaml = 2
    encoded = 3

    def __init__(self,fpath,conf_type=1,auto_apply=False):

        if not JSON_ENABLED or not YAML_ENABLED:
            mname = "pyyaml" if not YAML_ENABLED else "json"
            raise AssertionError("Missing Dependency: {}".format(mname))
        try:
            self.fpath = fpath
            self.load_config(conf_type)
            self.loaded_type = conf_type
            if auto_apply:
                self.apply_config()
        except Exception as e:
            raise

    def apply_config(self):
        # Creates class attributes from dictionary pairs
        # (Optional)

        for key in self.conf_dict:
            setattr(self,key,self.conf_dict[key])

    def load_json(self,fpath):
        assert fpath.endswith(".json"),"Invalid file path to load as JSON"
        with open(fpath) as json_data:
            retval = json.load(json_data)

        return retval

    def yaml_constructor(self,loader,node):
        return node.value

    def load_yaml(self,fpath):
        assert fpath.endswith(".yml"), \
            "Invalid file path to load as YAML : {}".format(fpath)
        with open(fpath) as yaml_data:
            yaml.SafeLoader.add_constructor(
                    "tag:yaml.org,2002:python/unicode",
                    self.yaml_constructor
                    )
            retval = yaml.safe_load(yaml_data)

        return retval

    def save_json(self,fpath,conf_dict):
        assert fpath.endswith(".json"),"Invalid file path to save as JSON"
        try:
            with open(fpath,'w') as json_out:
                json.dump(
                        conf_dict,
                        json_out,
                        sort_keys=True,
                        indent=4,
                        ensure_ascii=False
                        )
        except Exception as e:
            retval = e
        else:
            retval = True

    def save_yaml(self,fpath,conf_dict):
        assert fpath.endswith(".yml"),"Invalid file path to save as YAML"
        try:
            with open(fpath,'w') as yaml_out:
                yaml.dump(conf_dict,yaml_out,default_flow_style=True)
        except Exception as e:
            retval = e
        else:
            reval = True

    def convert_file_path(self,inpath,suffix):
        file_base = inpath.split('.')[:-1]
        file_base.append(suffix)
        return '.'.join(file_base)

    def convert_config(self,out_type):
        if self.loaded_type==out_type:
            print "Config file is already in this format"
            return
        else:
            cur_path = self.fpath
            data,opath = self.convert_delimited(self.fpath,out_type)
            print 'New config file created : {}'.format(opath)
            self.rm_config(cur_path)

    def rm_config(self,fpath):
        rm_path = os.path.realpath(fpath)
        print 'File : {}'.format(rm_path)
        ch = raw_input('Really delete? > ')
        if ch.upper() == 'Y':
            os.remove(rm_path)

    def convert_delimited(self,inpath,out_type):

        if out_type is PokeyConfig.json:
            suffix = 'json'
            write_method = self.save_json
            read_method = self.load_json
        elif out_type is PokeyConfig.yaml:
            suffix = 'yml'
            write_method = self.save_yaml
            read_method = self.load_yaml
        elif out_type is PokeyConfig.encoded:
            suffix = 'cfg'
            write_method = self.do_encode
            read_method = self.do_decode
        else:
            raise AssertionError('Invalid Output Type: {}'.format(out_type))

        opath = self.convert_file_path(inpath,suffix)
        write_method(opath,self.conf_dict)

        # Test twice before failing
        if not self.verify_conversion(read_method(opath)):
            if not self.verify_conversion(read_method(opath)):
                raise AssertionError('Conversion Error! Please log and report')

        # Reassign path/type setting to new value
        self.fpath = opath
        self.loaded_type = out_type
        return read_method(opath), opath

    def do_encode(self,opath,data_dict):
        # Format the data dictionary as a JSON object and
        # save it in a StringIO stream for encoding
        output = StringIO()
        json.dump(data_dict,output,sort_keys=True,indent=4,ensure_ascii=False)

        output.seek(0)
        #print output.readlines()

        with open(opath, 'w') as outfile:
            base64.encode(output,outfile)

        output.close()

    def do_decode(self,inpath):
        # Read the base64-encoded data, and convert it
        # from JSON to a data dictionary
        indata = StringIO()

        with open(inpath, 'r') as infile:
            base64.decode(infile,indata)

        indata.seek(0)
        retval = json.load(indata), inpath
        indata.close()
        return retval

    def write_config(self,**kw):

        if self.loaded_type == PokeyConfig.json:
            write_method = self.save_json
        elif self.loaded_type == PokeyConfig.yaml:
            write_method = self.save_yaml
        elif self.loaded_type == PokeyConfig.encoded:
            write_method = self.do_encode

        write_method(self.fpath,self.conf_dict)

    def verify_conversion(self,compare_dict):

        for key in self.conf_dict:
            try:
                print key
                assert compare_dict[key]==self.conf_dict[key], \
                    "Conversion error! Retrying (val:{}|comp:{})".format(
                                                        val,compare_dict[key]
                                                        )
            except AssertionError,KeyError:
                return False
        return True

    def load_config(self,conf_type,inpath=None):

        if inpath is None:
            inpath=self.fpath
        if conf_type not in [PokeyConfig.json,PokeyConfig.yaml]:
            print "[*] Legacy PokeyConfig configuration detected!"
            while True:
                print "\tConvert to [J]SON"
                print "\tConvert to [Y]AML"
                choice = raw_input("\tSelection > ")
                if choice.upper() == 'J':
                    out_type = PokeyConfig.json
                    break
                elif choice.upper() == 'Y':
                    out_type = PokeyConfig.yaml
                    break
                else:
                    print "[*] Invalid choice!  Conversion is required"

            self.load_delimited(inpath,conf_type)
            new_config,opath = self.convert_delimited(inpath,out_type)

            print "[*] Conversion complete : {}".format(opath)
            print "\tPlease update your configuration paths &"
            print "\tvisit https://pokeybill.us/new-pokeyconfig-release/"
            print "\tto review the new usage and update your apps"

        elif conf_type == PokeyConfig.json:
            self.conf_dict = self.load_json(inpath)

        elif conf_type == PokeyConfig.yaml:
            self.conf_dict = self.load_yaml(inpath)
        elif conf_type == PokeyConfig.encoded:
            self.conf_dict = self.do_decode(inpath)
        else:
            raise AssertionError("Invalid config type {}".format(conf_type))

        return True

    def load_delimited(self,inpath,delimiter):
        # Default delimiter for PokeyWorks applications was %

        self.conf_dict = {}

        with open(inpath, 'rb') as c:
            data = c.readlines()

        for row in data:
            if "#" not in row and row.strip():
                vals = row.rstrip().split(delimiter)
                self.conf_dict[vals[0]] = vals[1]

def install_module(path,mod):
	""" Installs the passed module at the path specified using easy_install """

	# Add the installation path to the pythonpath environment variable
	ex_path = 'export PYTHONPATH="${{PYTHONPATH}}:{0}"\n'.format(resource_path(path))

	with open(''.join([os.path.expanduser('~'),'/.bashrc']),'a+') as rc:
		# Add the line only if it doesn't exist (append only)
		if ex_path not in rc.readlines():
			rc.write(ex_path)

	# Assumes Python easy_install is available
	cmd = 'easy_install -d {0} {1}'.format(resource_path(path),mod)
	print cmd

	#result = shell_command(cmd,True)
	#return result

def shell_command(cmd_str,sh=False):
	""" Executes the passed shell command string, returning any output

	Assumes the executing platform supports subprocess
	"""

	proc = subprocess.Popen(cmd_str.split(),shell=sh)
	return proc.communicate()[0]

def mkdir(dpath,perms=PERM_0755[0]):
	""" Creates the requested directory(ies) if they do not exist """
	try:
		if not os.path.exists(dpath):
			print '\tFolder {0} not found, creating.'.format(dpath)
			os.makedirs(dpath,mode=perms)
	except (OSError,IOError) as e:
		print '\tmkdir({0}) IO/OS error detected.'.format(e)
		return False,e
	except:
		e = UnhandledException(
								'mkdir_error',
								inspect.currentframe()
								)
		return False,e
	else:
		return dpath,perms

class PokeyError(Exception):
	""" Base Class for custom exceptions """
	pass

class UnhandledException(PokeyError):
	""" Error raised for unhandled exceptions

	Attributes:
		https://docs.python.org/2/library/inspect.html
	"""
	def __init__(self,frame,time_stamp=time.clock()):
		self.frame = frame
		self.code = frame.f_code
		self.traceback = frame.f_exc_traceback
		self.line = frame.f_lineno
		self.trace = frame.f_trace
		self.exc_type = frame.t_exc_type
		self.exc_value = frame.f_exc_value
		self.mod = frame.f_code.co_name
		self.caller = frame.f_back.f_code.co_name
		self.time = time_stamp

	def __str__(self):
		""" Custom error traceback output """

		outp = 'Unhandled Exception Captured\n'
		outp += 'IN {0} at LINE {1} | CALLER {2}'.format(self.mod,self.line,self.caller)
		outp += '| AT {0}\n'.format(self.time)
		outp += 'Details :\nType - {0}\nValue - {1}\n'.format(self.exc_type,self.exc_value)
		outp += 'CODE : {0}\n'.format(self.code)
		outp += 'TRACEBACK : {0}'.format(self.trace)
		return outp

	def look_back(self,hops):
		""" Steps back through the stack and returns a list of frames """

		outp = []
		frm = self.frame
		i = 0

		while i < hops:
			frm = frm.f_back
			outp.append([i,frm])
			i += 1

		# Output format : [[depth,frame],] (skips the current frame)
		return outp

class Daemon():

    """ General linux daemon class """

    def __init__(
                self,
                pidfile,
                stdin='/dev/null',
                stdout='/dev/null',
                stderr='/dev/null'
                ):

        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile

    def daemonize(self):

        """ http://stackoverflow.com/questions/881388/what-is-the-reason-for-performing-a-double-fork-when-creating-a-daemon """

        # double forking forces the daemon into an orphaned
        # child process managed by init and incapable of 
        # becoming a session leader and control a tty
        for n in range(1,2):
            try:
                pid = os.fork()
                if pid > 0:
                    # exit first parent
                    sys.exit(0)
            except OSError as e:
                sys.stderr.write("fork {} failed: {} ({})".format(
                                                n,
                                                e.errno,
                                                e.strerror
                                                ))
                sys.exit(1)

        # redirect file descriptors and replace the
        # existing values
        sys.stdout.flush()
        sys.stderr.flush()
        si = file(self.stdin,'r')
        so = file(self.stdout,'a+')
        se = file(self.stderr,'a+',0)
        os.dup2(si.fileno(),sys.stdin.fileno())
        os.dup2(so.fileno(),sys.stdout.fileno())
        os.dup2(se.fileno(),sys.stderr.fileno())

    def delpid(self):
        os.remove(self.pidfile)

    def start(self):
        """ Start the daemon """

        # Check to see if running
        try:
            pf = file(self.pidfile,'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

        if pid:
            message = "pidfile {} already exists!".format(self.pidfile)
            sys.stderr.write(message)
            sys.exit(1)

        # Start
        self.daemonize()
        self.run()

    def stop(self):
        """ Stop the daemon """

        # Get pid from the pidfile
        try:
            pf = file(self.pidfile,'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

        if not pid:
            message = "pidfile {} does not exist!\n".format(self.pidfile)
            sys.stderr.write(message)
            return

        # Kill the daemon process
        try:
            while 1:
                os.kill(pid, SIGTERM)
                time.sleep(0.1)
        except OSError as e:
            err = str(e)
            if err.find("No such process") > 0:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
            else:
                print str(err)
                sys.exit(1)

    def restart(self):
        """ Restart """

        self.stop()
        self.start()

    def run(self):
        """ Must be replaced by child class """

        raise AssertionError("No run method in child class!")

class ColorIze(object):
    """ Allows colorizing (in available terminals)"""

    BLACK_ON_GREEN = '\x1b[1;30;42m'
    BLACK_ON_RED = '\x1b[0;30;41m'
    MAGENTA_ON_BLUE = '\x1b[1;35;44m'
    WHITE_ON_BLUE = '\x1b[5;37;44m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

    def __init__(self,val,opts):
        """ Takes the val, and wraps it in the passed opts """

        assert isinstance(opts,(list,tuple)), 'Invalid color option list!'

        retval = ''
        for opt in opts:
            retval += opt

        retval += '{}{}'.format(val,ColorIze.END)

        self.colorized = retval

        return
