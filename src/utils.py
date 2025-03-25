# filepath: c:\Users\champ\Trading_Bot_App\src\utils.py
import time
import logging
import datetime as dt
import pytz
from typing import List
import pandas as pd
import datetime

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
        spx_table = pd.read_html(
            "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        )[0]
        return spx_table["Symbol"].tolist()
    except Exception as e:
        print(f"Error fetching S&P 500 tickers: {e}")
        return []

def find_nearest_expiration(expirations: List[str], target_date: datetime) -> str:
    target_date = target_date.replace(tzinfo=None)
    # Convert string dates to datetime only once during comparison
    return min(
        expirations,
        key=lambda exp: abs(dt.datetime.strptime(exp, "%Y-%m-%d") - target_date),
    )
