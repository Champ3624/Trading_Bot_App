import os
import time
import logging
import datetime as dt
import requests
import pandas as pd
from trade_finder import get_calendar_trades, get_upcoming_earnings, get_spx_tickers
from option_finder import find_option_strategy

logger = logging.getLogger(__name__)

API_KEY = os.getenv("APCA_PAPER_KEY_ID", "").strip('"')
API_SECRET = os.getenv("APCA_PAPER_SECRET_KEY", "").strip('"')
BASE_URL = "https://paper-api.alpaca.markets/v2"

headers = {
    "accept": "application/json",
    "content-type": "application/json",
    "APCA-API-KEY-ID": API_KEY,
    "APCA-API-SECRET-KEY": API_SECRET
}

def find_option_symbol(symbol: str, strike: float, expiration_date: str) -> str:
    url = f"{BASE_URL}/options/contracts?underlying_symbols={symbol}&expiration_date={expiration_date}"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        for contract in data.get('option_contracts', []):
            if float(contract['strike_price']) == strike:
                return contract['symbol']
    except Exception as e:
        logger.error("Error fetching option symbol for %s: %s", symbol, e)
    return ""

def trade_calendar_spread(long_symbol: str, short_symbol: str, qty: int) -> None:
    payload = {
        "type": "limit",
        "time_in_force": "day",
        "order_class": "mleg",
        "limit_price": "10",  # Adjust as needed
        "qty": str(qty),
        "legs": [
            {"side": "buy", "position_intent": "buy_to_open", "symbol": long_symbol, "ratio_qty": str(qty)},
            {"side": "sell", "position_intent": "sell_to_open", "symbol": short_symbol, "ratio_qty": str(qty)}
        ]
    }
    try:
        response = requests.post(f"{BASE_URL}/orders", json=payload, headers=headers)
        response.raise_for_status()
        logger.info("Order submitted successfully: %s", response.json())
    except Exception as e:
        logger.error("Error submitting calendar spread orders: %s", e)

def close_all_positions() -> None:
    try:
        response = requests.delete(f"{BASE_URL}/positions", headers=headers)
        response.raise_for_status()
        logger.info("Positions closed successfully: %s", response.json())
    except Exception as e:
        logger.error("Error closing positions: %s", e)

def trader() -> None:
    """
    Daily schedule:
    - At 15 minutes before market close (assumed at 16:00), run the trade finder
      to process only earnings events scheduled between today's close and next day's open.
    - Then, on the next trading day at 15 minutes after market open (assumed at 9:30),
      close all positions.
    """
    while True:
        now = dt.datetime.now()
        # Assume market close at 16:00 local time
        market_close = dt.datetime(now.year, now.month, now.day, 16, 0, tzinfo=dt.timezone.utc)
        trade_exec_time = market_close - dt.timedelta(minutes=15)  # 15 min before close

        # Wait until trade execution time if needed
        if now < trade_exec_time:
            sleep_duration = (trade_exec_time - now).total_seconds()
            logger.info("Waiting %.2f seconds until trade execution at %s", sleep_duration, trade_exec_time)
            time.sleep(sleep_duration)
        
        # Compute next day's market open (assumed at 9:30)
        next_day = now + dt.timedelta(days=1)
        next_market_open = dt.datetime(next_day.year, next_day.month, next_day.day, 9, 30, tzinfo=dt.timezone.utc)
        
        # Get earnings events for tickers (retrieved over a 7-day window)
        tickers = get_spx_tickers()
        earnings = get_upcoming_earnings(tickers, days=1)
        # Filter to include only events scheduled after today's close and before next day's open
        filtered_earnings = {
            ticker: edate for ticker, edate in earnings.items()
            if market_close < edate < next_market_open
        }
        
        if filtered_earnings:
            logger.info("Found upcoming earnings between market close and next market open: %s", filtered_earnings)
            trades = get_calendar_trades(days=1)
            # Filter trades: only include those with earnings dates in the overnight window
            trades = trades[(trades['earnings_date'] > market_close) & (trades['earnings_date'] < next_market_open)]
            if not trades.empty:
                trades.to_csv("calendar_spreads.csv", index=False)
                for _, row in trades.iterrows():
                    ticker = row['ticker']
                    short_call = row['short_call']
                    long_call = row['long_call']
                    qty = row['qty']
                    
                    short_symbol = find_option_symbol(ticker, short_call['strike'], short_call['expiry'])
                    long_symbol = find_option_symbol(ticker, long_call['strike'], long_call['expiry'])
                    
                    if not short_symbol or not long_symbol:
                        logger.warning("Could not retrieve option symbols for %s", ticker)
                        continue
                    
                    trade_calendar_spread(long_symbol, short_symbol, qty)
            else:
                logger.info("No trades meet criteria after filtering for overnight earnings events.")
        else:
            logger.info("No upcoming earnings events between today's close and next market open.")

        # Wait until next trading day at 15 minutes after market open to close positions
        close_positions_time = next_market_open + dt.timedelta(minutes=15)
        sleep_duration = (close_positions_time - dt.datetime.now()).total_seconds()
        if sleep_duration > 0:
            logger.info("Waiting %.2f seconds until positions closing time at %s", sleep_duration, close_positions_time)
            time.sleep(sleep_duration)
        else:
            logger.warning("Positions closing time already passed, skipping sleep.")
        
        close_all_positions()
        
        # Pause briefly before the next cycle starts
        time.sleep(60)

if __name__ == '__main__':
    logger.info("Trader module ready.")
    trader()
