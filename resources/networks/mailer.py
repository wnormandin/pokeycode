#!/usr/local/bin/python2.7
# -*- coding: utf-8 -*-

import argparse
import smtplib
import time
import pdb

def parse_args():
    parser = argparse.ArgumentParser(
        prog='mailer.py',
        usage='%(prog)s OPTIONS -s [SERVER] -f [FROM] -t [TO] [LIST] -m "[MSG]"'
        )
    parser.add_argument(
                    '-v','--verbose',
                    help='Enable verbose output',
                    action='store_true'
                    )
    parser.add_argument(
                    '-l','--ssl',
                    action='store_true',
                    help='Use Secure SMTP over port 465'
                    )
    parser.add_argument(
                    '-p', '--port',
                    nargs = '?',
                    default = 25,
                    choices = [25,26,587,465],
                    type = int
                    )
    parser.add_argument('-s','--server',help='SMTP Server or IP',required=True)
    parser.add_argument('-f','--source',help='Source E-mail Address',required=True)
    # The TO argument returns a list (even if only 1 argument is present)
    parser.add_argument('-t','--to',nargs='+',help='Recipient List',required=True)
    parser.add_argument('-m','--message',nargs='?',help='Message body')
    return parser.parse_args()

class SMTPMessage():

    """ SMTP mailer class, takes header info as an argparse list """

    def __init__(self,args=None):
        self.message = None
        if args is not None:
            self.args = args
            self.args.smtp_pass = raw_input("SMTP Sender Password > ")
            self.execute()

    def execute(self):

        if self.args.smtp_port == 465:
            print '** Using smtplib.SMTP_SSL'
            conn_obj = smtplib.SMTP_SSL
        else:
            conn_obj = smtplib.SMTP

        server = conn_obj()
        debug = 1 if self.args.verbose else 0
        server.set_debuglevel(debug)

        try:
            server.connect(self.args.smtp_host, self.args.smtp_port)
            server.login(self.args.smtp_email, self.args.smtp_pass)
            ret = server.sendmail(
                                self.args.smtp_email,
                                self.args.alert_recipient,
                                self.build_message(self.message)
                                )
        except Exception as e:
            print '** Sendmail Failed!'
            print 'Error :\n{0}'.format(e)
        else:
            print '** Sendmail completed : {0}'.format(ret)
        finally:
            server.quit()

    def build_message(self,msg):
        if msg is None:
            frm = 'From: Python Mailer <{0}>'.format(self.args.smtp_email)
            to_list = [' <{0}>'.format(a) for a in self.args.alert_recipient]
            to = 'To:{0}'.format(','.join(to_list))
            sbj = 'Subject: Message send test {0}'.format(int(time.time()))
            ssl_str = 'n' if self.args.smtp_port==465 else ' <SECURE>'
            msg = 'This is a{0} SMTP mail test'.format(ssl_str)
            msg += '\n\nPlease disregard this message'
            return '\n'.join([frm,to,sbj,'',msg])
        else:
            return msg

if __name__=='__main__':
    args = parse_args()
    SMTPMessage(args)
