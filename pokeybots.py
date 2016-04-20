#!/usr/bin/env python2.7

import sys, os
import random
from twython import Twython, TwythonError
from pokeyworks import resource_path

APP_KEY = "nVJaVOPZGer4E65HSmDAzjswQ"
APP_SECRET = "MBcOPekSomIVibUIvkpwCoZM7Cn872TjWcrSQ5887pZA2LquAL"
OAUTH = "3840506773-XpG893az9BthEgiEIjysgIpakdVBACS3nqcdXgv"
OAUTH_SECRET = "16X55Yd48QYMLHofNH00WXGwO1gFospfyterx4Ed2ScYi"

class PokeyTwit():

    def __init__(self):

        try:
            print "Initializing twitter bot"
            self.twitter = Twython(APP_KEY, APP_SECRET,
                                    OAUTH, OAUTH_SECRET)

            print "Verifying credentials"
            self.twitter.verify_credentials()

            while True:
                msg = self.get_message().rstrip()
                if len(msg)!=0 and len(msg) < 140:
                    break

            print msg
            print "length: {}".format(len(msg))
            self.twitter.update_status(status=msg)
            msg=''
            self.exit_status=0

        except TwythonError:
            self.exit_status=1

    def get_timeline(self):
        try:
            self.timeline = self.twitter.get_home_timeline()
        except:
            raise

    def get_message(self):
        with open(resource_path(os.path.realpath(__file__),"resources/twit_lib.txt"), 'rb') as txt:
            twit_list = txt.readlines()

        line_stops=[]
        for idx, val in enumerate(twit_list):
            if val.rstrip()=='':
                line_stops.append(idx)

        row = random.randint(line_stops[0],len(line_stops))
        msg = ''
        while twit_list[row].rstrip() != '':
            msg += twit_list[row]
            msg += ' '
            row += 1

        return msg
        
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
