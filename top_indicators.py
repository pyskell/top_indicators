from enum import auto
from pytrends.request import TrendReq
from tabulate import tabulate
from sqlalchemy import Column, Integer, Date, Float, String, Enum, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

import pandas as pd
import requests
import locale
import enum
import sys

from metrics import *
import base

# All top indicators should reach 100% at their conservative estimate
# We want to predict when we're very close to the top,
# not observe when it happened after the fact

# This is more a collection of codified thoughts than anything else.

# For the most part I don't think data pre-2012 is very relevant or reliable
# Data from 2013 onward is preferable, 2014+ is ideal


if __name__ == "__main__":
	locale.setlocale(locale.LC_ALL, '')
	pytrends = TrendReq()
	if len(sys.argv) > 1 and sys.argv[1]:
		print("Saving DB to: " + sys.argv[1])
		engine = create_engine('sqlite:///' + sys.argv[1])
	else:
		engine = create_engine('sqlite:///top_indicators.db')
	# Base = declarative_base(bind=engine)

	base.Base.metadata.create_all(engine, checkfirst=True)
	Session = sessionmaker(bind=engine)
	s = Session()

	days_after_halvening = DaysAfterHalvening("Top after halvening", "Price has historically reached a peak 400-500 days after halvening events", 
		indicator_type=Indicator.LEADING)
	# There's some evidence/belief that cycles are lengthening and in that case 6 -> 6.5 years is more appropriate
	full_top_to_top_cycle = FullTopToTopCycle("Full top-to-top cycle", "Cycle lengths appear to be getting longer, based on previous cycle of ~4 years",
		indicator_type=Indicator.LEADING)
	# The below notes predict a price of 19,000 * 9 = 171,000
	# That is kind of nuts so a more "conservative" (but still nuts) target price of 135,000 was chosen
	price_from_previous_top = PriceFromPreviousTop("Price from previous top", "2011 -> 2013 was +3,500%, 2013 -> 2017 was +1,800%, prediction: +~700%",
		units="dollars",
		indicator_type=Indicator.LEADING)
	# Monthly jumped to 39 in Nov 2017 prior to taking off to 100 in December
	#google_trends = GoogleTrends("Google trends top", "Google trends spike hard at tops. Any move >=80 index is probably top on the longest timeframe. > Caveat: This is an index",
	#	units="index",
	#	indicator_type=Indicator.LEADING)
	average_fee = AverageFee("Average Fee", "Last run when fees jumped >25 we were close to the top",
		units="dollars",
		indicator_type=Indicator.LEADING)
	mvrv = MVRV("MVRV", "Last runs showed peak MVRVs of ~7.5 (2011), ~5.6 (2013-start), ~5.8 (2013-end), ~4.6 (2017). Assuming ~4 for next top.",
		units="index",
		indicator_type=Indicator.LEADING)
	gbtc = GBTC("GBTC over NAV", "Last run GBTC market price traded at a peak of 2x NAV at the top. Looking for 1.8x. ETFs and other products may reduce differential",
		units="dollars")
	fear_and_greed = FearAndGreed("Fear & Greed Index", 
		"Good short-term indicator on whether or not the market is greedy. >80 is very concerning. >90 is gtfo.",
		units="index")
	top_cap = TopCap("Top Cap", 
		"Bitcoin appears to hit tops when it's at 35x its forever average market cap. Targeting x32", 
		units="dollars")
	mayer_multiple = MayerMultiple("Mayer Multiple", 
		"Last bull run was ~3.8 at peak, this is declining though so targeting 3.1 (which is just a guess based on nothing)", 
		units="ratio")
	
	metrics = [days_after_halvening, full_top_to_top_cycle, price_from_previous_top, average_fee, top_cap, gbtc, mayer_multiple, mvrv, fear_and_greed]
	#google_trends,
	results = []

	for metric in metrics:

		# NOTE: Tabulate has an issue where if it encounters a value it can't 
		# format in a column it won't format the rest of the column
		# TODO: This is ugly, make better
		if not isinstance(metric.current, str):
			results.append([metric.name, "{:,.2f}".format(metric.current), "{:,.2f}".format(metric.target), "{:,.2f}".format(metric.remaining), metric.units, f'{metric.description}\n{metric.progress_bar if metric.progress_bar else ""}'])
		else:
			results.append([metric.name, metric.current, metric.target, metric.remaining, metric.units, f'{metric.description}\n{metric.progress_bar if metric.progress_bar else ""}'])

		# We only want to store this data once per day
		exists = s.query(Metric).get((metric.date, metric.name))
		if not exists:
			s.add(metric)

	# s.add_all(results)
	s.commit()

	print(tabulate(results,
		headers=['Name', 'Current', 'Target', 'Remaining', 'Units', 'Description + Progress'],
		colalign=["left", "center", "center", "right", "left", "left"],
		# floatfmt=["","","","","",""],
		tablefmt='fancy_grid'
		))
