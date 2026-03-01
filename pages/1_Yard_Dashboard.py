import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from src.yard_model import YardModel
from src.climate_profiles import CLIMATE_PROFILES, get_city_names

st.set_page_config(page_title="Yard Dashboard | AI-Cycle", page_icon="📊", layout="wide")

# ─────────────────────────────────────────────
# Load Dataset
# ─────────────────────────────────────────────
@st.cache_data
def load_data():
    try:
        return pd.read_csv("data/precast_dataset.csv")
    except Exception:
        return None

df = load_data()

# ─────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────
st.markdown("""
<h1 style="background: linear-gradient(90deg, #FFB74D, #FF9800, #F57C00);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; font-size: 2rem; margin-bottom: 0;">
    📊 Yard Performance Dashboard
</h1>
<p style="color: #8b949e; font-size: 0.95rem; margin-top: 4px;">
    Real-time yard utilization, throughput, and cost monitoring
</p>
""", unsafe_allow_html=True)

st.markdown("---")

# ─────────────────────────────────────────────
# Sidebar Controls
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🏗️ Yard Configuration")

    region = st.selectbox("Region / Climate", get_city_names())
    profile = CLIMATE_PROFILES[region]
    
    st.markdown(f"""
    <div style="background: rgba(255,183,77,0.08); border: 1px solid rgba(255,183,77,0.2);
        border-radius: 8px; padding: 10px 14px; margin: 8px 0;">
        <div style="color: #FFB74D; font-weight: 600; font-size: 0.85rem;">
            {profile['icon']} {profile['label']}
        </div>
        <div style="color: #8b949e; font-size: 0.75rem; margin-top: 4px;">
            {profile['description']}
        </div>
    </div>
    """, unsafe_allow_html=True)

    monsoon = st.toggle("🌧️ Monsoon Season", value=False)

    st.markdown("---")
    mold_count = st.slider("Available Molds", 5, 80, 30)
    daily_demand = st.slider("Daily Demand (elements)", 5, 100, 35)
    baseline_cycle = st.slider("Baseline Cycle Time (hrs)", 24, 120, 72)
    optimized_cycle = st.slider("Optimized Cycle Time (hrs)", 12, 96, 42)
    yard_day_cost = st.number_input("Yard Holding Cost (₹/day)", 500, 10000, 2500)

# ─────────────────────────────────────────────
# Yard Model Calculations
# ─────────────────────────────────────────────
yard = YardModel(mold_count, daily_demand)

base_summary = yard.summary(baseline_cycle, yard_day_cost)
opt_summary = yard.summary(optimized_cycle, yard_day_cost)

# ─────────────────────────────────────────────
# KPI Row 1: Core Metrics
# ─────────────────────────────────────────────
st.markdown("""<div style="color: #FFB74D; font-size: 0.8rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 10px;
    padding-bottom: 6px; border-bottom: 1px solid rgba(255,183,77,0.2);">
    🎯 Core Performance Metrics
</div>""", unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "Current Utilization",
    f"{base_summary['utilization_pct']}%",
    delta=f"{opt_summary['utilization_pct'] - base_summary['utilization_pct']:.1f}% (optimized)",
)
c2.metric(
    "Avg Cycle Time",
    f"{baseline_cycle} hrs",
    delta=f"-{baseline_cycle - optimized_cycle} hrs (target)",
)
c3.metric(
    "Weekly Yard Cost",
    f"₹{base_summary['weekly_cost']:,.0f}",
    delta=f"₹{opt_summary['weekly_cost'] - base_summary['weekly_cost']:,.0f} (potential)",
)
c4.metric(
    "Capacity Status",
    base_summary['status'],
    delta=f"{base_summary['capacity_gap']:+.0f} el/day gap",
)

# ─────────────────────────────────────────────
# KPI Row 2: Throughput
# ─────────────────────────────────────────────
st.markdown("")
t1, t2, t3, t4 = st.columns(4)

t1.metric("Baseline Throughput", f"{base_summary['throughput']:.1f} el/day")
t2.metric("Optimized Throughput", f"{opt_summary['throughput']:.1f} el/day",
          delta=f"+{((opt_summary['throughput']/base_summary['throughput'])-1)*100:.0f}%")
t3.metric("Congestion Factor", f"{base_summary['congestion_factor']}×")
t4.metric("Daily Demand", f"{daily_demand} el/day")

# ─────────────────────────────────────────────
# Charts
# ─────────────────────────────────────────────
st.markdown("---")

chart1, chart2 = st.columns(2)

with chart1:
    st.markdown("""<div style="color: #c9d1d9; font-weight: 600; font-size: 0.95rem; margin-bottom: 10px;">
        Throughput: Baseline vs Optimized
    </div>""", unsafe_allow_html=True)

    fig_tp = go.Figure()
    fig_tp.add_trace(go.Bar(
        x=['Baseline', 'Optimized'],
        y=[base_summary['throughput'], opt_summary['throughput']],
        marker=dict(
            color=['rgba(255,183,77,0.4)', 'rgba(255,183,77,0.9)'],
            line=dict(color=['#FFB74D', '#F57C00'], width=2)
        ),
        text=[f"{base_summary['throughput']:.1f}", f"{opt_summary['throughput']:.1f}"],
        textposition='outside',
        textfont=dict(color='#c9d1d9', size=14, family='Inter'),
    ))
    fig_tp.add_hline(y=daily_demand, line_dash="dash", line_color="#e74c3c",
                     annotation_text=f"Demand: {daily_demand}", annotation_font_color="#e74c3c")
    fig_tp.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=350, showlegend=False,
        yaxis_title="Elements / Day",
        margin=dict(t=30, b=30),
    )
    st.plotly_chart(fig_tp, use_container_width=True)

with chart2:
    st.markdown("""<div style="color: #c9d1d9; font-weight: 600; font-size: 0.95rem; margin-bottom: 10px;">
        Utilization & Congestion vs Cycle Time
    </div>""", unsafe_allow_html=True)

    cycle_range = np.arange(12, 121, 4)
    utils = [yard.utilization(ct) * 100 for ct in cycle_range]
    congs = [yard.congestion_factor(ct) for ct in cycle_range]

    fig_util = go.Figure()
    fig_util.add_trace(go.Scatter(
        x=cycle_range, y=utils, mode='lines', name='Utilization %',
        line=dict(color='#FFB74D', width=3),
        fill='tozeroy', fillcolor='rgba(255,183,77,0.1)',
    ))
    fig_util.add_trace(go.Scatter(
        x=cycle_range, y=[c * 50 for c in congs], mode='lines', name='Congestion (scaled)',
        line=dict(color='#e74c3c', width=2, dash='dot'),
        yaxis='y2',
    ))
    fig_util.add_vline(x=baseline_cycle, line_dash="dash", line_color="#4FC3F7",
                       annotation_text="Baseline", annotation_font_color="#4FC3F7")
    fig_util.add_vline(x=optimized_cycle, line_dash="dash", line_color="#81C784",
                       annotation_text="Optimized", annotation_font_color="#81C784")

    fig_util.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=350,
        xaxis_title="Cycle Time (hours)",
        yaxis=dict(title="Utilization %", range=[0, 110]),
        yaxis2=dict(title="Congestion Factor", overlaying='y', side='right'),
        margin=dict(t=30, b=30),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig_util, use_container_width=True)

# ─────────────────────────────────────────────
# Dataset Element Table
# ─────────────────────────────────────────────
if df is not None:
    st.markdown("---")
    st.markdown("""<div style="color: #FFB74D; font-size: 0.8rem; font-weight: 600;
        text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 10px;
        padding-bottom: 6px; border-bottom: 1px solid rgba(255,183,77,0.2);">
        📋 Recent Elements from Dataset
    </div>""", unsafe_allow_html=True)

    # Filter dataset by selected region
    region_key = profile["region"]
    df_region = df[df['region'] == region_key]

    if len(df_region) > 0:
        display_cols = ['element_id', 'element_type', 'cement_type', 'curing_method',
                        'ambient_temp_c', 'strength_hr24', 'strength_hr72',
                        'required_demould_strength', 'baseline_cycle_time']
        available_cols = [c for c in display_cols if c in df_region.columns]
        st.dataframe(
            df_region[available_cols].head(15),
            use_container_width=True,
            hide_index=True,
        )
        st.caption(f"Showing elements from **{region}** ({profile['region']} region) — {len(df_region)} total records")
    else:
        st.info(f"No elements found for region: {region_key}")

    # Regional comparison
    st.markdown("---")
    st.markdown("""<div style="color: #c9d1d9; font-weight: 600; font-size: 0.95rem; margin-bottom: 10px;">
        Average Strength by Region & Curing Method
    </div>""", unsafe_allow_html=True)

    region_curing = df.groupby(['region', 'curing_method'])['strength_hr24'].mean().reset_index()
    fig_rc = px.bar(
        region_curing, x='region', y='strength_hr24', color='curing_method',
        barmode='group',
        color_discrete_sequence=['#FFB74D', '#4FC3F7', '#81C784'],
        labels={'strength_hr24': 'Avg Strength @24h (MPa)', 'region': 'Region', 'curing_method': 'Curing'},
    )
    fig_rc.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=350,
        margin=dict(t=20, b=30),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig_rc, use_container_width=True)