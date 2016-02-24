#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import cgi
import cgitb; cgitb.enable()
import imp
import os, os.path
from os import listdir
import sys
import time

fw = imp.load_source('PokeyWorks','/home1/wnrmndn/pokeyworks/pokeyworks.py')
backend = imp.load_source('PokeyHost','/home1/wnrmndn/pokeyhost/tools/pokeyhost.py')

CSS_PATH = fw.resource_path(__file__,'dash_style.css')

# Enable cgitb debugging messages

class PokeyDash(object):
	""" The PokeyDash class serves as the CGI interface for the PokeyHost toolset """
	
	def __init__(self):
		
		# Read details about the hosting environment
		self.host = backend.PokeyHost()
		
		# Pick up post vars
		self.load_post()
		self.status = "Waiting"
		
		# Parse get vars
		self.load_get()
		
		print DashLib.content_text_html		# Print the content type header
		print DashLib.dev_dash_header_open	# Opens <html>, prints <head>/<title>, opens <body>		
		print self.status_bar()			# Dynamic Status Bar function

		print self.left_form_bar()		# Fill Form Bar
		print self.information_section()	# Fill Information Section
		print self.alerts_section()		# FIll Alerts Section		
		
		print '</body>'
		print '</html>'
		
	def left_form_bar(self):
		retval = '\t<aside id="left_form_bar">\n'
		retval += self.gen_hosting_status()
		retval += self.gen_manage_form()
		retval += self.gen_odb_form()
		retval += '\t</aside>\n'
		
		return retval
		
	def alerts_section(self):
		retval = '\t<section id="alerts_section">\n'
		retval += '\t\t<b>Alerts Section</b><br>\n'
		retval += '\t\tNot Yet Implemented\n'
		retval += '\t</section>\n'
		
		return retval
			
	def load_post(self):
		""" Loads any POST values """
		
		# format : self.<var> = form.getvalue(<var>,<val if none>)
		
		form = cgi.FieldStorage()
		self.message = form.getvalue('message','(no message)')
		
		# On Demand Backup Form Options
		self.odb_input_path = form.getvalue('odb_input_path',False)
		self.odb_db_name = form.getvalue('odb_db_name',False)
		self.odb_destination = form.getvalue('odb_dest',False)
		
		# Management Form Options
		self.man_dom_selected = form.getvalue('dom_selected',False)
		self.man_subd_selected = form.getvalue('subd_selected',False)
		self.man_docroot_selected = form.getvalue('docroot_selected',False)
		self.man_dbs_selected  = form.getvalue('dbs_selected',False)
		
		# Detects if a subdomain value is selected and that value
		# is in the list for the currently selected domain.  If the
		# subdomain does not end with the selected domain, then the
		# selected domain can be assumed to have changed and the
		# subdomain is reset to "None"
		if self.man_subd_selected and self.man_subd_selected.endswith(self.man_dom_selected):
			for dom in [d for d in self.host.dom_list if d.domain==self.man_dom_selected]:
				for subd in dom.subdomains:
					if subd.domain==self.man_subd_selected:
						self.selected=subd
		elif self.man_dom_selected:
			for dom in [d for d in self.host.dom_list if d.domain==self.man_dom_selected]:
				self.selected = dom
		else:
			self.selected = False
		
	def information_section(self):
		""" Displays selected domain information if one is selected """
		
		if self.selected:
			#retval = '<div id="information_section">\n'
			retval = '<section id="information_section">\n'
			
			# Domain information section
			retval += '\t<b>Domain Information</b>\n'
			retval += '\t<fieldset><p>\n'
			retval += '\t\t<b>Domain Name:\t</b>{0:>30}<br>\n'.format(self.selected.domain)
			retval += '\t\t<b>Domain Type:\t</b>{0:>30}<br>\n'.format(self.selected.dom_type)
			retval += '\t\t<b>cPanel SubDomain:\t</b>{0:>30}<br>\n'.format(self.selected.cp_subdomain)
			retval += '\t\t<b>Config Path:\t</b>{0:>30}<br>\n'.format(self.selected.dom_vhost_path)
			retval += '\t\t<b>IP Address:\t</b>{0:>30}<br>\n'.format(self.selected.ip)
			retval += '\t</p></fieldset><br>\n'
			
			# Filesystem information section
			retval += '\t<b>Filesystem</b>\n'
			retval += '\t<fieldset><p>\n'
			retval += '\t\t<b>Document Root:\t</b>{0:>30}<br>\n'.format(self.selected.doc_root)
			
			# FIX THIS
			retval += '\t\t<b>Inode Count:\t</b>{0}<br>\n'.format(len([name for name in os.listdir(self.selected.doc_root) if os.path.isfile(os.path.join(self.selected.doc_root, name))]))
			
			# Fix the formatting of Disk usage output, convert to MB
			retval += '\t\t<b>Disk Usage:\t</b>{0:>30}<br>\n'.format(self.get_folder_size(self.selected.doc_root))
			retval += '\t\t<b>Percent Available:\t</b>{0:>30}<br>\n'.format('Not Yet Implemented')
			retval += '\t\t<b>Last Backup:\t</b>{0:>30}<br>\n'.format('Not Yet Implemented')
			retval += '\t\t<b>Backup Path:\t</b>{0:>30}<br>\n'.format('Not Yet Implemented')
			retval += '\t</p></fieldset><br>\n'
			
			# DNS information section
			retval += '\t<b>DNS</b>\n'
			retval += '\t<fieldset><p>\n'
			retval += '\t\t<b>IP Address:\t</b>{0}<br>\n'.format(self.selected.ip)
			retval += '\t\t<b>Propagation:\t</b>{0}<br>\n'.format('Not Yet Implemented')
			retval += '\t\t<b>Nameservers:\t</b>{0}<br>\n'.format('Not Yet Implemented')
			retval += '\t\t<b>A Record:\t</b>{0}<br>\n'.format('Not Yet Implemented')
			retval += '\t</p></fieldset><br>\n'
			
			# Database information section
			retval += '\t<b>Databases</b>\n'
			retval += '\t<fieldset><p>\n'
			retval += '\t\t<b>Database List:\t</b>{0}<br>\n'.format('Not Yet Implemented')
			retval += '\t\t<b>Access Test:\t</b>{0}<br>\n'.format('Not Yet Implemented')
			retval += '\t\t<b>Record Counts:\t</b>{0}<br>\n'.format('Not Yet Implemented')
			#retval += '\t\t<b>OPTION:\t</b>{0}<br>\n'.format('Not Yet Implemented')
			#retval += '\t\t<b>OPTION:\t</b>{0}<br>\n'.format('Not Yet Implemented')
			retval += '\t</p></fieldset><br>\n'
			
			retval += '</section>'
			#retval += '</div>'
			
			return retval
		else:
			return ''
			
	def count_inodes(self,path):
		""" Counts the inodes at the passed path (recusrively) """
		
		return sum(1 for entry in listdir(path))
		
		#return len([name for name in os.listdir(path) if os.path.isfile(os.path.join(path, name))])
		
	def populate_doc_root_selected(self):
		""" Sets the displayed document root based on the selected domain/subdomain """
		
		if self.man_dom_selected:
			for dom in self.host.dom_list:
				if dom.domain==self.man_dom_selected:
					self.selected = dom
					self.man_docroot_selected = dom.doc_root
					this_dom=dom
					
		if self.man_subd_selected and self.man_subd_selected!='None':
			for sub in this_dom.subdomains:
				if sub.domain==self.man_subd_selected:
					self.selected = sub
					self.man_docroot_selected = sub.doc_root
		
					
		if self.man_docroot_selected and self.man_docroot_selected!='None Selected':
			return '\t<b>Doc Root</b><br><input size="35" type="text" name="man_docroot_selected" value="{0}"><br>\n'.format(self.man_docroot_selected)
		else:		
			return '\t<b>Doc Root</b><br><input size="35" type="text" name="man_docroot_selected" value="None Selected"><br>\n'
		
	def populate_domain_combo(self,sub=False):
		""" Populates the domain/subdomain combo boxes in the management area """
		
		if self.man_dom_selected:
			for dmn in self.host.dom_list:
				if dmn.domain==self.man_dom_selected:
					dom=dmn
		else:
			dom=False

		combo_opts = []
		opt_prefix = '\t\t<option value='
		opt_suffix = '</option>\n'
		
		if sub and dom:
			# If the domain is selected, populate the subdomain selection list
			# if no subdomain is selected, select "None" by default
			opt_value = 'none'
			opt_display = 'None'
			if not self.man_subd_selected:
				opt_selected = ' selected>'
			else:
				opt_selected = '>'
				
			# Add the "None" option to the list
			combo_opts.append([opt_prefix,opt_value,opt_selected,opt_display,opt_suffix])	
			
			for sub in dom.subdomains:
				opt_display=opt_value=sub.domain
				if self.man_subd_selected:
					if sub.domain==self.man_subd_selected:
						opt_selected=' selected>'
					else:
						opt_selected='>'
				else:
					opt_selected='>'
				combo_opts.append([opt_prefix,opt_value,opt_selected,opt_display,opt_suffix])
		else:
			# Add primary and addon domains, select the primary domain by default
			for dom in self.host.dom_list:
				opt_display=opt_value=dom.domain
				# If no domain is selected, select the primary domain by default
				if not self.man_dom_selected:
					if dom.dom_type=='primary':
						# Set the attribute so the subdomain list will populate
						self.man_dom_selected=dom.domain
						opt_selected=' selected>'
					else:
						opt_selected='>'
				else:
					if dom.domain==self.man_dom_selected:
						opt_selected=' selected>'
					else:
						opt_selected='>'
						
				combo_opts.append([opt_prefix,opt_value,opt_selected,opt_display,opt_suffix])
				
		return ''.join([''.join(row) for row in combo_opts])
		
	def gen_manage_form(self):
		""" Generates the domain/subdomain management form """
		
		retval = '\t<form method="post">\n\t<fieldset>\n'	# Open form/fieldset tags
		retval += '\t<b>Manage A Domain<p>Domain<br></b>\n'			# Form title
		retval += '\t<select name="dom_selected">\n'		# Open dom combobox tag
		retval += self.populate_domain_combo()			# Fill the options
		retval += '\t</select></p>\n'				# Close combobox tag
		retval += '\t<p><b>Subdomain Selection</b><br>\n'
		retval += '\t<select name="subd_selected">\n'		# Open subd combobox tag
		retval += self.populate_domain_combo(sub=True)		# Fill the options
		retval += '\t</select></p>\n'				# Close combobox tag
		
		retval += '\t<button type="submit" value="Submit">Select</button>\n'
		retval += '\t<button type="reset" value="Reset">Clear Selection</button>\n'
		retval += '\t</fieldset>\n'
		retval += '</form>'
		
		return retval
		
	def get_folder_size(self,folder):
		total_size = os.path.getsize(folder)
		for item in os.listdir(folder):
			itempath = os.path.join(folder, item)
			if os.path.isfile(itempath):
			    total_size += os.path.getsize(itempath)
			elif os.path.isdir(itempath):
			    total_size += self.get_folder_size(itempath)
		return total_size
	    
	def gen_hosting_status(self):
		""" Shows general hosting information (inodes/disk usage by top level dir, etc) """
	    
		retval = '<p><fieldset><p>\n'
		retval += '\t\t<b>Primary Domain:</b>\n'
		retval += '\t\t{0}\n'.format(self.host.primary_dom.domain)
		retval += '\t</p><p><table><td>\n'
		retval += '\t\t<table class="host_info">\n'
		retval += '\t\t\t<tr>\n'
		retval += '\t\t\t\t<th align="left"><b>Location</b></th>\n'
		retval += '\t\t\t\t<th align="right"><b>Inodes</b></th>\n'
		retval += '\t\t\t\t<th align="right"><b>Disk(Mb)</b></th>\n'
		retval += '\t\t\t</tr>\n'
		
		# Generate from this list for now, make a dynamic list in future
		# Isolating largest users of space/inodes by dir
		
		h = self.host.homedir
		for pth in ['{0}/'.format(h),'{0}/mail/'.format(h),'{0}/public_html/'.format(h)]:
			retval += '\t\t\t\t<tr>\n<td>{0}</td>\n<td align="right">{1}</td>\n<td align="right">{2}</td>\n</tr>\n'.format(
						pth,self.count_inodes(pth)*1.,self.get_folder_size(pth)/1000000)
		
		retval += '\t\t</table>\n\t\t</td>\n\t\t<td align="top" class="dash_menu" width="35%">\n'
		retval += '\t\t\t<img class="resize" src="resources/img/cactus_logo_bevel.png">\n'
		retval += '\t\t\t\t<a href="pokeydash.py"> Reload PokeyDash</a><br>\n'
		retval += '\t\t\t\t<a target="_blank" href="https://pokeybill.us"> pokeybill.us</a><br>\n'
		retval += '\t\t\t\t<br><br>Report bugs to:<br><a href=mailto:support@pokeybill.us>support@pokeybill.us</a>\n'
		retval += '\t\t</td>\n'
		retval += '\t\t</table></p>\n</fieldset></p>\n'  
		
		return retval
		
	def gen_odb_form(self):
		""" Generates the On-Demand Backup Form """
		
		retval = '<form class="odb" method="post">\n'
		retval += '\t<fieldset>\n'
		retval += '\t\t<b>Run an On-Demand Backup</b>\n'
		retval += '\t\t<p><b>Enter a directory path:</b><br>\n'
		
		if self.selected:
			retval += '\t\t<input size="35" type="text" name="odb_input_path" value="{0}"></p>'.format(self.selected.doc_root)
		else:
			retval += '\t\t<input size="35" type="text" name="odb_input_path" value="~/public_html"></p>'
		
		retval += '\t\t<p><b>Database(s)</b><br>\nComma-Separated List<br>\n'	
		retval += '\t\t<input size="35" type="text" name="obd_db_name" value="database name"></p>\n'
		retval += '\t\t<p><b>Destination</b><br>\n'
		retval += '\t\t<input size="35" type="text" name="odb_destination" value="{0}"></p>\n'.format(fw.resource_path(backend.__file__,self.host.conf.def_dest[0]))
		retval += '\t\t<p><b>Backup Name</b><br>\n'
		retval += '\t\t<input size="35" type="text" name="odb_file_name" value="{0}"></p>\n'.format(fw.resource_path(backend.__file__,self.host.conf.def_archive[0]))
		retval += '\t\t<input type="submit" value="Submit">\n'
		retval += '\t</fieldset>\n</form>\n</p>'
		
		return retval
		
	def load_get(self):
		""" Parses the GET content """
		pass
		
	def status_bar(self):
		""" Builds the status bar code placed in the Nav section """
		
		status_bar_val='<nav><div id="status_bar"><b>Status:</b> {0}'.format(self.status)
		
		if self.odb_input_path!=False and self.odb_input_path!='site document root':
			status_bar_val += ' | <b>Last Directory Backed Up:</b> {0}'.format(self.odb_input_path)
		if self.odb_db_name!=False and self.odb_db_name !='database name':
			status_bar_val += ' | <b>Last Database Backed Up:</b> {0}'.format(self.odb_db_name)
		
		status_bar_val += '</div></nav>'
			
		return status_bar_val
		
class PropagationTest(object):
	""" Takes the passed domain and runs various propagation tests """
	
	# List of servers to test from (may need to add to config later
	# to allow easy updates by the user)
	srv_list = [
		['Poland', '213.25.129.35'],
		['Indonesia',  '203.29.26.248'],
		['US', '216.218.184.19', '76.12.242.28'],
		['Australia', '203.59.9.223'],
		['Brazil', '177.135.144.210'],
		['Italy', '88.86.172.11'],
		['India',  '182.71.113.34'],
		['Nigeria', '41.58.157.70'],
		['Egypt', '41.41.107.38'],
		['UK', '109.228.25.69', '80.195.168.42'],
		['Google', '8.8.8.8']
		]
		
	def __init__(self,dom):
		
		self.domain = dom
		
		
	
		
class DashLib(object):
	# Library containing HTML snippets for PokeyDash
	# Maintain any logic-driven generators in the PokeyDash class
	
	content_text_html = "Content-type: text/html\n"
	
	close_body_html = "</body></html>"
	
	default_footer = "<footer></footer>"

	dev_dash_header_open = """
<html lang="en-us">
<head>
<title>PokeyDash</title>
<link rel="stylesheet" type="text/css" href="dash_style.css">
</head>
<body>
				"""
		
if  __name__ == '__main__':
	PokeyDash()