import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from src.yard_model import YardModel
from src.climate_profiles import CLIMATE_PROFILES, get_city_names

st.set_page_config(page_title="Yard Dashboard | AI-Cycle", page_icon="📊", layout="wide")

@st.cache_data
def load_data():
    try: return pd.read_csv("data/precast_dataset.csv")
    except: return None

df = load_data()

# ── Header ──
st.markdown("## 📊 Yard Performance Dashboard")
st.caption("Monitor yard utilization, throughput capacity, and operating costs")
st.markdown("---")

# ── Sidebar ──
with st.sidebar:
    st.markdown("### Yard Configuration")
    region = st.selectbox("Region", get_city_names())
    profile = CLIMATE_PROFILES[region]
    st.info(f"**{profile['icon']} {profile['label']}** — {profile['ambient_temp_c']}°C, {profile['ambient_rh_pct']}% RH")

    st.markdown("---")
    mold_count = st.slider("Available Molds", 5, 80, 30)
    daily_demand = st.slider("Daily Demand (elements)", 5, 100, 35)
    baseline_cycle = st.slider("Current Cycle Time (hrs)", 24, 120, 72)
    optimized_cycle = st.slider("Target Cycle Time (hrs)", 12, 96, 42)
    yard_day_cost = st.number_input("Yard Cost (₹/day)", 500, 10000, 2500)

# ── Calculations ──
yard = YardModel(mold_count, daily_demand)
base = yard.summary(baseline_cycle, yard_day_cost)
opt = yard.summary(optimized_cycle, yard_day_cost)

# ── KPIs ──
c1, c2, c3, c4 = st.columns(4)
c1.metric("Current Throughput", f"{base['throughput']:.1f} el/day",
          help="Elements produced per day at current cycle time")
c2.metric("Target Throughput", f"{opt['throughput']:.1f} el/day",
          delta=f"+{((opt['throughput']/max(base['throughput'],0.1))-1)*100:.0f}%",
          help="Throughput at optimized cycle time")
c3.metric("Utilization", f"{base['utilization_pct']:.0f}%",
          help="Yard capacity being used (>80% = congestion risk)")
c4.metric("Weekly Cost", f"₹{base['weekly_cost']:,.0f}",
          delta=f"₹{opt['weekly_cost'] - base['weekly_cost']:,.0f} savings possible",
          delta_color="inverse")

st.markdown("")

# ── Throughput Chart ──
col_chart, col_table = st.columns([3, 2])

with col_chart:
    st.markdown("**Throughput vs Cycle Time**")
    cycle_range = np.arange(12, 121, 4)
    throughputs = [yard.throughput(ct) for ct in cycle_range]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=cycle_range, y=throughputs, mode='lines',
        line=dict(color='#0d6efd', width=2.5), name='Throughput',
        fill='tozeroy', fillcolor='rgba(13,110,253,0.08)',
    ))
    fig.add_hline(y=daily_demand, line_dash="dash", line_color="#dc3545",
                  annotation_text=f"Demand: {daily_demand}/day")
    fig.add_vline(x=baseline_cycle, line_dash="dot", line_color="#6c757d",
                  annotation_text="Current")
    fig.add_vline(x=optimized_cycle, line_dash="dot", line_color="#198754",
                  annotation_text="Target")
    fig.update_layout(
        height=350, margin=dict(t=20, b=40, l=50, r=20),
        xaxis_title="Cycle Time (hours)", yaxis_title="Elements / Day",
        template="plotly_white", showlegend=False,
        font=dict(family="Inter"),
    )
    st.plotly_chart(fig, use_container_width=True)

with col_table:
    st.markdown("**Comparison Summary**")
    comparison = pd.DataFrame({
        "Metric": ["Cycle Time", "Throughput", "Utilization", "Weekly Cost",
                    "Congestion Factor", "Capacity vs Demand"],
        "Current": [
            f"{baseline_cycle}h", f"{base['throughput']:.1f}/day",
            f"{base['utilization_pct']:.0f}%", f"₹{base['weekly_cost']:,.0f}",
            f"{base['congestion_factor']}×", base['status'],
        ],
        "Optimized": [
            f"{optimized_cycle}h", f"{opt['throughput']:.1f}/day",
            f"{opt['utilization_pct']:.0f}%", f"₹{opt['weekly_cost']:,.0f}",
            f"{opt['congestion_factor']}×", opt['status'],
        ],
    })
    st.dataframe(comparison, use_container_width=True, hide_index=True)

# ── Regional data from dataset ──
if df is not None:
    st.markdown("---")
    st.markdown("**Regional Strength Performance (from dataset)**")

    region_key = profile["region"]
    region_summary = df.groupby('region').agg(
        Elements=('element_id', 'nunique'),
        Avg_24h=('strength_hr24', 'mean'),
        Avg_72h=('strength_hr72', 'mean'),
        Avg_Cycle=('baseline_cycle_time', 'mean'),
    ).round(1).reset_index()
    region_summary.columns = ['Region', 'Elements', 'Avg Strength @24h (MPa)',
                               'Avg Strength @72h (MPa)', 'Avg Baseline Cycle (h)']
    st.dataframe(region_summary, use_container_width=True, hide_index=True)