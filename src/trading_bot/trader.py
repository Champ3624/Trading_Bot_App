import logging
import datetime as dt
import json
import pytz
import pandas as pd
from trading_bot.utils import wait_until, log_trade
from trading_bot.api_client import AlpacaAPIClient
import signal
import sys
from trading_bot.option_finder import find_option_strategy
from trading_bot.earnings_getter import get_upcoming_earnings
from trading_bot.ticker_filter import process_tickers
from trading_bot import __version__
import functools
import time
from typing import Optional, Dict, Any, List
from trading_bot.circuit_breaker import CircuitBreaker
from trading_bot.logging_config import setup_logging

# Setup logging
logger = setup_logging()

# Load configuration
try:
    with open("config.json", "r") as config_file:
        config = json.load(config_file)
except FileNotFoundError:
    logger.error("config.json not found")
    sys.exit(1)
except json.JSONDecodeError:
    logger.error("Invalid JSON in config.json")
    sys.exit(1)

# Validate required configuration
required_config = ["api_key", "api_secret", "base_url", "market_close_time", "market_open_time", "default_limit_price"]
for key in required_config:
    if key not in config:
        logger.error(f"Missing required configuration: {key}")
        sys.exit(1)

API_KEY = config["api_key"]
API_SECRET = config["api_secret"]
BASE_URL = config["base_url"]
MARKET_CLOSE_TIME = config["market_close_time"]
MARKET_OPEN_TIME = config["market_open_time"]
DEFAULT_LIMIT_PRICE = config["default_limit_price"]

# Initialize API client with circuit breaker
api_client = AlpacaAPIClient(BASE_URL, API_KEY, API_SECRET)
circuit_breaker = CircuitBreaker()

eastern = pytz.timezone("America/New_York")

def signal_handler(sig, frame):
    """Handle shutdown signals gracefully."""
    logger.info("Shutdown signal received. Exiting gracefully.")
    sys.exit(0)

def add_retry_logic(func):
    """Decorator to add retry logic for rate-limited API calls."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        max_retries = 3
        base_delay = 1
        for attempt in range(max_retries):
            try:
                return circuit_breaker.execute(func, *args, **kwargs)
            except Exception as e:
                if "Too Many Requests" in str(e):
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"Rate limited, retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    raise
        return None
    return wrapper

def validate_trade_params(long_symbol: str, short_symbol: str, qty: int) -> bool:
    """Validate trading parameters."""
    if not isinstance(long_symbol, str) or not long_symbol:
        logger.error("Invalid long_symbol")
        return False
    if not isinstance(short_symbol, str) or not short_symbol:
        logger.error("Invalid short_symbol")
        return False
    if not isinstance(qty, int) or qty <= 0:
        logger.error("Invalid quantity")
        return False
    return True

@add_retry_logic
def trade_calendar_spread(long_symbol: str, short_symbol: str, qty: int = 10) -> Optional[Dict[str, Any]]:
    """
    Place a calendar spread trade.
    
    Args:
        long_symbol: Symbol for the long leg
        short_symbol: Symbol for the short leg
        qty: Quantity of contracts
        
    Returns:
        Dict containing order details if successful, None otherwise
    """
    if not validate_trade_params(long_symbol, short_symbol, qty):
        return None

    logger.info(
        "Placing calendar spread: Long %s | Short %s | Qty: %d",
        long_symbol,
        short_symbol,
        qty,
    )

    payload = {
        "type": "market",
        "time_in_force": "day",
        "order_class": "mleg",
        "qty": str(qty),
        "legs": [
            {
                "side": "buy",
                "position_intent": "buy_to_open",
                "symbol": long_symbol,
                "ratio_qty": str(qty),
            },
            {
                "side": "sell",
                "position_intent": "sell_to_open",
                "symbol": short_symbol,
                "ratio_qty": str(qty),
            },
        ],
    }
    
    try:
        response = api_client.post(endpoint="/orders", payload=payload)
        if response:
            logger.info("Order submitted successfully: %s", response)
            return response
        else:
            logger.error("Order submission failed.")
            return None
    except Exception as e:
        logger.error("Error submitting calendar spread orders: %s", e)
        return None

@add_retry_logic
def close_positions(positions: Optional[List[Dict[str, Any]]] = None) -> None:
    """
    Close all open positions.
    
    Args:
        positions: Optional list of positions to close. If None, fetches current positions.
    """
    try:
        positions = positions if positions is not None else api_client.get("/positions")
        if positions is None:
            logger.error("Failed to fetch positions or no positions open.")
            return
            
        for position in positions:
            symbol = position.get("symbol")
            if not symbol:
                logger.error("Invalid position data: missing symbol")
                continue

            logger.info("Closing position: %s", symbol)
            try:
                report = api_client.delete(f"/positions/{symbol}")
                if report:
                    logger.info(f"Successfully closed position for {symbol}")
                else:
                    logger.error(f"Failed to close position for {symbol}")
            except Exception as e:
                logger.error(f"Error closing position for {symbol}: {str(e)}")
    except Exception as e:
        logger.error(f"Error in close_positions: {str(e)}")

def get_todays_trades(days: int = 1) -> pd.DataFrame:
    """
    Get today's trading opportunities.
    
    Args:
        days: Number of days to look ahead for earnings
        
    Returns:
        DataFrame containing valid trading opportunities
    """
    try:
        tickers = config.get("tickers", [])
        if not tickers:
            logger.error("No tickers configured")
            return pd.DataFrame()
            
        upcoming = get_upcoming_earnings(tickers, days=days)
        if upcoming is None or upcoming.empty:
            logger.warning("No upcoming earnings found")
            return pd.DataFrame()
            
        df = process_tickers(upcoming)
        if df is None or df.empty:
            logger.warning("No valid trades after processing")
            return pd.DataFrame()
            
        for index, row in df.iterrows():
            strat = find_option_strategy(row["Ticker"], row["Earnings Date"], api_client)
            if isinstance(strat, str):
                logger.warning("Skipping %s: %s", row["Ticker"], strat)
                df.drop(index, inplace=True)
                continue
            df.at[index, "Short Leg"] = strat["near_term"]
            df.at[index, "Long Leg"] = strat["long_term"]

        return df[~df["Short Leg"].isnull() & ~df["Long Leg"].isnull()]
    except Exception as e:
        logger.error(f"Error in get_todays_trades: {str(e)}")
        return pd.DataFrame()

def trader() -> None:
    """
    Main trading loop.
    
    Daily schedule:
    - At 15 minutes before market close, run the trade finder
      to process only earnings events scheduled between today's close and next day's open.
    - Then, on the next trading day at 15 minutes after market open,
      close all positions.
    """
    while True:
        try:
            now = dt.datetime.now(eastern)
            logger.info("Running trade cycle on %s", now.strftime("%Y-%m-%d %H:%M:%S"))

            # Assume market close at 16:00 local time
            market_close = eastern.localize(
                dt.datetime(now.year, now.month, now.day, MARKET_CLOSE_TIME)
            )
            trade_exec_time = market_close - dt.timedelta(minutes=15)

            # Wait until trade execution time if needed
            if now < trade_exec_time:
                wait_until(trade_exec_time)

            # Compute next day's market open
            next_day = now + dt.timedelta(days=1)
            next_market_open = eastern.localize(
                dt.datetime(next_day.year, next_day.month, next_day.day, MARKET_OPEN_TIME)
            )

            trades = get_todays_trades()
            if not trades.empty:
                for _, row in trades.iterrows():
                    ticker = row["Ticker"]
                    short_call = row["Short Leg"]
                    long_call = row["Long Leg"]
                    qty = config.get("default_quantity", 10)

                    short_symbol = short_call["symbol"]
                    long_symbol = long_call["symbol"]

                    if not short_symbol or not long_symbol:
                        logger.warning("Could not retrieve option symbols for %s", ticker)
                        continue

                    trade_result = trade_calendar_spread(
                        long_symbol=long_symbol,
                        short_symbol=short_symbol,
                        qty=qty
                    )
                    
                    if trade_result:
                        log_trade(
                            ticker=ticker,
                            qty=qty,
                            long_symbol=long_symbol,
                            long_call=trade_result['legs'][0],
                            short_symbol=short_symbol,
                            short_call=trade_result['legs'][1],
                            recommendation=row['Recommendation']
                        )
            else:
                logger.info("No trades meet criteria after filtering for overnight earnings events.")

            # Wait until next trading day at 15 minutes after market open to close positions
            close_positions_time = next_market_open + dt.timedelta(minutes=45)
            sleep_duration = (close_positions_time - dt.datetime.now(eastern)).total_seconds()
            if sleep_duration > 0:
                wait_until(close_positions_time)
            else:
                logger.warning("Positions closing time already passed, skipping sleep.")

            close_positions()
            
        except Exception as e:
            logger.error(f"Error in main trading loop: {str(e)}")
            time.sleep(60)  # Wait a minute before retrying

if __name__ == "__main__":
    # Enable signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        trader()
    except Exception as e:
        logger.error(f"Fatal error in main: {str(e)}")
        sys.exit(1)