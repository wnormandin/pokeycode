#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import tarfile
import os,os.path 
import sys
import time
import logging
import subprocess
import imp

APP_START = time.time() # .clock() unavailable on 2.6?

fw = imp.load_source('PokeyWorks','/home1/wnrmndn/pokeyworks/pokeyworks.py')

# Check for module dependencies (non-standard modules starting @v2.6)
try:
	import argparse
except:
	argparse_loaded=False
else:
	argparse_loaded=True

try:
	import MySQLdb
except:
	mysqldb_loaded=False
else:
	mysqldb_loaded=True
	
def pre_exec():
	# PokeyWorks.install_module() installs a local copy using
	# easy_install and adds the ./includes dir to $PYTHONPATH
	missing = [m[1] for m in [(mysqldb_loaded,'MySQLdb'),(argparse_loaded,'argparse')] if not m[0]]
	
	for m in missing:
		print 'Error importing module {0}'.format(m)
		
		try:
			fw.install_module(fw.resource_path(__file__,'./includes'),m)
		except:
			print 'Unable to install {0}!  Exiting'.format(m)
			sys.exit(1)
			
		# Test module availability
		if m=='argparse':
			try:
				import argparse
			except:
				print 'Unable to load module argparse!  Exiting.'
				sys.exit(1)
		if m=='MySQLdb':
			try:
				import MySQLdb
			except:
				print 'Unable to load module MySQLdb!  Exiting.'
				sys.exit(1)

# Set Config File Path
CONFIG_PATH = './pokeyhost.conf' # Default application conf path

class BackupApplication(object):
	"""Application Class for on-demand and automated file/db backups
	
	Allows for easy automation of backup routines - will backup the 
	specified folder and all sub-directories, and/or export	the passed
	MySQL DB.  
	
	Command Format :
	
	python site_backups.py -[v|l] -c COMPRESSION -f FILE -d DATABASE DESTINATION
		-v = Verbose flag, for debugging output
		-l = Logging flag, enable logging for this run
		-f OR -d is required
		If no DESTINATION is specified, defaults to conf.def_dest
		
	Class Mode :
	
	As an alternative, the BackupApplication class can be instantiated in a variable
	using the following as a guideline :
	
	 from <path to your install>.site_backups import BackupApplication
	
	 conf_path = <path_to_your_config_file>  # Defaults to ./pokeyhost.conf
	 auto_exec = False
	
	 app = BackupApplication(auto_exec,conf_path)
	 
	 if app.do_execute() == True:	# Runs with the current parameters
	 	print 'Execution completed'
	 	app.application_end() 	# Optional application end output
	 else:
	 	print 'Execution failed'
	 	print sys.exc_info
	"""
	
	def __init__(self,auto_exec=False,conf=CONFIG_PATH):
		"""Load arguments, config, and enter the selected mode"""
		
		self.conf_path = conf
		self.auto_exec = auto_exec
		self.fpath = False
		self.dbs = False
		self.paused = False
		self.paused_time = 0.0 
		self.paused_start = 0.0
		self.file_list=[]
		
		# Detect initial logging level from command line argument list
		if '-l' in sys.argv or '--log' in sys.argv or '-t' in sys.argv or '--test' in sys.argv:
			start_level = logging.DEBUG
		elif '-c' in sys.argv or '--console' in sys.argv:
			start_level = logging.INFO
		else:
			start_level = logging.ERROR
			
		if '-v' in sys.argv or '--verbose' in sys.argv:
			self.verbose = True
		else:
			self.verbose = False
		
		# Initialize logger
		self.logger = fw.setup_logger('app_logger',start_level)
		self.logger.info("[*] Application Spawned")
		self.logger.info("[*] Logger Spawned")
		
		# Pre-run checks
		self.logger.info("[*] Pre-Run Checks")
		self.pre_run()
		
		# Set up command line parser and options
		self.parser = argparse.ArgumentParser()
		self.parser.add_argument("-c", "--console", help="enable console output",
							action="store_true")
		self.parser.add_argument("-l", "--log", help="enable output logging to log.txt",
							action="store_true")
		self.parser.add_argument("-t", "--test", help="ignores other arguments and runs diagnostic test",
							action="store_true")
		self.parser.add_argument("-v", "--verbose", help="verbose option and file listing",
							action="store_true")
		self.parser.add_argument("-f", '--folder', help="specify a folder to archive")
		self.parser.add_argument("-d", '--db', help="specify a database to archive")
		self.parser.add_argument("destination", help="specify a destination folder",
							default='', nargs='?')
		
		# Begin application load
		self.app_load_start = time.time() # .clock unavailable on 2.6?
		self.logger.info("[*] Loading Application")

		self.load_config(self.conf_path)
		self.parse_args()
			
		if self.test_mode:
			self.test_load()
		else:
			self.logger.info("[*] Application Loaded")
			self.logger.debug("\tTook {0:8.5f} seconds".format(time.time()-self.app_load_start))
			
		if auto_exec == True:

			self.logger.info("[*] Executing")
			self.do_execute()
			self.application_end()
			
	def test_load(self):
		""" Prepare test for execution """
		
		if isinstance(self.conf.db_names[0],basestring):
			test_db = self.conf.db_names[0]
		else:
			test_db = self.conf.db_names[0][0]
		
		mysql_tests = ["SELECT VERSION();",
				"SHOW SESSION STATUS;",
				"SHOW TABLES FROM {0};".format(test_db)
				]
		db_results = []
		
		self.logger.debug("[*] *** TEST MODE ENGAGED ***")
			
		# Optional test name
		self.test_name = self.user_input('\t> Enter name for this test (Enter to skip) : ')
		
		if self.test_name == '':
			self.test_name = 'Unnamed Test'
		self.logger.debug('\tTest name : {0}'.format(self.test_name))
		
		if self.user_input('\t> Verbose output? (y/n) : ').upper()=='Y':
			self.verbose=True
		else:
			self.verbose=False
			
		# Test database connectivity
		self.logger.info('\t*** Database test')
		
		success_count=0
		
		for test in mysql_tests:
			res = self.do_db_query(test_db,test)
			if len(res) > 0:
				self.logger.info('\t*** Test succeeded')
				success_count+=1
			db_results.extend(res)
			
		self.fpath = fw.resource_path(__file__,'./includes/test_dir')
		self.dest = fw.resource_path(__file__,'./tmp')
		
		# Write database output
		db_outpath = '{0}{1}'.format(self.dest,'/_DB_TEST_OUPUT.TXT')
		self.logger.debug('\tWriting database test info to {0}'.format(db_outpath))
		with open(db_outpath,'wb') as o:
			for row in db_results: 
			 	try:
			 		outp = '{0:<45}{1:<25}\n'.format(*row)
				except IndexError:
					outp = '{0:<70}\n'.format(row[0])
				if self.verbose: self.logger.debug('\t{0}'.format(outp.rstrip()))
				o.write(outp)
				
		# If test was successful, proceed with database backup
		if success_count==3:
			self.dbs = self.conf.db_names[0]
				
		# Print diagnostic test file paths
		self.logger.info('\t*** File backup test')
		self.logger.info('\tBacking up pokeyhost/resources/test_dir to pokeyhost/tmp')
		self.logger.info("\tPath = {0}".format(self.fpath))
		self.logger.info("\tDestination = {0}".format(self.dest))
			
	def do_db_query(self,database,sql):
		""" Create the MySQLdb connection, execute SQL, and return the result """
		start = time.time()
		
		self.logger.info('[*] Database query')
		
		try:
			if self.verbose:
				log_msg = "\tConnecting...\n\tHost: {0}\n\tUser: {1}\n\tDatabase: {1}".format(
						self.conf.db_host[0],
						self.conf.db_user[0],
						database
						)
				self.logger.info(log_msg)
								
			dbcon = MySQLdb.connect(
						self.conf.db_host[0],
						self.conf.db_user[0],
						self.conf.db_password[0],
						database
						)
			cursor = dbcon.cursor()
			
			self.logger.debug('\tSQL = {0}'.format(sql))
			cursor.execute(sql)
			results = cursor.fetchall()
			dbcon.close()
			self.logger.debug('\tReturned {0} rows'.format(len(results)))
		except:
			raise
			# In case of database error, rollback the changes
			if dbcon:
				dbcon.rollback()
		else:
			self.logger.debug('\tDatabase operation took {0:8.5f} seconds'.format((time.time()-start)))
			return results
			
	def do_db_archive(self):
		""" Execute the requested database archive """
		
		self.logger.info('[*] Database Backup')
		
		if self.dbs:
			databases = self.dbs
		else:
			databases = self.conf.db_names[0]
			
		self.logger.info('\tDatabase : {0}'.format(databases))
		
		opath = '{0}/{1}.sql'.format('tmp',databases)
		
		cmd = 'mysqldump'
		cmd += ' --user={0}'.format(self.conf.db_user[0])
		cmd += ' --password={0}'.format(self.conf.db_password[0])
		cmd += ' --result-file={0}'.format(opath)
		cmd += ' --port={0}'.format(self.conf.db_port[0])
		cmd += ' --verbose'
		
		self.logger.debug('\tTemp file path : {0}'.format(opath))
		
		if self.conf.db_host[0]!='localhost':
			cmd += ' --host={0}'.format(self.conf.db_host[0])
			
		cmd += ' --databases'
		
		# Using the evil isinstance! basestring to catch multiple encodings
		if isinstance(self.dbs,basestring):
			cmd += ' {0}'.format(self.dbs)
		else:
			for db in databases:
				cmd += ' {0}'.format(db)
			
		try:
			# shell=false to avoid shell injection						
			p = subprocess.Popen(
						cmd.split(),
						shell=False,
						stderr=subprocess.PIPE,
						stdout=subprocess.PIPE
						)
						
			outp = p.communicate()[0]
		except:
			self.logger.debug('Output : {0}'.format(outp))
			ip = raw_input('\t> Database backup failed!  Proceed? (y=yes) :')
			if ip.upper()!='Y':
				self.application_end()
		
		else:
			self.logger.info('\tDatabase backup succeeded!')
			self.file_list.append(fw.resource_path(__file__,opath))
			self.logger.debug('\tAdded {0} to the archive file list'.format(opath))			
			
	def application_end(self):
		""" Termination debugging and other output """
			
		self.logger.info("[*] Application Ending")
		self.logger.debug("\tExecuted : {0:8.5f} seconds".format((time.time()-APP_START)-self.paused_time))
		self.logger.debug("\tPaused   : {0:8.5f} seconds".format(self.paused_time))
		self.logger.debug("\tExisted  : {0:8.5f} seconds".format(time.time()-APP_START))
		sys.exit(0)
			
		
	def user_input(self,prompt):
		""" Function to automatically pause when user input is required, returns the input """
		
		# Time pause while awaiting user input
		self.toggle_pause()
		assert self.paused==True, 'Unexpected pause state : {0}'.format(self.paused)
		
		# Optional test name
		retval = raw_input(prompt)

		# End pause
		self.toggle_pause()
		assert self.paused==False, 'Unexpected pause state : {0}'.format(self.paused)
		
		return retval
		
		
	def toggle_pause(self):
		""" Toggles paused status for execution time calculation """
		if self.paused==True:
			self.paused_time+=time.time()-self.paused_start
			self.paused = False
		else:
			self.paused_start=time.time()
			self.paused = True
		
	def do_execute(self):
		""" Executes the appropriate actions """
		start = time.time() # .clock unavailable on 2.6?
		
		try:
		
			# Execute archive
			if self.dbs:
				self.do_db_archive()
			if self.fpath:
				self.do_file_archive()
				
			# Run post-execution validation
			self.after_execution_check()
			return True
			
		except:
			if self.auto_exec == True:
				raise
			return False
		
		self.logger.info("[*] Execution Ending")
		self.logger.debug("\tTook {0:8.5f} seconds".format(time.time()-start))
			
	def load_config(self,cpath):
		""" Loads the configuration from the passed file path """
		start = time.time() # .clock unavailable on 2.6?
		self.logger.info('[*] Loading Configuration from {0}'.format(cpath))
		
		# Load config from the cpath parameter
		self.conf = fw.PokeyConfig(CONFIG_PATH)
		
		# Print the values loaded
		if self.verbose==True:
			for item in self.conf.vals:
				self.logger.info('\t{0:<15}=\t{1:<20}\t{2:<30}'.format(*item))
		else:	
			self.logger.info('\tSkipping verbose config output')
			self.logger.info('\tLoaded {0} options'.format(len(self.conf.vals)))
			
		self.logger.debug('\tTook {0:8.5f} seconds'.format(time.time()-start*1))
		
	def parse_args(self):
		"""Parse command line arguments and set member variables"""
		start = time.time() # .clock unavailable on 2.6?
		args = self.parser.parse_args()

		self.logger.info("[*] Parsing Arguments")
		
		self.test_mode=args.test
		
		# If verbose, enable console logger.  If logging enabled, set
		# level to logging.DEBUG to enable file logger.  Option l forces
		# option v.  Uses PokeyWorks.fw.setup_logger()
		if args.console: 
			self.logger.level = logging.INFO
			self.logger.info("\tConsole Mode Enabled")
		elif args.log or self.test_mode: 
			self.logger.level = logging.DEBUG
			self.logger.info("\tLogging Mode Enabled")
			self.logger.debug("\tself.logger.level = logging.DEBUG")
		else: self.logger.level = logging.ERROR
		
		if not self.test_mode and self.auto_exec==True:
		
			# Handle file and database specifications, destination
			if args.folder or args.db:
				if args.folder:
					self.fpath = args.folder
					self.logger.info("\tPath = {0}".format(self.fpath))
				if args.db:
					self.dbs = args.db
					self.logger.info("\tDatabase = {0}".format(self.dbs))
				if args.destination:
					self.dest = args.destination
				else:
					self.logger.warning('\tNo DESTINATION specified, using default')
					self.dest = self.conf.def_dest[0]
				
				self.logger.info("\tDestination = {0}".format(self.dest))
				
			else:
				# Print message and exit if required options are missing
				self.logger.error('\tFolder (-f/--folder) or Database (-d/--db) must be specified')
				sys.exit(1)
			
		self.logger.debug("\tArguments parsed")
		self.logger.debug("\tTook {0:8.5f} seconds".format(time.time()-start)) 
		
	def do_file_archive(self):
		""" Execute the requested file archive operation (v is optional verbosity flag)"""
		
		start = time.time() # .clock unavailable on 2.6?
		self.logger.info("[*] Archiving Files")
		self.logger.debug("\tCompression : {0}".format(self.conf.comp[0]))
		
		# Set archive destination path
		self.file_archive = '{0}/{1}'.format(self.dest,self.conf.def_archive[0])
		
		# Set the file extension based on compression type
		if self.conf.comp[0] == 'w:gz':
			file_ext = '.tar.gz'
		elif self.conf.comp[0] == 'w:bz2':
			file_ext = '.tar.bz2'
		else:
			file_ext = '.tar'
		
		self.file_archive += file_ext
		self.logger.debug("\tArchive path : {0}".format(self.file_archive))
		
		self.logger.debug('\tPopulating file list')
		self.populate_file_list()
		
		# Open the tar archive with the specified compression and mode
		out = tarfile.open(self.file_archive, self.conf.comp[0])
		
		# Handle output verbosity appropriately
		if self.verbose: 
			self.logger.info("\tFiles to Archive")
		else:
			self.logger.info("\tSkipping verbose listing")
			
		ctr = 1 		# Archive item counter
		#print self.file_list
		for f in self.file_list:
			try:
				out.add(f[1],arcname=f[0])
				if self.verbose: self.logger.info("\t{0:>6} {1}".format(ctr,f[0]))
				ctr+=1
			except:
				self.logger.error('\tCould not add file "{0}" to the archive, continuing'.format(f))
				continue
				
		if not self.verbose: self.logger.info("\tArchived {0} files".format(ctr))
		out.close()
					
	def populate_file_list(self):
		""" Populates self.file_list from self.fpath """

		try:
			self.logger.debug('\t\tReading {0}'.format(fw.resource_path(__file__,self.fpath)))
			for f in os.listdir(self.fpath):
				self.file_list.append([f,fw.resource_path(__file__,'{0}/{1}'.format(self.fpath,f))])
		except:
			raise
			
	def after_execution_check(self):
		""" Compare archive(s) to initial values """
		if self.fpath:
			self.do_file_check()
		if self.dbs:
			self.do_db_check()
			
	def do_file_check(self):
		""" Post Execution file check """
		
	def do_db_check(self):
		""" Post Execution database check """
			
	def pre_run(self):
		""" Pre-Run checks and routines """
		
		start = time.time() # .clock unavailable on 2.6?
		
		# Check for dependent folders
		folder_list = ['../includes','../tmp']
		
		for fld in folder_list:
			fld_path=fw.resource_path(__file__,fld)
			
			self.logger.debug('\tChecking {0}'.format(fld_path))
			
			try:
				fw.mkdir(fld_path)
			except:
				raise
				#print 'Unable to stat {0}!  Please czech your install paths!'.format(fld_path)
				#sys.exit(1)
			
		# Disk usage check (for execution dir, will check destination later)
		self.logger.debug('\tChecking execution partition usage')
		
		try:
			df = subprocess.Popen(["df", os.path.realpath(__file__)], stdout=subprocess.PIPE)
			output = df.communicate()[0]
		except Exception as e:
			# print 'Disk usage check failed! Error : {0}'.format(e)
			self.logger.warning('\tDisk usage check failed!')
			raise
		else:
			device,size,used,available,percent,mountpoint = output.split("\n")[1].split()
			
			if int(percent[:-1])<25:
				self.logger.warning('\tWarning!  Available space on current partition is {0}!'.format(percent))
			
			self.logger.debug('\t{0} : {2}/{1}kb used : {3}kb available ({4}) : mountpoint={5}'.format(device,long(size,10)/1024,long(used,10)/1024,long(available,10)/1024,percent,mountpoint))
		
		self.logger.info('\tPre-Run checks completed')
		self.logger.debug('\tTook {0:8.5f} seconds'.format(time.time()-start))
		
		# Databases connection test
		#try:
			
		#except:
			
if __name__=='__main__':
	try:
		BackupApplication(auto_exec=True)
	except (KeyboardInterrupt, SystemExit):
		sys.exit(0)
	except:
		raise