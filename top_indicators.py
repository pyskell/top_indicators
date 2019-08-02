from datetime import datetime, timedelta
from pytrends.request import TrendReq
from tabulate import tabulate
from requests_html import HTMLSession
from shared_vars import BITCOIN_PRICE, BITCOIN_AVERAGE_FEE
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
	def __init__(self, name, description, remaining=0, units="days"):
		self.name = name
		self.description = description
		self.remaining = remaining
		self.units = units

	# TODO: Add inverse of remaining (progress)?
	# TODO: Maybe add a "target" value
	# TODO: Maybe start, end, current, remaining
	@property
	def remaining(self):
		return self.__remaining

	@remaining.setter
	def remaining(self, remaining):
		if isinstance(remaining, numbers.Number):
			self.__remaining = remaining
		else:
			self.__remaining = remaining
			raise Exception('progress must be a number')
	

def days_after_halvening():
	result = Result("Top after halvening", "Price has historically reached a peak 400-500 days after halvening events")

	halvening = datetime(2020, 5, 19) # Predicted halvening May 19 2020
	end = halvening + timedelta(days=400) # 400-500 days after halvening

	result.remaining = (end - datetime.now()).days

	return result


def full_top_to_top_cycle():
	result = Result("Full top-to-top cycle", "Cycle lengths appear to be getting longer, based on previous cycle of ~4 years")
	# There's some evidence/belief that cycles are lengthening and in that case 6 -> 6.5 years is more appropriate

	start = datetime(2017, 12, 17) # Top of last cycle
	end = start + timedelta(days=1477)

	result.remaining = (end - datetime.now()).days

	return result


def price_from_previous_top():
	result = Result("Price from previous top", "2011 -> 2013 was +3,500%, 2013 -> 2017 was +1,800%, prediction: +900%", units="dollars")
	# The above predicts a price of 19,000 * 9 = 171,000
	# That is kind of nuts so a more "conservative" (but still nuts) target price of 135,000 was chosen

	result.remaining = 15000 * 9 - BITCOIN_PRICE

	return result


def google_trends():
	result = Result("Google trends top", "Google trends spike hard at tops. Any move >=80 index is probably top on the longest timeframe. > Caveat: This is an index", units="units")
	# Caveat: I'm not sure if indexes lag at all
	# Monthly jumped to 39 in Nov 2017 prior to taking off to 100 in December

	pytrends.build_payload(["bitcoin"], timeframe='all')

	trends = pytrends.interest_over_time()

	latest_index = trends.iloc[-1]['bitcoin'] # last row, bitcoin column

	result.remaining = 80 - latest_index

	return result


# TODO: Finish once we get API access
def sopr():
	result = Result("SOPR Ratio", "Tends to go >=1.04 near tops (also local tops)")

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

	sopr = float(sopr_int.text + sopr_dec.text)

	result.remaining = 1.04 - sopr

	return result


def average_fee():
	# Fees jump substantially off of the bottom, 370x 2011 ($0.001) -> 2013 ($0.30), and 625x 2015 ($0.04) -> 2017 ($25.00)
	# Some considerations:
	# Practical block sizes have changed (0.7 -> 0.8, segwit, increases early in bitcoin's history that im unaware of the timing of)
	# Segwit effectively doubles the amount of typical transactions you can get in a block if everyone use SegWit
	# Current SegWit usage is about 35% (8/2/19) https://segwit.space/

	# TODO: Median fees are also interesting.
	# TODO: There seems to be a big run up in fees, a drop, and then another run up before each bubble popped
	result = Result("Average Fee", "Last run when fees jumped >25 we were close to the top")

	result.remaining = 25 - BITCOIN_AVERAGE_FEE

	return result


if __name__ == "__main__":
	# indicators = [days_after_halvening(), full_top_to_top_cycle(), price_from_previous_top(), google_trends()]
	# indicators = [sopr()]
	indicators = [average_fee()]

	for indicator in indicators:
		print(f'{indicator.name}: {indicator.remaining:n} {indicator.units} remaining')