# Trading Bot

An automated options trading bot that specializes in calendar spreads around earnings events. The bot uses the Alpaca API to execute trades and implements various risk management strategies.

## Features

- Automated calendar spread trading around earnings events
- Risk management with circuit breakers
- Configurable trading parameters
- Comprehensive logging and monitoring
- Retry logic for API calls
- Position management and automatic closing

## Prerequisites

- Python 3.8 or higher
- Alpaca trading account (paper or live)
- Required Python packages (see requirements.txt)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/trading-bot.git
cd trading-bot
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

1. Create a `config.json` file in the root directory with the following structure:
```json
{
    "api_key": "your_alpaca_api_key",
    "api_secret": "your_alpaca_api_secret",
    "base_url": "https://paper-api.alpaca.markets",
    "market_close_time": 16,
    "market_open_time": 9,
    "default_limit_price": 100,
    "tickers": ["AAPL", "MSFT", "GOOGL"],
    "default_quantity": 10
}
```

2. Adjust the configuration parameters according to your trading strategy.

## Usage

1. Start the trading bot:
```bash
python -m trading_bot.trader
```

2. Monitor the logs in `trading_bot.log`

3. View trading history in `calendar_spreads.csv`

## Development

### Running Tests
```bash
pytest tests/
```

### Code Coverage
```bash
pytest --cov=src tests/
```

## Monitoring

The bot includes several monitoring features:
- Detailed logging of all trades and operations
- Circuit breaker for risk management
- Position tracking and management
- Error handling and recovery

## Safety Features

- Circuit breaker implementation to prevent excessive losses
- Position size limits
- Automatic position closing
- Retry logic for API calls
- Comprehensive error handling

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This trading bot is for educational purposes only. Use at your own risk. Past performance is not indicative of future results. Always test thoroughly in a paper trading environment before using with real money.
