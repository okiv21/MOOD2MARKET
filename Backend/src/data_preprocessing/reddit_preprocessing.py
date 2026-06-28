"""
Strict Reddit Data Preprocessing
Handles messy Reddit data - filters bots, emojis, threads, memes
Keeps only Bitcoin-related posts with valid dates
"""

import pandas as pd
import numpy as np
from pathlib import Path
import re
from datetime import datetime

class StrictRedditPreprocessor:
    """Clean and filter messy Reddit data"""
    
    def __init__(
        self,
        input_path=r"C:\Users\OKIO\Desktop\mood2market\Backend\Data\raw\reddit_combined.csv",
        output_path=r"C:\Users\OKIO\Desktop\mood2market\Backend\Data\processed\reddit_clean.csv"
    ):
        self.input_path = Path(input_path)
        self.output_path = Path(output_path)
        
        # Bitcoin keywords (strict)
        self.btc_keywords = ['bitcoin', 'btc', 'bitcoins']
        
        # Bot indicators to filter out
        self.bot_indicators = [
            'bot',
            'automoderator',
            'automod',
            'u/automoderator',
            '[removed]',
            '[deleted]',
            'this post was automatically',
            'your submission has been removed',
            'this is an automated',
            'i am a bot'
        ]
        
        # Thread/meta indicators to filter
        self.meta_indicators = [
            'daily discussion',
            'daily thread',
            'megathread',
            'weekly thread',
            'monthly thread',
            'reminder:',
            'read the rules',
            'please use the',
            'sticky thread'
        ]
        
        # Meme/joke indicators
        self.meme_indicators = [
            'hodl',
            'to the moon',
            'when lambo',
            'buy the dip',
            'diamond hands',
            'paper hands',
            'wen moon'
        ]
    
    def has_valid_date(self, row):
        """Check if row has valid date or timestamp"""
        # Check date column
        if 'date' in row.index and pd.notna(row['date']):
            return True
        
        # Check timestamp column
        if 'timestamp' in row.index and pd.notna(row['timestamp']):
            return True
        
        # Check created_utc
        if 'created_utc' in row.index and pd.notna(row['created_utc']):
            return True
        
        return False
    
    def extract_date(self, row):
        """Extract date from various possible columns"""
        # Try date column first
        if 'date' in row.index and pd.notna(row['date']):
            try:
                return pd.to_datetime(row['date']).date()
            except:
                pass
        
        # Try timestamp
        if 'timestamp' in row.index and pd.notna(row['timestamp']):
            try:
                return pd.to_datetime(row['timestamp']).date()
            except:
                pass
        
        # Try created_utc (Unix timestamp)
        if 'created_utc' in row.index and pd.notna(row['created_utc']):
            try:
                return datetime.fromtimestamp(float(row['created_utc'])).date()
            except:
                pass
        
        return None
    
    def is_bot_post(self, text):
        """Check if post is from a bot or automated"""
        if pd.isna(text):
            return False
        
        text_lower = str(text).lower()
        
        for indicator in self.bot_indicators:
            if indicator in text_lower:
                return True
        
        return False
    
    def is_meta_thread(self, text):
        """Check if post is a meta/discussion thread"""
        if pd.isna(text):
            return False
        
        text_lower = str(text).lower()
        
        for indicator in self.meta_indicators:
            if indicator in text_lower:
                return True
        
        return False
    
    def is_likely_meme(self, text):
        """Check if post is likely a meme/joke (optional filter)"""
        if pd.isna(text):
            return False
        
        text_lower = str(text).lower()
        
        # Count meme indicators
        meme_count = sum(1 for indicator in self.meme_indicators if indicator in text_lower)
        
        # If has 2+ meme indicators, likely a meme
        return meme_count >= 2
    
    def is_btc_related(self, text):
        """Check if text is Bitcoin-related"""
        if pd.isna(text) or text == '':
            return False
        
        text_lower = str(text).lower()
        
        for keyword in self.btc_keywords:
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, text_lower):
                return True
        
        return False
    
    def remove_emojis(self, text):
        """Remove emojis from text"""
        if pd.isna(text):
            return ''
        
        # Emoji pattern
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]+", 
            flags=re.UNICODE
        )
        
        return emoji_pattern.sub(r'', text)
    
    def clean_reddit_text(self, text):
        """Clean Reddit-specific formatting"""
        if pd.isna(text):
            return ''
        
        text = str(text)
        
        # Remove [removed] and [deleted]
        if text.lower() in ['[removed]', '[deleted]', 'none', 'nan']:
            return ''
        
        # Remove emojis
        text = self.remove_emojis(text)
        
        # Remove URLs
        text = re.sub(r'http\S+|www.\S+', '', text)
        
        # Remove Reddit formatting
        text = re.sub(r'\*\*', '', text)  # Bold
        text = re.sub(r'~~', '', text)    # Strikethrough
        text = re.sub(r'^\>', '', text, flags=re.MULTILINE)  # Quotes
        
        # Remove u/ mentions
        text = re.sub(r'u/\w+', '', text)
        
        # Remove r/ mentions
        text = re.sub(r'r/\w+', '', text)
        
        # Remove excessive newlines
        text = re.sub(r'\n+', ' ', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Strip
        text = text.strip()
        
        return text
    
    def run_preprocessing(self):
        """Execute full Reddit preprocessing"""
        
        print("="*70)
        print("STRICT REDDIT DATA PREPROCESSING")
        print("="*70)
        print()
        print("Filters applied:")
        print("  1. Remove posts without valid dates")
        print("  2. Remove bot posts")
        print("  3. Remove meta/discussion threads")
        print("  4. Remove heavy meme posts (2+ meme indicators)")
        print("  5. Keep only Bitcoin-related posts")
        print("  6. Remove emojis and Reddit formatting")
        print()
        
        # Load data
        print("="*70)
        print("LOADING RAW REDDIT DATA")
        print("="*70)
        print(f"Source: {self.input_path}")
        
        if not self.input_path.exists():
            print("ERROR: File not found")
            return None
        
        df = pd.read_csv(self.input_path)
        print(f"Loaded: {len(df):,} posts")
        print(f"Columns: {list(df.columns)}")
        print()
        
        initial_count = len(df)
        
        # Step 1: Filter by valid dates
        print("="*70)
        print("STEP 1: FILTERING BY VALID DATES")
        print("="*70)
        
        print("Extracting dates...")
        df['date_extracted'] = df.apply(self.extract_date, axis=1)
        
        no_date = df['date_extracted'].isna().sum()
        print(f"  Posts without valid date: {no_date:,}")
        
        if no_date > 0:
            print(f"  Removing {no_date:,} posts without dates")
            df = df.dropna(subset=['date_extracted'])
        
        df['date'] = df['date_extracted']
        df = df.drop('date_extracted', axis=1)
        
        print(f"  Remaining: {len(df):,}")
        print(f"  Date range: {df['date'].min()} to {df['date'].max()}")
        print()
        
        # Step 2: Create text field
        print("="*70)
        print("STEP 2: CREATING TEXT FIELD")
        print("="*70)
        
        # Combine title and selftext
        if 'title' in df.columns:
            df['text_raw'] = df['title'].fillna('').astype(str)
            
            if 'selftext' in df.columns:
                df['text_raw'] = df['text_raw'] + ' ' + df['selftext'].fillna('').astype(str)
        elif 'text' in df.columns:
            df['text_raw'] = df['text'].fillna('').astype(str)
        else:
            print("ERROR: No text columns found")
            return None
        
        print(f"  Combined text created")
        print()
        
        # Step 3: Filter bots
        print("="*70)
        print("STEP 3: FILTERING BOT POSTS")
        print("="*70)
        
        df['is_bot'] = df['text_raw'].apply(self.is_bot_post)
        bot_count = df['is_bot'].sum()
        
        print(f"  Bot posts detected: {bot_count:,}")
        
        if bot_count > 0:
            print(f"  Examples of bot posts:")
            bot_examples = df[df['is_bot']]['text_raw'].head(5)
            for i, text in enumerate(bot_examples, 1):
                print(f"    {i}. {str(text)[:70]}...")
            print()
            
            df = df[~df['is_bot']]
            print(f"  Removed {bot_count:,} bot posts")
        
        df = df.drop('is_bot', axis=1)
        print(f"  Remaining: {len(df):,}")
        print()
        
        # Step 4: Filter meta threads
        print("="*70)
        print("STEP 4: FILTERING META THREADS")
        print("="*70)
        
        df['is_meta'] = df['text_raw'].apply(self.is_meta_thread)
        meta_count = df['is_meta'].sum()
        
        print(f"  Meta threads detected: {meta_count:,}")
        
        if meta_count > 0:
            df = df[~df['is_meta']]
            print(f"  Removed {meta_count:,} meta threads")
        
        df = df.drop('is_meta', axis=1)
        print(f"  Remaining: {len(df):,}")
        print()
        
        # Step 5: Filter heavy meme posts (optional)
        print("="*70)
        print("STEP 5: FILTERING HEAVY MEME POSTS")
        print("="*70)
        
        df['is_meme'] = df['text_raw'].apply(self.is_likely_meme)
        meme_count = df['is_meme'].sum()
        
        print(f"  Heavy meme posts detected: {meme_count:,}")
        
        if meme_count > 0:
            print(f"  Examples:")
            meme_examples = df[df['is_meme']]['text_raw'].head(3)
            for i, text in enumerate(meme_examples, 1):
                print(f"    {i}. {str(text)[:70]}...")
            print()
            
            df = df[~df['is_meme']]
            print(f"  Removed {meme_count:,} meme posts")
        
        df = df.drop('is_meme', axis=1)
        print(f"  Remaining: {len(df):,}")
        print()
        
        # Step 6: Filter for Bitcoin-only
        print("="*70)
        print("STEP 6: FILTERING FOR BITCOIN-ONLY")
        print("="*70)
        
        df['is_btc'] = df['text_raw'].apply(self.is_btc_related)
        btc_count = df['is_btc'].sum()
        non_btc = len(df) - btc_count
        
        print(f"  Bitcoin-related: {btc_count:,}")
        print(f"  Not Bitcoin: {non_btc:,}")
        
        if non_btc > 0:
            df = df[df['is_btc']]
            print(f"  Removed {non_btc:,} non-Bitcoin posts")
        
        df = df.drop('is_btc', axis=1)
        print(f"  Remaining: {len(df):,}")
        print()
        
        # Step 7: Clean text
        print("="*70)
        print("STEP 7: CLEANING TEXT")
        print("="*70)
        
        print("Removing emojis and Reddit formatting...")
        df['text_for_sentiment'] = df['text_raw'].apply(self.clean_reddit_text)
        
        # Remove empty text
        empty = (df['text_for_sentiment'].str.strip() == '').sum()
        if empty > 0:
            print(f"  Removing {empty:,} posts with empty text after cleaning")
            df = df[df['text_for_sentiment'].str.strip() != '']
        
        print(f"  Remaining: {len(df):,}")
        print()
        
        print("Sample cleaned text:")
        for i, text in enumerate(df['text_for_sentiment'].head(3), 1):
            print(f"  {i}. {text[:80]}...")
        print()
        
        # Step 8: Remove duplicates
        print("="*70)
        print("STEP 8: REMOVING DUPLICATES")
        print("="*70)
        
        initial = len(df)
        
        if 'id' in df.columns:
            df = df.drop_duplicates(subset='id', keep='first')
            print(f"  Removed {initial - len(df):,} duplicate IDs")
            initial = len(df)
        
        df = df.drop_duplicates(subset='text_for_sentiment', keep='first')
        print(f"  Removed {initial - len(df):,} duplicate texts")
        print(f"  Remaining: {len(df):,}")
        print()
        
        # Step 9: Add features
        print("="*70)
        print("STEP 9: ADDING FEATURES")
        print("="*70)
        
        df['text_length'] = df['text_for_sentiment'].str.len()
        df['word_count'] = df['text_for_sentiment'].str.split().str.len()
        
        print(f"  Avg text length: {df['text_length'].mean():.0f} chars")
        print(f"  Avg word count: {df['word_count'].mean():.0f} words")
        print()
        
        # Step 10: Select columns
        print("="*70)
        print("STEP 10: SELECTING FINAL COLUMNS")
        print("="*70)
        
        final_cols = ['date', 'text_for_sentiment']
        
        optional = ['title', 'subreddit', 'score', 'num_comments', 
                   'author', 'text_length', 'word_count']
        
        for col in optional:
            if col in df.columns:
                final_cols.append(col)
        
        df = df[final_cols]
        df = df.sort_values('date').reset_index(drop=True)
        
        print(f"  Final columns: {final_cols}")
        print()
        
        # Summary
        print("="*70)
        print("PREPROCESSING SUMMARY")
        print("="*70)
        print(f"Initial posts: {initial_count:,}")
        print(f"Final posts: {len(df):,}")
        print(f"Filtered out: {initial_count - len(df):,} ({(initial_count - len(df))/initial_count*100:.1f}%)")
        print()
        
        if len(df) == 0:
            print("ERROR: No posts remaining")
            return None
        
        print(f"Date range: {df['date'].min()} to {df['date'].max()}")
        print(f"Unique dates: {df['date'].nunique()}")
        print()
        
        daily = df.groupby('date').size()
        print(f"Posts per day:")
        print(f"  Average: {daily.mean():.1f}")
        print(f"  Min: {daily.min()}")
        print(f"  Max: {daily.max()}")
        print()
        
        if 'subreddit' in df.columns:
            print("Posts per subreddit:")
            for sub, count in df['subreddit'].value_counts().items():
                print(f"  r/{sub:20} - {count:5,}")
            print()
        
        print("Sample posts:")
        for i, row in df.head(5).iterrows():
            print(f"\nPost {i+1}:")
            print(f"  Date: {row['date']}")
            if 'title' in df.columns:
                print(f"  Title: {row['title'][:60]}...")
            print(f"  Text: {row['text_for_sentiment'][:80]}...")
        
        print()
        
        # Save
        print("="*70)
        print("SAVING")
        print("="*70)
        
        try:
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(self.output_path, index=False)
            
            size = self.output_path.stat().st_size
            print(f"SUCCESS!")
            print(f"  Location: {self.output_path.resolve()}")
            print(f"  Size: {size/1024:.2f} KB")
            
            verify = pd.read_csv(self.output_path)
            print(f"  Verified: {len(verify):,} rows")
            
            print()
            print("="*70)
            print("COMPLETE")
            print("="*70)
            print()
            print("Reddit data cleaned and ready for sentiment analysis!")
            
            return df
            
        except Exception as e:
            print(f"ERROR: {e}")
            return None


def main():
    """Main execution"""
    
    print()
    print("This will strictly filter Reddit data to keep only:")
    print("  - Posts with valid dates")
    print("  - Bitcoin-related content")
    print("  - Non-bot, non-meme, non-meta posts")
    print("  - Clean text (no emojis, formatting)")
    print()
    
    response = input("Continue? (y/n): ").strip().lower()
    if response != 'y':
        print("Cancelled")
        return
    
    print()
    
    preprocessor = StrictRedditPreprocessor()
    df = preprocessor.run_preprocessing()
    
    if df is not None and not df.empty:
        print()
        print(f"Success! {len(df):,} clean Reddit posts ready.")
    else:
        print()
        print("Preprocessing failed")


if __name__ == "__main__":
    main()