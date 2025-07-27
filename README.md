
# Spot Bot for Bybit (Conservative Strategy + Virtual Trading Mode)

## Features
- Conservative trading using EMA200 + EMA20 + RSI
- Supports BTCUSDT and ETHUSDT
- Stop-loss enabled
- Trade size based on % of balance
- Telegram alerts
- Logging to file
- Virtual trading mode (DRY_RUN) — no real orders
- Saves virtual balance to `virtual_wallet.json`

## Usage
1. Set your API keys and Telegram credentials in config.py
2. Run the bot:
    source venv/bin/activate
    python bot.py
3. Set DRY_RUN = False to enable real trading
