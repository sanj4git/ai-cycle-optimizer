import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from src.strength_engine import StrengthEngine, CEMENT_FACTORS, CURING_FACTORS
from src.economic_engine import EconomicEngine
from src.optimization_engine import OptimizationEngine
from src.yard_model import YardModel
from src.model_loader import load_model
from src.climate_profiles import CLIMATE_PROFILES, get_city_names

st.set_page_config(page_title="What-If Analysis | AI-Cycle", page_icon="🔬", layout="wide")

# ── Header ──
st.markdown("## 🔬 What-If Analysis")
st.caption("Compare scenarios and test sensitivity to temperature, curing method, and mold availability")
st.markdown("---")

# ── Engine Setup ──
model = load_model()
strength_engine = StrengthEngine(model)
economic_engine = EconomicEngine()
optimizer = OptimizationEngine(strength_engine, economic_engine)

# ── Sidebar: Common Settings ──
with st.sidebar:
    st.markdown("### Fixed Parameters")
    cement_type = st.selectbox("Cement Type", list(CEMENT_FACTORS.keys()))
    wc_ratio = st.slider("W/C Ratio", 0.28, 0.60, 0.40, 0.02)
    admixture = st.selectbox("Admixture", ["None", "Plasticizer", "Accelerator", "Retarder"])
    admixture_dose = st.slider("Dose (%)", 0.0, 3.0, 1.0, 0.1) if admixture != "None" else 0.0

    st.markdown("---")
    required_strength = st.slider("Required Strength (MPa)", 10, 45, 25)
    yard_day_cost = st.number_input("Yard Cost (₹/day)", 500, 10000, 2000)
    rework_cost = st.number_input("Rework Cost (₹)", 5000, 80000, 25000)
    steam_cost = st.number_input("Steam Cost (₹/hr)", 0, 2000, 200)
    mold_count = st.slider("Mold Count", 5, 80, 25)
    daily_demand = st.slider("Daily Demand", 5, 100, 35)

# ── Two-Column Scenario Controls ──
st.markdown("#### Configure Scenarios")
col_base, col_whatif = st.columns(2)

with col_base:
    st.markdown("**📌 Base Scenario**")
    base_temp = st.slider("Temperature (°C)", 10, 48, 30, key="b_temp")
    base_rh = st.slider("Humidity (%)", 20, 100, 60, key="b_rh")
    base_curing = st.selectbox("Curing", list(CURING_FACTORS.keys()), key="b_cure")
    base_molds = mold_count

with col_whatif:
    st.markdown("**🔬 What-If Scenario**")
    wi_temp = st.slider("Temperature (°C)", 10, 48, 38, key="w_temp")
    wi_rh = st.slider("Humidity (%)", 20, 100, 85, key="w_rh")
    wi_curing = st.selectbox("Curing", list(CURING_FACTORS.keys()), index=2, key="w_cure")
    wi_molds = st.slider("Mold Count", 5, 80, 40, key="w_molds")

# ── Quick Regional Presets ──
st.markdown("---")
st.markdown("**Quick Regional Presets** — click to load a What-If scenario")
preset_cols = st.columns(len(CLIMATE_PROFILES))
for i, (city, prof) in enumerate(CLIMATE_PROFILES.items()):
    with preset_cols[i]:
        if st.button(f"{prof['icon']} {city.split(' (')[0]}", key=f"p{i}", use_container_width=True):
            st.info(f"Loaded: {city} — {prof['ambient_temp_c']}°C, {prof['ambient_rh_pct']}% RH")

# ── Run Both Scenarios ──
def make_features(temp, rh, curing):
    return {
        "wc_ratio": wc_ratio, "ambient_temp": temp, "ambient_rh_pct": rh,
        "curing_method": curing, "cement_type": cement_type,
        "admixture": admixture, "admixture_dose_pct": admixture_dose,
    }

base_feat = make_features(base_temp, base_rh, base_curing)
wi_feat = make_features(wi_temp, wi_rh, wi_curing)

b_steam = steam_cost if base_curing == "Steam" else 0
w_steam = steam_cost if wi_curing == "Steam" else 0

_, b_best = optimizer.optimize(base_feat, required_strength, yard_day_cost, rework_cost, b_steam, base_curing)
wi_results, w_best = optimizer.optimize(wi_feat, required_strength, yard_day_cost, rework_cost, w_steam, wi_curing)

b_tp = YardModel(base_molds, daily_demand).throughput(b_best['time_h'])
w_tp = YardModel(wi_molds, daily_demand).throughput(w_best['time_h'])

# ── Comparison Metrics ──
st.markdown("---")
st.markdown("#### Impact Comparison")

d1, d2, d3, d4, d5 = st.columns(5)
d1.metric("Cycle Time", f"{w_best['time_h']}h",
          delta=f"{w_best['time_h'] - b_best['time_h']:+.0f}h vs base",
          delta_color="inverse")
d2.metric("Total Cost", f"₹{w_best['total_cost']:,.0f}",
          delta=f"₹{w_best['total_cost'] - b_best['total_cost']:+,.0f}",
          delta_color="inverse")
d3.metric("Risk", f"{w_best['risk_pct']:.2f}%",
          delta=f"{w_best['risk_pct'] - b_best['risk_pct']:+.2f}%",
          delta_color="inverse")
d4.metric("Throughput", f"{w_tp:.1f}/day",
          delta=f"{w_tp - b_tp:+.1f} vs base")
d5.metric("Strength", f"{w_best['mean_strength']:.1f} MPa",
          delta=f"{w_best['mean_strength'] - b_best['mean_strength']:+.1f}")

# ── Strength Curve Overlay ──
st.markdown("---")
ch1, ch2 = st.columns(2)

with ch1:
    st.markdown("**Strength Development Comparison**")
    time_hours = np.linspace(1, 168, 80)
    b_curve = strength_engine.predict_curve(base_feat, time_hours)
    w_curve = strength_engine.predict_curve(wi_feat, time_hours)

    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=time_hours, y=b_curve["means"], mode='lines',
                              line=dict(color='#6c757d', width=2), name='Base'))
    fig1.add_trace(go.Scatter(x=time_hours, y=w_curve["means"], mode='lines',
                              line=dict(color='#0d6efd', width=2.5), name='What-If'))
    fig1.add_hline(y=required_strength, line_dash="dash", line_color="#dc3545",
                   annotation_text=f"Required: {required_strength}")
    fig1.update_layout(
        template="plotly_white", height=350, font=dict(family="Inter"),
        xaxis_title="Time (hours)", yaxis_title="Strength (MPa)",
        margin=dict(t=20, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig1, use_container_width=True)

with ch2:
    st.markdown("**Sensitivity Analysis**")
    sensitivity = optimizer.sensitivity_analysis(
        base_feat, required_strength, yard_day_cost, rework_cost, b_steam, base_curing,
    )
    df_s = pd.DataFrame(sensitivity).sort_values('delta_cost', key=abs, ascending=True)

    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        y=df_s['parameter'], x=df_s['delta_cost'], orientation='h',
        marker_color=['#198754' if d < 0 else '#dc3545' for d in df_s['delta_cost']],
        text=[f"₹{d:+,.0f}" for d in df_s['delta_cost']],
        textposition='outside', textfont=dict(size=11),
    ))
    fig2.add_vline(x=0, line_color="#dee2e6")
    fig2.update_layout(
        template="plotly_white", height=350, font=dict(family="Inter"),
        xaxis_title="Impact on Optimal Cost (₹)",
        margin=dict(t=20, b=40, l=140), showlegend=False,
    )
    st.plotly_chart(fig2, use_container_width=True)

# ── Cross-Regional Table ──
st.markdown("---")
st.markdown("**Cross-Regional Comparison**")
st.caption("How the optimal strategy changes across India's climatic regions")

region_data = []
for city, prof in CLIMATE_PROFILES.items():
    rf = make_features(prof["ambient_temp_c"], prof["ambient_rh_pct"], base_curing)
    _, rb = optimizer.optimize(rf, required_strength, yard_day_cost, rework_cost, b_steam, base_curing)
    region_data.append({
        "Region": f"{prof['icon']} {city}",
        "Climate": prof['label'],
        "Temp (°C)": prof['ambient_temp_c'],
        "RH (%)": prof['ambient_rh_pct'],
        "Optimal Time (h)": rb['time_h'],
        "Cost (₹)": f"₹{rb['total_cost']:,.0f}",
        "Risk (%)": f"{rb['risk_pct']:.2f}",
    })
st.dataframe(pd.DataFrame(region_data), use_container_width=True, hide_index=True)
