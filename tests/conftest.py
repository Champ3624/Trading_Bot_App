import pytest
import sys
from pathlib import Path

# Add the src directory to the Python path
src_path = str(Path(__file__).parent.parent)
if src_path not in sys.path:
    sys.path.insert(0, src_path)

@pytest.fixture
def mock_api_client():
    """Fixture to provide a mock API client."""
    from unittest.mock import Mock
    client = Mock()
    client.post.return_value = {
        'id': 'test_order_id',
        'legs': [
            {'symbol': 'TEST1', 'side': 'buy'},
            {'symbol': 'TEST2', 'side': 'sell'}
        ]
    }
    client.get.return_value = [
        {'symbol': 'TEST1', 'qty': '10'},
        {'symbol': 'TEST2', 'qty': '10'}
    ]
    return client

@pytest.fixture
def sample_trade_data():
    """Fixture to provide sample trade data."""
    return {
        'ticker': 'TEST',
        'qty': 10,
        'long_symbol': 'TEST1',
        'short_symbol': 'TEST2',
        'success': True,
        'profit_loss': 100.0
    } 