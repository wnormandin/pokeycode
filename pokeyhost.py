#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

# PokeyHost library file, the PokeyHost class collects information on the hosting environment
# and can be used to perform various monitoring tasks.  Meant to be the back-end library for
# the site_backups.py and site_alerts.py tools, and feeds data to the pokeydash.py CGI dashboard.

import subprocess
import cgitb; cgitb.enable()

import imp
fw = imp.load_source('PokeyWorks','/home1/wnrmndn/pokeyworks/pokeyworks.py')

class PokeyHost(object):
	""" The PokeyHost class collects information on the hosting environment
	and can be used to perform various monitoring tasks.  Meant to be the back-end library for
	the site_backups.py and site_alerts.py tools, and feeds data to the pokeydash.py CGI dashboard.
	"""
	
	def __init__(self):
		
		try:
			self.dom_list=[]
			self.subdomains=[]
			self.conf = fw.PokeyConfig(fw.resource_path(__file__,'pokeyhost.conf'))
			self.user = fw.shell_command('whoami')[0].strip()
			self.user_path = '{0}/{1}'.format(self.conf.cp_user_data[0],self.user)
			
			self.get_domain_list()
			for domain in self.dom_list:
				domain.populate_subdomains(self.subdomains)
				
			#self.php_info = self.get_php_info()	
			#self.web_info = self.get_webserver_info()
			#self.alerts = self.run_alerts()
		except:
			raise

			
	def __str__(self):
		retval = '[*] PokeyHost Environment Information :\n'
		retval += '\tcPanel Username : {0}\n'.format(self.user)
		retval += '\tUser Config Path : {0}\n'.format(self.user_path)
		retval += '[*] Hosted Domains :\n'
		for dom in self.dom_list:
			retval += '\t- Domain Name : {0}\n'.format(dom.domain)
			retval += '\t- Domain Type : {0}\n'.format(dom.dom_type)
			retval += '\t- cPanel SubDomain : {0}\n'.format(dom.cp_subdomain)
			retval += '\t- Config Path : {0}\n'.format(dom.dom_vhost_path)
			retval += '\t- Document Root : {0}\n'.format(dom.doc_root)
			retval += '\t- IP : {0}\n'.format(dom.ip)				
			retval += '\t- Subdomain details -\n'
			for sub in dom.subdomains:
				retval += '\t\tSubdomain : {0}\n'.format(sub.domain)
				retval += '\t\t\tDocument Root : {0}\n'.format(sub.doc_root)
				retval += '\t\t\tIP : {0}\n'.format(sub.ip)
				retval += '\t\t\tvHost Path : {0}\n'.format(sub.dom_vhost_path)
			retval += '[*] Next Domain\n'
				
		return retval.strip('[*] Next Domain\n') # Strip the final \n
	
	def get_domain_list(self):
		""" Reads the user's 'main' configuration file for domain and other information.
		Pulls doc root and other data from the domain configuration files. """
		
		# Read primary configuration file details
		with open('{0}/main'.format(self.user_path),'rb') as main_file:
			start_addons = False
			start_subs = False
			for row in main_file:
				if row.startswith('sub_domains:') or row.startswith('parked_domains:'):
					start_addons=False
				if row.startswith('main_domain:'):
					start_addons=False
					split_row = row.split()
					self.primary_dom=Domain(self,split_row[1],False,'primary')
					self.dom_list.append(self.primary_dom)
					self.homedir = self.primary_dom.homedir
				if row.startswith('addon_domains:'):
					start_addons=True
				if row.startswith('sub_domains:'):
					start_addons=False
					start_subs=True
					
				if start_addons and row.strip()!='addon_domains:':
					assert start_subs==False, 'Unexpected flag state : start_subs = True while start_addons = True'
					split_row = row.split()
					self.dom_list.append(Domain(self,split_row[0].replace(':',''),split_row[1],'addon'))
					
				if start_subs and row.strip()!='sub_domains:':
					assert start_addons==False, 'Unexpected flag state : start_addons = True while start_subs = True'
					self.subdomains.append(row.strip().split()[1])
					
class Domain(object):
	""" Base class to contain domain attributes """
	
	def __init__(self,host,dom,cp_subd,dom_type):
		self.domain = dom
		self.subdomains=[]
		self.cp_subdomain = cp_subd
		self.dom_type=dom_type
		self.host = host
		
		if self.dom_type=='primary':
			self.dom_vhost_path = '{0}/{1}'.format(host.user_path,self.domain)
		elif self.dom_type in ['addon','sub']:
			self.dom_vhost_path = '{0}/{1}'.format(host.user_path,self.cp_subdomain)
			
		with open(self.dom_vhost_path,'rb') as vhost:
			for line in vhost:
				if line.startswith('documentroot:'):
					self.doc_root = line.split()[1]
				if line.startswith('homedir:'):
					self.homedir = line.split()[1]
				if line.startswith('ip:'):
					self.ip = line.split()[1]

				
	def populate_subdomains(self,subdomains):
		for sub in subdomains:
			if sub.endswith(self.domain):
				self.subdomains.append(Domain(self.host,sub,sub,'sub'))
				
				
if __name__=="__main__":
	PokeyHost()
		
	