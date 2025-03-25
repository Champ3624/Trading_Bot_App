import pandas as pd
import yfinance as yf
import datetime as dt
from typing import List
import pytz


def get_upcoming_earnings(tickers: List[str], days: int = 1) -> pd.DataFrame:
    ticker_earnings = pd.DataFrame(
        columns=[
            "Ticker",
            "Earnings DateTime",
            "Recommendation",
            "Expected Move",
            "Short Leg",
            "Long Leg",
        ]
    )
    now = dt.datetime.now(dt.timezone.utc)
    future_limit = now + dt.timedelta(days=days)
    ny_tz = pytz.timezone("America/New_York")

    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            # Fetch earnings dates
            dates = stock.earnings_dates.sort_index()
            if not dates.empty:
                for earnings_date in dates.index:
                    earnings_datetime = (
                        pd.to_datetime(earnings_date)
                        .tz_convert("UTC")
                        .astimezone(ny_tz)
                    )
                    if now < earnings_datetime < future_limit:
                        ticker_earnings = pd.concat(
                            [
                                ticker_earnings,
                                pd.DataFrame(
                                    {
                                        "Ticker": [ticker],
                                        "Earnings DateTime": [earnings_datetime],
                                        "Recommendation": [
                                            None
                                        ],  # Placeholder for recommendation
                                        "Expected Move": [None],
                                        "Short Leg": [
                                            None
                                        ],  # Placeholder for short leg
                                        "Long Leg": [None],  # Placeholder for long leg
                                    }
                                ),
                            ],
                            ignore_index=True,
                        )
        except Exception as e:
            print(f"Error fetching earnings for {ticker}: {e}")

    return ticker_earnings
