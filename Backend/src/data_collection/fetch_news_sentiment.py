"""
Mood2Market - GDELT News Collector
Fetches news articles matching Bitcoin-related keywords from GDELT
for the date range Jan 6 - Mar 5 2026.
Feed the output CSV into your existing FinBERT sentiment script.
"""

import requests
import pandas as pd
import time
from datetime import datetime, timedelta

# ── CONFIG ────────────────────────────────────────────────────────────────────

KEYWORDS = [
    "Bitcoin"
]

START_DATE  = "2026-01-06"
END_DATE    = "2026-03-05"
OUTPUT_PATH = r"C:\Users\OKIO\Desktop\mood2market\Backend\Data\raw\news_second.csv"

# GDELT doc API base URL
GDELT_URL = "https://api.gdeltproject.org/api/v2/doc/doc"

# Seconds to wait between requests -- be respectful to GDELT's free API
REQUEST_DELAY = 10

# ── FETCH ─────────────────────────────────────────────────────────────────────

def fetch_gdelt_day(keyword, date_str):
    """
    Query GDELT for a single keyword on a single day.
    GDELT date format: YYYYMMDD for startdatetime / enddatetime.
    Returns a list of article dicts or empty list if nothing found.
    """
    # Build start and end timestamps for the full day
    date_obj  = datetime.strptime(date_str, "%Y-%m-%d")
    start_dt  = date_obj.strftime("%Y%m%d%H%M%S")
    end_dt    = (date_obj + timedelta(days=1) - timedelta(seconds=1)).strftime("%Y%m%d%H%M%S")

    params = {
        "query":          keyword,
        "mode":           "artlist",       # return article list
        "maxrecords":     250,             # max allowed per request
        "startdatetime":  start_dt,
        "enddatetime":    end_dt,
        "format":         "json",
        "sort":           "datedesc",
    }

    try:
        for attempt in range(3):  # retry up to 3 times on 429
            response = requests.get(GDELT_URL, params=params, timeout=30)

            if response.status_code == 429:
                wait = 60 * (attempt + 1)  # 60s, 120s, 180s
                print(f"  Rate limited -- waiting {wait}s before retry ...")
                time.sleep(wait)
                continue

            response.raise_for_status()
            data = response.json()

            articles = data.get("articles", [])
            results  = []
            for article in articles:
                results.append({
                    "date":     date_str,
                    "keyword":  keyword,
                    "title":    article.get("title",  ""),
                    "url":      article.get("url",    ""),
                    "source":   article.get("domain", ""),
                    "seendate": article.get("seendate", ""),
                })
            return results

        # All retries exhausted
        print(f"  Skipping {keyword} on {date_str} after 3 failed attempts")
        return []

    except Exception as e:
        print(f"  Error fetching {keyword} on {date_str}: {e}")
        return []


def generate_date_range(start_date, end_date):
    """Generate a list of date strings between start and end inclusive."""
    start  = datetime.strptime(start_date, "%Y-%m-%d")
    end    = datetime.strptime(end_date,   "%Y-%m-%d")
    dates  = []
    current = start
    while current <= end:
        dates.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)
    return dates


# ── MAIN ──────────────────────────────────────────────────────────────────────

dates = generate_date_range(START_DATE, END_DATE)
print(f"Fetching {len(dates)} days x {len(KEYWORDS)} keywords = {len(dates) * len(KEYWORDS)} requests")
print(f"Estimated time: ~{len(dates) * len(KEYWORDS) * REQUEST_DELAY // 60} minutes\n")

all_articles = []

for date_str in dates:
    print(f"Date: {date_str}")
    for keyword in KEYWORDS:
        articles = fetch_gdelt_day(keyword, date_str)
        all_articles.extend(articles)
        print(f"  [{keyword}] -> {len(articles)} articles")
        time.sleep(REQUEST_DELAY)  # avoid hammering the API

print(f"\nTotal articles fetched: {len(all_articles)}")

# Build dataframe
df = pd.DataFrame(all_articles)

# Drop duplicate URLs -- same article may appear under multiple keywords
df.drop_duplicates(subset="url", inplace=True)
df.sort_values("date", inplace=True)
df.reset_index(drop=True, inplace=True)

print(f"After deduplication: {len(df)} articles")
print(f"Date range: {df['date'].min()} -> {df['date'].max()}")

df.to_csv(OUTPUT_PATH, index=False)
print(f"\nSaved to: {OUTPUT_PATH}")
print(df.head())