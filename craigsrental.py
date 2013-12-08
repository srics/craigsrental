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


class CraigslistRental:

	urls = ["http://sfbay.craigslist.org/search/apa/sby?query=cupertino+school&zoomToPosting=&minAsk=3000&maxAsk=4000&bedrooms=3&housing_type=&nh=32&nh=40&nh=44",
	        "http://sfbay.craigslist.com/"]

	def __init__(self):
		'''
		Initialize ourselves using config file
		Global constants and configuration for Crglist App
		'''
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

	def run(self):
		page_content = self.downloadPage(self.urls[0])

		# lets get to the data, call the analyser
		adlistings = self.listingCollector(page_content)
		
		if self.DEBUG > 1:
			print adlistings

		# Special processing
		key1 = [keyword, keyword_listings] =  ["stocklmeir", self.listingSearchKeyword(adlistings, "stocklmeir")]

		print key1

		self.listingSendMail(adlistings, key1)

	def downloadPage(self, url, write_to_file=None):
		''' 
		Download / scrap data from Craigslist
		Download webpage to a buffer 
			- whole page in buffer for now; 
			- TODO: improve to do chunks reads 
		'''
		try:
			print "Downloading...%s" % url

			req = urllib2.Request(url)
			page = urllib2.urlopen(req)
			if self.DEBUG > 1:
				print page.info()
				print "Successfully connected...downloading..."
			
			# Yes, we are reading the whole page into one buffer;
			# TODO: memory in-efficient, fix it someday
			page_content = page.read()
			if self.DEBUG > 1:
				print page_content

			# Cleanup
			page.close()

			# Debug hook to save the content in a file for analysis
			if write_to_file:
				print "writing to file %s" % write_to_file
				pfile = open(write_to_file, 'w')
				pfile.write(page_content)
				pfile.close()

			return page_content

		except urllib2.HTTPError as e:
			print e


	def listingCollector(self, page_content):
		'''
		Analyze data grathered from Craigslist

		Take a raw page from rental listing with header, listing links and footer,
		return an dictionary of 
			{ link, date, adtext, price, bedrooms, sqft, city }
		'''

		print "Analyzing page content..."
		adlistings = []

		soup = BeautifulSoup(page_content)

		listing = soup.body.find_all('p')
		for ad in listing:
			if self.DEBUG > 1:
				print "Ad: " + str(ad)
			elements = ad.contents

			'''
			Recipe:
				elements[5] = date, url link to ad, adtitle
				elements[7] = price, sqft, city
			'''
			if self.DEBUG > 1:
				for elem in elements:
					print "  Elem: " + str(elem)

			date = elements[5].find("span", "date").contents[0].encode("ascii")
			adtitle = elements[5].a.get_text().encode("ascii", "ignore")
			url = elements[5].a['href'].encode("ascii")
			price = elements[7].find("span","price").contents[0].encode("ascii")
			sqft = elements[7].contents[2].encode("ascii", "ignore")
			city = elements[7].find("span", "pnr").contents[1].contents[0].encode("ascii")

			if self.DEBUG > 1:
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

		
	def listingCollectorFromFile(self, page_file):
		'''
		Unit test / debug method

		Take a raw page from rental listing with header, listing links and footer,
		return an dictionary of 
			{ link, date, adtext, price, bedrooms, sqft, city }

		Usage:
		 listings = listingCollectorFromFile(page_file=CrglistGlobals.CG)
		'''

		if (None is page_file):
			# TODO: raise an exception
			pass

		print "Opening file " + page_file
		f = open(page_file, "r")
		page_content = f.read()
		f.close()
		self.listingCollector(page_content)

	def listingSearchKeyword(self, adlistings, keyword):

		keyword_adlistings = []

		for ad in adlistings:
			print "Searching keyword in url %s" % ad[2]
			page_content = self.downloadPage("http://sfbay.craigslist.org" + ad[2])
			# TODO: this is really inefficient (tolower the whole page content);
			#       find another way perhaps using regex
			if page_content.lower().find(keyword.lower()) == -1: continue 
			print "Found keyword match"
			keyword_adlistings.append(ad)

		return keyword_adlistings

	def listingSendMail(self, adlistings, keyword_search1):

		curdatetime = time.strftime("%c")

		html = """<html>
 				<head></head>
  				<body>
    			<p>Hi!<br>
       			Craigslist Cupertino Rental Listing<br>
      			Generated at {page_gen_datetime}.
			    </p>
			    """.format(page_gen_datetime=curdatetime)

		if len(keyword_search1[1]) > 0:
			# Table header for keyword search listing
			html += """
					<p> Found listing matching {keyword} </p>
				    <table>
				    <tr>
				    <th> Date </th>
				    <th> Title </th>
				    <th> City </th>
				    <th> Price </th>
				    <th>    Bedroom / SQFT    </th>
				    </tr>
				    """.format(keyword=keyword_search1[0])

			for ad in keyword_search1[1]:
				html_line = "<tr><td> {date} </td><td> <a href=""http://sfbay.craigslist.org/{url}"">{title}</a> </td><td> {city} </td><td> {price} </td><td> {sqft} </td></tr>".format(date=ad[0], title=ad[1], url=ad[2], price=ad[3], sqft=ad[4], city=ad[5])
				if self.DEBUG > 1:
					print "html_line is" + html_line
				html += html_line

			html += "</table>"

		# Other listings
		html += """
				<p> Other listings </p>
			    <table>
			    <tr>
			    <th> Date </th>
			    <th> Title </th>
			    <th> City </th>
			    <th> Price </th>
			    <th>    Bedroom / SQFT    </th>
			    </tr>
			    """

		for ad in adlistings: 			
			html_line = "<tr><td> {date} </td><td> <a href=""http://sfbay.craigslist.org/{url}"">{title}</a> </td><td> {city} </td><td> {price} </td><td> {sqft} </td></tr>".format(date=ad[0], title=ad[1], url=ad[2], price=ad[3], sqft=ad[4], city=ad[5])
			if self.DEBUG > 1:
				print "html_line is" + html_line
			html += html_line

		html += "</table>"
				
		html +="""
			  	</body>
				</html>
				"""

		print "Prepare sending email ...."

		msg = MIMEMultipart('alternative')
		
		# me == the sender's email address
		# you == the recipient's email address
		msg['Subject'] = 'CG Listings ' + curdatetime
		msg['From'] = self.EMAIL_SENDER
		msg['To'] = self.EMAIL_RECIPIENTS

		part1 = MIMEText(html, 'html')
		msg.attach(part1)

		if self.DEBUG > 1:
			print "Sending email via %s user %s pw %s sender %s, recv %s" % (self.SMTP_HOST, self.SMTP_USER, self.SMTP_PW, self.EMAIL_SENDER, self.EMAIL_RECIPIENTS)

		s = smtplib.SMTP_SSL(self.SMTP_HOST)
		s.login(self.SMTP_USER, self.SMTP_PW)
		s.sendmail(self.EMAIL_SENDER, [self.EMAIL_RECIPIENTS], msg.as_string())
		
		s.quit()

		print "Successfully sent email"



def timed(f):
  @wraps(f)
  def wrapper(*args, **kwds):
    start = time.time()
    result = f(*args, **kwds)
    elapsed = time.time() - start
    print "%s took %d secs to finish" % (f.__name__, elapsed)
    return result
  return wrapper


'''
Invoker and Tester code
'''
if __name__ == '__main__':
	print "Starting..."
	cg = CraigslistRental()
	cg.run()

