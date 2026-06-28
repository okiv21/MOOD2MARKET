import pandas as pd
from pathlib import Path
import numpy as np

def clean_price_data(
    input_path=r"C:\Users\OKIO\Desktop\mood2market\Backend\Data\raw\single_btc.csv",
    output_path=r"C:\Users\OKIO\Desktop\mood2market\Backend\Data\processed\single_pre.csv"
):
    """
    Incremental BTC price preprocessing.
    - Safely handles empty processed files
    - Only processes new dates
    - Preserves rolling-feature correctness
    """

    raw_path = Path(input_path)
    processed_path = Path(output_path)

    # --------------------------------------------------
    # 1. LOAD RAW DATA
    # --------------------------------------------------
    df_raw = pd.read_csv(raw_path)

    if "date" in df_raw.columns:
        df_raw["date"] = pd.to_datetime(df_raw["date"])
    else:
        df_raw["date"] = pd.to_datetime(df_raw["timestamp"], unit="ms")

    df_raw = df_raw.sort_values("date").reset_index(drop=True)

    # --------------------------------------------------
    # 2. LOAD PROCESSED DATA (SAFE)
    # --------------------------------------------------
    df_processed = pd.DataFrame()
    last_date = None

    if processed_path.exists() and processed_path.stat().st_size > 0:
        df_processed = pd.read_csv(processed_path)
        df_processed["date"] = pd.to_datetime(df_processed["date"])
        last_date = df_processed["date"].max()

    # --------------------------------------------------
    # 3. DETERMINE NEW DATA
    # --------------------------------------------------
    if last_date is not None:
        df_new = df_raw[df_raw["date"] > last_date].copy()

        if df_new.empty:
            print("BTC prices already up to date.")
            return df_processed

        # Buffer for rolling features
        buffer_start = last_date - pd.Timedelta(days=7)
        df_buffer = df_raw[
            (df_raw["date"] > buffer_start) &
            (df_raw["date"] <= last_date)
        ]

        df_work = pd.concat([df_buffer, df_new], ignore_index=True)
    else:
        df_work = df_raw.copy()

    # --------------------------------------------------
    # 4. FEATURE ENGINEERING
    # --------------------------------------------------
    df_work["return"] = df_work["close"].pct_change()
    df_work["log_return"] = np.log(df_work["close"] / df_work["close"].shift(1))
    df_work["volatility_7d"] = df_work["return"].rolling(7, min_periods=1).std()
    df_work["ma_7"] = df_work["close"].rolling(7, min_periods=1).mean()
    df_work["ma_30"] = df_work["close"].rolling(30, min_periods=1).mean()
    df_work["momentum_7d"] = df_work["close"] - df_work["close"].shift(7)

    if "high" in df_work.columns and "low" in df_work.columns:
        df_work["hl_range"] = df_work["high"] - df_work["low"]
        df_work["hl_pct"] = df_work["hl_range"] / df_work["close"]

    # --------------------------------------------------
    # 5. REMOVE BUFFER ROWS
    # --------------------------------------------------
    if last_date is not None:
        df_work = df_work[df_work["date"] > last_date]

    # --------------------------------------------------
    # 6. HANDLE NaNs (DO NOT DROP VALID DATES)
    # --------------------------------------------------
    df_work["return"] = df_work["return"].fillna(0)
    df_work["log_return"] = df_work["log_return"].fillna(0)
    df_work["volatility_7d"] = df_work["volatility_7d"].fillna(0)
    df_work["momentum_7d"] = df_work["momentum_7d"].fillna(0)
    df_work = df_work.fillna(method="ffill").fillna(0)

    # --------------------------------------------------
    # 7. MERGE + SAVE
    # --------------------------------------------------
    if not df_processed.empty:
        final_df = pd.concat([df_processed, df_work], ignore_index=True)
    else:
        final_df = df_work

    final_df = final_df.drop_duplicates(subset="date", keep="last")
    final_df = final_df.sort_values("date").reset_index(drop=True)

    processed_path.parent.mkdir(parents=True, exist_ok=True)
    final_df.to_csv(processed_path, index=False)

    print("BTC preprocessing complete")
    print(f"Rows: {len(final_df)}")
    print(f"Date range: {final_df['date'].min().date()} → {final_df['date'].max().date()}")

    return final_df


if __name__ == "__main__":
    clean_price_data()
