"""
Prepare the EA Sports FC 26 player-attribute dataset (SoFIFA scrape) for a
player-similarity model.

Reads data/fifa_raw/FC26_*.csv, keeps identity + the 41 numeric attribute
columns (the 6 headline ratings + ~35 detailed skills), optionally filters to
the top-5 European leagues, and saves data/fifa_players.parquet.

Run:  python load_fifa.py
"""

import glob
import sys

import pandas as pd

RAW_GLOB = "data/fifa_raw/FC26_*.csv"
OUTPUT = "data/fifa_players.parquet"

# Set to None to keep ALL top-division players worldwide (bigger candidate pool
# for similarity). Leave as the set below to restrict to the top-5 leagues.
TOP5 = {"Premier League", "La Liga", "Serie A", "Bundesliga", "Ligue 1"}

IDENTITY = [
    "player_id", "short_name", "long_name", "player_positions",
    "club_name", "league_name", "nationality_name", "age",
    "height_cm", "weight_kg", "preferred_foot", "overall", "potential",
    "value_eur",
]

# The contiguous block of 0-99 numeric attributes in this dataset.
HEADLINE = ["pace", "shooting", "passing", "dribbling", "defending", "physic"]
SKILL_PREFIXES = (
    "attacking_", "skill_", "movement_", "power_",
    "mentality_", "defending_", "goalkeeping_",
)
# Extra useful ordinal attributes worth including as features.
# (skill_moves is already captured by the 'skill_' prefix above.)
EXTRA = ["weak_foot", "international_reputation"]


def main() -> None:
    paths = sorted(glob.glob(RAW_GLOB))
    if not paths:
        sys.exit(f"No files matched {RAW_GLOB} — drop the FC26 CSV there first.")
    df = pd.concat(
        [pd.read_csv(p, low_memory=False) for p in paths], ignore_index=True
    )
    print(f"Loaded {len(df)} players from {len(paths)} file(s).")

    if TOP5 is not None:
        df = df[df["league_name"].isin(TOP5)]
        print(f"Filtered to top-5 leagues: {len(df)} players.")
    else:
        df = df[df["league_level"] == 1]
        print(f"Kept top-division players worldwide: {len(df)} players.")

    skill_cols = [c for c in df.columns if c.startswith(SKILL_PREFIXES)]
    feature_cols = list(
        dict.fromkeys(  # preserve order, drop any accidental dupes
            HEADLINE + skill_cols + [c for c in EXTRA if c in df.columns]
        )
    )
    keep = [c for c in IDENTITY if c in df.columns] + feature_cols
    out = df[keep].copy()

    # Goalkeepers legitimately lack outfield headline ratings (pace, etc.) and
    # outfielders lack goalkeeping_* — that's expected. Fill those structural
    # NaNs with 0 so every row has a complete vector; downstream we filter
    # similarity by position anyway.
    out[feature_cols] = out[feature_cols].apply(pd.to_numeric, errors="coerce")
    out[feature_cols] = out[feature_cols].fillna(0)

    out.to_parquet(OUTPUT, index=False)
    print(f"\nSaved {len(out)} players x {len(feature_cols)} features -> {OUTPUT}")
    print(f"Features ({len(feature_cols)}):", feature_cols[:8], "...")
    print(out[["short_name", "player_positions", "overall"]].head(5).to_string(index=False))


if __name__ == "__main__":
    main()
