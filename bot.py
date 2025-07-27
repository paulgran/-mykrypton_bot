
import time
import os
import json
import logging
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator
from pybit.unified_trading import HTTP
import requests

# === ENVIRONMENT VARIABLES ===
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
DRY_RUN = os.getenv("DRY_RUN", "False") == "True"
TRADE_PERCENT = float(os.getenv("TRADE_PERCENT", "0.1"))
RSI_PERIOD = int(os.getenv("RSI_PERIOD", "14"))
RSI_BUY = int(os.getenv("RSI_BUY", "30"))
RSI_SELL = int(os.getenv("RSI_SELL", "70"))
STOP_LOSS = float(os.getenv("STOP_LOSS", "-5"))
SYMBOLS = os.getenv("SYMBOLS", "BTCUSDT,ETHUSDT").split(",")
INTERVAL = os.getenv("INTERVAL", "1m")
ENABLE_TG = os.getenv("ENABLE_TG", "True") == "True"
ENABLE_LOG = os.getenv("ENABLE_LOG", "True") == "True"

session = HTTP(testnet=False, api_key=API_KEY, api_secret=API_SECRET)

portfolio_log_path = "portfolio_log.csv"
trades_log_path = "trades_log.csv"
wallet_path = "virtual_wallet.json"

positions = {symbol: None for symbol in SYMBOLS}

# === LOGGING ===
logging.basicConfig(filename="bot.log", level=logging.INFO, format="%(asctime)s - %(message)s")

def get_klines(symbol):
    try:
        response = session.get_kline(category="spot", symbol=symbol, interval=INTERVAL, limit=200)
        data = response['result']['list']
        df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close", "volume", "_", "_", "_", "_", "_", "_"])
        df = df[["timestamp", "open", "high", "low", "close", "volume"]].astype(float)
        return df
    except Exception as e:
        print(f"Error getting klines for {symbol}:", e)
        return None

def send_telegram_message(message):
    if ENABLE_TG:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            data = {"chat_id": CHAT_ID, "text": message}
            requests.post(url, data=data)
        except Exception as e:
            print("Telegram Error:", e)

def get_trade_qty(price):
    if DRY_RUN:
        try:
            with open(wallet_path, "r") as f:
                balance = json.load(f)
            usdt_balance = balance["USDT"]
            trade_value = usdt_balance * TRADE_PERCENT
            return round(trade_value / price, 6)
        except Exception as e:
            print("Dry run balance error:", e)
            return 0
    else:
        try:
            balance = session.get_wallet_balance(accountType="UNIFIED")["result"]["list"][0]["coin"]
            usdt_balance = float(balance[0]["availableToTrade"])
            trade_value = usdt_balance * TRADE_PERCENT
            return round(trade_value / price, 6)
        except Exception as e:
            print("Balance error:", e)
            return 0

def log_virtual_trade(symbol, side, qty, price):
    with open(wallet_path, "r") as f:
        wallet = json.load(f)
    usdt_value = qty * price
    if side.lower() == "buy" and wallet["USDT"] >= usdt_value:
        wallet["USDT"] -= usdt_value
        wallet[symbol[:3]] += qty
    elif side.lower() == "sell" and wallet[symbol[:3]] >= qty:
        wallet["USDT"] += usdt_value
        wallet[symbol[:3]] -= qty
    with open(wallet_path, "w") as f:
        json.dump(wallet, f, indent=2)

    if os.path.exists(trades_log_path):
        df = pd.read_csv(trades_log_path)
    else:
        df = pd.DataFrame(columns=["timestamp", "symbol", "side", "qty", "price", "usdt_value"])

    df.loc[len(df)] = [pd.Timestamp.now(), symbol, side, qty, price, round(usdt_value, 2)]
    df.to_csv(trades_log_path, index=False)

    msg = f"[VIRTUAL TRADE] {side.upper()} {symbol} {qty} @ {price:.2f} | USDT value: {usdt_value:.2f}"
    print(msg)
    logging.info(msg)
    send_telegram_message(msg)

def analyze(df):
    df["ema_200"] = EMAIndicator(df["close"], window=200).ema_indicator()
    df["ema_20"] = EMAIndicator(df["close"], window=20).ema_indicator()
    df["rsi"] = RSIIndicator(df["close"], window=RSI_PERIOD).rsi()
    latest = df.iloc[-1]

    entry = latest["close"] > latest["ema_200"] and latest["close"] > latest["ema_20"] and latest["rsi"] < RSI_BUY
    exit_ = latest["rsi"] > RSI_SELL
    return entry, exit_, latest["close"]

def run_bot():
    while True:
        for symbol in SYMBOLS:
            df = get_klines(symbol)
            if df is None:
                continue

            entry, exit_, current_price = analyze(df)

            if positions[symbol] is None:
                if entry:
                    qty = get_trade_qty(current_price)
                    if qty > 0:
                        if DRY_RUN:
                            log_virtual_trade(symbol, "buy", qty, current_price)
                        else:
                            pass
                        positions[symbol] = {"entry_price": current_price}
            else:
                entry_price = positions[symbol]["entry_price"]
                change_pct = (current_price - entry_price) / entry_price * 100
                if exit_ or change_pct <= STOP_LOSS:
                    qty = get_trade_qty(current_price)
                    if qty > 0:
                        if DRY_RUN:
                            log_virtual_trade(symbol, "sell", qty, current_price)
                        else:
                            pass
                        positions[symbol] = None

        time.sleep(60)

if __name__ == "__main__":
    run_bot()
