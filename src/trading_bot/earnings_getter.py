# Improved earnings_getter.py
import pandas as pd
import yfinance as yf
import datetime as dt
from typing import List
import pytz
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from trading_bot.utils import get_spx_tickers


logger = logging.getLogger("trading_bot")


def get_upcoming_earnings(tickers: List[str], days: int = 1) -> pd.DataFrame:
    ticker_earnings = (
        []
    )  # Store data as a list to avoid expensive DataFrame concatenation
    now = dt.datetime.now(dt.timezone.utc)
    future_limit = now + dt.timedelta(days=days)
    ny_tz = pytz.timezone("America/New_York")

    def fetch_earnings(ticker):
        try:
            # Handle .B suffix stocks by removing it for yfinance
            yf_ticker = ticker.replace('.B', '-B')
            stock = yf.Ticker(yf_ticker)
            
            try:
                dates = stock.earnings_dates
                if dates is None or dates.empty:
                    logger.warning(f"No earnings dates found for {ticker}.")
                    return None
                    
                dates = dates.sort_index()
            except (AttributeError, TypeError):
                logger.warning(f"No earnings dates found for {ticker}.")
                return None

            for earnings_date in dates.index:
                earnings_datetime = (
                    pd.to_datetime(earnings_date).tz_convert("UTC").astimezone(ny_tz)
                )
                if now < earnings_datetime < future_limit:
                    return {
                        "Ticker": ticker,
                        "Earnings DateTime": earnings_datetime,
                        "Recommendation": None,
                        "Expected Move": None,
                        "Short Leg": None,
                        "Long Leg": None,
                    }
        except Exception as e:
            logger.error(f"Error fetching earnings for {ticker}: {e}")
        return None

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(fetch_earnings, ticker): ticker for ticker in tickers
        }
        for future in as_completed(futures):
            result = future.result()
            if result:
                ticker_earnings.append(result)

    # Convert the list of dictionaries to a DataFrame
    df = pd.DataFrame(ticker_earnings)
    if df.empty:
        logger.warning("No earnings data retrieved.")

    return df


if __name__ == '__main__':
    # Example usage
    tickers = get_spx_tickers()  # Fetch S&P 500 tickers
    earnings_data = get_upcoming_earnings(tickers, days=1)
    print(earnings_data)