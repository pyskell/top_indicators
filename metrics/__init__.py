import numbers
import enum
from enum import auto

from datetime import datetime, timedelta, date
from pytrends.request import TrendReq
from sqlalchemy import Column, Integer, Date, Float, String, Enum, create_engine
from sqlalchemy.ext.hybrid import hybrid_property
from progress_bar import progress_bar
from requests_html import HTMLSession, HTML
import cloudscraper

from shared_vars import BITCOIN_PRICE, BITCOIN_AVERAGE_FEE, BITCOIN_MVRV, BITCOIN_FEAR_GREED_INDEX, BITCOIN_AVERAGE_MCAP, BITCOIN_CURRENT_MCAP, BITCOIN_200D_AVG_MCAP
from base import Base

pytrends = TrendReq()

class Indicator(enum.Enum):
	LEADING = auto() # Should reach its target *before* the top
	LAGGING = auto() # Should reach its target *after* the top

class Metric(Base):
	__tablename__ = 'metrics'
	# id = Column(Integer, primary_key=True)
	date = Column(Date, primary_key=True)
	name = Column(String(40), primary_key=True)
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
		self.date = datetime.now().date()

	# TODO: In most cases remaining = target - current. May want to handle that in this object & create a special case for datetime/timedelta
	@hybrid_property
	def remaining(self):
		return float(self.__remaining)

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

		return float(self.__target)

	@target.setter
	def target(self, target):
		self.__target = target

	@hybrid_property
	def current(self):
		if isinstance(self.__current, date):
			return self.__current.strftime("%Y-%m-%d")

		return float(self.__current)

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


class DaysAfterHalvening(Metric):
	def __init__(self, *args, **kwargs):
		super(DaysAfterHalvening, self).__init__(*args, **kwargs)
		halvening = datetime(2020, 5, 19) # Predicted halvening May 19 2020
		end = halvening + timedelta(days=400) # 400-500 days after halvening

		self.current = datetime.now()
		self.target = end
		self.remaining = (end - datetime.now()).days


class FullTopToTopCycle(Metric):
	def __init__(self, *args, **kwargs):
		super(FullTopToTopCycle, self).__init__(*args, **kwargs)

		start = datetime(2017, 12, 17) # Top of last cycle
		end = start + timedelta(days=1477)

		self.current = datetime.now()
		self.target = end
		self.remaining = (end - datetime.now()).days


class PriceFromPreviousTop(Metric):
	def __init__(self, *args, **kwargs):
		super(PriceFromPreviousTop, self).__init__(*args, **kwargs)
		self.current = BITCOIN_PRICE
		self.target = 15000 * 9
		self.remaining = self.target - self.current


class GoogleTrends(Metric):
	def __init__(self, *args, **kwargs):
		super(GoogleTrends, self).__init__(*args, **kwargs)
		pytrends.build_payload(["bitcoin"], timeframe='all')

		trends = pytrends.interest_over_time()

		self.current = int(trends.iloc[-1]['bitcoin']) # last row, bitcoin column
		self.target = 80
		self.remaining = int(self.target - self.current)


# TODO: Finish once we get API access
# def sopr():
# 	metric = Metric("SOPR Ratio", "Tends to go >=1.04 near tops (also local tops)",
# 		units="index")

# 	session = HTMLSession()
# 	request = session.get('https://studio.glassnode.com/metrics?a=BTC&m=valuation.Sopr')

# 	request.html.render()

# 	# f = open('sopr.html', 'w+')
# 	# f.write(request.html.text)
# 	# f.close()

# 	# print(request.html)

# 	sopr_elem = request.html.search('SOPR')

# 	sopr_int = request.html.find('.ant-statistic-content-value-int')
# 	sopr_dec = request.html.find('.ant-statistic-content-value-decimal')

# 	metric.current = float(sopr_int.text + sopr_dec.text)
# 	metric.target = 1.04
# 	metric.remaining = metric.target - metric.current

# 	return metric

class AverageFee(Metric):
	def __init__(self, *args, **kwargs):
		# Fees jump substantially off of the bottom, 370x 2011 ($0.001) -> 2013 ($0.30), and 625x 2015 ($0.04) -> 2017 ($25.00)
		# Some considerations:
		# Practical block sizes have changed (0.7 -> 0.8, segwit, increases early in bitcoin's history that im unaware of the timing of)
		# Segwit effectively doubles the amount of typical transactions you can get in a block if everyone use SegWit
		# Current SegWit usage is about 35% (8/2/19) https://segwit.space/
		super(AverageFee, self).__init__(*args, **kwargs)
		self.current = BITCOIN_AVERAGE_FEE
		self.target = 25
		self.remaining = self.target - self.current


class MVRV(Metric):
	def __init__(self, *args, **kwargs):
		# MVRV differs slightly between CoinMetrics and Woobull's charts. The below uses CoinMetrics data.
		# https://coinmetrics.io/charts/#assets=btc_right=CapMVRVCur
		# https://charts.woobull.com/bitcoin-mvrv-ratio/
		super(MVRV, self).__init__(*args, **kwargs)
		self.current = BITCOIN_MVRV
		self.target = 4
		self.remaining = self.target - self.current


class GBTC(Metric):
	def __init__(self, *args, **kwargs):
		super(GBTC, self).__init__(*args, **kwargs)
		# ETFs and other products may reduce the effectiveness of this indicator https://twitter.com/krugermacro/status/1168913327159992320
		# https://www.vaneck.com/institutional/bitcoin-144a/faq?vecs=true
		scraper = cloudscraper.create_scraper()
		session = HTMLSession()
		html = HTML(html=scraper.get('https://grayscale.co/bitcoin-investment-trust/').text)

		gbtc_market_pp_share = float(html.find('.price-market .body .price', first=True).text.replace('$',''))
		gbtc_nav_pp_share = float(html.find('.price-nav .body .price', first=True).text.replace('$',''))

		self.current = gbtc_nav_pp_share
		self.target = gbtc_market_pp_share * 1.8
		self.remaining = self.target - self.current


class FearAndGreed(Metric):
	def __init__(self, *args, **kwargs):
		# https://alternative.me/crypto/fear-and-greed-index/#data-sources
		super(FearAndGreed, self).__init__(*args, **kwargs)
		self.current = BITCOIN_FEAR_GREED_INDEX
		self.target = 80
		self.remaining = self.target - self.current


class TopCap(Metric):
	def __init__(self, *args, **kwargs):
		# https://charts.woobull.com/bitcoin-price-models/
		super(TopCap, self).__init__(*args, **kwargs)
		self.current = BITCOIN_CURRENT_MCAP
		self.target = BITCOIN_AVERAGE_MCAP * 32
		self.remaining = self.target - self.current


class MayerMultiple(Metric):
	def __init__(self, *args, **kwargs):
		# http://charts.woobull.com/bitcoin-mayer-multiple/
		super(MayerMultiple, self).__init__(*args, **kwargs)
		# Note: Using market cap instead of price to cut down on queries but shouldn't make a difference
		self.current = BITCOIN_CURRENT_MCAP / BITCOIN_200D_AVG_MCAP
		self.target = 3.1
		self.remaining = self.target - self.current