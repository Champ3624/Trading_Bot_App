# Trading Bot Deployment Guide

This guide explains how to deploy the trading bot in various environments.

## Local Deployment

### Prerequisites
- Python 3.8 or higher
- pip
- virtualenv (recommended)

### Steps
1. Clone the repository
2. Create and activate virtual environment
3. Install dependencies
4. Configure the bot
5. Run the bot
6. Access the web interface at http://localhost:5000

```bash
# Clone repository
git clone https://github.com/yourusername/trading-bot.git
cd trading-bot

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure the bot
cp config.example.json config.json
# Edit config.json with your settings

# Run the bot
python -m trading_bot.run
```

## Docker Deployment

### Prerequisites
- Docker
- Docker Compose (optional)

### Steps
1. Build the Docker image
2. Run the container
3. Access the web interface at http://localhost:5000

```bash
# Build image
docker build -t trading-bot .

# Run container
docker run -d \
  --name trading-bot \
  -p 5000:5000 \
  -v $(pwd)/config.json:/app/config.json \
  -v $(pwd)/logs:/app/logs \
  trading-bot
```

### Docker Compose
```yaml
version: '3'
services:
  trading-bot:
    build: .
    volumes:
      - ./config.json:/app/config.json
      - ./logs:/app/logs
    environment:
      - TZ=America/New_York
    restart: unless-stopped
```

## AWS EC2 Deployment

### Prerequisites
- AWS EC2 instance
- Docker

### Steps
1. Launch EC2 instance
2. Install Docker
3. Clone the repository and build the Docker image
4. Run the container
5. Access the web interface at http://<ec2-public-ip>:5000

```bash
# Install Docker
# Amazon Linux 2
sudo yum update -y
sudo amazon-linux-extras install docker
sudo service docker start
sudo usermod -a -G docker ec2-user

# Ubuntu
sudo apt-get update
sudo apt-get install -y docker.io
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ubuntu

# Clone and setup
git clone https://github.com/yourusername/trading-bot.git
cd trading-bot
docker build -t trading-bot .

# Run container
docker run -d \
  --name trading-bot \
  -p 5000:5000 \
  -v $(pwd)/config.json:/app/config.json \
  -v $(pwd)/logs:/app/logs \
  trading-bot
```

## Monitoring

### System Health
- CPU usage
- Memory usage
- Disk usage
- Network connectivity
- API response times

### Trading Performance
- Total trades
- Win rate
- Total P&L
- Average trade duration
- Risk metrics

### Web Interface
The web interface provides real-time monitoring of:
- System health metrics
- Trading performance
- Recent trades
- Key statistics

Access the dashboard at http://localhost:5000 (or your server's IP:5000)

## Backup and Recovery

### Configuration Backup
```bash
# Backup configuration
cp config.json config.json.backup

# Backup logs
tar -czf logs_backup.tar.gz logs/
```

### Database Backup
- Regularly backup trade history
- Export trading logs
- Backup position data

## Security

### API Key Security
- Use environment variables
- Implement key rotation
- Monitor API usage

### System Security
- Keep system updated
- Use firewall rules
- Implement access controls

## Maintenance

### Regular Updates
```bash
# Update code
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade

# Update Docker image
docker pull trading-bot
```

### Performance Optimization
- Monitor resource usage
- Optimize database queries
- Implement caching where appropriate

### Log Rotation
```bash
# Set up logrotate
sudo nano /etc/logrotate.d/trading-bot
```

Add:
```
/path/to/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0640 trading_bot trading_bot
}
```

## Troubleshooting

### Common Issues
1. API Connection Issues
   - Check API keys
   - Verify network connectivity
   - Check API rate limits

2. System Issues
   - Check system resources
   - Verify service status
   - Check logs for errors

3. Trading Issues
   - Verify market hours
   - Check position limits
   - Monitor for errors

### Recovery Procedures
1. Service Recovery
```bash
sudo systemctl restart trading-bot
```

2. Data Recovery
```bash
# Restore from backup
cp config.json.backup config.json

# Restore logs
tar -xzf logs_backup.tar.gz
```

3. System Recovery
```bash
# Rebuild environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Support

For issues and support:
1. Check the logs in the `logs` directory
2. Review the documentation
3. Contact support with:
   - Log files
   - Configuration (with sensitive data removed)
   - System information
   - Steps to reproduce the issue 