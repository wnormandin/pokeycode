#!/opt/python27
# -*- coding: utf-8 -*-

from pokeyworks import PokeyConfig
import pokeycode.resources.networks.mailer.SMTPMessage as SMTPMessage

# Scan e-mail directory for bouncebacks
# Store the messages identified as potential 
# bounces and e-mail to host

class MailMonitor():

    def __init__(self):
        self.cfg = PokeyConfig('mailmonitor.cfg',PokeyConfig.encoded)
        

    def find_suspects(self):

    def confirm_bouncebacks(self):

    def prepare_report(self):

    def send_report(self):

