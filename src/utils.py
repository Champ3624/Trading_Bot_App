# filepath: c:\Users\champ\Trading_Bot_App\src\utils.py
import time
import logging
import datetime as dt
import pytz
from typing import List
import pandas as pd
import datetime
from earnings_getter import get_upcoming_earnings
from ticker_filter import process_tickers
from option_finder import find_option_strategy

eastern = pytz.timezone("America/New_York")

logger = logging.getLogger(__name__)

def wait_until(target_time):
    """Wait until the specified datetime."""
    now = dt.datetime.now(eastern)
    sleep_duration = (target_time - now).total_seconds()
    if sleep_duration > 0:
        logger.info("Waiting %.2f seconds until %s", sleep_duration, target_time)
        time.sleep(sleep_duration)
    else:
        logger.warning("Target time %s already passed, skipping wait.", target_time)
        
def get_spx_tickers() -> List[str]:
    try:
        spx_table = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]
        return spx_table['Symbol'].tolist()
    except Exception as e:
        print(f"Error fetching S&P 500 tickers: {e}")
        return []

def get_current_price(ticker):
    todays_data = ticker.history(period='1d')
    if todays_data.empty:
        raise ValueError("No market data available for today.")
    return todays_data['Close'].iloc[0]

def find_nearest_expiration(expirations: List[str], target_date: datetime) -> str:
    target_date = target_date.replace(tzinfo=None)
    # Convert string dates to datetime only once during comparison
    return min(expirations, key=lambda exp: abs(datetime.strptime(exp, '%Y-%m-%d') - target_date))

def get_todays_trades() -> pd.DataFrame:
    tickers = get_spx_tickers()
    upcoming = get_upcoming_earnings(tickers)
    df = process_tickers(upcoming)
    for index, row in df.iterrows():
        strat = find_option_strategy(row[0], row[1])
        df.at[index, 'Short Leg'] = strat['short_call']
        df.at[index, 'Long Leg'] = strat['long_call']
        
    return df