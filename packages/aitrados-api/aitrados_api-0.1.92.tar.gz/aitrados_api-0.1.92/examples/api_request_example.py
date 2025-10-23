import os
from aitrados_api import *
from aitrados_api.common_lib.common import load_env_file

#load_env_file(".env", override=True)

config = ClientConfig(
    secret_key=os.getenv("AITRADOS_SECRET_KEY","YOUR_SECRET_KEY"),
    timeout=30,
    max_retries=1000,
    rate_limit=RateLimitConfig(
        daily_limit=100000,
        requests_per_second=2,
        requests_per_minute=30
    ),
    debug=True
)

client=DatasetClient(config=config)
params = {
    "schema_asset": SchemaAsset.CRYPTO,
    "country_symbol": "GLOBAL:BTCUSD",
    "interval": IntervalName.M60,
    "from_date": "2025-07-18T00:00:00+00:00",
    "to_date": "2025-09-05T23:59:59+00:00",
    "format": "csv",
    "limit": 30
}
#***************************************OHLC DATA***************************#

## Get historical OHLC data

for ohlc in client.ohlc.ohlcs(**params):
    print(ohlc)


'''
# Get latest OHLC data.use for real-time data
ohlc_latest=client.ohlc.ohlcs_latest(**params)
print(ohlc_latest)

rename_column_name_mapping={"interval":"timeframe",}
filter_column_names=["datetime","timeframe","open","high","low","close","volume","close_datetime"]
to_format=ApiListResultToFormatData(ohlc_latest,rename_column_name_mapping=rename_column_name_mapping,filter_column_names=filter_column_names,limit=None)
pl_df=to_format.get_polars()
pd_df=to_format.get_pandas()
csv_string=to_format.get_csv()
data_list=to_format.get_list()
pass
'''
'''


#***************************************symbol reference***************************#

stock_reference=client.reference.reference(schema_asset=SchemaAsset.STOCK,country_symbol="US:TSLA")
crypto_reference=client.reference.reference(schema_asset=SchemaAsset.CRYPTO,country_symbol="GLOBAL:BTCUSD")
forex_reference=client.reference.reference(schema_asset=SchemaAsset.FOREX,country_symbol="GLOBAL:EURUSD")
'''




#***************************************OPTIONS INFORMATION***************************#
'''
# Get options information
for options in client.reference.search_option(schema_asset=SchemaAsset.STOCK,country_symbol="US:spy",option_type="call",moneyness="in_the_money",ref_asset_price=450.50,limit=100):
    print(options)
'''
'''
# Get options expiration date list
expiration_date_list= client.reference.options_expiration_date_list(schema_asset=SchemaAsset.STOCK, country_symbol="US:SPY")
pass
'''
#***************************************stock corporate action***************************#
'''
# Get stock corporate action list
for actions in client.reference.stock_corporate_action_list(country_symbol="US:TSLA",from_date="2020-08-18",action_type="split",limit=100):
    print(actions)
'''
#***************************************economic event***************************#
'''
# Get economic event codes of all countries
event_codes= client.economic.event_codes(country_iso_code="US")
'''

'''
# Get economic event list
for event_list in  client.economic.event_list(country_iso_code="US",limit=5):
    print(event_list)

'''
'''
# Get economic event by date
event= client.economic.event()
print(event)
'''
'''
# Get economic latest event list
latest_events = client.economic.latest_events(country_iso_code="us")
print(latest_events)
'''
#***************************************holiday***************************#
'''
# Get holiday list
for holiday_list in client.holiday.holiday_list(full_symbol="stock:US:*",from_date="2023-01-01",to_date="2026-12-31",limit=100):
    print(holiday_list)
'''

'''
# Get holiday codes of all countries
holiday_codes= client.holiday.holiday_codes()
'''

#***************************************news***************************#

'''
# Get news list
for news_list in client.news.news_list(full_symbol="stock:US:TSLA",from_date="2025-07-01",to_date="2025-12-31",limit=100):
    print(news_list)
'''

'''
# Get latest news.use for real-time data
news_latest= client.news.news_latest(full_symbol="stock:US:TSLA",limit=5)
print(news_latest)
'''
client.close()