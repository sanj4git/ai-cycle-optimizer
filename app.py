import streamlit as st
import pandas as pd
from src.model_loader import load_model

st.set_page_config(
    page_title="AI-Cycle Optimizer",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Dark professional CSS ──
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* Dark background */
.stApp { background: #0e1117; }
[data-testid="stSidebar"] { background: #1a1d24; border-right: 1px solid #2d333b; }

/* Metric cards */
[data-testid="stMetric"] {
    background: #1a1d24;
    border: 1px solid #2d333b;
    border-radius: 8px;
    padding: 16px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.3);
}
[data-testid="stMetric"] label { color: #8b949e !important; font-size: 0.78rem !important; font-weight: 500 !important; text-transform: uppercase; letter-spacing: 0.5px; }
[data-testid="stMetric"] [data-testid="stMetricValue"] { color: #f0f6fc !important; font-weight: 700 !important; }

h1, h2, h3 { color: #f0f6fc !important; font-weight: 700 !important; }
p, li, span, div, label, .stMarkdown { color: #c9d1d9 !important; }
[data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] li { color: #c9d1d9 !important; }

/* Section labels */
.section-label {
    color: #58a6ff; font-size: 0.72rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 1.2px;
    margin-bottom: 12px; padding-bottom: 6px;
    border-bottom: 2px solid #58a6ff;
    display: inline-block;
}

.card {
    background: #1a1d24; border: 1px solid #2d333b; border-radius: 8px;
    padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.3);
}

/* Buttons */
.stButton > button {
    background: #238636; color: #fff; border: none;
    border-radius: 6px; font-weight: 600; padding: 8px 20px;
}
.stButton > button:hover { background: #2ea043; }

hr { border-color: #2d333b !important; }

/* Clean dataframe */
[data-testid="stDataFrame"] { border: 1px solid #2d333b; border-radius: 8px; overflow: hidden; }

/* Active model badge */
.model-badge {
    display: inline-block; padding: 4px 12px; border-radius: 20px;
    font-size: 0.75rem; font-weight: 600;
}
.model-badge.active { background: #1a4731; color: #3fb950; }
.model-badge.fallback { background: #3d2e00; color: #d29922; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ──
with st.sidebar:
    st.markdown("### ⚙️ AI-Cycle Optimizer")
    st.caption("Team AI-Cycle &nbsp;•&nbsp; CreaTech 2026")
    st.markdown("---")

    model = load_model()
    if model:
        st.markdown('<span class="model-badge active">✅ ML Model Active (XGBoost ×10)</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="model-badge fallback">⚡ Physics Model (Fallback)</span>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
    **Pages**
    - 📊 Yard Dashboard
    - 🧪 Scenario Builder
    - 🎯 Optimizer
    - 🔬 What-If Analysis
    """)

# ── Load Data ──
@st.cache_data
def load_data():
    try: return pd.read_csv("data/precast_dataset.csv")
    except: return None

df = load_data()

# ── Hero ──
st.markdown("# AI-Cycle Optimizer")
st.markdown("**AI-powered decision support for precast yard cycle time optimization** — balancing strength gain, cost, risk, and throughput across Indian climatic regions.")

st.markdown("---")

# ── What This System Does (concise) ──
st.markdown('<div class="section-label">What This System Does</div>', unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown("""**🧠 Predict Strength**

Given mix design, curing method, and climate conditions — predict when concrete
reaches the required demoulding strength, with uncertainty bounds.""")
with c2:
    st.markdown("""**💰 Estimate Costs**

For any demoulding time, compute the total expected cost — yard holding,
steam treatment, and risk of rework from premature demoulding.""")
with c3:
    st.markdown("""**🎯 Recommend Action**

Find the optimal demoulding time that minimizes total cost while keeping
failure risk below acceptable thresholds. Adapts to region and season.""")

# ── Dataset Summary (if available) ──
if df is not None:
    st.markdown("---")
    st.markdown('<div class="section-label">Dataset Summary</div>', unsafe_allow_html=True)

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Elements", f"{df['element_id'].nunique():,}")
    k2.metric("Regions", df['region'].nunique())
    k3.metric("Curing Methods", df['curing_method'].nunique())
    k4.metric("Avg Strength @24h", f"{df['strength_hr24'].mean():.1f} MPa")
    k5.metric("Avg Strength @72h", f"{df['strength_hr72'].mean():.1f} MPa")

    with st.expander("View sample data"):
        cols = ['element_id', 'element_type', 'cement_type', 'curing_method',
                'ambient_temp_c', 'region', 'strength_hr24', 'strength_hr72',
                'required_demould_strength']
        avail = [c for c in cols if c in df.columns]
        st.dataframe(df[avail].head(10), use_container_width=True, hide_index=True)

# ── Footer ──
st.markdown("---")
st.caption("AI-Cycle Optimizer v1.0 • Team AI-Cycle • CreaTech Hackathon 2026")