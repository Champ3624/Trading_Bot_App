import yfinance as yf
from datetime import datetime, timedelta
from ticker_filter import get_current_price
from typing import Dict, Union
from utils import find_nearest_expiration

def find_option_strategy(ticker: str, earnings_date: datetime) -> Union[Dict, str]:
    stock = yf.Ticker(ticker)
    current_price = get_current_price(stock)
    if current_price is None:
        return "Error: Unable to retrieve underlying stock price."
    
    expirations = stock.options
    near_term_expiry = find_nearest_expiration(expirations, earnings_date + timedelta(days=10))
    # Convert near_term_expiry to datetime once
    near_term_date = datetime.strptime(near_term_expiry, '%Y-%m-%d')
    long_term_expiry = find_nearest_expiration(expirations, near_term_date + timedelta(days=30))
    
    # Get both option chains once
    near_chain = stock.option_chain(near_term_expiry).calls
    long_chain = stock.option_chain(long_term_expiry).calls

    # Vectorized computation to find the nearest strike
    diffs = (long_chain['strike'] - current_price).abs()
    nearest_strike = long_chain.loc[diffs.idxmin(), 'strike']

    near_call_price = near_chain.loc[near_chain['strike'] == nearest_strike, 'lastPrice'].values
    long_call_price = long_chain.loc[long_chain['strike'] == nearest_strike, 'lastPrice'].values
    
    return {
        'short_call': {
            'strike': nearest_strike,
            'expiry': near_term_expiry,
            'price': near_call_price[0] if near_call_price.size else None
        },
        'long_call': {
            'strike': nearest_strike,
            'expiry': long_term_expiry,
            'price': long_call_price[0] if long_call_price.size else None
        }
    }
