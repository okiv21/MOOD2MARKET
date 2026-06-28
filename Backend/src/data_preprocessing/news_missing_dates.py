"""
Check for Missing Dates in News Data
Compares news dates with BTC price dates to find gaps
"""

import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

class DateGapChecker:
    """Check for missing dates in news data"""
    
    def __init__(
        self,
        btc_path=r"C:\Users\OKIO\Desktop\mood2market\Backend\Data\processed\btc_price_data.csv",
        news_path=r"C:\Users\OKIO\Desktop\mood2market\Backend\Data\processed\news_clean.csv"
    ):
        self.btc_path = Path(btc_path)
        self.news_path = Path(news_path)
    
    def check_missing_dates(self):
        """Check for missing dates and coverage gaps"""
        
        print("="*70)
        print("DATE COVERAGE CHECK")
        print("="*70)
        print()
        
        # Load BTC data
        print("Loading BTC price data...")
        if not self.btc_path.exists():
            print(f"ERROR: BTC file not found at {self.btc_path}")
            return
        
        btc_df = pd.read_csv(self.btc_path)
        btc_df['date'] = pd.to_datetime(btc_df['date']).dt.date
        
        print(f"  Rows: {len(btc_df):,}")
        print(f"  Date range: {btc_df['date'].min()} to {btc_df['date'].max()}")
        print(f"  Unique dates: {btc_df['date'].nunique()}")
        print()
        
        # Load News data
        print("Loading news data...")
        if not self.news_path.exists():
            print(f"ERROR: News file not found at {self.news_path}")
            return
        
        news_df = pd.read_csv(self.news_path)
        news_df['date'] = pd.to_datetime(news_df['date']).dt.date
        
        print(f"  Rows: {len(news_df):,}")
        print(f"  Date range: {news_df['date'].min()} to {news_df['date'].max()}")
        print(f"  Unique dates: {news_df['date'].nunique()}")
        print()
        
        # Get date sets
        btc_dates = set(btc_df['date'])
        news_dates = set(news_df['date'])
        
        # Find overlaps and gaps
        print("="*70)
        print("DATE COMPARISON")
        print("="*70)
        print()
        
        # Dates in both
        common_dates = btc_dates & news_dates
        print(f"Dates in BOTH datasets: {len(common_dates)}")
        
        # Dates only in BTC
        btc_only = btc_dates - news_dates
        print(f"Dates ONLY in BTC (missing news): {len(btc_only)}")
        
        # Dates only in News
        news_only = news_dates - btc_dates
        print(f"Dates ONLY in News (missing BTC): {len(news_only)}")
        print()
        
        # Coverage percentage
        btc_start = min(btc_dates)
        btc_end = max(btc_dates)
        news_start = min(news_dates)
        news_end = max(news_dates)
        
        # Use the common range
        common_start = max(btc_start, news_start)
        common_end = min(btc_end, news_end)
        
        print("="*70)
        print("COVERAGE ANALYSIS")
        print("="*70)
        print()
        print(f"BTC data range:  {btc_start} to {btc_end}")
        print(f"News data range: {news_start} to {news_end}")
        print(f"Common range:    {common_start} to {common_end}")
        print()
        
        # Calculate expected days in common range
        expected_days = (common_end - common_start).days + 1
        actual_common = len(common_dates)
        
        print(f"Expected days in common range: {expected_days}")
        print(f"Actual days with both:         {actual_common}")
        print(f"Coverage:                      {actual_common/expected_days*100:.1f}%")
        print()
        
        # Missing dates in common range
        all_dates_in_range = set()
        current = common_start
        while current <= common_end:
            all_dates_in_range.add(current)
            current += timedelta(days=1)
        
        missing_in_btc = all_dates_in_range - btc_dates
        missing_in_news = all_dates_in_range - news_dates
        
        print("="*70)
        print("MISSING DATES IN COMMON RANGE")
        print("="*70)
        print()
        print(f"Missing in BTC:  {len(missing_in_btc)}")
        print(f"Missing in News: {len(missing_in_news)}")
        print()
        
        # Show missing dates
        if missing_in_btc:
            print(f"Dates missing in BTC (first 20):")
            for i, date in enumerate(sorted(missing_in_btc)[:20], 1):
                print(f"  {i:2}. {date}")
            if len(missing_in_btc) > 20:
                print(f"  ... and {len(missing_in_btc) - 20} more")
            print()
        
        if missing_in_news:
            print(f"Dates missing in News (first 20):")
            for i, date in enumerate(sorted(missing_in_news)[:20], 1):
                articles_on_date = len(news_df[news_df['date'] == date])
                print(f"  {i:2}. {date}")
            if len(missing_in_news) > 20:
                print(f"  ... and {len(missing_in_news) - 20} more")
            print()
        
        # Articles per day statistics
        print("="*70)
        print("ARTICLES PER DAY STATISTICS")
        print("="*70)
        print()
        
        daily_counts = news_df.groupby('date').size()
        
        print(f"News articles per day:")
        print(f"  Average:  {daily_counts.mean():.1f}")
        print(f"  Median:   {daily_counts.median():.0f}")
        print(f"  Minimum:  {daily_counts.min()}")
        print(f"  Maximum:  {daily_counts.max()}")
        print()
        
        # Days with low coverage
        low_coverage = daily_counts[daily_counts < 5]
        if len(low_coverage) > 0:
            print(f"Days with < 5 articles: {len(low_coverage)}")
            print("First 10:")
            for date, count in low_coverage.head(10).items():
                print(f"  {date}: {count} articles")
            print()
        
        # Days with zero articles in common range
        zero_days = []
        for date in all_dates_in_range:
            if date not in news_dates:
                zero_days.append(date)
        
        if zero_days:
            print(f"Days with ZERO articles in common range: {len(zero_days)}")
            print("First 20:")
            for i, date in enumerate(sorted(zero_days)[:20], 1):
                print(f"  {i:2}. {date}")
            if len(zero_days) > 20:
                print(f"  ... and {len(zero_days) - 20} more")
            print()
        
        # Summary
        print("="*70)
        print("SUMMARY")
        print("="*70)
        print()
        
        if len(missing_in_news) == 0 and len(zero_days) == 0:
            print("PERFECT COVERAGE!")
            print(f"  All {expected_days} days have news articles")
            print(f"  All {len(btc_dates)} BTC dates have matching news")
        else:
            print("COVERAGE ISSUES FOUND:")
            if missing_in_news:
                print(f"  - {len(missing_in_news)} dates missing in news")
            if zero_days:
                print(f"  - {len(zero_days)} days with zero articles")
            
            print()
            print("RECOMMENDATIONS:")
            if len(missing_in_news) > 0:
                print(f"  1. Re-run GDELT collection for missing dates")
                print(f"  2. Or accept {len(missing_in_news)} days without news")
            
            if len(zero_days) > 50:
                print(f"  3. Many missing dates - consider re-collecting GDELT data")
            elif len(zero_days) > 0:
                print(f"  3. Few missing dates - acceptable for model training")
        
        print()
        
        # Data alignment status
        print("="*70)
        print("DATA ALIGNMENT STATUS")
        print("="*70)
        print()
        
        alignment_score = (actual_common / expected_days) * 100
        
        if alignment_score >= 95:
            status = "EXCELLENT"
            emoji = "✅"
        elif alignment_score >= 85:
            status = "GOOD"
            emoji = "✓"
        elif alignment_score >= 70:
            status = "ACCEPTABLE"
            emoji = "⚠"
        else:
            status = "POOR"
            emoji = "❌"
        
        print(f"Alignment Score: {alignment_score:.1f}% - {status} {emoji}")
        print()
        
        if alignment_score >= 85:
            print("Your data is well-aligned and ready for model training!")
        elif alignment_score >= 70:
            print("Data alignment is acceptable for training.")
            print("Some gaps exist but shouldn't significantly impact results.")
        else:
            print("Data alignment needs improvement.")
            print("Consider re-collecting news data for better coverage.")
        
        print()
        
        # Return statistics
        return {
            'btc_dates': len(btc_dates),
            'news_dates': len(news_dates),
            'common_dates': len(common_dates),
            'missing_in_news': len(missing_in_news),
            'zero_article_days': len(zero_days),
            'coverage_pct': alignment_score
        }


def main():
    """Main execution"""
    
    checker = DateGapChecker()
    stats = checker.check_missing_dates()
    
    if stats:
        print()
        print("Check complete!")


if __name__ == "__main__":
    main()