# filepath: c:\Users\champ\Trading_Bot_App\src\api_client.py
import requests
import logging
import time

logger = logging.getLogger("trade_bot.log")


class AlpacaAPIClient:
    def __init__(self, base_url, api_key, api_secret):
        self.base_url = base_url
        self.headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "APCA-API-KEY-ID": api_key,
            "APCA-API-SECRET-KEY": api_secret,
        }

    def get(self, endpoint, params=None, retries=3, url_part="v2", base="paper"):
        base_url = self.base_url if base == "paper" else "https://data.alpaca.markets"
        for attempt in range(retries):
            try:
                full_url = f"{base_url}/{url_part}{endpoint}"
                response = requests.get(full_url, headers=self.headers, params=params)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.warning("GET failed (%d/%d): %s", attempt + 1, retries, e)
                time.sleep(2**attempt)
        return None

    def post(self, endpoint, payload, retries=3, url_part="v2", base="paper"):
        base_url = self.base_url if base == "paper" else "https://data.alpaca.markets"
        for attempt in range(retries):
            try:
                full_url = f"{base_url}/{url_part}{endpoint}"
                response = requests.post(full_url, headers=self.headers, json=payload)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.warning("POST failed (%d/%d): %s", attempt + 1, retries, e)
                time.sleep(2**attempt)
        return None

    def delete(self, endpoint, retries=3, url_part="v2", base="paper"):
        base_url = self.base_url if base == "paper" else "https://data.alpaca.markets"
        for attempt in range(retries):
            try:
                full_url = f"{base_url}/{url_part}{endpoint}"
                response = requests.delete(full_url, headers=self.headers)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.warning("DELETE failed (%d/%d): %s", attempt + 1, retries, e)
                time.sleep(2**attempt)
        return None

    def get_asset_price(self, symbol, type="stocks"):
        if type != "stocks" and type != "options":
            raise ValueError("Invalid type. Must be 'stocks' or 'options'")
        if type == "options":
            url = "v1beta1"
        else:
            url = "v2"
        endpoint = f"/{type}/{symbol}/trades/latest"
        try:
            response = self.get(endpoint=endpoint, base="data", url_part=url)
            return response['trade']['p']
        except Exception as e:
            logger.error("Failed to get asset price for %s: %s", symbol, e)
            return None

    def get_expirations(self, symbol):
        options = self.get("/options/contracts", params={"underlying_symbols": symbol})
        if options is None:
            logger.error(f"Failed to fetch expiration dates for {symbol}")
            return None
        return [exp["expiration_date"] for exp in options["option_contracts"]]
