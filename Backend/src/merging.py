"""
Mood2Market - BTC Dataset Updater
Appends the new preprocessed BTC data (Jan 7 - Mar 5) to the existing
merged dataset and saves the result.
"""

import pandas as pd

# ── CONFIG ────────────────────────────────────────────────────────────────────

EXISTING_PATH = r"C:\Users\OKIO\Desktop\mood2market\Backend\Data\processed\main Data\btc_price_data.csv"
NEW_PATH      = r"C:\Users\OKIO\Desktop\mood2market\Backend\Data\processed\single_pre.csv"
OUTPUT_PATH   = r"C:\Users\OKIO\Desktop\mood2market\Backend\Data\processed\main Data\btc_price_data.csv"

# ── MERGE ─────────────────────────────────────────────────────────────────────

# Load both files
existing = pd.read_csv(EXISTING_PATH, parse_dates=["date"])
new_data = pd.read_csv(NEW_PATH,      parse_dates=["date"])

print(f"Existing : {len(existing)} rows | {existing['date'].min().date()} -> {existing['date'].max().date()}")
print(f"New data : {len(new_data)} rows | {new_data['date'].min().date()} -> {new_data['date'].max().date()}")

# Stack vertically, sort by date, drop any accidental duplicates
merged = (
    pd.concat([existing, new_data], ignore_index=True)
    .sort_values("date")
    .drop_duplicates(subset="date", keep="last")  # keep new data if dates overlap
    .reset_index(drop=True)
)

print(f"Combined : {len(merged)} rows | {merged['date'].min().date()} -> {merged['date'].max().date()}")

# Save -- overwrites the existing merged_dataset.csv
merged.to_csv(OUTPUT_PATH, index=False)
print(f"Saved to : {OUTPUT_PATH}")