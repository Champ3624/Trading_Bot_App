# src/trading_bot/__init__.py

from .ticker_getter import get_spx_tickers, get_upcoming_earnings
from .trader import trader, close_all_positions, trade_calendar_spread
from .option_finder import find_option_strategy
from .ticker_filter import compute_recommendation, process_tickers
from .trade_finder import get_calendar_trades

# Optional: configure logging for the package
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
