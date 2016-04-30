import os
import mechanize
#import dns.resolver
import urlparse
from sys import argv

surl = argv[1] if 'http' in argv[1] else 'http://{0}'.format(argv[1])

#surl = argv[1]
#if 'http' not in surl:
#   surl = 'http://'+surl

urls = []
cachedDoms = set()

#cachedDoms = {}

br = mechanize.Browser()
br.set_handle_robots(False)
br.addheaders = [('User-agent', 'Firefox')]

def dig(domain):
   if domain in cachedDoms: return cachedDoms[domain]
   cachedDoms[domain]=socket.gethostbyname(domain)
   return address

   #if domain in cachedDoms:
      #return cachedDoms[domain]   
   #address = os.popen("dig +short "+domain).read()
   #cachedDoms[domain] = address 
   #return address

ip = dig(urlparse.urlparse(surl).hostname)

def getLinks(url):
   print "Scraping: "+url
   if 'http' not in url:
      url = 'http://'+url
   resp = br.open(url)
   for link in br.links():
      if link.absolute_url not in urls:
         dom = urlparse.urlparse(link.absolute_url).hostname
         if dom and  ip == dig(dom):
            urls.append(link.absolute_url)
            try:
               getLinks(link.absolute_url)

            except:
               print "ERROR: skipping "+url

getLinks(surl)
