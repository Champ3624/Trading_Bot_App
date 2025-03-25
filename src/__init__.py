# Optional: configure logging for the package
import logging
from logging.handlers import RotatingFileHandler

file_handler = RotatingFileHandler("trading_bot.log", maxBytes=2_000_000, backupCount=5)
file_handler.setFormatter(
    logging.Formatter("%(asctime)s [%(levelname)s] %(name)s - %(message)s")
)
logging.getLogger().addHandler(file_handler)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
