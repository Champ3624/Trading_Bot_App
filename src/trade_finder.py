import pandas as pd
from ticker_getter import get_spx_tickers, get_upcoming_earnings
from ticker_filter import process_tickers
from option_finder import find_option_strategy
import logging

logger = logging.getLogger(__name__)

def get_calendar_trades(days=7) -> pd.DataFrame:
    spx_tickers = get_spx_tickers()
    earnings = get_upcoming_earnings(spx_tickers, days=days)
    approved_tickers = process_tickers(list(earnings.keys()))
    trades_list = []
    
    for ticker, details in approved_tickers.items():
        try:
            strategy = find_option_strategy(ticker, earnings[ticker])
            trades_list.append({
                'ticker': ticker,
                'earnings_date': earnings[ticker],
                'recommendation': details['Recommendation'],
                'short_call': strategy['short_call'],
                'long_call': strategy['long_call'],
                'qty': 1  # default quantity; adjust as needed
            })
        except Exception as e:
            logger.error("Error processing %s: %s", ticker, e)
    
    return pd.DataFrame(trades_list)


print(get_calendar_trades())