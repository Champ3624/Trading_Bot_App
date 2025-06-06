import unittest
from unittest.mock import Mock, patch
import datetime as dt
import pandas as pd
from trading_bot.trader import (
    trade_calendar_spread,
    close_positions,
    get_todays_trades,
    add_retry_logic,
    validate_trade_params
)
import json
from unittest.mock import mock_open

class TestTrader(unittest.TestCase):
    def setUp(self):
        self.mock_api_client = Mock()
        self.mock_api_client.post.return_value = {
            'id': 'test_order_id',
            'legs': [
                {'symbol': 'TEST1', 'side': 'buy'},
                {'symbol': 'TEST2', 'side': 'sell'}
            ]
        }
        self.mock_api_client.get.return_value = [
            {'symbol': 'TEST1', 'qty': '10'},
            {'symbol': 'TEST2', 'qty': '10'}
        ]

    def test_validate_trade_params_valid(self):
        """Test valid trade parameters."""
        self.assertTrue(validate_trade_params('TEST1', 'TEST2', 10))

    def test_validate_trade_params_invalid(self):
        """Test invalid trade parameters."""
        self.assertFalse(validate_trade_params('', 'TEST2', 10))
        self.assertFalse(validate_trade_params('TEST1', '', 10))
        self.assertFalse(validate_trade_params('TEST1', 'TEST2', 0))
        self.assertFalse(validate_trade_params('TEST1', 'TEST2', -1))

    def test_trade_calendar_spread_success(self):
        """Test successful calendar spread trade."""
        # Create a mock instance for the API client
        mock_instance = Mock()
        mock_instance.post.return_value = {
            'id': 'test_order_id',
            'legs': [
                {'symbol': 'TEST1', 'side': 'buy'},
                {'symbol': 'TEST2', 'side': 'sell'}
            ]
        }

        # Mock the config file opening
        mock_config = {
            'api_key': 'test_key',
            'api_secret': 'test_secret',
            'base_url': 'test_url',
            'market_close_time': 16,
            'market_open_time': 9,
            'default_limit_price': 100
        }

        # Mock both the API client and circuit breaker
        with patch('trading_bot.trader.api_client', mock_instance) as mock_client, \
             patch('trading_bot.trader.circuit_breaker') as mock_circuit_breaker, \
             patch('builtins.open', mock_open(read_data=json.dumps(mock_config))):
            
            # Configure circuit breaker to pass through the function call
            mock_circuit_breaker.execute.side_effect = lambda func, *args, **kwargs: func(*args, **kwargs)
            
            # Call the function under test
            result = trade_calendar_spread('TEST1', 'TEST2', 10)
            
            # Verify the result
            self.assertIsNotNone(result)
            self.assertEqual(result['id'], 'test_order_id')
            
            # Verify the API was called with correct payload
            mock_instance.post.assert_called_once()
            call_args = mock_instance.post.call_args[1]
            self.assertEqual(call_args['endpoint'], '/orders')
            self.assertEqual(call_args['payload']['type'], 'market')
            self.assertEqual(call_args['payload']['time_in_force'], 'day')
            self.assertEqual(call_args['payload']['order_class'], 'mleg')
            self.assertEqual(call_args['payload']['qty'], '10')

    def test_trade_calendar_spread_failure(self):
        """Test failed calendar spread trade."""
        self.mock_api_client.post.return_value = None
        result = trade_calendar_spread(
            long_symbol='TEST1',
            short_symbol='TEST2',
            qty=10
        )
        self.assertIsNone(result)

    def test_close_positions_success(self):
        """Test successful position closing."""
        result = close_positions(positions=[
            {'symbol': 'TEST1'},
            {'symbol': 'TEST2'}
        ])
        self.assertIsNone(result)  # Function returns None on success

    def test_close_positions_no_positions(self):
        """Test closing when no positions exist."""
        result = close_positions(positions=None)
        self.assertIsNone(result)

    def test_close_positions_invalid_data(self):
        """Test closing positions with invalid data."""
        result = close_positions(positions=[{'invalid': 'data'}])
        self.assertIsNone(result)

    def test_get_todays_trades(self):
        """Test getting today's trades."""
        with patch('trading_bot.trader.get_upcoming_earnings') as mock_earnings:
            mock_earnings.return_value = pd.DataFrame({
                'Ticker': ['TEST1', 'TEST2'],
                'Earnings Date': [dt.datetime.now(), dt.datetime.now()]
            })
            
            with patch('trading_bot.trader.process_tickers') as mock_process:
                mock_process.return_value = pd.DataFrame({
                    'Ticker': ['TEST1'],
                    'Earnings Date': [dt.datetime.now()],
                    'Short Leg': [{'symbol': 'TEST1'}],
                    'Long Leg': [{'symbol': 'TEST2'}]
                })
                
                with patch('trading_bot.trader.find_option_strategy') as mock_find:
                    mock_find.return_value = {
                        'near_term': {'symbol': 'TEST1'},
                        'long_term': {'symbol': 'TEST2'}
                    }
                    
                    result = get_todays_trades()
                    self.assertIsInstance(result, pd.DataFrame)
                    self.assertFalse(result.empty)
                    self.assertEqual(len(result), 1)
                    self.assertEqual(result.iloc[0]['Ticker'], 'TEST1')

    def test_get_todays_trades_empty(self):
        """Test getting trades when none are available."""
        with patch('trading_bot.trader.get_upcoming_earnings') as mock_earnings:
            mock_earnings.return_value = pd.DataFrame()
            result = get_todays_trades()
            self.assertIsInstance(result, pd.DataFrame)
            self.assertTrue(result.empty)

    def test_retry_logic(self):
        """Test retry logic for rate-limited calls."""
        call_count = 0
        
        @add_retry_logic
        def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:  # Fail twice, succeed on third try
                raise Exception("Too Many Requests")
            return "Success"
        
        result = failing_function()
        self.assertEqual(result, "Success")
        self.assertEqual(call_count, 3)  # Should have been called 3 times

if __name__ == '__main__':
    unittest.main() 