# __init__.py
import logging
from logging.handlers import RotatingFileHandler
import sys

logger = logging.getLogger("trading_bot")
logger.setLevel(logging.INFO)

# File handler (rotates at 2MB, keeps 5 old logs)
file_handler = RotatingFileHandler("trading_bot.log", maxBytes=2_000_000, backupCount=5)
file_handler.setFormatter(
    logging.Formatter("%(asctime)s [%(levelname)s] %(name)s - %(message)s")
)

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(
    logging.Formatter("%(asctime)s [%(levelname)s] %(name)s - %(message)s")
)

# Avoid duplicate logging by checking for existing handlers
if not logger.hasHandlers():
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
