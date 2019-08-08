import requests
from urllib.parse import urlencode
from datetime import datetime, timedelta
# from itertools import accumulate

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

## Bitcoin Average Market Cap
cm_avg_mcap_query = urlencode({
  'metrics': 'CapMrktCurUSD',
  'start': '2011-02-02', # TODO: change to earliest date 20110202
  'end': cm_yesterday
})

url = f"{COINMETRICS_API}/assets/btc/metricdata?{cm_avg_mcap_query}"

cm_avg_mcap_response = requests.get(f"{COINMETRICS_API}/assets/btc/metricdata?{cm_avg_mcap_query}")
cm_avg_mcap_json = cm_avg_mcap_response.json()
cm_mcaps = cm_avg_mcap_json['metricData']['series']

def get_val(series):
  return float(series["values"][0])

cm_mcaps_sum = sum(map(get_val, cm_mcaps))
cm_mcap_length = len(cm_mcaps)
BITCOIN_CURRENT_MCAP = get_val(cm_mcaps[-1])
BITCOIN_AVERAGE_MCAP = cm_mcaps_sum / cm_mcap_length

## Bitcoin fear & greed index
fgi_response = requests.get('https://api.alternative.me/fng/?limit=1')
fgi_json = fgi_response.json()
BITCOIN_FEAR_GREED_INDEX = int(fgi_json['data'][0]['value'])