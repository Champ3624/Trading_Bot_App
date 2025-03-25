# filepath: c:\Users\champ\Trading_Bot_App\src\api_client.py
import requests
import logging
import time

logger = logging.getLogger(__name__)


class AlpacaAPIClient:
    def __init__(self, base_url, api_key, api_secret):
        self.base_url = base_url
        self.headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "APCA-API-KEY-ID": api_key,
            "APCA-API-SECRET-KEY": api_secret,
        }

    def get(self, endpoint, params=None, retries=3):
        for attempt in range(retries):
            try:
                response = requests.get(
                    f"{self.base_url}{endpoint}", headers=self.headers, params=params
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.warning("GET failed (%d/%d): %s", attempt + 1, retries, e)
                time.sleep(2**attempt)
        return None

    def post(self, endpoint, payload, retries=3):
        for attempt in range(retries):
            try:
                response = requests.post(
                    f"{self.base_url}{endpoint}", headers=self.headers, json=payload
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.warning("POST failed (%d/%d): %s", attempt + 1, retries, e)
                time.sleep(2**attempt)
        return None

    def delete(self, endpoint, retries=3):
        for attempt in range(retries):
            try:
                response = requests.delete(
                    f"{self.base_url}{endpoint}", headers=self.headers
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.warning("DELETE failed (%d/%d): %s", attempt + 1, retries, e)
                time.sleep(2**attempt)
        return None
