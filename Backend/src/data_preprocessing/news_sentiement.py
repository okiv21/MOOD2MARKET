"""
Mood2Market - News Preprocessor
Cleans raw GDELT news and prepares it for FinBERT sentiment scoring.
Overwrites the input file in place.
Output columns: date, text_for_sentiment, title, url, domain, text_length, word_count
"""

import pandas as pd
import re

# ── CONFIG ────────────────────────────────────────────────────────────────────

FILE_PATH = r"C:\Users\OKIO\Desktop\mood2market\Backend\Data\raw\news_raw_update.csv"

CRYPTO_KEYWORDS = [
    r"\bbitcoin\b", r"\bbtc\b", r"\bcryptocurrency\b", r"\bcrypto\b",
    r"\bblockchain\b", r"\bethereum\b", r"\baltcoin\b", r"\bdefi\b",
    r"\bnft\b", r"\bweb3\b", r"\bstrategy\b", r"\bmstr\b",
    r"\bbtcusd\b", r"\bsatoshi\b", r"\bhalving\b", r"\bcoinbase\b",
    r"\bbinance\b", r"\bcrypto market\b",
]

SPAM_PATTERNS = [
    r"presale", r"pepenode", r"bitcoin hyper", r"next crypto to explode",
    r"meme coin", r"best crypto to buy", r"100x", r"get rich",
    r"airdrop", r"giveaway", r"pump", r"shill",
]

# ── LOAD ──────────────────────────────────────────────────────────────────────

df = pd.read_csv(FILE_PATH)
print(f"Loaded                     : {len(df)} rows")

# ── STEP 1: Valid dates ───────────────────────────────────────────────────────

df["date"] = pd.to_datetime(df["date"], errors="coerce")
df = df[df["date"].notna()].copy()
df["date"] = df["date"].dt.strftime("%Y-%m-%d")
print(f"After date filter          : {len(df)} rows")

# ── STEP 2: Remove non-English ────────────────────────────────────────────────

def is_mostly_english(text):
    if not isinstance(text, str):
        return False
    ascii_chars = sum(1 for c in text if ord(c) < 128)
    return (ascii_chars / max(len(text), 1)) > 0.92

df = df[df["title"].apply(is_mostly_english)].copy()
print(f"After language filter      : {len(df)} rows")

# ── STEP 3: Keep only crypto-relevant articles ────────────────────────────────

crypto_pattern = "|".join(CRYPTO_KEYWORDS)
df = df[df["title"].str.contains(crypto_pattern, na=False, case=False, regex=True)].copy()
print(f"After crypto keyword filter: {len(df)} rows")

# ── STEP 4: Remove spam ───────────────────────────────────────────────────────

spam_pattern = "|".join(SPAM_PATTERNS)
df = df[~df["title"].str.contains(spam_pattern, na=False, case=False, regex=True)].copy()
print(f"After spam filter          : {len(df)} rows")

# ── STEP 5: Deduplicate ───────────────────────────────────────────────────────

df.drop_duplicates(subset="title", inplace=True)
df.drop_duplicates(subset="url",   inplace=True)
print(f"After dedup                : {len(df)} rows")

# ── STEP 6: Build required output columns ────────────────────────────────────

# Clean title -- strip extra whitespace
df["title"] = df["title"].str.strip()

# text_for_sentiment is just the title since GDELT doesn't provide article body
df["text_for_sentiment"] = df["title"]

# domain comes from the source column in GDELT raw data
df["domain"] = df["source"].str.strip() if "source" in df.columns else df["url"].str.extract(r"https?://([^/]+)")[0]

# text_length = character count, word_count = word count
df["text_length"] = df["text_for_sentiment"].str.len()
df["word_count"]  = df["text_for_sentiment"].str.split().str.len()

# ── STEP 7: Select and order final columns ────────────────────────────────────

df = df[["date", "text_for_sentiment", "title", "url", "domain", "text_length", "word_count"]]

df.sort_values("date", inplace=True)
df.reset_index(drop=True, inplace=True)

# ── SAVE ──────────────────────────────────────────────────────────────────────

print(f"\nDate range  : {df['date'].min()} -> {df['date'].max()}")
print(f"Unique dates: {df['date'].nunique()}")
print(f"Avg articles/day: {len(df) / max(df['date'].nunique(), 1):.1f}")

df.to_csv(FILE_PATH, index=False)
print(f"\nOverwritten : {FILE_PATH}")
print(df.head())