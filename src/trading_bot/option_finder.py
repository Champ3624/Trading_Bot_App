# Improved option_finder.py
import yfinance as yf
import datetime as dt
from typing import Dict, Union
from .utils import find_nearest_expiration
import logging
import json
from .api_client import AlpacaAPIClient

logger = logging.getLogger("trading_bot")


def find_option_strategy(
    ticker: str, earnings_date: dt.datetime, client: AlpacaAPIClient
) -> Union[Dict[str, Dict[str, str]], None]:
    try:
        logger.info(f"Starting to find option strategy for ticker: {ticker}")
        stock = yf.Ticker(ticker)

        try:
            expirations = list(stock.options)
            if not expirations:
                logger.error(f"No options found for ticker {ticker}.")
                return None
        except Exception as e:
            logger.error(f"Error fetching options for {ticker}: {e}")
            return None

        current_price = client.get(endpoint='stocks/trades/latest', params={'symbols': ticker}, base='data')['trades'][ticker]['p']
        if current_price is None:
            logger.error(f"Failed to fetch current price for {ticker}.")
            return None
        logger.info(f"Current price for {ticker}: {current_price}")

        near_term_expiry = find_nearest_expiration(
            expirations, earnings_date + dt.timedelta(days=7)
        )
        long_term_expiry = find_nearest_expiration(
            expirations,
            dt.datetime.strptime(near_term_expiry, "%Y-%m-%d") + dt.timedelta(days=30),
        )

        logger.info(
            f"Near-term expiration date: {near_term_expiry}, Long-term expiration date: {long_term_expiry}"
        )

        try:
            near_term_options = client.get(
                f"/options/contracts",
                params={
                    "underlying_symbols": ticker,
                    "expiration_date": near_term_expiry,
                    "type": "call",
                },
            )
            long_term_options = client.get(
                f"/options/contracts",
                params={
                    "underlying_symbols": ticker,
                    "expiration_date": long_term_expiry,
                    "type": "call",
                },
            )

            if near_term_options is None or long_term_options is None:
                logger.error(f"Failed to fetch options data for {ticker}.")
                return None

        except Exception as e:
            logger.error(f"Error fetching options data for {ticker}: {e}")
            return None

        try:
            long_term_strike = min(
                long_term_options.get("option_contracts", []),
                key=lambda x: abs(float(x["strike_price"]) - current_price),
            )
        except Exception as e:
            logger.error(f"Failed to find nearest strike price for {ticker}: {e}")
            return None

        try:
            long_call = next(
                option
                for option in long_term_options["option_contracts"]
                if float(option["strike_price"])
                == float(long_term_strike["strike_price"])
            )

            near_call = next(
                option
                for option in near_term_options["option_contracts"]
                if float(option["strike_price"])
                == float(long_term_strike["strike_price"])
            )
        except StopIteration:
            logger.error(f"Could not find matching strike prices for {ticker}.")
            return None

        logger.info(f"Option strategy successfully found for {ticker}")
        return {"near_term": near_call, "long_term": long_call}

    except Exception as e:
        logger.error(f"Error in find_option_strategy for {ticker}: {e}")
        return None

if __name__ == '__main__':
    # Example usage
    ticker = "AAPL"
    earnings_date = dt.datetime.now() + dt.timedelta(days=1)  # Example earnings date
    
    with open("config.json", "r") as config_file:
        config = json.load(config_file)
    # Assuming the config file contains API_KEY, API_SECRET, and BASE_URL
    API_KEY = config["api_key"]
    API_SECRET = config["api_secret"]
    BASE_URL = config["base_url"]
    
    api_client = AlpacaAPIClient(BASE_URL, API_KEY, API_SECRET)

    strategy = find_option_strategy(ticker, earnings_date, api_client)
    
    if strategy:
        print(f"Option strategy for {ticker}: {strategy}")
    else:
        print(f"No option strategy found for {ticker}.")