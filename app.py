"""
Scout — player similarity explorer (Streamlit).

Custom-themed UI over the FC 26 attribute similarity model.
Run:  streamlit run app.py
"""

import plotly.graph_objects as go
import streamlit as st

from similarity import PlayerSimilarity

st.set_page_config(page_title="SCOUT", page_icon="◎", layout="wide")

# ---------------------------------------------------------------- styling ---
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=JetBrains+Mono:wght@400;700&display=swap');

html, body, [class*="css"]  { font-family: 'Space Grotesk', sans-serif; }

/* kill the stock chrome */
#MainMenu, header, footer {visibility: hidden;}
.block-container {padding-top: 2.2rem; max-width: 1200px;}

/* page background: subtle pitch-line gradient */
.stApp {
  background:
    radial-gradient(1200px 600px at 80% -10%, rgba(200,255,0,.06), transparent 60%),
    #0d1117;
}

/* wordmark */
.brand { font-family:'JetBrains Mono',monospace; font-weight:700;
  letter-spacing:.5em; font-size:.8rem; color:#c8ff00; text-transform:uppercase; }
.headline { font-size:2.6rem; font-weight:700; line-height:1.05; margin:.1rem 0 .2rem; }
.sub { color:#7d8590; font-size:.95rem; margin-bottom:1.4rem; }

/* target player banner */
.target {
  border:1px solid #30363d; border-left:3px solid #c8ff00;
  background:linear-gradient(90deg, rgba(200,255,0,.05), transparent);
  border-radius:10px; padding:1rem 1.3rem; margin:.4rem 0 1.6rem;
}
.target .name { font-size:1.5rem; font-weight:700; }
.target .meta { color:#7d8590; font-size:.9rem; }
.pill { display:inline-block; font-family:'JetBrains Mono',monospace;
  font-size:.7rem; padding:.15rem .5rem; border:1px solid #30363d;
  border-radius:999px; color:#c8ff00; margin-right:.4rem; }

/* comp rows */
.row {
  display:grid; grid-template-columns: 2.4fr 1fr 1.1fr 1fr 1.6fr;
  align-items:center; gap:.6rem;
  border:1px solid #21262d; border-radius:9px;
  padding:.7rem 1rem; margin-bottom:.5rem; background:#161b22;
  transition:border-color .15s ease;
}
.row:hover { border-color:#c8ff00; }
.row .pname { font-weight:600; font-size:1.05rem; }
.row .pclub { color:#7d8590; font-size:.8rem; }
.row .stat  { font-family:'JetBrains Mono',monospace; color:#adbac7; font-size:.9rem; }
.bar-wrap { background:#21262d; border-radius:6px; height:22px; position:relative; overflow:hidden; }
.bar { height:100%; background:linear-gradient(90deg,#5a7000,#c8ff00); border-radius:6px; }
.bar-txt { position:absolute; right:8px; top:0; line-height:22px;
  font-family:'JetBrains Mono',monospace; font-weight:700; font-size:.8rem; color:#0d1117; }

label, .stSlider, .stSelectbox { font-family:'Space Grotesk',sans-serif !important; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


@st.cache_resource
def load_model() -> PlayerSimilarity:
    return PlayerSimilarity()


model = load_model()
df = model.df
HEADLINE = ["pace", "shooting", "passing", "dribbling", "defending", "physic"]

# ----------------------------------------------------------------- header ---
st.markdown('<div class="brand">◎ scout</div>', unsafe_allow_html=True)
st.markdown('<div class="headline">Find a player\'s nearest profiles.</div>',
            unsafe_allow_html=True)
st.markdown('<div class="sub">EA Sports FC 26 · top-5 leagues · '
            f'{len(df):,} players · cosine similarity on 44 attributes</div>',
            unsafe_allow_html=True)

# --------------------------------------------------------------- controls ---
names = sorted(df["short_name"].unique().tolist())
default = names.index("Rodri") if "Rodri" in names else 0
c1, c2, c3, c4 = st.columns([3, 1, 1.3, 1])
with c1:
    player = st.selectbox("Player", names, index=default)
with c2:
    n = st.slider("Results", 5, 25, 10)
with c3:
    max_age = st.slider("Max age", 16, 40, 40)
with c4:
    same_group = st.toggle("Same position", value=True)

# ------------------------------------------------------------------ query ---
res = model.find_similar(
    player, n=n, same_group=same_group,
    max_age=None if max_age >= 40 else max_age,
)
t = df[df["short_name"] == player].iloc[0]

# target banner
st.markdown(
    f'<div class="target"><div class="name">{t["long_name"]}</div>'
    f'<div class="meta">'
    f'<span class="pill">{t["primary_pos"]}</span>'
    f'<span class="pill">OVR {t["overall"]}</span>'
    f'{t["club_name"]} · {t["league_name"]} · age {t["age"]}'
    f'</div></div>',
    unsafe_allow_html=True,
)

left, right = st.columns([1.55, 1])

# comp list
with left:
    st.markdown("**Nearest profiles**")
    for _, r in res.iterrows():
        pct = r["similarity"]
        st.markdown(
            f'<div class="row">'
            f'<div><div class="pname">{r["short_name"]}</div>'
            f'<div class="pclub">{r["club_name"]}</div></div>'
            f'<div class="stat">{r["primary_pos"]}</div>'
            f'<div class="stat">age {r["age"]}</div>'
            f'<div class="stat">OVR {r["overall"]}</div>'
            f'<div class="bar-wrap"><div class="bar" style="width:{pct}%"></div>'
            f'<div class="bar-txt">{pct:.1f}%</div></div>'
            f'</div>',
            unsafe_allow_html=True,
        )

# radar: target vs top comp
with right:
    st.markdown("**Attribute radar**")
    compare_to = st.selectbox("Overlay", res["short_name"].tolist(), index=0,
                              label_visibility="collapsed")
    comp = df[df["short_name"] == compare_to].iloc[0]
    fig = go.Figure()
    for row, color in [(t, "#c8ff00"), (comp, "#58a6ff")]:
        fig.add_trace(go.Scatterpolar(
            r=[row[a] for a in HEADLINE] + [row[HEADLINE[0]]],
            theta=[a.title() for a in HEADLINE] + [HEADLINE[0].title()],
            fill="toself", name=row["short_name"],
            line=dict(color=color, width=2), opacity=.6,
        ))
    fig.update_layout(
        polar=dict(
            bgcolor="#161b22",
            radialaxis=dict(range=[0, 99], showticklabels=False, gridcolor="#30363d"),
            angularaxis=dict(gridcolor="#30363d", tickfont=dict(size=11)),
        ),
        paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#e6edf3"),
        showlegend=True, legend=dict(orientation="h", y=-.1),
        margin=dict(l=30, r=30, t=20, b=20), height=380,
    )
    st.plotly_chart(fig, use_container_width=True)
