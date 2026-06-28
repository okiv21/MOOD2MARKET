"""
Mood2Market - Reddit Raw CSV Cleaner (Final Version)
Fixes embedded newlines at byte level before any filtering.
Run this to overwrite second_redditclean.csv with a clean version.
"""

import pandas as pd
import re
import io

# ── CONFIG ────────────────────────────────────────────────────────────────────

INPUT_PATH  = r"C:\Users\OKIO\Desktop\mood2market\Backend\Data\processed\reddit_clean_second.csv"
OUTPUT_PATH = r"C:\Users\OKIO\Desktop\mood2market\Backend\Data\processed\main Data\second_redditclean.csv"

MIN_TEXT_LENGTH = 50

MEME_KEYWORDS = [
    "to the moon", "wen lambo", "giveaway", "airdrop",
    "follow for follow", "lets go", "let's go", "we did it",
    "here we go again", "going to zero", "just bought",
    "just sold", "diamond hands", "wen moon",
]

# ── STEP 0: Fix embedded newlines at byte level ───────────────────────────────
# Read raw text, keep only lines that start with a valid date or are the header.
# Lines that start with anything else are continuation lines from broken selftext
# and get dropped entirely before pandas ever sees the file.

print("Fixing embedded newlines...")

date_re = re.compile(r"^\d{4}-\d{2}-\d{2},")

with open(INPUT_PATH, "r", encoding="utf-8", errors="replace") as f:
    raw_lines = f.readlines()

header = raw_lines[0]
clean_lines = [header]
for line in raw_lines[1:]:
    if date_re.match(line):
        clean_lines.append(line)

print(f"Raw lines     : {len(raw_lines)}")
print(f"Clean lines   : {len(clean_lines)} (header + valid rows)")

# Parse the cleaned lines directly
df = pd.read_csv(io.StringIO("".join(clean_lines)), on_bad_lines="skip")
print(f"Loaded        : {len(df)} rows")

# ── STEP 1: Confirm all dates are valid ───────────────────────────────────────

df["date"] = pd.to_datetime(df["date"], errors="coerce")
df = df[df["date"].notna()].copy()
df["date"] = df["date"].dt.strftime("%Y-%m-%d")
print(f"After date filter       : {len(df)} rows")

# ── STEP 2: Fill NaN selftext ─────────────────────────────────────────────────

df["selftext"] = df["selftext"].fillna("")

# ── STEP 3: Remove image-only posts ──────────────────────────────────────────

image_url   = df["url"].str.contains(
    r"i\.redd\.it|imgur\.com|\.jpeg|\.jpg|\.png|\.gif|\.webp",
    na=False, case=False, regex=True
)
no_selftext = df["selftext"].str.strip() == ""
df = df[~(image_url & no_selftext)].copy()
print(f"After image post filter : {len(df)} rows")

# ── STEP 4: Remove video-only posts ──────────────────────────────────────────

video = (
    df["selftext"].str.contains(r"youtube\.com|youtu\.be", na=False, case=False, regex=True) |
    df["url"].str.contains(r"youtube\.com|youtu\.be", na=False, case=False, regex=True)
)
df = df[~video].copy()
print(f"After video post filter : {len(df)} rows")

# ── STEP 5: Remove deleted/removed posts ─────────────────────────────────────

removed = df["selftext"].str.strip().isin(["[removed]", "[deleted]"])
df = df[~removed].copy()
print(f"After removed filter    : {len(df)} rows")

# ── STEP 6: Remove non-English posts ─────────────────────────────────────────

def is_mostly_english(text):
    if not isinstance(text, str):
        return False
    ascii_chars = sum(1 for c in text if ord(c) < 128)
    return (ascii_chars / max(len(text), 1)) > 0.85

df = df[df["title"].apply(is_mostly_english)].copy()
print(f"After language filter   : {len(df)} rows")

# ── STEP 7: Remove meme/low-quality posts ────────────────────────────────────

meme_pattern = "|".join(re.escape(k) for k in MEME_KEYWORDS)
df = df[~df["title"].str.lower().str.contains(meme_pattern, na=False)].copy()
print(f"After meme filter       : {len(df)} rows")

# ── STEP 8: Rebuild text_for_sentiment ───────────────────────────────────────

df["text_for_sentiment"] = (df["title"] + " " + df["selftext"]).str.strip()

# ── STEP 9: Keep only posts mentioning Bitcoin or BTC ────────────────────────

btc = df["text_for_sentiment"].str.contains(
    r"\bbitcoin\b|\bbtc\b", na=False, case=False, regex=True
)
df = df[btc].copy()
print(f"After BTC keyword filter: {len(df)} rows")

# ── STEP 10: Remove low effort posts ─────────────────────────────────────────

low_effort = (df["score"] == 0) & (df["text_for_sentiment"].str.len() < MIN_TEXT_LENGTH)
df = df[~low_effort].copy()
print(f"After low effort filter : {len(df)} rows")

# ── STEP 11: Deduplicate by post ID ──────────────────────────────────────────

if "id" in df.columns:
    df.drop_duplicates(subset="id", inplace=True)
    print(f"After dedup             : {len(df)} rows")

# ── FINALISE ──────────────────────────────────────────────────────────────────

df.sort_values("date", inplace=True)
df.reset_index(drop=True, inplace=True)

print(f"\nDate range  : {df['date'].min()} -> {df['date'].max()}")
print(f"Unique dates: {df['date'].nunique()}")
print(f"\nPosts per subreddit:\n{df['subreddit'].value_counts()}")

df.to_csv(OUTPUT_PATH, index=False)
print(f"\nSaved to: {OUTPUT_PATH}")