import logging
import time
from datetime import datetime
import psutil
import requests
from typing import Dict, Any, Optional
import json
import os

logger = logging.getLogger(__name__)

class SystemMonitor:
    def __init__(self, alert_thresholds: Optional[Dict[str, float]] = None):
        self.alert_thresholds = alert_thresholds or {
            'cpu_percent': 80.0,
            'memory_percent': 80.0,
            'disk_percent': 80.0
        }
        self.last_check = time.time()
        self.metrics_history = []

    def get_system_metrics(self) -> Dict[str, float]:
        """Get current system metrics."""
        return {
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'timestamp': time.time()
        }

    def check_alerts(self, metrics: Dict[str, float]) -> None:
        """Check if any metrics exceed thresholds and log alerts."""
        for metric, value in metrics.items():
            if metric in self.alert_thresholds and value > self.alert_thresholds[metric]:
                logger.warning(
                    f"Alert: {metric} at {value}% exceeds threshold of {self.alert_thresholds[metric]}%"
                )

    def monitor(self) -> None:
        """Monitor system health and log metrics."""
        try:
            metrics = self.get_system_metrics()
            self.check_alerts(metrics)
            self.metrics_history.append(metrics)
            
            # Keep only last 24 hours of metrics (assuming 1-minute intervals)
            if len(self.metrics_history) > 1440:
                self.metrics_history = self.metrics_history[-1440:]
                
            logger.info(f"System metrics: {json.dumps(metrics)}")
            
        except Exception as e:
            logger.error(f"Error in system monitoring: {str(e)}")

class APIMonitor:
    def __init__(self, api_client):
        self.api_client = api_client
        self.request_history = []
        self.error_count = 0
        self.last_successful_request = None

    def track_request(self, endpoint: str, success: bool, response_time: float) -> None:
        """Track API request metrics."""
        request_data = {
            'endpoint': endpoint,
            'success': success,
            'response_time': response_time,
            'timestamp': time.time()
        }
        self.request_history.append(request_data)
        
        if not success:
            self.error_count += 1
        else:
            self.last_successful_request = time.time()
            self.error_count = 0

    def get_api_health(self) -> Dict[str, Any]:
        """Get API health metrics."""
        if not self.request_history:
            return {'status': 'unknown', 'error_rate': 0.0}
            
        recent_requests = self.request_history[-100:]  # Last 100 requests
        error_rate = sum(1 for r in recent_requests if not r['success']) / len(recent_requests)
        
        return {
            'status': 'healthy' if error_rate < 0.1 else 'degraded',
            'error_rate': error_rate,
            'last_successful_request': self.last_successful_request,
            'total_requests': len(self.request_history),
            'error_count': self.error_count
        }

    def monitor(self) -> None:
        """Monitor API health and log metrics."""
        try:
            health_metrics = self.get_api_health()
            logger.info(f"API health metrics: {json.dumps(health_metrics)}")
            
            if health_metrics['status'] == 'degraded':
                logger.warning("API health is degraded")
                
        except Exception as e:
            logger.error(f"Error in API monitoring: {str(e)}")

class TradeMonitor:
    def __init__(self):
        self.trade_history = []
        self.profit_loss = 0.0
        self.total_trades = 0
        self.successful_trades = 0

    def track_trade(self, trade_data: Dict[str, Any]) -> None:
        """Track trade execution and results."""
        self.trade_history.append({
            **trade_data,
            'timestamp': time.time()
        })
        self.total_trades += 1
        
        if trade_data.get('success', False):
            self.successful_trades += 1
            self.profit_loss += trade_data.get('profit_loss', 0.0)

    def get_trade_metrics(self) -> Dict[str, Any]:
        """Get trading performance metrics."""
        if not self.trade_history:
            return {
                'total_trades': 0,
                'success_rate': 0.0,
                'profit_loss': 0.0
            }
            
        return {
            'total_trades': self.total_trades,
            'success_rate': self.successful_trades / self.total_trades,
            'profit_loss': self.profit_loss,
            'recent_trades': self.trade_history[-10:]  # Last 10 trades
        }

    def monitor(self) -> None:
        """Monitor trading performance and log metrics."""
        try:
            trade_metrics = self.get_trade_metrics()
            logger.info(f"Trading metrics: {json.dumps(trade_metrics)}")
            
            if trade_metrics['success_rate'] < 0.5:
                logger.warning("Trading success rate is below 50%")
                
        except Exception as e:
            logger.error(f"Error in trade monitoring: {str(e)}")

class Monitoring:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.telegram_enabled = config.get('monitoring', {}).get('enable_telegram', False)
        self.telegram_token = config.get('monitoring', {}).get('telegram_bot_token')
        self.telegram_chat_id = config.get('monitoring', {}).get('telegram_chat_id')
        self.alert_on_trade = config.get('monitoring', {}).get('alert_on_trade', True)
        self.alert_on_error = config.get('monitoring', {}).get('alert_on_error', True)
        self.alert_on_circuit_breaker = config.get('monitoring', {}).get('alert_on_circuit_breaker', True)

    def send_telegram_message(self, message: str) -> bool:
        """Send a message via Telegram."""
        if not self.telegram_enabled or not self.telegram_token or not self.telegram_chat_id:
            return False

        try:
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            data = {
                "chat_id": self.telegram_chat_id,
                "text": message,
                "parse_mode": "HTML"
            }
            response = requests.post(url, data=data)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {str(e)}")
            return False

    def alert_trade(self, trade_details: Dict[str, Any]) -> None:
        """Alert on trade execution."""
        if not self.alert_on_trade:
            return

        message = (
            f"🔔 <b>Trade Executed</b>\n\n"
            f"Symbol: {trade_details.get('symbol')}\n"
            f"Type: {trade_details.get('type')}\n"
            f"Quantity: {trade_details.get('qty')}\n"
            f"Price: ${trade_details.get('price', 'N/A')}\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        self.send_telegram_message(message)

    def alert_error(self, error_message: str) -> None:
        """Alert on error occurrence."""
        if not self.alert_on_error:
            return

        message = (
            f"⚠️ <b>Error Alert</b>\n\n"
            f"Message: {error_message}\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        self.send_telegram_message(message)

    def alert_circuit_breaker(self, reason: str) -> None:
        """Alert on circuit breaker trigger."""
        if not self.alert_on_circuit_breaker:
            return

        message = (
            f"🔴 <b>Circuit Breaker Triggered</b>\n\n"
            f"Reason: {reason}\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        self.send_telegram_message(message)

    def check_system_health(self) -> Dict[str, Any]:
        """Check system health metrics."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            health_data = {
                'cpu_usage': cpu_percent,
                'memory_usage': memory.percent,
                'disk_usage': disk.percent,
                'timestamp': datetime.now().isoformat()
            }

            # Alert if any metric is above threshold
            if cpu_percent > 80 or memory.percent > 80 or disk.percent > 80:
                message = (
                    f"⚠️ <b>System Health Alert</b>\n\n"
                    f"CPU Usage: {cpu_percent}%\n"
                    f"Memory Usage: {memory.percent}%\n"
                    f"Disk Usage: {disk.percent}%\n"
                    f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                self.send_telegram_message(message)

            return health_data
        except Exception as e:
            logger.error(f"Failed to check system health: {str(e)}")
            return {}

    def log_health_metrics(self, health_data: Dict[str, Any]) -> None:
        """Log health metrics to file."""
        try:
            log_file = os.path.join('logs', 'health_metrics.log')
            with open(log_file, 'a') as f:
                f.write(json.dumps(health_data) + '\n')
        except Exception as e:
            logger.error(f"Failed to log health metrics: {str(e)}")

    def monitor_trading_performance(self, trade_history: Dict[str, Any]) -> None:
        """Monitor trading performance metrics."""
        try:
            total_trades = len(trade_history)
            winning_trades = sum(1 for trade in trade_history.values() if trade.get('pnl', 0) > 0)
            total_pnl = sum(trade.get('pnl', 0) for trade in trade_history.values())
            
            performance_data = {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'win_rate': (winning_trades / total_trades * 100) if total_trades > 0 else 0,
                'total_pnl': total_pnl,
                'timestamp': datetime.now().isoformat()
            }

            # Alert on significant performance metrics
            if total_trades > 0:
                message = (
                    f"📊 <b>Trading Performance Update</b>\n\n"
                    f"Total Trades: {total_trades}\n"
                    f"Win Rate: {performance_data['win_rate']:.2f}%\n"
                    f"Total P&L: ${total_pnl:.2f}\n"
                    f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                self.send_telegram_message(message)

            # Log performance metrics
            log_file = os.path.join('logs', 'performance_metrics.log')
            with open(log_file, 'a') as f:
                f.write(json.dumps(performance_data) + '\n')

        except Exception as e:
            logger.error(f"Failed to monitor trading performance: {str(e)}") 