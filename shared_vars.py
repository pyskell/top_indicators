import requests
from urllib.parse import urlencode
from datetime import datetime, timedelta


# Bitcoin current price
CRYPTO_WATCH_API = "https://api.cryptowat.ch"
cw_price_response = requests.get(f"{CRYPTO_WATCH_API}/markets/coinbase-pro/btcusd/price")
cw_price_json = cw_price_response.json()
BITCOIN_PRICE = round(float(cw_price_json["result"]["price"]),2)

# Bitcoin average fee today
COINMETRICS_API = "https://community-api.coinmetrics.io/v2"
yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
cm_fee_query = urlencode({
  'metrics': 'FeeMeanUSD',
  'start': yesterday,
  'end': yesterday
})
cm_fee_response = requests.get(f"{COINMETRICS_API}/assets/btc/metricdata?{cm_fee_query}")
cm_fee_json = cm_fee_response.json()
BITCOIN_AVERAGE_FEE = round(float(cm_fee_json['metricData']['series'][0]['values'][0]),2)