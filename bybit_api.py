import requests

class BybitClient:
    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api.bybit.com"

    def get_klines(self, symbol, interval="1", limit=200):
        endpoint = "/v5/market/kline"
        url = f"{self.base_url}{endpoint}"

        params = {
            "category": "spot",
            "symbol": symbol,
            "interval": interval,
            "limit": limit
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            result = response.json()
            return result["result"]["list"]
        except Exception as e:
            print(f"Error getting klines for {symbol}: {e}")
            return []
