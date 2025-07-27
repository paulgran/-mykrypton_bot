import time
import os
import json
import logging
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator
from pybit.unified_trading import HTTP
import requests

# === НАСТРОЙКИ ===
API_KEY = "your_api_key"
API_SECRET = "your_api_secret"
BOT_TOKEN = "your_telegram_bot_token"
CHAT_ID = "your_chat_id"

SYMBOLS = ["BTCUSDT", "ETHUSDT"]
INTERVAL = "1"  # <--- ИСПРАВЛЕНО С "1m"
RSI_PERIOD = 14
RSI_BUY = 30
RSI_SELL = 70
EMA_FAST = 20
EMA_SLOW = 200
TRADE_PERCENT = 0.1
STOP_LOSS = -5  # в процентах
DRY_RUN = True
ENABLE_TG = True
ENABLE_LOG = True

session = HTTP(testnet=False, api_key=API_KEY, api_secret=API_SECRET)
positions = {symbol: None for symbol in SYMBOLS}

wallet_path = "virtual_wallet.json"
portfolio_log = "portfolio_log.csv"
trades_log = "trades_log.csv"

logging.basicConfig(filename="bot.log", level=logging.INFO, format="%(asctime)s - %(message)s")

def get_klines(symbol):
    try:
        response = session.get_kline(category="spot", symbol=symbol, interval=INTERVAL, limit=200)
        data = response["result"]["list"]
        df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df = df.astype(float)
        return df
    except Exception as e:
        print(f"Error getting klines for {symbol}:", e)
        return None

def send_telegram_message(text):
    if not ENABLE_TG:
        return
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": text})
    except Exception as e:
        print("Telegram Error:", e)

def get_trade_qty(price):
    if DRY_RUN:
        with open(wallet_path, "r") as f:
            wallet = json.load(f)
        usdt = wallet.get("USDT", 0)
        return round((usdt * TRADE_PERCENT) / price, 6)
    else:
        try:
            wallet = session.get_wallet_balance(accountType="UNIFIED")["result"]["list"][0]["coin"]
            usdt_balance = float(wallet[0]["availableToTrade"])
            return round((usdt_balance * TRADE_PERCENT) / price, 6)
        except Exception as e:
            print("Balance error:", e)
            return 0

def log_virtual_trade(symbol, side, qty, price):
    usdt_value = qty * price
    with open(wallet_path, "r") as f:
        wallet = json.load(f)

    base = symbol.replace("USDT", "")
    if side == "buy" and wallet["USDT"] >= usdt_value:
        wallet["USDT"] -= usdt_value
        wallet[base] += qty
    elif side == "sell" and wallet[base] >= qty:
        wallet["USDT"] += usdt_value
        wallet[base] -= qty

    with open(wallet_path, "w") as f:
        json.dump(wallet, f, indent=2)

    df = pd.read_csv(trades_log) if os.path.exists(trades_log) else pd.DataFrame(columns=["timestamp", "symbol", "side", "qty", "price", "usdt_value"])
    df.loc[len(df)] = [pd.Timestamp.now(), symbol, side, qty, price, usdt_value]
    df.to_csv(trades_log, index=False)

    msg = f"[VIRTUAL] {side.upper()} {symbol}: qty={qty}, price={price:.2f}, value={usdt_value:.2f}"
    print(msg)
    send_telegram_message(msg)
    logging.info(msg)

def analyze(df):
    df["ema_slow"] = EMAIndicator(df["close"], window=EMA_SLOW).ema_indicator()
    df["ema_fast"] = EMAIndicator(df["close"], window=EMA_FAST).ema_indicator()
    df["rsi"] = RSIIndicator(df["close"], window=RSI_PERIOD).rsi()
    last = df.iloc[-1]

    entry = last["close"] > last["ema_slow"] and last["close"] > last["ema_fast"] and last["rsi"] < RSI_BUY
    exit_ = last["rsi"] > RSI_SELL
    return entry, exit_, last["close"]

def run_bot():
    while True:
        for symbol in SYMBOLS:
            df = get_klines(symbol)
            if df is None:
                continue

            entry, exit_, price = analyze(df)
            qty = get_trade_qty(price)

            if positions[symbol] is None and entry and qty > 0:
                if DRY_RUN:
                    log_virtual_trade(symbol, "buy", qty, price)
                positions[symbol] = {"entry_price": price}
            elif positions[symbol] and (exit_ or ((price - positions[symbol]["entry_price"]) / positions[symbol]["entry_price"] * 100 <= STOP_LOSS)):
                if DRY_RUN:
                    log_virtual_trade(symbol, "sell", qty, price)
                positions[symbol] = None

        time.sleep(60)

if __name__ == "__main__":
    # если файл виртуального кошелька отсутствует — создаём
    if not os.path.exists(wallet_path):
        with open(wallet_path, "w") as f:
            json.dump({"USDT": 100.0, "BTC": 0.0, "ETH": 0.0}, f)
    run_bot()
