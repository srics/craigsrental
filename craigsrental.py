'''
Craigslist Stocklmeir Rental home scrappy

Dependencies:
	BeautifulSoup
'''

import urllib2

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
	DEBUG=1
	PAGE_SAVE_FILE='/Users/srramasw/craigs.html'

class CrglistDownloader:
	'''
	Download / scrap data from Craigslist
	'''

	urls = ["http://sfbay.craigslist.org/search/apa/sby?query=cupertino+school&zoomToPosting=&minAsk=3000&maxAsk=4000&bedrooms=3&housing_type=&nh=32&nh=40&nh=44",
	        "http://sfbay.craigslist.com/"]

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
			if CrglistGlobals.DEBUG > 1:
				print page.info()

			print "Successfully connected...downloading..."
			

			# Yes, we are reading the whole page into one buffer;
			# TODO: memory in-efficient, fix it someday
			page_content = page.read()
			if CrglistGlobals.DEBUG > 1:
				print page_content

			# Cleanup
			page.close()

			if write_to_file:
				page_file = CrglistGlobals.PAGE_SAVE_FILE
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

	def ListingCollector(self, page_content):
		'''
		Take a raw page from rental listing with header, listing links and footer,
		return an dictionary of 
			{ link, date, adtext, price, bedrooms, sqft, city }
		'''

		print "Analyzing page content..."

		soup = BeautifulSoup(page_content)

		listing = soup.body.find_all('p')
		for ad in listing:
			if CrglistGlobals.DEBUG > 1:
				print "Ad: " + str(ad)
			elements = ad.contents

			'''
			Recipe:
				elements[5] = date, url link to ad, adtitle
				elements[7] = price, sqft, city
			'''
			if CrglistGlobals.DEBUG > 1:
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
	c = CrglistDownloader()
	page_content = c.download(write_to_file=False)

	# lets get to the data, call the analyser
	ca = CrglistAnalyser()
	listings = ca.ListingCollector(page_content)
	# listings = ca.ListingCollectorFromFile(page_file=CrglistGlobals.PAGE_SAVE_FILE)

