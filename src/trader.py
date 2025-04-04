import logging
import datetime as dt
import json
import pytz
import pandas as pd
from utils import wait_until, log_trade
from api_client import AlpacaAPIClient
import signal
import sys
from option_finder import find_option_strategy
from earnings_getter import get_upcoming_earnings
from ticker_filter import process_tickers
import __init__

logger = logging.getLogger("trading_bot")

with open("config.json", "r") as config_file:
    config = json.load(config_file)

API_KEY = config["api_key"]
API_SECRET = config["api_secret"]
BASE_URL = config["base_url"]
MARKET_CLOSE_TIME = config["market_close_time"]
MARKET_OPEN_TIME = config["market_open_time"]
DEFAULT_LIMIT_PRICE = config["default_limit_price"]

api_client = AlpacaAPIClient(BASE_URL, API_KEY, API_SECRET)

eastern = pytz.timezone("America/New_York")


def signal_handler(sig, frame):
    logger.info("Shutdown signal received. Exiting gracefully.")
    sys.exit(0)


def trade_calendar_spread(long_symbol: str, short_symbol: str, qty: int = 10):
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


def close_positions(positions=None) -> None:
    positions = positions if positions is not None else api_client.get("/positions")
    if positions is None:
        logger.error("Failed to fetch positions or no positions open.")
        return
    for position in positions:
        symbol = position["symbol"]

        logger.info("Closing position: %s", symbol)

        try:
            api_client.delete(f"/positions/{symbol}")
        except Exception as e:
            logger.error(
                "Error closing position for %s or %s: %s", symbol, e
            )


def get_todays_trades(days=1) -> pd.DataFrame:
    tickers = config["tickers"]
    upcoming = get_upcoming_earnings(tickers, days=days)
    df = process_tickers(upcoming)
    for index, row in df.iterrows():
        strat = find_option_strategy(row["Ticker"], row["Earnings Date"], api_client)
        if isinstance(strat, str):
            logger.warning("Skipping %s: %s", row["Ticker"], strat)
            df.drop(index, inplace=True)
            continue
        df.at[index, "Short Leg"] = strat["near_term"]
        df.at[index, "Long Leg"] = strat["long_term"]

    return df[~df["Short Leg"].isnull() & ~df["Long Leg"].isnull()]


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
        logger.info("Running trade cycle on %s", now.strftime("%Y-%m-%d %H:%M:%S"))

        # Assume market close at 16:00 local time
        market_close = eastern.localize(
            dt.datetime(now.year, now.month, now.day, MARKET_CLOSE_TIME)
        )
        trade_exec_time = market_close - dt.timedelta(minutes=15)  # 15 min before close

        # Wait until trade execution time if needed
        if now < trade_exec_time:
            wait_until(trade_exec_time)

        # Compute next day's market open (assumed at 9:30)
        next_day = now + dt.timedelta(days=1)
        next_market_open = eastern.localize(
            dt.datetime(next_day.year, next_day.month, next_day.day, MARKET_OPEN_TIME)
        )

        try:
            trades = get_todays_trades()
        except Exception as e:
            logger.error("Error fetching today's trades: %s", e)
            trades = pd.DataFrame()

        if not trades.empty:
            for _, row in trades.iterrows():
                ticker = row["Ticker"]
                short_call = row["Short Leg"]
                long_call = row["Long Leg"]
                qty = 10 # Default quantity

                short_symbol = short_call["symbol"]
                long_symbol = long_call["symbol"]

                if not short_symbol or not long_symbol:
                    logger.warning("Could not retrieve option symbols for %s", ticker)
                    continue

                trade_result = trade_calendar_spread(long_symbol=long_symbol, short_symbol=short_symbol, qty=qty)
                
                if trade_result:
                    log_trade(
                        ticker=ticker,
                        qty=qty,
                        long_symbol=long_symbol,
                        long_call=trade_result['legs'][0],
                        short_symbol=short_symbol,
                        short_call=trade_result['legs'][1],
                        recommendation=row['Recommendation']  # or come from 'df' column
                    )
        else:
            logger.info(
                "No trades meet criteria after filtering for overnight earnings events."
            )

        # Wait until next trading day at 15 minutes after market open to close positions
        close_positions_time = next_market_open + dt.timedelta(minutes=45)
        sleep_duration = (
            close_positions_time - dt.datetime.now(eastern)
        ).total_seconds()
        if sleep_duration > 0:
            wait_until(close_positions_time)
        else:
            logger.warning("Positions closing time already passed, skipping sleep.")

        # positions = trades[["Short Leg", "Long Leg"]].values.flatten().tolist()
        # close_positions(positions=positions)
        close_positions()


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    trader()