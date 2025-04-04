# Improved api_client.py
import requests
import logging
import time
import random

logger = logging.getLogger("trading_bot")


def exponential_backoff(retry_count):
    return min(60, (2**retry_count) + random.uniform(0, 1))


class AlpacaAPIClient:
    def __init__(self, base_url, api_key, api_secret):
        self.base_url = base_url
        self.headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "APCA-API-KEY-ID": api_key,
            "APCA-API-SECRET-KEY": api_secret,
        }

    def get(self, endpoint, url_part='v2', params=None, retries=3, base="paper"):
        base_url = self.base_url if base == "paper" else "https://data.alpaca.markets"
        for attempt in range(retries):
            try:
                response = requests.get(
                    f"{base_url}/{url_part}/{endpoint}", headers=self.headers, params=params
                )
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e:
                wait_time = exponential_backoff(attempt)
                logger.warning(
                    f"GET request failed ({attempt + 1}/{retries}): {e}. Retrying in {wait_time:.2f} seconds..."
                )
                time.sleep(wait_time)
            except ValueError as e:
                logger.error(f"Failed to parse JSON response: {e}")
        return None

    def post(self, endpoint, payload, retries=3, url_part="v2"):
        for attempt in range(retries):
            try:
                full_url = f"{self.base_url}/{url_part}{endpoint}"
                response = requests.post(full_url, headers=self.headers, json=payload)
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e:
                wait_time = exponential_backoff(attempt)
                logger.warning(
                    f"POST request failed ({attempt + 1}/{retries}): {e}. Retrying in {wait_time:.2f} seconds..."
                )
                time.sleep(wait_time)
            except ValueError as e:
                logger.error(f"Failed to parse JSON response: {e}")
        return None

    def delete(self, endpoint, retries=3, url_part="v2", base="paper"):
        base_url = self.base_url if base == "paper" else "https://data.alpaca.markets"
        for attempt in range(retries):
            try:
                full_url = f"{base_url}/{url_part}{endpoint}"
                response = requests.delete(full_url, headers=self.headers)
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e:
                wait_time = exponential_backoff(attempt)
                logger.warning(
                    f"DELETE request failed ({attempt + 1}/{retries}): {e}. Retrying in {wait_time:.2f} seconds..."
                )
                time.sleep(wait_time)
            except ValueError as e:
                logger.error(f"Failed to parse JSON response: {e}")
        return None
    
