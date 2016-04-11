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
