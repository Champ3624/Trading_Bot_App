import logging
import datetime as dt
import json
import pytz
from utils import wait_until, get_todays_trades
from api_client import AlpacaAPIClient

logger = logging.getLogger(__name__)

with open("config.json", "r") as config_file:
    config = json.load(config_file)

API_KEY = config['api_key']
API_SECRET = config['api_secret']
BASE_URL = config["base_url"]
MARKET_CLOSE_TIME = config["market_close_time"]
MARKET_OPEN_TIME = config["market_open_time"]
DEFAULT_LIMIT_PRICE = config["default_limit_price"]

api_client = AlpacaAPIClient(BASE_URL, API_KEY, API_SECRET)

eastern = pytz.timezone("America/New_York")

def find_option_symbol(symbol, strike, expiration_date):
    endpoint = f"/options/contracts?underlying_symbols={symbol}&expiration_date={expiration_date}"
    data = api_client.get(endpoint)
    if data:
        for contract in data.get('option_contracts', []):
            if float(contract['strike_price']) == strike:
                return contract['symbol']
    return ""

def trade_calendar_spread(long_symbol: str, short_symbol: str, qty: int) -> None:
    payload = {
        "type": "limit",
        "time_in_force": "day",
        "order_class": "mleg",
        "limit_price": DEFAULT_LIMIT_PRICE,  # Adjust as needed
        "qty": str(qty),
        "legs": [
            {"side": "buy", "position_intent": "buy_to_open", "symbol": long_symbol, "ratio_qty": str(qty)},
            {"side": "sell", "position_intent": "sell_to_open", "symbol": short_symbol, "ratio_qty": str(qty)}
        ]
    }
    try:
        response = AlpacaAPIClient.post(endpoint="/orders", payload=payload)
        response.raise_for_status()
        logger.info("Order submitted successfully: %s", response.json())
    except Exception as e:
        logger.error("Error submitting calendar spread orders: %s", e)

def close_all_positions() -> None:
    api_client.delete("/positions")
    

def trader() -> None:
    """
    Daily schedule:
    - At 15 minutes before market close (assumed at 16:00), run the trade finder
      to process only earnings events scheduled between today's close and next day's open.
    - Then, on the next trading day at 15 minutes after market open (assumed at 9:30),
      close all positions.
    """
    while True:
        now = dt.datetime.now(eastern)
        # Assume market close at 16:00 local time
        market_close = eastern.localize(dt.datetime(now.year, now.month, now.day, MARKET_CLOSE_TIME))
        trade_exec_time = market_close - dt.timedelta(minutes=15)  # 15 min before close

        # Wait until trade execution time if needed
        if now < trade_exec_time:
            wait_until(trade_exec_time)
        
        # Compute next day's market open (assumed at 9:30)
        next_day = now + dt.timedelta(days=1)
        next_market_open = eastern.localize(dt.datetime(next_day.year, next_day.month, next_day.day, MARKET_OPEN_TIME))
        
        trades = get_todays_trades()
        
        if not trades.empty:
            trades.to_csv("calendar_spreads.csv", index=False)
            for _, row in trades.iterrows():
                ticker = row['ticker']
                short_call = row['Short Leg']
                long_call = row['Long Leg']
                qty = 1
                
                short_symbol = find_option_symbol(ticker, short_call['strike'], short_call['expiry'])
                long_symbol = find_option_symbol(ticker, long_call['strike'], long_call['expiry'])
                
                if not short_symbol or not long_symbol:
                    logger.warning("Could not retrieve option symbols for %s", ticker)
                    continue
                
                trade_calendar_spread(long_symbol, short_symbol, qty)
        else:
            logger.info("No trades meet criteria after filtering for overnight earnings events.")
        
        # Wait until next trading day at 15 minutes after market open to close positions
        close_positions_time = next_market_open + dt.timedelta(minutes=15)
        sleep_duration = (close_positions_time - dt.datetime.now(eastern)).total_seconds()
        if sleep_duration > 0:
            wait_until(close_positions_time)
        else:
            logger.warning("Positions closing time already passed, skipping sleep.")
        
        close_all_positions()
        
if __name__ =='__main__':
    trader()