from flask import Flask, render_template, jsonify
import json
import os
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, Any, List

app = Flask(__name__)

def load_health_metrics() -> List[Dict[str, Any]]:
    """Load health metrics from log file."""
    try:
        with open('logs/health_metrics.log', 'r') as f:
            return [json.loads(line) for line in f.readlines()]
    except Exception:
        return []

def load_performance_metrics() -> List[Dict[str, Any]]:
    """Load performance metrics from log file."""
    try:
        with open('logs/performance_metrics.log', 'r') as f:
            return [json.loads(line) for line in f.readlines()]
    except Exception:
        return []

def load_trade_history() -> List[Dict[str, Any]]:
    """Load trade history from CSV file."""
    try:
        return pd.read_csv('calendar_spreads.csv').to_dict('records')
    except Exception:
        return []

@app.route('/')
def index():
    """Render the main dashboard."""
    return render_template('index.html')

@app.route('/api/health')
def health_metrics():
    """Get health metrics."""
    metrics = load_health_metrics()
    # Get last 24 hours of data
    cutoff = datetime.now() - timedelta(hours=24)
    recent_metrics = [
        m for m in metrics 
        if datetime.fromisoformat(m['timestamp']) > cutoff
    ]
    return jsonify(recent_metrics)

@app.route('/api/performance')
def performance_metrics():
    """Get performance metrics."""
    metrics = load_performance_metrics()
    # Get last 24 hours of data
    cutoff = datetime.now() - timedelta(hours=24)
    recent_metrics = [
        m for m in metrics 
        if datetime.fromisoformat(m['timestamp']) > cutoff
    ]
    return jsonify(recent_metrics)

@app.route('/api/trades')
def trades():
    """Get trade history."""
    trades = load_trade_history()
    return jsonify(trades)

@app.route('/api/summary')
def summary():
    """Get summary statistics."""
    trades = load_trade_history()
    performance = load_performance_metrics()
    health = load_health_metrics()

    if not trades:
        return jsonify({
            'total_trades': 0,
            'win_rate': 0,
            'total_pnl': 0,
            'system_health': 'Unknown'
        })

    # Calculate trade statistics
    total_trades = len(trades)
    winning_trades = sum(1 for t in trades if t.get('pnl', 0) > 0)
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
    total_pnl = sum(t.get('pnl', 0) for t in trades)

    # Get latest system health
    latest_health = health[-1] if health else {}
    system_health = 'Healthy'
    if latest_health:
        if (latest_health.get('cpu_usage', 0) > 80 or 
            latest_health.get('memory_usage', 0) > 80 or 
            latest_health.get('disk_usage', 0) > 80):
            system_health = 'Warning'
        if (latest_health.get('cpu_usage', 0) > 90 or 
            latest_health.get('memory_usage', 0) > 90 or 
            latest_health.get('disk_usage', 0) > 90):
            system_health = 'Critical'

    return jsonify({
        'total_trades': total_trades,
        'win_rate': win_rate,
        'total_pnl': total_pnl,
        'system_health': system_health
    })

def run_web_interface(host: str = '0.0.0.0', port: int = 5000) -> None:
    """Run the web interface."""
    app.run(host=host, port=port) 