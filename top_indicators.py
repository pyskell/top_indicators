from datetime import datetime, timedelta, date
from enum import auto
from pytrends.request import TrendReq
from tabulate import tabulate
from requests_html import HTMLSession
from tabulate import tabulate
from sqlalchemy import Column, Integer, Date, Float, String, Enum, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property

import pandas as pd
import numbers
import requests
import locale
import enum

from shared_vars import BITCOIN_PRICE, BITCOIN_AVERAGE_FEE, BITCOIN_MVRV
from progress_bar import progress_bar

# All top indicators should reach 100% at their conservative estimate
# We want to predict when we're very close to the top, 
# not observe when it happened after the fact

# This is more a collection of codified thoughts than anything else.

# For the most part I don't think data pre-2012 is very relevant or reliable
# Data from 2013 onward is preferable, 2014+ is ideal


locale.setlocale(locale.LC_ALL, '')
pytrends = TrendReq()
engine = create_engine('sqlite:///top_indicators.db')
Base = declarative_base(bind=engine)

class Indicator(enum.Enum):
	LEADING = auto() # Should reach its target *before* the top
	LAGGING = auto() # Should reach its target *after* the top

class Metric(Base):
	__tablename__ = 'metrics'
	id = Column(Integer, primary_key=True)
	name = Column(String(40))
	# description = Column(String(256))
	__current = Column("current", String(40), nullable=True)
	__target = Column("target", String(40), nullable=True)
	__remaining = Column("remaining", String(40), nullable=True)
	units = Column(String(40))
	# indicator_type = Column(Enum(Indicator))

	def __init__(self, name, description, current=0, remaining=0, target=0, units="days", indicator_type=Indicator.LEADING):
		self.name = name
		self.description = description
		self.current = current
		self.target = target
		self.remaining = remaining
		self.units = units
		self.indicator_type = indicator_type

	# TODO: In most cases remaining = target - current. May want to handle that in this object & create a special case for datetime/timedelta
	@hybrid_property
	def remaining(self):
		return self.__remaining

	@remaining.setter
	def remaining(self, remaining):
		if isinstance(remaining, numbers.Number):
			self.__remaining = remaining
		else:
			self.__remaining = remaining
			raise Exception('remaining must be a number')

	@hybrid_property
	def target(self):
		if isinstance(self.__target, date):
			return self.__target.strftime("%Y-%m-%d")

		return self.__target
	
	@target.setter
	def target(self, target):
		self.__target = target
	
	@hybrid_property
	def current(self):
		if isinstance(self.__current, date):
			return self.__current.strftime("%Y-%m-%d")

		return self.__current

	@current.setter
	def current(self, current):
		self.__current = current

	@property
	def completion(self):
		if isinstance(self.__current, numbers.Number) and isinstance(self.__target, numbers.Number):
			return self.__current / self.__target

		return None

	@property
	def progress_bar(self):
		if isinstance(self.__current, numbers.Number) and isinstance(self.__target, numbers.Number):
			return progress_bar(self.__current, self.__target)
		else:
			return None

# TODO: Remove this once we're saving the data correctly	
Base.metadata.drop_all(engine)   # all tables are deleted
Base.metadata.create_all()
Session = sessionmaker(bind=engine)
s = Session()


def days_after_halvening():
	metric = Metric("Top after halvening", "Price has historically reached a peak 400-500 days after halvening events", 
		indicator_type=Indicator.LEADING)

	halvening = datetime(2020, 5, 19) # Predicted halvening May 19 2020
	end = halvening + timedelta(days=400) # 400-500 days after halvening

	metric.current = datetime.now()
	metric.target = end
	metric.remaining = (end - datetime.now()).days

	return metric


def full_top_to_top_cycle():
	metric = Metric("Full top-to-top cycle", "Cycle lengths appear to be getting longer, based on previous cycle of ~4 years", 
		indicator_type=Indicator.LEADING)
	# There's some evidence/belief that cycles are lengthening and in that case 6 -> 6.5 years is more appropriate

	start = datetime(2017, 12, 17) # Top of last cycle
	end = start + timedelta(days=1477)

	metric.current = datetime.now()
	metric.target = end
	metric.remaining = (end - datetime.now()).days

	return metric


def price_from_previous_top():
	metric = Metric("Price from previous top", "2011 -> 2013 was +3,500%, 2013 -> 2017 was +1,800%, prediction: +~700%", 
		units="dollars", 
		indicator_type=Indicator.LEADING)
	# The above predicts a price of 19,000 * 9 = 171,000
	# That is kind of nuts so a more "conservative" (but still nuts) target price of 135,000 was chosen

	metric.current = BITCOIN_PRICE
	metric.target = 15000 * 9
	metric.remaining = metric.target - metric.current

	return metric


def google_trends():
	metric = Metric("Google trends top", "Google trends spike hard at tops. Any move >=80 index is probably top on the longest timeframe. > Caveat: This is an index", 
		units="index", 
		indicator_type=Indicator.LEADING)
	# Caveat: I'm not sure if indexes lag at all
	# Monthly jumped to 39 in Nov 2017 prior to taking off to 100 in December

	pytrends.build_payload(["bitcoin"], timeframe='all')

	trends = pytrends.interest_over_time()

	metric.current = trends.iloc[-1]['bitcoin'] # last row, bitcoin column
	metric.target = 80
	metric.remaining = metric.target - metric.current

	return metric


# TODO: Finish once we get API access
def sopr():
	metric = Metric("SOPR Ratio", "Tends to go >=1.04 near tops (also local tops)", 
		units="index")

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

	metric.current = float(sopr_int.text + sopr_dec.text)
	metric.target = 1.04
	metric.remaining = metric.target - metric.current

	return metric



def average_fee():
	# Fees jump substantially off of the bottom, 370x 2011 ($0.001) -> 2013 ($0.30), and 625x 2015 ($0.04) -> 2017 ($25.00)
	# Some considerations:
	# Practical block sizes have changed (0.7 -> 0.8, segwit, increases early in bitcoin's history that im unaware of the timing of)
	# Segwit effectively doubles the amount of typical transactions you can get in a block if everyone use SegWit
	# Current SegWit usage is about 35% (8/2/19) https://segwit.space/

	# TODO: Median fees are also interesting.
	# TODO: There seems to be a big run up in fees, a drop, and then another run up before each bubble popped
	metric = Metric("Average Fee", "Last run when fees jumped >25 we were close to the top", 
		units="dollars", 
		indicator_type=Indicator.LEADING)

	metric.current = BITCOIN_AVERAGE_FEE
	metric.target = 25
	metric.remaining = metric.target - metric.current

	return metric


def mvrv():
	# MVRV differs slightly between CoinMetrics and Woobull's charts. The below uses CoinMetrics data.
	# https://coinmetrics.io/charts/#assets=btc_right=CapMVRVCur
	# https://charts.woobull.com/bitcoin-mvrv-ratio/
	metric = Metric("MVRV", "Last runs showed peak MVRVs of ~7.5 (2011), ~5.6 (2013-start), ~5.8 (2013-end), ~4.6 (2017). Assuming ~4 for next top.", 
		units="index", 
		indicator_type=Indicator.LEADING)

	metric.current = BITCOIN_MVRV
	metric.target = 4
	metric.remaining = metric.target - metric.current

	return metric


def gbtc():
	metric = Metric("GBTC over NAV", "Last run GBTC market price traded at a peak of 2x NAV at the top. Looking for 1.8x.", "dollars")

	session = HTMLSession()
	request = session.get('https://grayscale.co/bitcoin-investment-trust/')

	gbtc_market_pp_share = float(request.html.find('.price-market .body .price', first=True).text.replace('$',''))
	gbtc_nav_pp_share = float(request.html.find('.price-nav .body .price', first=True).text.replace('$',''))

	metric.current = gbtc_nav_pp_share
	metric.target = gbtc_market_pp_share * 1.8
	metric.remaining = metric.target - metric.current

	return metric

if __name__ == "__main__":
	metrics = [days_after_halvening(), full_top_to_top_cycle(), price_from_previous_top(), google_trends(), average_fee(), mvrv(), gbtc()]
	# indicators = [sopr()]
	# indicators = [mvrv()]
	results = []

	for metric in metrics:
		results.append([metric.name, metric.current, metric.target, metric.remaining, metric.units, f'{metric.description}\n{metric.progress_bar if metric.progress_bar else ""}'])
		s.add(metric)
		# print(f'{indicator.name}: {indicator.remaining:n} {indicator.units} remaining')
	
	# s.add_all(results)
	s.commit()
	
	print(tabulate(results, 
		headers=['Name', 'Current', 'Target', 'Remaining', 'Units', 'Description + Progress'], 
		colalign=["left", "center", "center", "right", "left", "left"],
		floatfmt=["",",.2f",",.2f",",.2f","",""],
		tablefmt='fancy_grid'
		))