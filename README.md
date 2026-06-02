# ◎ Scout — Football Player Similarity

**▶ Live app: [find-similar-player-profiles.streamlit.app](https://find-similar-player-profiles.streamlit.app/)**

Find a player's nearest stylistic profiles from their attributes. Pick a player
and the model surfaces the most similar players in Europe's top-5 leagues —
position-aware, with an attribute radar to compare them side by side.

Built on **EA Sports FC 26** standard-card attributes (SoFIFA), with a
custom-themed Streamlit UI.

```
Rodri      → Rice · Tchouaméni · Locatelli      (deep-lying holders)
Bellingham → Reijnders · Barella · Valverde      (box-to-box creators)
Saliba     → Konaté · Gabriel · Buongiorno       (ball-playing centre-backs)
```

## How it works

- **Data** — one standard card per player (top-5 leagues, 3,204 players), 44
  numeric attributes: the 6 headline ratings (`pace, shooting, passing,
  dribbling, defending, physic`) plus ~35 detailed SoFIFA skills.
- **Model** — features are standardized (`StandardScaler`) so no single rating
  dominates, then ranked by **cosine similarity**. Comparisons are
  position-aware by default (a striker is matched against attackers, a keeper
  against keepers), which also neutralizes the structural zeros keepers and
  outfielders have in each other's attributes.
- **UI** — a dark, pitch-themed Streamlit app: searchable player picker,
  result/age/position filters, ranked comp list with similarity bars, and a
  Plotly attribute radar.

## Run locally

```bash
git clone https://github.com/kalsangNoe/player-similarity.git
cd player-similarity

python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

streamlit run app.py
```

Then open http://localhost:8501.

To query the model directly without the UI:

```python
from similarity import PlayerSimilarity

model = PlayerSimilarity()
model.find_similar("Rodri")                    # top 10, same position group
model.find_similar("Saliba", max_age=23)       # young alternatives (scouting)
model.find_similar("Vinícius", same_group=False)  # pure attribute match
```

## Project layout

| File | Purpose |
|------|---------|
| `app.py` | Streamlit scouting UI |
| `similarity.py` | similarity model (`PlayerSimilarity`) |
| `load_fifa.py` | raw FC 26 CSV → cleaned `data/fifa_players.parquet` |
| `data/fifa_players.parquet` | model-ready attribute table (committed) |
| `.streamlit/config.toml` | UI theme |
| `collect_data.py` | FBref match-stat collector (kept for reference) |

## Rebuilding the data

The processed parquet is committed, so the app runs as-is. To rebuild from
source, download the [EA Sports FC 26 SoFIFA dataset](https://www.kaggle.com/datasets/rovnez/fc-26-fifa-26-player-data),
drop the CSV into `data/fifa_raw/`, then:

```bash
python load_fifa.py        # set TOP5 = None inside to go global
```

## Deploy

Deployed free on [Streamlit Community Cloud](https://share.streamlit.io) at
**[find-similar-player-profiles.streamlit.app](https://find-similar-player-profiles.streamlit.app/)**
— repo `kalsangNoe/player-similarity`, branch `main`, main file `app.py`. Every
push to `main` auto-redeploys.

## Notes & limitations

- This is **attribute** similarity (player archetype/profile), not
  season-performance similarity. It answers "who plays a similar style," not
  "who's producing similar output right now."
- Attributes are EA's editorial ratings — a useful, consistent proxy, but not
  ground-truth event data.

---

*Data: EA Sports FC 26 / SoFIFA. This project is unaffiliated with EA Sports.*
