from top_indicators import *
from shared_vars import BITCOIN_AVERAGE_MCAP


def test_sopr():
  result = sopr()

  assert result.remaining is not None


def test_price_from_prev_top():
  result = price_from_previous_top()

  assert result.remaining is not None


def test_average_fee():
  result = average_fee()

  assert result.remaining is not None


def test_mvrv():
  result = mvrv()

  assert result.remaining is not None


def test_gbtc():
  result = gbtc()

  assert result.remaining is not None


def test_metric_completion():
  result = Metric("","", current=1, target=2)

  assert result.completion == 0.5


def test_progress_bar():
  result = Metric("","", current=1, target=2)

  assert result.progress_bar == "|##################################################--------------------------------------------------| 50.0%"


def test_fear_and_greed():
  result = fear_and_greed()

  assert result.remaining is not None


def test_top_cap():
  result = top_cap()

  assert result.remaining is not None


def test_mayer_multiple():
  result = mayer_multiple()

  assert result.remaining is not None