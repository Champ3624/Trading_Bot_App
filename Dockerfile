# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y gcc && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy all files
COPY . .

# Install Python dependencies and the package
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install -e .

# Create logs directory
RUN mkdir -p /app/logs

# Run the application
CMD ["python", "-m", "src.trader"] 