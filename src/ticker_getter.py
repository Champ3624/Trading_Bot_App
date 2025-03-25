import pandas as pd
import yfinance as yf
import datetime as dt
from typing import List, Dict

def get_spx_tickers() -> List[str]:
    try:
        spx_table = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]
        return spx_table['Symbol'].tolist()
    except Exception as e:
        print(f"Error fetching S&P 500 tickers: {e}")
        return []

def get_upcoming_earnings(tickers: List[str], days: int = 2) -> Dict[str, dt.datetime]:
    ticker_earnings = {}
    now = dt.datetime.now()
    future_limit = now + dt.timedelta(days=days)

    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            # Compute earnings dates once and filter using list comprehension.
            earnings_dates = (date for date in stock.earnings_dates.sort_index().index
                              if now < dt.datetime(date.year, date.month, date.day) < future_limit)
            # Get the first upcoming earnings date (if any)
            upcoming = next(earnings_dates, None)
            if upcoming:
                ticker_earnings[ticker] = upcoming.to_pydatetime()
        except Exception as e:
            print(f"Error fetching earnings for {ticker}: {e}")
    return ticker_earnings