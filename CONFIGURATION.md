# Configuration Guide

This guide explains how to configure the trading bot for your specific needs.

## Configuration File

The bot uses a `config.json` file for all configuration settings. Here's a detailed explanation of each setting:

### API Configuration
```json
{
    "api_key": "your_alpaca_api_key",
    "api_secret": "your_alpaca_api_secret",
    "base_url": "https://paper-api.alpaca.markets"
}
```
- `api_key`: Your Alpaca API key
- `api_secret`: Your Alpaca API secret
- `base_url`: The Alpaca API endpoint (use paper trading URL for testing)

### Market Hours
```json
{
    "market_open_time": 9,
    "market_close_time": 16
}
```
- `market_open_time`: Market open hour (24-hour format)
- `market_close_time`: Market close hour (24-hour format)

### Trading Parameters
```json
{
    "default_limit_price": 100,
    "default_quantity": 10,
    "tickers": ["AAPL", "MSFT", "GOOGL"]
}
```
- `default_limit_price`: Default limit price for orders
- `default_quantity`: Default number of contracts per trade
- `tickers`: List of stock symbols to monitor

### Risk Management
```json
{
    "max_position_size": 1000,
    "max_daily_trades": 5,
    "max_loss_per_trade": 100
}
```
- `max_position_size`: Maximum position size in dollars
- `max_daily_trades`: Maximum number of trades per day
- `max_loss_per_trade`: Maximum loss allowed per trade

### Circuit Breaker Settings
```json
{
    "circuit_breaker": {
        "max_daily_loss": 500,
        "max_consecutive_losses": 3,
        "cooldown_period": 24
    }
}
```
- `max_daily_loss`: Maximum loss allowed per day
- `max_consecutive_losses`: Maximum consecutive losing trades
- `cooldown_period`: Hours to wait after circuit breaker triggers

## Environment Variables

The bot also supports configuration through environment variables:

```bash
export ALPACA_API_KEY="your_api_key"
export ALPACA_API_SECRET="your_api_secret"
export ALPACA_BASE_URL="https://paper-api.alpaca.markets"
```

## Logging Configuration

Logging can be configured in `logging_config.py`:

```python
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = "trading_bot.log"
```

## Best Practices

1. Always start with paper trading
2. Use conservative position sizes initially
3. Monitor the bot's performance regularly
4. Keep your API keys secure
5. Regularly backup your configuration
6. Test configuration changes in a paper trading environment first

## Troubleshooting

Common configuration issues and solutions:

1. API Connection Issues
   - Verify API keys are correct
   - Check internet connection
   - Ensure you're using the correct base URL

2. Trading Issues
   - Verify market hours are correct
   - Check position size limits
   - Ensure sufficient buying power

3. Logging Issues
   - Check log file permissions
   - Verify log directory exists
   - Ensure sufficient disk space

## Security Considerations

1. Never commit API keys to version control
2. Use environment variables for sensitive data
3. Regularly rotate API keys
4. Use paper trading for testing
5. Implement proper error handling
6. Monitor for suspicious activity 