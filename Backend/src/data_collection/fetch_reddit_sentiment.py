"""
Mood2Market - Reddit PRAW Collector
Fetches posts from Bitcoin-related subreddits for Jan 6 - Mar 5 2026.
Output matches your existing reddit raw data structure exactly.
Feed the output into your existing FinBERT sentiment script.
"""

import os

import praw
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# ── CONFIG ────────────────────────────────────────────────────────────────────

# Credentials are loaded from a local .env file (see .env.example). Never hardcode them.
load_dotenv()

CLIENT_ID     = os.getenv("REDDIT_CLIENT_ID")
CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
USER_AGENT    = os.getenv("REDDIT_USER_AGENT", "Mood2MarketApp")

if not CLIENT_ID or not CLIENT_SECRET:
    raise SystemExit(
        "Missing Reddit credentials. Copy .env.example to .env and set "
        "REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET."
    )

SUBREDDITS = ["Bitcoin", "BTC", "BTCTrading", "BTCMarkets"]

START_DATE  = "2026-01-06"
END_DATE    = "2026-03-05"
OUTPUT_PATH = r"C:\Users\OKIO\Desktop\mood2market\Backend\Data\raw\reddit_second.csv"

# Max posts to pull per subreddit -- PRAW caps at 1000 per call
LIMIT = 1000

# ── FETCH ─────────────────────────────────────────────────────────────────────

def fetch_subreddit(reddit, subreddit_name, start_ts, end_ts):
    """
    Fetch posts from a subreddit and filter to the target date range.
    PRAW does not support direct date filtering so we pull the max
    available posts and filter by created_utc timestamp afterwards.
    """
    subreddit = reddit.subreddit(subreddit_name)
    results   = []

    print(f"  Fetching r/{subreddit_name} ...")

    try:
        # 'new' gives the most recent posts in reverse chronological order
        for submission in subreddit.new(limit=LIMIT):
            created = submission.created_utc

            # Skip posts outside our date range
            if created < start_ts or created > end_ts:
                continue

            results.append({
                "date":               datetime.utcfromtimestamp(created).strftime("%Y-%m-%d"),
                "timestamp":          datetime.utcfromtimestamp(created).strftime("%Y-%m-%d %H:%M:%S"),
                "subreddit":          subreddit_name,
                "title":              submission.title,
                "selftext":           submission.selftext,
                "score":              submission.score,
                "num_comments":       submission.num_comments,
                "author":             str(submission.author),
                "url":                submission.url,
                "id":                 submission.id,
                "text_for_sentiment": (submission.title + " " + submission.selftext).strip(),
            })

        print(f"  r/{subreddit_name} -> {len(results)} posts in range")

    except Exception as e:
        print(f"  Error on r/{subreddit_name}: {e}")

    return results


# ── MAIN ──────────────────────────────────────────────────────────────────────

# Convert date strings to UTC timestamps for filtering
start_ts = datetime.strptime(START_DATE, "%Y-%m-%d").timestamp()
end_ts   = datetime.strptime(END_DATE,   "%Y-%m-%d").timestamp() + 86399  # include full end day

# Initialise PRAW
reddit = praw.Reddit(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    user_agent=USER_AGENT,
)

print(f"Collecting Reddit posts from {START_DATE} to {END_DATE} ...\n")

all_posts = []
for subreddit_name in SUBREDDITS:
    posts = fetch_subreddit(reddit, subreddit_name, start_ts, end_ts)
    all_posts.extend(posts)

df = pd.DataFrame(all_posts)

if df.empty:
    print("\nNo posts found in the date range.")
else:
    # Drop duplicate posts -- same post can appear across subreddits
    df.drop_duplicates(subset="id", inplace=True)
    df.sort_values(["date", "subreddit"], inplace=True)
    df.reset_index(drop=True, inplace=True)

    print(f"\nTotal posts after deduplication: {len(df)}")
    print(f"Date range: {df['date'].min()} -> {df['date'].max()}")
    print(f"Posts per subreddit:\n{df['subreddit'].value_counts()}")

    df.to_csv(OUTPUT_PATH, index=False)
    print(f"\nSaved to: {OUTPUT_PATH}")