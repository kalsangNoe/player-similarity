"""
Collect free football player data from FBref (StatsBomb-powered) for a
player-similarity model.

Pulls per-90 performance stats for the top-5 European leagues across
multiple seasons, merges the different stat categories into one wide table,
and saves it to data/players.parquet.

Run:  python collect_data.py
"""

import functools

import pandas as pd
import soccerdata as sd

# --- Configuration ----------------------------------------------------------

LEAGUES = [
    "ENG-Premier League",
    "ESP-La Liga",
    "ITA-Serie A",
    "GER-Bundesliga",
    "FRA-Ligue 1",
]

# FBref season strings. "2324" == 2023-2024. Add/remove as you like.
SEASONS = ["2122", "2223", "2324"]

# FBref groups its stats into these tables. We pull each and merge them.
# This gives a very wide feature set covering every phase of play.
STAT_TYPES = [
    "standard",      # goals, assists, xG, xA, minutes
    "shooting",      # shots, shot quality
    "passing",       # pass completion, progressive passes, key passes
    "passing_types", # crosses, through balls, switches
    "goal_shot_creation",  # SCA / GCA
    "defense",       # tackles, interceptions, blocks
    "possession",    # carries, touches by zone, take-ons
    "misc",          # fouls, aerials won, recoveries
]

# Only keep players with at least this many minutes — low-minute players have
# noisy per-90 numbers that pollute similarity.
MIN_MINUTES = 500

OUTPUT = "data/players.parquet"


# --- Collection -------------------------------------------------------------

def fetch_stat_type(fbref: sd.FBref, stat_type: str) -> pd.DataFrame:
    """Read one stat table and flatten its multi-level columns."""
    print(f"  fetching '{stat_type}' ...")
    df = fbref.read_player_season_stats(stat_type=stat_type)

    # FBref returns a MultiIndex on columns like ('Passing', 'Cmp%').
    # Flatten to 'Passing_Cmp%' and prefix with the stat_type to avoid
    # collisions between tables.
    df = df.copy()
    df.columns = [
        "_".join(str(c) for c in col if c and "Unnamed" not in str(c)).strip("_")
        for col in df.columns.to_flat_index()
    ]
    # Prefix everything except the shared identity/minutes columns.
    keep_as_is = {"nation", "pos", "age", "born", "90s", "MP", "Min"}
    df = df.rename(
        columns={
            c: f"{stat_type}__{c}" for c in df.columns if c not in keep_as_is
        }
    )
    return df


def main() -> None:
    fbref = sd.FBref(leagues=LEAGUES, seasons=SEASONS)

    print(f"Collecting {len(STAT_TYPES)} stat tables for "
          f"{len(LEAGUES)} leagues x {len(SEASONS)} seasons...")

    frames = [fetch_stat_type(fbref, st) for st in STAT_TYPES]

    # The index (league, season, team, player) is shared across tables, so we
    # can join them on the index. Drop duplicate identity columns as we go.
    def merge(left: pd.DataFrame, right: pd.DataFrame) -> pd.DataFrame:
        dupes = [c for c in right.columns if c in left.columns]
        return left.join(right.drop(columns=dupes), how="outer")

    players = functools.reduce(merge, frames)
    players = players.reset_index()

    # Minutes column is named 'Min' under the standard table; guard for both.
    min_col = "Min" if "Min" in players.columns else "standard__Min"
    if min_col in players.columns:
        before = len(players)
        players = players[players[min_col].fillna(0) >= MIN_MINUTES]
        print(f"Filtered to >= {MIN_MINUTES} mins: {before} -> {len(players)} rows")

    players.to_parquet(OUTPUT, index=False)
    print(f"\nSaved {len(players)} player-seasons x {players.shape[1]} columns "
          f"-> {OUTPUT}")
    print("Sample columns:", list(players.columns[:12]), "...")


if __name__ == "__main__":
    main()
