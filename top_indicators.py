from datetime import datetime, timedelta
from pytrends.request import TrendReq
from tabulate import tabulate
from requests_html import HTMLSession
from tabulate import tabulate
from shared_vars import BITCOIN_PRICE, BITCOIN_AVERAGE_FEE, BITCOIN_MVRV
import pandas as pd
import numbers
import requests
import locale


# All top indicators should reach 100% at their conservative estimate
# We want to predict when we're very close to the top, 
# not observe when it happened after the fact

# This is more a collection of codified thoughts than anything else.

# For the most part I don't think data pre-2012 is very relevant or reliable
# Data from 2013 onward is preferable, 2014+ is ideal


locale.setlocale(locale.LC_ALL, '')
pytrends = TrendReq()

class Result(object):
	def __init__(self, name, description, current=0, remaining=0, target=0, units="days"):
		self.name = name
		self.description = description
		self.current = current
		self.target = target
		self.remaining = remaining
		self.units = units

	# TODO: In most cases remaining = target - current. May want to handle that in this object & create a special case for datetime/timedelta
	@property
	def remaining(self):
		return self.__remaining

	@remaining.setter
	def remaining(self, remaining):
		if isinstance(remaining, numbers.Number):
			self.__remaining = remaining
		else:
			self.__remaining = remaining
			raise Exception('remaining must be a number')

	@property
	def target(self):
		return self.__target
	
	@target.setter
	def target(self, target):
		self.__target = target
	
	@property
	def current(self):
		return self.__current

	@current.setter
	def current(self, current):
		self.__current = current
	

def days_after_halvening():
	result = Result("Top after halvening", "Price has historically reached a peak 400-500 days after halvening events")

	halvening = datetime(2020, 5, 19) # Predicted halvening May 19 2020
	end = halvening + timedelta(days=400) # 400-500 days after halvening

	result.current = datetime.now()
	# result.target = (end + datetime.now()).days
	result.remaining = (end - datetime.now()).days

	return result


def full_top_to_top_cycle():
	result = Result("Full top-to-top cycle", "Cycle lengths appear to be getting longer, based on previous cycle of ~4 years")
	# There's some evidence/belief that cycles are lengthening and in that case 6 -> 6.5 years is more appropriate

	start = datetime(2017, 12, 17) # Top of last cycle
	end = start + timedelta(days=1477)

	# result.target = (end + datetime.now()).days
	result.current = datetime.now()
	result.remaining = (end - datetime.now()).days

	return result


def price_from_previous_top():
	result = Result("Price from previous top", "2011 -> 2013 was +3,500%, 2013 -> 2017 was +1,800%, prediction: +~700%", units="dollars")
	# The above predicts a price of 19,000 * 9 = 171,000
	# That is kind of nuts so a more "conservative" (but still nuts) target price of 135,000 was chosen

	result.current = BITCOIN_PRICE
	result.target = 15000 * 9
	result.remaining = result.target - result.current

	return result


def google_trends():
	result = Result("Google trends top", "Google trends spike hard at tops. Any move >=80 index is probably top on the longest timeframe. > Caveat: This is an index", units="units")
	# Caveat: I'm not sure if indexes lag at all
	# Monthly jumped to 39 in Nov 2017 prior to taking off to 100 in December

	pytrends.build_payload(["bitcoin"], timeframe='all')

	trends = pytrends.interest_over_time()

	result.current = trends.iloc[-1]['bitcoin'] # last row, bitcoin column
	result.target = 80
	result.remaining = result.target - result.current

	return result


# TODO: Finish once we get API access
def sopr():
	result = Result("SOPR Ratio", "Tends to go >=1.04 near tops (also local tops)", units="index")

	session = HTMLSession()
	request = session.get('https://studio.glassnode.com/metrics?a=BTC&m=valuation.Sopr')

	request.html.render()

	# f = open('sopr.html', 'w+')
	# f.write(request.html.text)
	# f.close()

	# print(request.html)

	sopr_elem = request.html.search('SOPR')

	sopr_int = request.html.find('.ant-statistic-content-value-int')
	sopr_dec = request.html.find('.ant-statistic-content-value-decimal')

	result.current = float(sopr_int.text + sopr_dec.text)
	result.target = 1.04
	result.remaining = result.target - result.current

	return result


def average_fee():
	# Fees jump substantially off of the bottom, 370x 2011 ($0.001) -> 2013 ($0.30), and 625x 2015 ($0.04) -> 2017 ($25.00)
	# Some considerations:
	# Practical block sizes have changed (0.7 -> 0.8, segwit, increases early in bitcoin's history that im unaware of the timing of)
	# Segwit effectively doubles the amount of typical transactions you can get in a block if everyone use SegWit
	# Current SegWit usage is about 35% (8/2/19) https://segwit.space/

	# TODO: Median fees are also interesting.
	# TODO: There seems to be a big run up in fees, a drop, and then another run up before each bubble popped
	result = Result("Average Fee", "Last run when fees jumped >25 we were close to the top", units="dollars")

	result.current = BITCOIN_AVERAGE_FEE
	result.target = 25
	result.remaining = result.target - result.current

	return result


def mvrv():
	result = Result("MVRV", "Last runs showed peak MVRVs of ~7.5 (2011), ~5.6 (2013-start), ~5.8 (2013-end), ~4.6 (2017). Assuming ~4 for next top.", units="index")

	result.current = BITCOIN_MVRV
	result.target = 4
	result.remaining = result.target - result.current

	return result

if __name__ == "__main__":
	indicators = [days_after_halvening(), full_top_to_top_cycle(), price_from_previous_top(), google_trends(), average_fee(), mvrv()]
	# indicators = [sopr()]
	# indicators = [mvrv()]
	results = []

	for indicator in indicators:
		results.append([indicator.name, indicator.current, indicator.target, indicator.remaining, indicator.units, indicator.description])
		# print(f'{indicator.name}: {indicator.remaining:n} {indicator.units} remaining')
	
	print(tabulate(results, headers=['Name', 'Current', 'Target', 'Remaining', 'Units', 'Description'], tablefmt='fancy_grid'))