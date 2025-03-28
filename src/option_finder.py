import yfinance as yf
import datetime as dt
from ticker_filter import get_current_price
from typing import Dict, Union
from utils import find_nearest_expiration
import logging
from api_client import AlpacaAPIClient
import json

logger = logging.getLogger("trade_bot.log")
logging.basicConfig(level=logging.INFO)

def find_option_strategy(ticker: str, earnings_date: dt.datetime, client: AlpacaAPIClient) -> Union[Dict[str, Dict[str, str]], None]:
    try:
        logger.info(f"Starting to find option strategy for ticker: {ticker}")
        
        # Fetch expiration dates using Alpaca API
        stock = yf.Ticker(ticker)
        options = stock.options
        expirations = list(options)
         
        logger.info(f"Fetched expiration dates for {ticker}: {expirations}")
        
        current_price = client.get_asset_price(ticker)
        logger.info(f"Current price for {ticker}: {current_price}")
        
        # Find near-term and long-term expirations
        near_term_expiry = find_nearest_expiration(
            expirations, earnings_date + dt.timedelta(days=10)
        )
        logger.info(f"Near-term expiration date for {ticker}: {near_term_expiry}")
        
        long_term_expiry = find_nearest_expiration(
            expirations, dt.datetime.strptime(near_term_expiry, "%Y-%m-%d") + dt.timedelta(days=30)
        )
        logger.info(f"Long-term expiration date for {ticker}: {long_term_expiry}")

        # Fetch options data from Alpaca API
        logger.info(f"Fetching near-term options for {ticker} with expiration {near_term_expiry}")
        near_term_options = client.get(
            f"/options/contracts",
            params={"underlying_symbols": ticker, "expiration_date": near_term_expiry, "type": "call"}
        )
        
        logger.info(f"Fetching long-term options for {ticker} with expiration {long_term_expiry}")
        long_term_options = client.get(
            f"/options/contracts",
            params={"underlying_symbols": ticker, "expiration_date": long_term_expiry, "type": "call"}
        )

        # Check if data was retrieved successfully
        if near_term_options is None or long_term_options is None:
            logger.error("Failed to fetch options data from Alpaca.")
            return None

        logger.info(f"Successfully fetched options data for {ticker}")

        # Find the strike closest to the current price
        long_term_strike = min(
            long_term_options["option_contracts"],
            key=lambda x: abs(float(x["strike_price"]) - current_price),
        )
        logger.info(f"Closest strike price to current price for long-term options: {long_term_strike['strike_price']}")

        # Extract the corresponding option contracts
        long_call = next(
            option for option in long_term_options["option_contracts"]
            if float(option["strike_price"]) == float(long_term_strike["strike_price"])
        )
        logger.info(f"Selected long-term call option: {long_call}")
        
        near_call = next(
            option for option in near_term_options["option_contracts"]
            if float(option["strike_price"]) == float(long_term_strike["strike_price"])
        )
        logger.info(f"Selected near-term call option: {near_call}")
        
        # Return the fetched data
        logger.info(f"Option strategy successfully found for {ticker}")
        return {
            "near_term": near_call,
            "long_term": long_call
        }

    except Exception as e:
        logger.error(f"Error in find_option_strategy for {ticker}: {e}")
        return None