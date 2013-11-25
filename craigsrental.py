'''
Craigslist Stocklmeir Rental home scrappy
'''

import urllib2

from functools import wraps
from time import time


def timed(f):
  @wraps(f)
  def wrapper(*args, **kwds):
    start = time()
    result = f(*args, **kwds)
    elapsed = time() - start
    print "%s took %d secs to finish" % (f.__name__, elapsed)
    return result
  return wrapper

class CrglistLogger:
	'''Logging class for Crglist'''
	DEBUG=1

class CrglistDownloader:
	'''Download / scrap data from Craigslist'''

	urls = ["http://sfbay.craigslist.org/search/apa/sby?query=cupertino+school&zoomToPosting=&minAsk=3000&maxAsk=4000&bedrooms=3&housing_type=&nh=32&nh=40&nh=44",
	        "http://sfbay.craigslist.com/"]

	@timed
	def download(self):
		try:
			print "Downloading...%s" % self.urls[0]

			req = urllib2.Request(self.urls[0])
			page = urllib2.urlopen(req)
			if CrglistLogger.DEBUG > 1:
				print page.info()

			print "Successfully connected...downloading..."
			

			# Yes, we are reading the whole page into one buffer;
			# TODO: memory in-efficient, fix it someday
			page_content = page.read()
			if CrglistLogger.DEBUG > 1:
				print page_content

			# Cleanup
			page.close()
			del page # is this necessary ?

			return page_content

		except urllib2.HTTPError as e:
			print e


class CrglistAnalyser:
	'''Analyze data grathered from Craigslist'''

	@staticmethod
	def ListingCollector(page_content):
		'''
		Take a raw page from rental listing with header, listing links and footer,
		return an dictionary of 
			{ link, date, adtext, price, bedrooms, sqft, city }
		'''
		print "extracting data"

		if CrglistLogger.DEBUG == 1:
			page_file = '/tmp/craigs.html'
			print "writing to file %s" % page_file
			page_file = open(page_file, 'w')
			page_file.write(page_content)
			page_file.close()
		pass

'''
Invoker and Tester code
'''
if __name__ == '__main__':
	print "Starting"
	c = CrglistDownloader()
	page_content = c.download()

	# lets get to the data, call the analyser
	listings = CrglistAnalyser.ListingCollector(page_content)

