# filepath: c:\Users\champ\Trading_Bot_App\src\api_client.py
import requests
import logging

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

    def get(self, endpoint, params=None):
        try:
            response = requests.get(f"{self.base_url}{endpoint}", headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error("GET request failed: %s", e)
            return None

    def post(self, endpoint, payload):
        try:
            response = requests.post(f"{self.base_url}{endpoint}", headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error("POST request failed: %s", e)
            return None

    def delete(self, endpoint):
        try:
            response = requests.delete(f"{self.base_url}{endpoint}", headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error("DELETE request failed: %s", e)
            return None