'''
Craigslist Stocklmeir Rental home scrappy

Dependencies:
	BeautifulSoup
'''

import urllib2
import ConfigParser
import smtplib

from email.mime.text import MIMEText
from functools import wraps
from time import time
from bs4 import BeautifulSoup

def timed(f):
  @wraps(f)
  def wrapper(*args, **kwds):
    start = time()
    result = f(*args, **kwds)
    elapsed = time() - start
    print "%s took %d secs to finish" % (f.__name__, elapsed)
    return result
  return wrapper

class CrglistGlobals:
	'''
	Global constants for Crglist
	'''

	def CraigsMain(self):
		config_defaults = {'level':"1", "page_save_file": "/Users/srramasw/craigs.html"}
		config = ConfigParser.ConfigParser(config_defaults)
		config.read('config')
		
		self.EMAIL_SENDER = eval(config.get('Main', 'email_sender'))
		self.EMAIL_RECIPIENTS = eval(config.get('Main', 'email_recipients'))
		self.SMTP_HOST = eval(config.get('Main', 'smtphost'))
		self.SMTP_USER = eval(config.get('Main', 'smtpuser'))
		self.SMTP_PW = eval(config.get('Main', 'smtppw'))

		self.DEBUG = config.getint('Debug', 'level')
		self.PAGE_SAVE_FILE = config.get('Debug', 'page_save_file')

		print self.PAGE_SAVE_FILE

		print self.EMAIL_SENDER + " " + \
			self.EMAIL_RECIPIENTS + " " + \
			self.SMTP_USER + " " + \
			self.SMTP_PW + " " + \
			self.SMTP_HOST + " " + \
			str(self.DEBUG) + " " + \
			self.PAGE_SAVE_FILE


		c = CrglistDownloader(self)
		# TODO: change to use a decorator
		page_content = c.download(write_to_file=False)

		# lets get to the data, call the analyser
		ca = CrglistAnalyser(self)
		adlistings = ca.ListingCollector(page_content)
		# listings = ca.ListingCollectorFromFile(page_file=CrglistGlobals.PAGE_SAVE_FILE)

		print adlistings

		CraigsEmailer.sendemail(self, adlistings)

class CraigsEmailer:

	@staticmethod
	def sendemail(CG, adlistings):

		admsg = []
		for ad in adlistings: 
			adline = "Date: {date}, Title: {title}, City: {city}, Price: {price}\n".format(date=ad[0], title=ad[1], url=ad[2], price=ad[3], sqft=ad[4], city=ad[5])
			print "Adline " + adline
			admsg.append(adline)
			print "Admsg " + str(admsg)

		print "Emailer ...."
		email_body = ''.join(admsg)
		print email_body

		msg = MIMEText(email_body)
		
		# me == the sender's email address
		# you == the recipient's email address
		msg['Subject'] = 'CG Listings'
		msg['From'] = CG.EMAIL_SENDER
		msg['To'] = CG.EMAIL_RECIPIENTS


		print "Sending email via %s user %s pw %s sender %s, recv %s" % (CG.SMTP_HOST, CG.SMTP_USER, CG.SMTP_PW, CG.EMAIL_SENDER, CG.EMAIL_RECIPIENTS)

		print "start ssl"
		s = smtplib.SMTP_SSL(CG.SMTP_HOST)
		print "after ssl"
		s.login(CG.SMTP_USER, CG.SMTP_PW)
		print "after login"
		s.sendmail(CG.EMAIL_SENDER, [CG.EMAIL_RECIPIENTS], msg.as_string())
		print "after sendmail"
		s.quit()


class CrglistDownloader:
	'''
	Download / scrap data from Craigslist
	'''

	urls = ["http://sfbay.craigslist.org/search/apa/sby?query=cupertino+school&zoomToPosting=&minAsk=3000&maxAsk=4000&bedrooms=3&housing_type=&nh=32&nh=40&nh=44",
	        "http://sfbay.craigslist.com/"]

	def __init__ (self, cg):
		self.CG = cg

	@timed
	def download(self, write_to_file=False):
		''' 
		Download webpage to a buffer 
			- whole page in buffer for now; 
			- TODO: improve to do chunks reads 
		'''
		try:
			url = self.urls[0]
			print "Downloading...%s" % url

			req = urllib2.Request(url)
			page = urllib2.urlopen(req)
			if self.CG.DEBUG > 1:
				print page.info()

			print "Successfully connected...downloading..."
			

			# Yes, we are reading the whole page into one buffer;
			# TODO: memory in-efficient, fix it someday
			page_content = page.read()
			print "My debug is " + str(self.CG.DEBUG)
			if self.CG.DEBUG > 1:
				print page_content

			# Cleanup
			page.close()

			if write_to_file:
				page_file = self.CG.PAGE_SAVE_FILE
				print "writing to file %s" % page_file
				page_file = open(page_file, 'w')
				page_file.write(page_content)
				page_file.close()

			return page_content

		except urllib2.HTTPError as e:
			print e


class CrglistAnalyser:
	'''
	Analyze data grathered from Craigslist
	'''

	def __init__ (self, cg):
		self.CG = cg

	def ListingCollector(self, page_content):
		'''
		Take a raw page from rental listing with header, listing links and footer,
		return an dictionary of 
			{ link, date, adtext, price, bedrooms, sqft, city }
		'''

		print "Analyzing page content..."
		adlistings = []

		soup = BeautifulSoup(page_content)

		listing = soup.body.find_all('p')
		for ad in listing:
			if self.CG.DEBUG > 1:
				print "Ad: " + str(ad)
			elements = ad.contents

			'''
			Recipe:
				elements[5] = date, url link to ad, adtitle
				elements[7] = price, sqft, city
			'''
			if self.CG.DEBUG > 1:
				for elem in elements:
					print "  Elem: " + str(elem)

			date = elements[5].find("span", "date").contents
			adtitle = elements[5].a.get_text()
			url = elements[5].a['href']
			price = elements[7].find("span","price").contents
			sqft = elements[7].contents[2]
			city = elements[7].find("span", "pnr").contents[1].contents

			print "---------------------------"
			print "Date  " + repr(date)
			print "Title " + repr(adtitle)
			print "URL   " + repr(url)
			print "Price " + repr(price)
			print "SQFt  " + repr(sqft)
			print "City  " + repr(city)

			adlistings.append([repr(date), repr(adtitle), repr(url), repr(price), repr(sqft), repr(city)])

		print "Found %d listings" % len(adlistings)
		return adlistings


		
	def ListingCollectorFromFile(self, page_file):
		'''
		Take a raw page from rental listing with header, listing links and footer,
		return an dictionary of 
			{ link, date, adtext, price, bedrooms, sqft, city }
		'''

		if (None is page_file):
			# TODO: raise an exception
			pass

		print "Opening file " + page_file
		f = open(page_file, "r")
		page_content = f.read()
		f.close()
		self.ListingCollector(page_content)




'''
Invoker and Tester code
'''
if __name__ == '__main__':
	print "Starting..."
	cg = CrglistGlobals()
	cg.CraigsMain()

