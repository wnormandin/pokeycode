#!/usr/bin/env python
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
	Basic Social media bots
	Local module installations
	
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

def read_csv(fpath, delim='\t',qchar="'"):
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
	hgt_logger.debug('\t valid_date args : {}'.format(s))
	
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
class Color:
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

#****************************** Dialogs ********************************
#class InfoDialog(Gtk.Dialog):
	
	#global _icon_path

	#def __init__(self, ttl, msg, icpth=_icon_path):
		#Gtk.Dialog.__init__(self, ttl, None, 0,
			#(Gtk.STOCK_OK, Gtk.ResponseType.OK))
		#self.set_modal(True)

		#self.set_default_size(150, 100)
		
		#if icpth:
			#self.set_icon_from_file(icpth)

		#label = Gtk.Label(msg)

		#box = self.get_content_area()
		#box.add(label)
		#self.show_all()
		
#*****************************PokeyConfig*******************************

class PokeyConfig(object):
	'''Config Class Usage:

	1. Take any value you wish to allow to be configurable in config.dat

	2. Add a record in config.dat (format :  name%value%description)
	   *%-delimited, single-quote quotechar
	   
	3. Load the PokeyConfig Class in the module (pass the path to config.dat)

	4. Access the .check_attr([var name, value]) method in any location you
	   would use the variable
	   
	5. Example :

	   import data.utils as utils
	   
	   c = utils.BastilleConfig()
	   
	   for row in c.check_attr([c_var_name, c_default_value]):
			<do stuff>
			
		* Where c_var is a configurable variable
		** In usage, set default to False to test for attribute existence
		
	6. Functionality - the Class method check_attr will check the dictionary
	   containing the class members (excluding sytem '__' members).  If the
	   attribute exists in the dictionary, the attribute value is returned.
	   Otherwise, the default passed value is returned.
	'''
	
	def __init__(self,fpath):
		try:
			self.fpath = fpath
			self.vals = self.load_config()
			# Dynamically set class attributes from config
			for row in self.vals:
				setattr(self, row[0], [row[1],row[2]])
		except Exception as e:
			raise
			
	def __str__(self):
		#Prints all non-standard methods and attributes
		retval = ''
		for key, value in self.__dict__.items():
			if not key.startswith("__"):
				retval+='{}.{}={}\n'.format(type(self).__name__,key, value[0])
		return retval.strip('\n') # Strip the final \n
		
	def check_attr(self, val):
		if val[0] in self.__dict__.keys():
			return self.__dict__[val[0]][0]
		else:
			return val[1]
	
	# Saves config (overwrites) - Not yet implemented
	def write_config(self):
		try:
			with open(self.fpath, 'wb') as o:
				conf_dec(o, True)
				o.writelines(''.join(["'{}'\t'{}'\t'{}'".format((key, self.__dict__[key][0],
												self.__dict__[key][1]) for key in self.__dict__.keys())]))
				conf_dec(o)
		except Exception as e:
			raise
			
	def load_config(self):
		try:
			with open(self.fpath, 'rb') as c:
				return [row.rstrip().split('%') for row in c.readlines() if '#' not in row and row.strip() != '']
		except:
			raise
			return 1

#****************************PokeyLanguage******************************
#class PokeyLanguage(object):
	#""" The PokeyLanguage class takes vocabulary and grammar files and 
	#returns basic emulated conversation from a variety of PokeyBot
	#triggers.
	#"""
	#def __init__(self, vocabulary, grammar):
		#self.vocab = v = vocabulary
		#self.gramm = g = grammar
		
		#pass

#*******************************PokeyBot********************************
class PokeyBot(object):
	""" The PokeyBot class expects a PokeyConfig 'conf' to be passed
	containing the following :
		
		server
		channel
		name
		password
		friends
		debug
		mode
		
	As an alternative, these values can each be passed as keyword args
	if there is no conf included.
	"""

	def __init__(
				self, 
				**kwargs
				):
		
		if conf:
			self.populate_from_conf(conf)
		else:
			if server and channel and password:
				self.config = None
				self.server = server
				self.debug = debug
				self.channel = channel
				self.name = name
				self.password = password
				self.friends = friends
				self.mode = mode
			else:
				print 'Pokeybot could not initialize : missing parameter (server, channel, pass)'
				sys.exit(1)
				
		if not conf.channel.startswith('#'):
			self.channel = '#{}'.format(self.channel)
			
		if self.mode == 'silent':
			self.silent = True
		else:
			self.silent = False
			
		if self.mode != 'interactive':
			self.execute()
			
	def change_mode(self,mode):
		self.mode = mode
		if mode.lower() == 'silent':
			self.silent = True
		else:
			self.silent = False
			
	def populate_from_conf(c):
		self.config = conf
		self.server = conf.server
		self.debug = conf.debug
		self.channel = conf.channel
		self.name = conf.name
		self.password = conf.password
		self.friends = conf.friends
		self.mode = conf.mode
			
	def execute(self):
		
		self.connected = self.do_connect()
		time.sleep(0.15)
		self.join_channel(self.channel)
		
	def main_loop(self,d=False):
		
		v = self.vocab
		
		try:
			while True:
				data = self.irc.recv(4096).rstrip()
				print data
				if self.silent:
					if self.name in data and 'speak' in data:
						self.silent = False
						if d: print('>>> SILENT MODE OFF <<<')
						self.send_message(self.channel,'Who is ready for some annoyance!')
					elif data.startswith('PING'):
						if d: print('>>> PING RECEIVED <<<')
						self.ping(data.replace('PING :','').rstrip())
				elif len(data)==0:
					try:
						self.do_connect()
						self.join_channel(self.channel)
					except:
						break
				elif data.startswith('PING'):
					if d: print('>>> PING RECEIVED <<<')
					self.ping(data.replace('PING :','').rstrip())
				elif 'KICK' in data:
					time.sleep(random.randint(0,10))
					self.join_channel(self.channel)
				elif '{} help'.format(self.name) in data:
					self.send_message(self.channel, v.HELP)
				elif 'hello' in data and self.name in data :
					self.send_message(self.channel, v.GREET[random.randint(0,len(v.GREET)-1)])
				elif self.name in data and 'tell' in data and 'story' in data:
					msg = ''.join(['{}{}'.format(tmplt[0],plurals(tmplt[1][random.randint(0,len(tmplt[1])-1)],tmplt[2])[1]) for tmplt in v.STORY_TEMPLATE])
					msg+='\n'
					self.send_message(self.channel, msg)
				elif '{} silence'.format(self.name) in data and 'pokeybill' in data:
					self.send_message(self.channel,'Shutting up now, master')
					self.silent = True
					if d: print('>>> SILENT MODE ON <<<')
				elif '{} speak'.format(self.name) in data:
					if self.silent and 'pokeybill' in data:
						self.silent = False
						self.send_message(self.channel,'Thank you master, being quiet is difficult')
					else:
						self.send_message(self.channel, v.SPEAK[random.randint(0,len(v.SPEAK)-1)])
				elif '{} die'.format(self.name) in data:
					self.send_message(self.channel, v.DIE[random.randint(0,len(v.DIE)-1)])
					self.irc.send('QUIT\n')
					time.sleep(random.randint(0,10))
					self.do_connect()
					self.join_channel(self.channel)
				if random.randint(0,1000)%59==0:
					self.send_message(self.channel, v.RIDICULOUS_CLAIM[random.randint(0,len(v.RIDICULOUS_CLAIM)-1)])
				if random.randint(0,1000)%71==0:
					self.irc.send('TOPIC {} {}\n'.format(self.channel, 
												v.TOPICS[random.randint(0,len(v.TOPICS)-1)]))
												
					time.sleep(0.10)

		except (KeyboardInterrupt, SystemExit):
			self.irc.send('QUIT\n')
			if d: print('>>> EXIT DETECTED <<<')
			self.connected = False
		except:
			raise

	def do_connect(self):
		self.irc = irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			irc.connect((self.server, 6667))
			print irc.recv(4096)
			irc.send('PASS {}\n'.format(self.password))
			irc.send('NICK {}\n'.format(self.name))
			irc.send('USER {}\n'.format('{0} {0} {0} :Python IRC'.format(self.name)))
			resp = irc.recv(4096)
			print resp
			
			if 'PING' in resp:
				self.ping(resp.replace('PING :','').rstrip())
				print irc.recv(4096)
			
			return True
		except:
			raise
			return False
		
	def join_channel(self, c):
		self.irc.send('JOIN {}\n'.format(c))
		self.send_message(c, 'I am alive\n')
		
	def send_message(self, c, msg):
		out_msg = 'PRIVMSG {} :{}\n'.format(c,msg)
		self.irc.send(out_msg)
		print out_msg.rstrip()
		
	def ping(self, msg):
		self.irc.send('PONG :{}\n'.format(msg))
		print 'PONG'
		
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
						
