"""
Player similarity model over EA Sports FC 26 standard-card attributes.

Standardizes the 44 attribute features, then finds nearest neighbours by
cosine similarity. Comparisons are position-aware by default (a striker is
matched against attackers, a keeper against keepers) which also neutralizes
the structural zeros GKs/outfielders have in each other's attributes.

Usage:
    from similarity import PlayerSimilarity
    model = PlayerSimilarity()
    model.find_similar("Bellingham")
    model.find_similar("Rodri", n=10, same_group=True)
"""

from __future__ import annotations

import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler

DATA = "data/fifa_players.parquet"

ID_COLS = [
    "player_id", "short_name", "long_name", "player_positions", "club_name",
    "league_name", "nationality_name", "age", "height_cm", "weight_kg",
    "preferred_foot", "overall", "potential", "value_eur",
]

# Map a primary position to a broad group for position-aware comparison.
POS_GROUP = {
    "GK": "GK",
    "CB": "DEF", "RB": "DEF", "LB": "DEF", "RWB": "DEF", "LWB": "DEF",
    "CDM": "MID", "CM": "MID", "CAM": "MID", "RM": "MID", "LM": "MID",
    "RW": "FWD", "LW": "FWD", "ST": "FWD", "CF": "FWD",
}


class PlayerSimilarity:
    def __init__(self, data_path: str = DATA):
        df = pd.read_parquet(data_path).reset_index(drop=True)
        self.feature_cols = [c for c in df.columns if c not in ID_COLS]

        df["primary_pos"] = (
            df["player_positions"].str.split(",").str[0].str.strip()
        )
        df["pos_group"] = df["primary_pos"].map(POS_GROUP).fillna("OTHER")
        self.df = df

        # Standardize features so every attribute contributes comparably.
        self.scaler = StandardScaler()
        self.X = self.scaler.fit_transform(df[self.feature_cols])

        # Full pairwise cosine similarity (3.2k players -> tiny, instant).
        self.sim = cosine_similarity(self.X)

    # -- lookup helpers ------------------------------------------------------
    def _find_index(self, name: str) -> int:
        name = name.strip().lower()
        d = self.df
        exact = d.index[d["short_name"].str.lower() == name]
        if len(exact):
            return int(exact[0])
        # substring match on short or long name
        mask = (
            d["short_name"].str.lower().str.contains(name, na=False)
            | d["long_name"].str.lower().str.contains(name, na=False)
        )
        hits = d.index[mask]
        if len(hits) == 0:
            raise ValueError(f"No player matching {name!r}.")
        if len(hits) > 1:
            options = d.loc[hits, "short_name"].tolist()[:8]
            print(f"Multiple matches for {name!r}: {options} — using first.")
        return int(hits[0])

    # -- main API ------------------------------------------------------------
    def find_similar(
        self,
        name: str,
        n: int = 10,
        same_group: bool = True,
        max_age: int | None = None,
        positions: list[str] | None = None,
    ) -> pd.DataFrame:
        i = self._find_index(name)
        target = self.df.loc[i]
        scores = self.sim[i]

        cand = self.df.copy()
        cand["similarity"] = scores
        cand = cand.drop(index=i)  # exclude the player themselves

        if same_group:
            cand = cand[cand["pos_group"] == target["pos_group"]]
        if positions:
            cand = cand[cand["primary_pos"].isin(positions)]
        if max_age is not None:
            cand = cand[cand["age"] <= max_age]

        cols = ["short_name", "primary_pos", "club_name", "league_name",
                "age", "overall", "value_eur", "similarity"]
        out = cand.sort_values("similarity", ascending=False).head(n)[cols]
        out["similarity"] = (out["similarity"] * 100).round(1)
        print(f"Most similar to {target['short_name']} "
              f"({target['primary_pos']}, {target['club_name']}, "
              f"overall {target['overall']}):")
        return out.reset_index(drop=True)


if __name__ == "__main__":
    model = PlayerSimilarity()
    for who in ["Bellingham", "Rodri", "Saliba"]:
        print(model.find_similar(who, n=6).to_string(index=False))
        print()
