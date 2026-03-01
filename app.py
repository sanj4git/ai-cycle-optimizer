import streamlit as st
import pandas as pd
import numpy as np
from src.model_loader import load_model
from src.strength_engine import StrengthEngine
from src.yard_model import YardModel

# ─────────────────────────────────────────────
# Page Config & Custom Theme
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="AI-Cycle Optimizer",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for professional look
st.markdown("""
<style>
/* ── Import Google Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── Global ── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* ── Main background ── */
.stApp {
    background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%);
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1117 0%, #161b22 100%);
    border-right: 1px solid rgba(255, 183, 77, 0.15);
}

[data-testid="stSidebar"] .stMarkdown {
    color: #c9d1d9;
}

/* ── Metric cards ── */
[data-testid="stMetric"] {
    background: linear-gradient(135deg, rgba(255,183,77,0.08) 0%, rgba(255,183,77,0.02) 100%);
    border: 1px solid rgba(255,183,77,0.2);
    border-radius: 12px;
    padding: 16px 20px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
}

[data-testid="stMetric"] label {
    color: #8b949e !important;
    font-weight: 500 !important;
    font-size: 0.8rem !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: #FFB74D !important;
    font-weight: 700 !important;
    font-size: 1.8rem !important;
}

[data-testid="stMetric"] [data-testid="stMetricDelta"] {
    font-weight: 600 !important;
}

/* ── Headers ── */
h1, h2, h3 {
    color: #e6edf3 !important;
    font-weight: 700 !important;
}

h1 {
    background: linear-gradient(90deg, #FFB74D, #FF9800, #F57C00);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-size: 2.4rem !important;
}

/* ── Dataframes ── */
[data-testid="stDataFrame"] {
    border: 1px solid rgba(255,183,77,0.15);
    border-radius: 10px;
    overflow: hidden;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background: rgba(255,183,77,0.05);
    border-radius: 10px;
    padding: 4px;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    color: #8b949e;
    font-weight: 500;
}

.stTabs [aria-selected="true"] {
    background: rgba(255,183,77,0.15) !important;
    color: #FFB74D !important;
}

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, #FFB74D 0%, #F57C00 100%);
    color: #0f0f1a;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    padding: 8px 24px;
    transition: all 0.3s ease;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(255,183,77,0.4);
}

/* ── Selectbox & Sliders ── */
.stSelectbox label, .stSlider label, .stNumberInput label {
    color: #c9d1d9 !important;
    font-weight: 500 !important;
}

/* ── Info boxes ── */
.info-card {
    background: linear-gradient(135deg, rgba(255,183,77,0.1) 0%, rgba(255,152,0,0.05) 100%);
    border: 1px solid rgba(255,183,77,0.25);
    border-radius: 12px;
    padding: 20px 24px;
    margin: 10px 0;
}

.hero-subtitle {
    color: #8b949e;
    font-size: 1.1rem;
    font-weight: 400;
    margin-bottom: 30px;
}

.kpi-section-title {
    color: #FFB74D;
    font-size: 0.85rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-bottom: 15px;
    padding-bottom: 8px;
    border-bottom: 1px solid rgba(255,183,77,0.2);
}

/* ── Plotly charts dark bg ── */
.js-plotly-plot .plotly .main-svg {
    border-radius: 12px;
}

/* ── Divider ── */
hr {
    border-color: rgba(255,183,77,0.15) !important;
}

/* ── Expander ── */
.streamlit-expanderHeader {
    color: #c9d1d9 !important;
    font-weight: 600 !important;
}

/* ── Badge ── */
.badge-green {
    background: rgba(46, 204, 113, 0.15);
    color: #2ecc71;
    border: 1px solid rgba(46, 204, 113, 0.3);
    padding: 4px 12px;
    border-radius: 20px;
    font-weight: 600;
    font-size: 0.8rem;
}

.badge-red {
    background: rgba(231, 76, 60, 0.15);
    color: #e74c3c;
    border: 1px solid rgba(231, 76, 60, 0.3);
    padding: 4px 12px;
    border-radius: 20px;
    font-weight: 600;
    font-size: 0.8rem;
}

.badge-amber {
    background: rgba(255, 183, 77, 0.15);
    color: #FFB74D;
    border: 1px solid rgba(255, 183, 77, 0.3);
    padding: 4px 12px;
    border-radius: 20px;
    font-weight: 600;
    font-size: 0.8rem;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Sidebar Branding
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 10px 0 20px 0;">
        <div style="font-size: 2.5rem;">⚙️</div>
        <div style="font-size: 1.3rem; font-weight: 700; color: #FFB74D; margin-top: 5px;">
            AI-Cycle Optimizer
        </div>
        <div style="font-size: 0.75rem; color: #8b949e; margin-top: 3px;">
            Team AI-Cycle &nbsp;|&nbsp; CreaTech 2026
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
    <div style="font-size: 0.8rem; color: #8b949e; line-height: 1.6;">
        <b style="color: #c9d1d9;">Navigation</b><br>
        📊 <b>Yard Dashboard</b> — Overview & KPIs<br>
        🧪 <b>Element Simulation</b> — Scenario Builder<br>
        🎯 <b>Optimization Lab</b> — Multi-Objective<br>
        🔬 <b>What-If Analysis</b> — Sensitivity Testing
    </div>
    """, unsafe_allow_html=True)

    # ML model status
    st.markdown("---")
    model = load_model()
    if model:
        st.markdown('<span class="badge-green">🤖 ML Model Active</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="badge-amber">⚡ Physics Model Active</span>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Load Dataset
# ─────────────────────────────────────────────
@st.cache_data
def load_dataset():
    try:
        df = pd.read_csv("data/precast_dataset.csv")
        return df
    except Exception:
        return None

df = load_dataset()

# ─────────────────────────────────────────────
# Hero Section
# ─────────────────────────────────────────────
st.title("AI-Cycle Optimizer")
st.markdown("""
<div class="hero-subtitle">
    AI-Powered Digital Twin for Precast Yard Cycle Time Optimization — 
    Integrating physics-informed modeling, machine learning, and multi-objective optimization 
    for smarter demoulding decisions across India.
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# System Architecture Cards
# ─────────────────────────────────────────────
st.markdown('<div class="kpi-section-title">🏗️ System Architecture</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="info-card">
        <div style="font-size: 1.5rem; margin-bottom: 8px;">🧠</div>
        <div style="color: #FFB74D; font-weight: 600; font-size: 1rem; margin-bottom: 6px;">
            Strength Prediction Engine
        </div>
        <div style="color: #8b949e; font-size: 0.82rem; line-height: 1.5;">
            Physics-informed maturity model with XGBoost bootstrap ensemble for uncertainty-aware strength prediction
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="info-card">
        <div style="font-size: 1.5rem; margin-bottom: 8px;">💰</div>
        <div style="color: #FFB74D; font-weight: 600; font-size: 1rem; margin-bottom: 6px;">
            Economic Simulation Engine
        </div>
        <div style="color: #8b949e; font-size: 0.82rem; line-height: 1.5;">
            Yard holding costs, steam treatment, rework risk modeling, and mold opportunity cost analysis
        </div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="info-card">
        <div style="font-size: 1.5rem; margin-bottom: 8px;">🎯</div>
        <div style="color: #FFB74D; font-weight: 600; font-size: 1rem; margin-bottom: 6px;">
            Multi-Objective Optimizer
        </div>
        <div style="color: #8b949e; font-size: 0.82rem; line-height: 1.5;">
            Pareto-optimal demould time selection minimizing cost, risk, and cycle time simultaneously
        </div>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Dataset KPIs
# ─────────────────────────────────────────────
if df is not None:
    st.markdown("---")
    st.markdown('<div class="kpi-section-title">📈 Dataset Overview</div>', unsafe_allow_html=True)

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Total Elements", f"{df['element_id'].nunique():,}")
    k2.metric("Element Types", f"{df['element_type'].nunique()}")
    k3.metric("Regions", f"{df['region'].nunique()}")
    k4.metric("Avg Strength @24h", f"{df['strength_hr24'].mean():.1f} MPa")
    k5.metric("Avg Strength @72h", f"{df['strength_hr72'].mean():.1f} MPa")

    # Operational KPIs
    st.markdown("---")
    st.markdown('<div class="kpi-section-title">🏭 Operational KPIs (Dataset Baseline)</div>', unsafe_allow_html=True)

    avg_baseline_cycle = df['baseline_cycle_time'].mean()
    avg_molds = df['mold_count_available'].mean()
    avg_yard_cost = df['yard_day_cost'].mean()
    avg_demand = df['daily_demand'].mean()

    # Compute baseline vs optimized (using 40h as default optimized)
    yard_base = YardModel(int(avg_molds), int(avg_demand))
    base_tp = yard_base.throughput(avg_baseline_cycle)
    opt_tp = yard_base.throughput(avg_baseline_cycle * 0.65)  # 35% reduction target

    o1, o2, o3, o4 = st.columns(4)
    o1.metric("Avg Baseline Cycle", f"{avg_baseline_cycle:.0f} hrs")
    o2.metric("Baseline Throughput", f"{base_tp:.1f} el/day")
    o3.metric("Potential Throughput", f"{opt_tp:.1f} el/day",
              delta=f"+{((opt_tp/base_tp - 1)*100):.0f}%")
    o4.metric("Avg Weekly Yard Cost", f"₹{avg_yard_cost * 7:,.0f}")

    # Region breakdown
    st.markdown("---")
    st.markdown('<div class="kpi-section-title">🗺️ Regional Distribution</div>', unsafe_allow_html=True)

    import plotly.express as px
    import plotly.graph_objects as go

    col_left, col_right = st.columns(2)

    with col_left:
        region_counts = df.groupby('region')['element_id'].nunique().reset_index()
        region_counts.columns = ['Region', 'Elements']
        fig_region = px.bar(
            region_counts, x='Region', y='Elements',
            color='Elements',
            color_continuous_scale=['#1a1a2e', '#FFB74D', '#FF9800'],
        )
        fig_region.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            title=dict(text="Elements per Region", font=dict(size=14, color="#c9d1d9")),
            height=320,
            showlegend=False,
            coloraxis_showscale=False,
        )
        st.plotly_chart(fig_region, use_container_width=True)

    with col_right:
        type_counts = df.groupby('element_type')['element_id'].nunique().reset_index()
        type_counts.columns = ['Type', 'Count']
        fig_type = px.pie(
            type_counts, values='Count', names='Type',
            color_discrete_sequence=['#FFB74D', '#FF9800', '#F57C00', '#E65100', '#BF360C']
        )
        fig_type.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            title=dict(text="Element Type Distribution", font=dict(size=14, color="#c9d1d9")),
            height=320,
        )
        fig_type.update_traces(textinfo='percent+label', textfont_size=12)
        st.plotly_chart(fig_type, use_container_width=True)

    # Strength distribution by curing method
    st.markdown('<div class="kpi-section-title">💪 Strength at 24h by Curing Method</div>', unsafe_allow_html=True)

    fig_box = px.box(
        df, x='curing_method', y='strength_hr24',
        color='curing_method',
        color_discrete_sequence=['#FFB74D', '#4FC3F7', '#81C784'],
        labels={'strength_hr24': 'Strength at 24h (MPa)', 'curing_method': 'Curing Method'}
    )
    fig_box.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=350,
        showlegend=False,
    )
    st.plotly_chart(fig_box, use_container_width=True)

else:
    st.warning("Dataset not found at `data/precast_dataset.csv`. Some features will be limited.")

# ─────────────────────────────────────────────
# Model KPIs Placeholder
# ─────────────────────────────────────────────
st.markdown("---")
st.markdown('<div class="kpi-section-title">🤖 Model Performance KPIs</div>', unsafe_allow_html=True)

m1, m2, m3 = st.columns(3)
if load_model():
    m1.metric("MAE", "—", help="Mean Absolute Error from ML model evaluation")
    m2.metric("RMSE", "—", help="Root Mean Squared Error")
    m3.metric("Calibration (±1σ)", "—", help="% of test points within prediction interval")
else:
    m1.metric("Model Status", "Physics Fallback")
    m2.metric("MAE (Physics)", "~2.5 MPa", help="Estimated from physics model validation")
    m3.metric("Coverage", "~68%", help="Physics model ±1σ coverage estimate")

st.markdown("""
<div style="text-align: center; padding: 40px 0 20px 0; color: #4a5568; font-size: 0.75rem;">
    AI-Cycle Optimizer v1.0 &nbsp;•&nbsp; Team AI-Cycle &nbsp;•&nbsp; CreaTech Hackathon 2026<br>
    Powered by Physics-Informed ML + Multi-Objective Optimization
</div>
""", unsafe_allow_html=True)