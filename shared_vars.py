import requests
from urllib.parse import urlencode
from datetime import datetime, timedelta

CRYPTO_WATCH_API = "https://api.cryptowat.ch"
COINMETRICS_API = "https://community-api.coinmetrics.io/v2"
YESTERDAY = datetime.now() - timedelta(days=1)


# Cryptowat.ch Data
## Bitcoin current price
cw_price_response = requests.get(f"{CRYPTO_WATCH_API}/markets/coinbase-pro/btcusd/price")
cw_price_json = cw_price_response.json()
BITCOIN_PRICE = round(float(cw_price_json["result"]["price"]),2)


# CoinMetrics Data
cm_yesterday = YESTERDAY.strftime("%Y%m%d")

## Bitcoin average fee today
cm_fee_query = urlencode({
  'metrics': 'FeeMeanUSD',
  'start': cm_yesterday,
  'end': cm_yesterday
})
cm_fee_response = requests.get(f"{COINMETRICS_API}/assets/btc/metricdata?{cm_fee_query}")
cm_fee_json = cm_fee_response.json()
BITCOIN_AVERAGE_FEE = round(float(cm_fee_json['metricData']['series'][0]['values'][0]),2)

## Bitcoin MVRV
cm_mvrv_query = urlencode({
  'metrics': 'CapMVRVCur',
  'start': cm_yesterday,
  'end': cm_yesterday
})

cm_mvrv_response = requests.get(f"{COINMETRICS_API}/assets/btc/metricdata?{cm_mvrv_query}")
cm_mvrv_json = cm_mvrv_response.json()
BITCOIN_MVRV = float(cm_mvrv_json['metricData']['series'][0]['values'][0])

## Bitcoin fear & greed index
fgi_response = requests.get('https://api.alternative.me/fng/?limit=1')
fgi_json = fgi_response.json()
BITCOIN_FEAR_GREED_INDEX = int(fgi_json['data'][0]['value'])