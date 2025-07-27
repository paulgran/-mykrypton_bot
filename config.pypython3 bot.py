мAPI_KEY = "your_api_key"
API_SECRET = "your_api_secret"

# Telegram
BOT_TOKEN = "8285739419:AAH4AUiHOcAL21VyV0-JiotL1V-DZra5iEo"
CHAT_ID = "381103315"
ENABLE_TG = True
ENABLE_LOG = True

# Режим торговли
DRY_RUN = True  # True — виртуальная торговля, False — реальные ордера
VIRTUAL_BALANCE = {
    "USDT": 100.0,
    "BTC": 0.0,
    "ETH": 0.0
}


# Торговля
SYMBOLS = ["BTCUSDT", "ETHUSDT"]
INTERVAL = "1"
RSI_PERIOD = 14
EMA_FAST = 20
EMA_SLOW = 200
RSI_BUY = 30
RSI_SELL = 70
STOP_LOSS = -5  # %
TRADE_PERCENT = 0.1  # 10% от баланса
