"""
Mood2Market - BTC OHLCV Data Collector (Binance)
Fetches daily OHLCV data for a given date range and saves to CSV.
"""

import requests
import pandas as pd
from datetime import datetime

# ── CONFIG ────────────────────────────────────────────────────────────────────

SYMBOL     = "BTCUSDT"
INTERVAL   = "1d"
START_DATE = "2026-01-06"   # start of the gap
END_DATE   = "2026-01-06"   # end of the gap

OUTPUT_PATH = r"C:\Users\OKIO\Desktop\mood2market\Backend\Data\raw\single_btc.csv"

# ── FETCH ─────────────────────────────────────────────────────────────────────

def fetch_ohlcv(symbol, interval, start_date, end_date):
    """
    Fetch daily OHLCV candles from Binance public API.
    No API key required for historical klines.
    Returns a DataFrame with columns matching your existing dataset.
    """
    # Convert dates to millisecond timestamps that Binance expects
    start_ms = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp() * 1000)
    end_ms   = int(datetime.strptime(end_date,   "%Y-%m-%d").timestamp() * 1000)

    url    = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol":    symbol,
        "interval":  interval,
        "startTime": start_ms,
        "endTime":   end_ms,
        "limit":     1000,   # max per request; 1000 days is well above our range
    }

    print(f"Fetching {symbol} {interval} data from {start_date} to {end_date} ...")
    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()

    if not data:
        raise ValueError("No data returned from Binance. Check your date range.")

    # Binance returns a list of lists -- map to named columns
    df = pd.DataFrame(data, columns=[
        "timestamp", "open", "high", "low", "close", "volume",
        "close_time", "quote_volume", "trades",
        "taker_buy_base", "taker_buy_quote", "ignore"
    ])

    # Keep only the columns you need
    df = df[["timestamp", "open", "high", "low", "close", "volume"]]

    # Convert timestamp from milliseconds to a readable date
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df["date"]      = df["timestamp"].dt.strftime("%Y-%m-%d")

    # Cast price and volume columns to float
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = df[col].astype(float)

    # Reorder to match your existing dataset column order
    df = df[["date", "timestamp", "open", "high", "low", "close", "volume"]]

    print(f"Fetched {len(df)} rows | {df['date'].iloc[0]} -> {df['date'].iloc[-1]}")
    return df


# ── MAIN ──────────────────────────────────────────────────────────────────────

df = fetch_ohlcv(SYMBOL, INTERVAL, START_DATE, END_DATE)

df.to_csv(OUTPUT_PATH, index=False)
print(f"Saved to: {OUTPUT_PATH}")
print(df.head())
