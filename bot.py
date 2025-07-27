
import time
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator
from pybit.unified_trading import HTTP
import config
import logging
from telegram_utils import send_telegram_message

session = HTTP(
    testnet=False,
    api_key=config.API_KEY,
    api_secret=config.API_SECRET
)

positions = {
    "BTCUSDT": None,
    "ETHUSDT": None
}

def get_klines(symbol):
    try:
        response = session.get_kline(
            category="spot",
            symbol=symbol,
            interval=config.INTERVAL,
            limit=200
        )
        data = response['result']['list']
        df = pd.DataFrame(data, columns=[
            "timestamp", "open", "high", "low", "close", "volume", "_", "_", "_", "_", "_", "_"
        ])
        df = df[["timestamp", "open", "high", "low", "close", "volume"]].astype(float)
        return df
    except Exception as e:
        print(f"Error getting klines for {symbol}:", e)
        return None

def analyze(df):
    df['ema_200'] = EMAIndicator(df['close'], window=200).ema_indicator()
    df['ema_20'] = EMAIndicator(df['close'], window=20).ema_indicator()
    df['rsi'] = RSIIndicator(df['close'], window=14).rsi()
    latest = df.iloc[-1]

    entry_signal = (
        latest['close'] > latest['ema_200'] and
        latest['close'] > latest['ema_20'] and
        latest['rsi'] < config.RSI_BUY
    )

    exit_signal = latest['rsi'] > config.RSI_SELL

    return entry_signal, exit_signal, latest['close']

def place_order(symbol, side, qty):
    try:
        order = session.place_order(
            category="spot",
            symbol=symbol,
            side=side.capitalize(),
            order_type="Market",
            qty=qty
        )
        msg = f"{symbol} {side.upper()} @ qty={qty} ✅"
        print(msg)
        if config.ENABLE_LOG:
            logging.info(msg)
        if config.ENABLE_TG:
            send_telegram_message(msg)
        return True
    except Exception as e:
        print(f"Error placing {side} order for {symbol}:", e)
        return False
    try:
        order = session.place_order(
            category="spot",
            symbol=symbol,
            side=side.capitalize(),
            order_type="Market",
            qty=config.TRADE_QTY
        )
        print(f"{symbol}: {side.upper()} ORDER PLACED ✅:", order["result"]["orderId"])
        return True
    except Exception as e:
        print(f"Error placing {side} order for {symbol}:", e)
        return False

logging.basicConfig(filename="bot.log", level=logging.INFO, format="%(asctime)s - %(message)s")

def get_trade_qty(symbol, price):
    try:
        balance = session.get_wallet_balance(accountType="UNIFIED")["result"]["list"][0]["coin"]
        usdt_balance = float(balance[0]["availableToTrade"])
        trade_value = usdt_balance * config.TRADE_PERCENT
        qty = round(trade_value / price, 6)
        return qty
    except Exception as e:
        print("Balance error:", e)
        return 0


    print("Starting conservative bot...")
    while True:
        for symbol in positions.keys():
            df = get_klines(symbol)
            if df is None:
                continue

            entry_signal, exit_signal, current_price = analyze(df)

            if positions[symbol] is None:
                if entry_signal:
                    success = qty = get_trade_qty(symbol, current_price)
                    if qty > 0:
                        success = place_order(symbol, "buy", qty)
                    if success:
                        positions[symbol] = {
                            "entry_price": current_price,
                            "timestamp": time.time()
                        }
            else:
                entry_price = positions[symbol]["entry_price"]
                change_pct = (current_price - entry_price) / entry_price * 100

                if exit_signal or change_pct <= -5:
                    success = place_order(symbol, "sell")
                    if success:
                        positions[symbol] = None

            time.sleep(2)
        time.sleep(60)

if __name__ == "__main__":
    main_loop()
