from top_indicators import *


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