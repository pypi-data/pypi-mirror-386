import datetime
import json
import os
import signal
from time import sleep
from typing import Dict, List

import pandas as pd
import polars as pl
from loguru import logger

from aitrados_api import SubscribeEndpoint, ChartDataFormat
from aitrados_api import ClientConfig
from aitrados_api import DatasetClient
from aitrados_api import WebSocketClient
from aitrados_api import LatestOhlcMultiTimeframeManager
from aitrados_api import IntervalName

api_config = ClientConfig(
    secret_key=os.getenv("AITRADOS_SECRET_KEY", "YOUR_SECRET_KEY"),
    debug=True
)
api_client = DatasetClient(config=api_config)


def show_subscribe_handle_msg(client: WebSocketClient, message):
    print("subscriptions", json.dumps(client.all_subscribed_topics))


ws_client = WebSocketClient(
    secret_key=os.getenv("AITRADOS_SECRET_KEY", "YOUR_SECRET_KEY"),
    is_reconnect=True,
    show_subscribe_handle_msg=show_subscribe_handle_msg,
    endpoint=SubscribeEndpoint.REALTIME,
    debug=True
)


def multi_timeframe_callback(name, data: Dict[str, List[str | list | pl.DataFrame | pd.DataFrame]], *args,**kwargs):
    print(f"==================Received data:{name}========================{datetime.datetime.now()}")

    for full_symbol, tf_data_list in data.items():
        for tf_data in tf_data_list:
            if isinstance(tf_data, list):
                print(json.dumps(tf_data[-2:], indent=2), "===len===", len(tf_data))
            else:
                print(tf_data)


latest_ohlc_multi_timeframe_manager = LatestOhlcMultiTimeframeManager(
    api_client=api_client,
    ws_client=ws_client,
    multi_timeframe_callback=multi_timeframe_callback,
    limit=150,  # data length limit
    works=10,
    data_format=ChartDataFormat.DICT  # multi_timeframe_callback return data format
)

is_close = False


def signal_handler(sig, frame):
    ws_client.close()
    global is_close
    is_close = True


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    ws_client.run(is_thread=True)

    # Add single symbol with single timeframe
    latest_ohlc_multi_timeframe_manager.add_item(
        item_data={
            "CRYPTO:GLOBAL:BTCUSD": [IntervalName.M60],
        },
        name="single_timeframe"
    )

    # Add single symbol with multiple timeframes
    latest_ohlc_multi_timeframe_manager.add_item(
        item_data={
            "CRYPTO:GLOBAL:BTCUSD": [IntervalName.M60, IntervalName.DAY],
        },
        name="multi_timeframe"
    )
    pass
    # Add multiple symbols with multiple timeframes
    latest_ohlc_multi_timeframe_manager.add_item(
        item_data={
            "CRYPTO:GLOBAL:BTCUSD": [IntervalName.M15, IntervalName.M60, IntervalName.DAY],
            "CRYPTO:GLOBAL:ETHUSD": [IntervalName.M15, IntervalName.M60, IntervalName.DAY]
        },
        name="multi_symbol_multi_timeframe"
    )

    # Add multiple stocks with multiple timeframes

    latest_ohlc_multi_timeframe_manager.add_item(
        item_data={
            "stock:us:tsla": [IntervalName.M5, IntervalName.M60, IntervalName.DAY],
            "stock:us:spy": [IntervalName.M5, IntervalName.M60, IntervalName.WEEK],
        },
        name="stock_multi_timeframe"
    )

    while not is_close:
        sleep(2)
    # Remove item example
    # latest_ohlc_multi_timeframe_manager.remove_item(name="multi_symbol_multi_timeframe")
    # latest_ohlc_multi_timeframe_manager.remove_item(name="multi_timeframe")
    # latest_ohlc_multi_timeframe_manager.remove_item(name="single_timeframe")
    # latest_ohlc_multi_timeframe_manager.remove_item(name="stock_multi_timeframe")
    logger.info("Exited")
