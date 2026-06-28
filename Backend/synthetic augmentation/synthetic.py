"""
Mood2Market — Gaussian Noise Synthetic Data Augmentation
Augments the merged_dataset.csv training split with synthetic samples.
Only the training set is augmented — validation and test sets remain real data only.
"""

import pandas as pd
import numpy as np
import os

# FILE PATHS
MERGED_CSV   = r"C:\Users\OKIO\Desktop\mood2market\Backend\Data\processed\main Data\new_merged.csv"
OUTPUT_CSV   = r"C:\Users\OKIO\Desktop\mood2market\Backend\Data\processed\main Data\merged_augmented.csv"

# CONFIG 
NOISE_SCALE  = 0.01     # standard deviation of Gaussian noise (1% of feature scale)
N_AUGMENTED  = 600      # number of synthetic rows to generate
RANDOM_SEED  = 42
TRAIN_RATIO  = 0.80     # must match  LSTM  uses

# FEATURES to augment (continuous only — do NOT augment binary flags)
CONTINUOUS_FEATURES = [
    "log_return",
    "volatility_7d",
    "hl_pct",
    "momentum_7d",
    "sentiment_score_x",   # news sentiment
    "sentiment_score_y",   # reddit sentiment
    "news_count",
    "reddit_count",
    "volume",
]

# Binary / categorical columns — kept as-is from sampled rows
BINARY_FEATURES = [
    "has_news",
    "has_reddit",
    "reddit_available",
]


def load_and_split(path):
    df = pd.read_csv(path, parse_dates=["date"])
    df.sort_values("date", inplace=True)
    df.reset_index(drop=True, inplace=True)

    n_train = int(len(df) * TRAIN_RATIO)
    train   = df.iloc[:n_train].copy()
    val_test = df.iloc[n_train:].copy()

    print(f"Loaded  : {len(df)} total rows")
    print(f"Train   : {len(train)} rows  ({train['date'].min().date()} → {train['date'].max().date()})")
    print(f"Val+Test: {len(val_test)} rows  ({val_test['date'].min().date()} → {val_test['date'].max().date()})")
    return train, val_test, df.columns.tolist()


def generate_synthetic(train_df, n_samples, noise_scale, seed):
    np.random.seed(seed)
    rng = np.random.default_rng(seed)

    # Sample rows from training set with replacement as base
    base = train_df.sample(n=n_samples, replace=True, random_state=seed).copy()
    base.reset_index(drop=True, inplace=True)

    # Compute per-feature std from training set
    feature_stds = train_df[CONTINUOUS_FEATURES].std()

    # Add Gaussian noise scaled by feature std
    noise = pd.DataFrame(
        rng.normal(loc=0.0, scale=noise_scale, size=(n_samples, len(CONTINUOUS_FEATURES))),
        columns=CONTINUOUS_FEATURES
    )
    # Scale noise by each feature's std so noise is proportional to feature magnitude
    noise = noise * feature_stds.values

    # Apply noise to continuous features only
    for col in CONTINUOUS_FEATURES:
        if col in base.columns:
            base[col] = base[col] + noise[col]

    # Clip sentiment scores to valid range [-1, 1]
    for col in ["sentiment_score_x", "sentiment_score_y"]:
        if col in base.columns:
            base[col] = base[col].clip(-1.0, 1.0)

    # Clip log_return to prevent extreme outliers
    lr_std = train_df["log_return"].std()
    base["log_return"] = base["log_return"].clip(-4 * lr_std, 4 * lr_std)

    # Clip counts to non-negative
    for col in ["news_count", "reddit_count", "volume"]:
        if col in base.columns:
            base[col] = base[col].clip(lower=0)

    # Mark synthetic rows with a flag
    base["is_synthetic"] = 1

    # Assign synthetic dates — offset from the sampled date by a small jitter
    # (keeps temporal ordering roughly intact for identification purposes)
    base["date"] = pd.NaT  # synthetic rows have no real date

    return base


def build_augmented_dataset(train_df, synthetic_df, val_test_df, all_cols):
    # Add is_synthetic flag to real data
    train_real = train_df.copy()
    train_real["is_synthetic"] = 0
    val_test_real = val_test_df.copy()
    val_test_real["is_synthetic"] = 0

    # Combine real train + synthetic
    augmented_train = pd.concat([train_real, synthetic_df], ignore_index=True)

    # Shuffle augmented training set
    augmented_train = augmented_train.sample(frac=1, random_state=RANDOM_SEED).reset_index(drop=True)

    # Full augmented dataset: augmented train + real val/test
    full = pd.concat([augmented_train, val_test_real], ignore_index=True)

    return augmented_train, full


def print_stats(train_df, synthetic_df, augmented_train):
    print("\n── Feature statistics comparison ──────────────────────────────")
    print(f"{'Feature':<25} {'Real mean':>12} {'Synth mean':>12} {'Real std':>10} {'Synth std':>10}")
    print("-" * 72)
    for col in CONTINUOUS_FEATURES:
        if col in train_df.columns and col in synthetic_df.columns:
            rm = train_df[col].mean()
            sm = synthetic_df[col].mean()
            rs = train_df[col].std()
            ss = synthetic_df[col].std()
            print(f"{col:<25} {rm:>12.5f} {sm:>12.5f} {rs:>10.5f} {ss:>10.5f}")
    print(f"\nAugmented training set : {len(augmented_train)} rows")
    print(f"  Real samples         : {(augmented_train['is_synthetic'] == 0).sum()}")
    print(f"  Synthetic samples    : {(augmented_train['is_synthetic'] == 1).sum()}")


def main():
    print("=" * 60)
    print("Mood2Market — Gaussian Noise Augmentation")
    print("=" * 60)

    if not os.path.exists(MERGED_CSV):
        print(f"\nERROR: File not found: {MERGED_CSV}")
        return

    train_df, val_test_df, all_cols = load_and_split(MERGED_CSV)

    print(f"\nGenerating {N_AUGMENTED} synthetic samples (noise_scale={NOISE_SCALE})...")
    synthetic_df = generate_synthetic(train_df, N_AUGMENTED, NOISE_SCALE, RANDOM_SEED)

    augmented_train, full_df = build_augmented_dataset(
        train_df, synthetic_df, val_test_df, all_cols
    )

    print_stats(train_df, synthetic_df, augmented_train)

    # Save augmented dataset
    full_df.to_csv(OUTPUT_CSV, index=False)
    print(f"\nSaved augmented dataset to:\n  {OUTPUT_CSV}")
    print(f"Total rows (train aug + real val/test): {len(full_df)}")
    print("\nNOTE: Use 'is_synthetic' column to filter during evaluation.")
    print("      Always evaluate on real data only (is_synthetic == 0).")


if __name__ == "__main__":
    main()