
import pandas as pd
import matplotlib.pyplot as plt
import config
import requests
import datetime

def send_photo(file_path, caption=""):
    try:
        url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/sendPhoto"
        with open(file_path, 'rb') as photo:
            data = {
                "chat_id": config.CHAT_ID,
                "caption": caption
            }
            files = {
                "photo": photo
            }
            requests.post(url, data=data, files=files)
    except Exception as e:
        print("Error sending photo:", e)

def plot_portfolio():
    df = pd.read_csv('portfolio_log.csv')
    if df.empty:
        print("Portfolio log is empty.")
        return

    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['usdt_total'] = df['USDT'] + df['BTC'] * df['BTC_price'] + df['ETH'] * df['ETH_price']

    plt.figure(figsize=(10, 6))
    plt.plot(df['timestamp'], df['usdt_total'], marker='o')
    plt.title("Virtual Portfolio Value Over Time")
    plt.xlabel("Time")
    plt.ylabel("Total Value (USDT)")
    plt.grid(True)
    plt.tight_layout()
    file_path = "portfolio_chart.png"
    plt.savefig(file_path)
    plt.close()

    send_photo(file_path, caption=f"📊 Доходность виртуального портфеля на {datetime.datetime.now().strftime('%Y-%m-%d')}")

if __name__ == "__main__":
    plot_portfolio()
