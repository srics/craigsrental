'''
Craigslist Stocklmeir Rental home scrappy

Dependencies:
	BeautifulSoup
'''

import urllib2
import ConfigParser
import time

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from functools import wraps
from bs4 import BeautifulSoup

def timed(f):
  @wraps(f)
  def wrapper(*args, **kwds):
    start = time.time()
    result = f(*args, **kwds)
    elapsed = time.time() - start
    print "%s took %d secs to finish" % (f.__name__, elapsed)
    return result
  return wrapper

class CrglistGlobals:
	'''
	Global constants and configuration for Crglist App
	'''

	def CraigsMain(self):
		config_defaults = {'level':"1"}
		config = ConfigParser.ConfigParser(config_defaults)
		config.read('config')
		
		self.EMAIL_SENDER = eval(config.get('Main', 'email_sender'))
		self.EMAIL_RECIPIENTS = eval(config.get('Main', 'email_recipients'))
		self.SMTP_HOST = eval(config.get('Main', 'smtphost'))
		self.SMTP_USER = eval(config.get('Main', 'smtpuser'))
		self.SMTP_PW = eval(config.get('Main', 'smtppw'))

		self.DEBUG = config.getint('Debug', 'level')
		self.PAGE_SAVE_FILE = eval(config.get('Debug', 'page_save_file'))

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
		
		if self.DEBUG > 1:
			print adlistings

		CraigsEmailer.sendemail(self, adlistings)

class CraigsEmailer:

	@staticmethod
	def sendemail(CG, adlistings):

		curdatetime = time.strftime("%c")

		html = """<html>
 				<head></head>
  				<body>
    			<p>Hi!<br>
       			Craigslist Cupertino Rental Listing<br>
      			Generated at {page_gen_datetime}.
			    </p>
			    <table>
			    <tr>
			    <th> Date </th>
			    <th> Title </th>
			    <th> City </th>
			    <th> Price </th>
			    <th>    Bedroom / SQFT    </th>
			    </tr>
			    """.format(page_gen_datetime=curdatetime)


		for ad in adlistings: 			
			html_line = "<tr><td> {date} </td><td> <a href=""http://sfbay.craigslist.org/{url}"">{title}</a> </td><td> {city} </td><td> {price} </td><td> {sqft} </td></tr>".format(date=ad[0], title=ad[1], url=ad[2], price=ad[3], sqft=ad[4], city=ad[5])
			if CG.DEBUG > 1:
				print "html_line is" + html_line
			html += html_line

		html +="""
				</table>
			  	</body>
				</html>
				"""

		print "Prepare sending email ...."

		msg = MIMEMultipart('alternative')
		
		# me == the sender's email address
		# you == the recipient's email address
		msg['Subject'] = 'CG Listings ' + curdatetime
		msg['From'] = CG.EMAIL_SENDER
		msg['To'] = CG.EMAIL_RECIPIENTS

		part1 = MIMEText(html, 'html')
		msg.attach(part1)

		if CG.DEBUG > 1:
			print "Sending email via %s user %s pw %s sender %s, recv %s" % (CG.SMTP_HOST, CG.SMTP_USER, CG.SMTP_PW, CG.EMAIL_SENDER, CG.EMAIL_RECIPIENTS)

		s = smtplib.SMTP_SSL(CG.SMTP_HOST)
		s.login(CG.SMTP_USER, CG.SMTP_PW)
		s.sendmail(CG.EMAIL_SENDER, [CG.EMAIL_RECIPIENTS], msg.as_string())
		
		s.quit()

		print "Successfully sent email"


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

			date = elements[5].find("span", "date").contents[0].encode("ascii")
			adtitle = elements[5].a.get_text().encode("ascii", "ignore")
			url = elements[5].a['href'].encode("ascii")
			price = elements[7].find("span","price").contents[0].encode("ascii")
			sqft = elements[7].contents[2].encode("ascii", "ignore")
			city = elements[7].find("span", "pnr").contents[1].contents[0].encode("ascii")

			if self.CG.DEBUG > 1:
				print "---------------------------"
				print "Date  " + date
				print "Title " + adtitle
				print "URL   " + url
				print "Price " + price
				print "SQFt  " + sqft
				print "City  " + city

			adlistings.append([date, adtitle, url, price, sqft, city])

		print "Found %d listings" % len(adlistings)
		return adlistings


		
	def ListingCollectorFromFile(self, page_file):
		'''
		Unit test / debug method

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

