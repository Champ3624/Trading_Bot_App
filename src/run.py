import threading
from trading_bot.trader import trader as run_trader
from trading_bot.web_interface import run_web_interface

def main():
    # Start the trading bot in a separate thread
    trader_thread = threading.Thread(target=run_trader)
    trader_thread.daemon = True
    trader_thread.start()

    # Run the web interface in the main thread
    run_web_interface(host='0.0.0.0', port=5000)

if __name__ == '__main__':
    main() 