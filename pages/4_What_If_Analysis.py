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

st.set_page_config(page_title="What-If Analysis | AI-Cycle", page_icon="", layout="wide")

# ─────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────
st.markdown("""
<h1 style="background: linear-gradient(90deg, #FFB74D, #FF9800, #F57C00);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; font-size: 2rem; margin-bottom: 0;">
    What-If Analysis
</h1>
<p style="color: #8b949e; font-size: 0.95rem; margin-top: 4px;">
    Explore how changes in temperature, curing, and mold availability impact your optimal strategy
</p>
""", unsafe_allow_html=True)

st.markdown("---")

# ─────────────────────────────────────────────
# Engine Setup
# ─────────────────────────────────────────────
model = load_model()
strength_engine = StrengthEngine(model)
economic_engine = EconomicEngine()
optimizer = OptimizationEngine(strength_engine, economic_engine)

# ─────────────────────────────────────────────
# Sidebar: Base Configuration
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Base Configuration")

    cement_type = st.selectbox("Cement Type", list(CEMENT_FACTORS.keys()))
    wc_ratio = st.slider("W/C Ratio", 0.28, 0.60, 0.40, 0.02)
    admixture = st.selectbox("Admixture", ["None", "Plasticizer", "Accelerator", "Retarder"])
    admixture_dose = st.slider("Dose (%)", 0.0, 3.0, 1.0, 0.1) if admixture != "None" else 0.0

    st.markdown("---")
    required_strength = st.slider("Required Strength (MPa)", 10, 45, 25)
    yard_day_cost = st.number_input("Yard Cost (₹/day)", 500, 10000, 2000)
    rework_cost = st.number_input("Rework Cost (₹)", 5000, 80000, 25000)
    mold_count = st.slider("Mold Count (base)", 5, 80, 25)
    daily_demand = st.slider("Daily Demand", 5, 100, 35)

# ─────────────────────────────────────────────
# What-If Control Panel
# ─────────────────────────────────────────────
st.markdown("""<div style="color: #FFB74D; font-size: 0.8rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 12px;
    padding-bottom: 6px; border-bottom: 1px solid rgba(255,183,77,0.2);">
    Scenario Controls
</div>""", unsafe_allow_html=True)

ctrl1, ctrl2, ctrl3, ctrl4 = st.columns(4)

with ctrl1:
    base_temp = st.slider("Base Temperature (°C)", 10, 48, 30)
with ctrl2:
    what_if_temp = st.slider("What-If Temperature (°C)", 10, 48, 38)
with ctrl3:
    base_curing = st.selectbox("Base Curing", list(CURING_FACTORS.keys()), key="base_curing")
with ctrl4:
    what_if_curing = st.selectbox("What-If Curing", list(CURING_FACTORS.keys()), index=2, key="wif_curing")

ctrl5, ctrl6, ctrl7, ctrl8 = st.columns(4)
with ctrl5:
    base_rh = st.slider("Base RH (%)", 20, 100, 60)
with ctrl6:
    what_if_rh = st.slider("What-If RH (%)", 20, 100, 85)
with ctrl7:
    what_if_molds = st.slider("What-If Mold Count", 5, 80, 40)
with ctrl8:
    steam_cost = st.number_input("Steam Cost (₹/hr)", 0, 2000, 200)

# ─────────────────────────────────────────────
# Regional Presets
# ─────────────────────────────────────────────
st.markdown("")
st.markdown("""<div style="color: #c9d1d9; font-weight: 600; font-size: 0.9rem; margin-bottom: 8px;">
    Quick Regional Presets
</div>""", unsafe_allow_html=True)

preset_cols = st.columns(len(CLIMATE_PROFILES))
selected_preset = None

for i, (city, profile) in enumerate(CLIMATE_PROFILES.items()):
    with preset_cols[i]:
        if st.button(f"{city.split(' (')[0]}", key=f"preset_{i}", use_container_width=True):
            selected_preset = city

if selected_preset:
    p = CLIMATE_PROFILES[selected_preset]
    st.info(f"Loaded **{selected_preset}**: {p['ambient_temp_c']}°C, {p['ambient_rh_pct']}% RH — {p['description']}")

# ─────────────────────────────────────────────
# Run Both Scenarios
# ─────────────────────────────────────────────
base_features = {
    "wc_ratio": wc_ratio, "ambient_temp": base_temp, "ambient_rh_pct": base_rh,
    "curing_method": base_curing, "cement_type": cement_type,
    "admixture": admixture, "admixture_dose_pct": admixture_dose,
}

whatif_features = {
    "wc_ratio": wc_ratio, "ambient_temp": what_if_temp, "ambient_rh_pct": what_if_rh,
    "curing_method": what_if_curing, "cement_type": cement_type,
    "admixture": admixture, "admixture_dose_pct": admixture_dose,
}

base_steam = steam_cost if base_curing == "Steam" else 0
whatif_steam = steam_cost if what_if_curing == "Steam" else 0

base_results, base_best = optimizer.optimize(
    base_features, required_strength, yard_day_cost, rework_cost, base_steam, base_curing,
)
whatif_results, whatif_best = optimizer.optimize(
    whatif_features, required_strength, yard_day_cost, rework_cost, whatif_steam, what_if_curing,
)

base_yard = YardModel(mold_count, daily_demand)
whatif_yard = YardModel(what_if_molds, daily_demand)

base_tp = base_yard.throughput(base_best['time_h'])
whatif_tp = whatif_yard.throughput(whatif_best['time_h'])

# ─────────────────────────────────────────────
# Delta Metrics
# ─────────────────────────────────────────────
st.markdown("---")
st.markdown("""<div style="color: #FFB74D; font-size: 0.8rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 12px;
    padding-bottom: 6px; border-bottom: 1px solid rgba(255,183,77,0.2);">
    Scenario Comparison
</div>""", unsafe_allow_html=True)

d1, d2, d3, d4, d5 = st.columns(5)

delta_cost = whatif_best['total_cost'] - base_best['total_cost']
delta_risk = whatif_best['risk_pct'] - base_best['risk_pct']
delta_time = whatif_best['time_h'] - base_best['time_h']
delta_tp = whatif_tp - base_tp
delta_strength = whatif_best['mean_strength'] - base_best['mean_strength']

d1.metric("Δ Total Cost", f"₹{delta_cost:+,.0f}",
          delta=f"{'Savings' if delta_cost < 0 else 'Increase'}", delta_color="inverse")
d2.metric("Δ Risk", f"{delta_risk:+.2f}%",
          delta=f"{'Lower' if delta_risk < 0 else 'Higher'}", delta_color="inverse")
d3.metric("Δ Cycle Time", f"{delta_time:+.0f}h",
          delta=f"{'Faster' if delta_time < 0 else 'Slower'}", delta_color="inverse")
d4.metric("Δ Throughput", f"{delta_tp:+.1f} el/day",
          delta=f"{'Increase' if delta_tp > 0 else 'Decrease'}")
d5.metric("Δ Strength", f"{delta_strength:+.1f} MPa",
          delta=f"{'Higher' if delta_strength > 0 else 'Lower'}")

# ─────────────────────────────────────────────
# Side-by-Side Comparison
# ─────────────────────────────────────────────
st.markdown("---")

comp1, comp_mid, comp2 = st.columns([5, 1, 5])

with comp1:
    st.markdown(f"""
    <div style="background: rgba(79,195,247,0.08); border: 1px solid rgba(79,195,247,0.25);
        border-radius: 12px; padding: 20px; text-align: center;">
        <div style="color: #4FC3F7; font-size: 0.75rem; font-weight: 600;
            text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 12px;">
            📌 Base Scenario
        </div>
        <div style="color: #e6edf3; font-size: 1.6rem; font-weight: 700; margin-bottom: 8px;">
            Demould @ {base_best['time_h']}h
        </div>
        <div style="display: flex; justify-content: center; gap: 20px; flex-wrap: wrap;">
            <div>
                <div style="color: #8b949e; font-size: 0.7rem;">Cost</div>
                <div style="color: #4FC3F7; font-size: 1.1rem; font-weight: 600;">₹{base_best['total_cost']:,.0f}</div>
            </div>
            <div>
                <div style="color: #8b949e; font-size: 0.7rem;">Risk</div>
                <div style="color: #4FC3F7; font-size: 1.1rem; font-weight: 600;">{base_best['risk_pct']:.1f}%</div>
            </div>
            <div>
                <div style="color: #8b949e; font-size: 0.7rem;">Throughput</div>
                <div style="color: #4FC3F7; font-size: 1.1rem; font-weight: 600;">{base_tp:.1f}/day</div>
            </div>
        </div>
        <div style="color: #8b949e; font-size: 0.75rem; margin-top: 10px;">
            {base_temp}°C • {base_rh}% RH • {base_curing} • {mold_count} molds
        </div>
    </div>
    """, unsafe_allow_html=True)

with comp_mid:
    st.markdown("""
    <div style="display: flex; align-items: center; justify-content: center; height: 200px;">
        <div style="color: #FFB74D; font-size: 2rem;">→</div>
    </div>
    """, unsafe_allow_html=True)

with comp2:
    border_color = "rgba(46,204,113,0.3)" if delta_cost <= 0 else "rgba(231,76,60,0.3)"
    bg_color = "rgba(46,204,113,0.08)" if delta_cost <= 0 else "rgba(231,76,60,0.08)"
    text_color = "#2ecc71" if delta_cost <= 0 else "#e74c3c"

    st.markdown(f"""
    <div style="background: {bg_color}; border: 1px solid {border_color};
        border-radius: 12px; padding: 20px; text-align: center;">
        <div style="color: {text_color}; font-size: 0.75rem; font-weight: 600;
            text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 12px;">
            🔬 What-If Scenario
        </div>
        <div style="color: #e6edf3; font-size: 1.6rem; font-weight: 700; margin-bottom: 8px;">
            Demould @ {whatif_best['time_h']}h
        </div>
        <div style="display: flex; justify-content: center; gap: 20px; flex-wrap: wrap;">
            <div>
                <div style="color: #8b949e; font-size: 0.7rem;">Cost</div>
                <div style="color: {text_color}; font-size: 1.1rem; font-weight: 600;">₹{whatif_best['total_cost']:,.0f}</div>
            </div>
            <div>
                <div style="color: #8b949e; font-size: 0.7rem;">Risk</div>
                <div style="color: {text_color}; font-size: 1.1rem; font-weight: 600;">{whatif_best['risk_pct']:.1f}%</div>
            </div>
            <div>
                <div style="color: #8b949e; font-size: 0.7rem;">Throughput</div>
                <div style="color: {text_color}; font-size: 1.1rem; font-weight: 600;">{whatif_tp:.1f}/day</div>
            </div>
        </div>
        <div style="color: #8b949e; font-size: 0.75rem; margin-top: 10px;">
            {what_if_temp}°C • {what_if_rh}% RH • {what_if_curing} • {what_if_molds} molds
        </div>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Strength Curve Comparison
# ─────────────────────────────────────────────
st.markdown("---")
st.markdown("""<div style="color: #FFB74D; font-size: 0.8rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 10px;
    padding-bottom: 6px; border-bottom: 1px solid rgba(255,183,77,0.2);">
    Strength Curve Comparison
</div>""", unsafe_allow_html=True)

time_hours = np.linspace(1, 168, 100)
base_curve = strength_engine.predict_curve(base_features, time_hours)
whatif_curve = strength_engine.predict_curve(whatif_features, time_hours)

fig_curves = make_subplots(rows=1, cols=2,
                           subplot_titles=("Strength Development", "Cost Comparison"),
                           horizontal_spacing=0.1)

# Strength curves
fig_curves.add_trace(go.Scatter(
    x=time_hours, y=base_curve["means"], mode='lines',
    line=dict(color='#4FC3F7', width=3), name='Base Strength',
), row=1, col=1)
fig_curves.add_trace(go.Scatter(
    x=time_hours, y=base_curve["uppers"], mode='lines',
    line=dict(width=0), showlegend=False,
), row=1, col=1)
fig_curves.add_trace(go.Scatter(
    x=time_hours, y=base_curve["lowers"], mode='lines',
    line=dict(width=0), fill='tonexty', fillcolor='rgba(79,195,247,0.1)',
    showlegend=False,
), row=1, col=1)

fig_curves.add_trace(go.Scatter(
    x=time_hours, y=whatif_curve["means"], mode='lines',
    line=dict(color='#FFB74D', width=3), name='What-If Strength',
), row=1, col=1)
fig_curves.add_trace(go.Scatter(
    x=time_hours, y=whatif_curve["uppers"], mode='lines',
    line=dict(width=0), showlegend=False,
), row=1, col=1)
fig_curves.add_trace(go.Scatter(
    x=time_hours, y=whatif_curve["lowers"], mode='lines',
    line=dict(width=0), fill='tonexty', fillcolor='rgba(255,183,77,0.1)',
    showlegend=False,
), row=1, col=1)

fig_curves.add_hline(y=required_strength, line_dash="dash", line_color="#e74c3c",
                     annotation_text=f"Required: {required_strength} MPa",
                     annotation_font_color="#e74c3c", row=1, col=1)

# Cost comparison
base_costs = [r['total_cost'] for r in base_results]
whatif_costs = [r['total_cost'] for r in whatif_results]
base_times = [r['time_h'] for r in base_results]
whatif_times = [r['time_h'] for r in whatif_results]

fig_curves.add_trace(go.Bar(
    x=[f"{t}h" for t in base_times], y=base_costs,
    name='Base Cost', marker_color='rgba(79,195,247,0.7)',
), row=1, col=2)
fig_curves.add_trace(go.Bar(
    x=[f"{t}h" for t in whatif_times], y=whatif_costs,
    name='What-If Cost', marker_color='rgba(255,183,77,0.7)',
), row=1, col=2)

fig_curves.update_layout(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    height=450,
    margin=dict(t=50, b=40),
    legend=dict(orientation="h", yanchor="bottom", y=1.05),
    barmode='group',
    font=dict(family="Inter"),
)

fig_curves.update_yaxes(title_text="Strength (MPa)", row=1, col=1)
fig_curves.update_yaxes(title_text="Total Cost (₹)", row=1, col=2)
fig_curves.update_xaxes(title_text="Time (hours)", row=1, col=1)
fig_curves.update_xaxes(title_text="Demould Time", row=1, col=2)

for annotation in fig_curves['layout']['annotations']:
    annotation['font'] = dict(size=13, color='#c9d1d9', family='Inter')

st.plotly_chart(fig_curves, use_container_width=True)

# ─────────────────────────────────────────────
# Sensitivity Tornado Chart
# ─────────────────────────────────────────────
st.markdown("---")
st.markdown("""<div style="color: #FFB74D; font-size: 0.8rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 10px;
    padding-bottom: 6px; border-bottom: 1px solid rgba(255,183,77,0.2);">
    Sensitivity Analysis (Tornado Chart)
</div>""", unsafe_allow_html=True)

sensitivity = optimizer.sensitivity_analysis(
    base_features, required_strength, yard_day_cost, rework_cost,
    steam_cost if base_curing == "Steam" else 0, base_curing,
)

df_sens = pd.DataFrame(sensitivity)
df_sens = df_sens.sort_values('delta_cost', key=abs, ascending=True)

colors = ['#2ecc71' if d < 0 else '#e74c3c' for d in df_sens['delta_cost']]

fig_tornado = go.Figure()
fig_tornado.add_trace(go.Bar(
    y=df_sens['parameter'],
    x=df_sens['delta_cost'],
    orientation='h',
    marker_color=colors,
    text=[f"₹{d:+,.0f}" for d in df_sens['delta_cost']],
    textposition='outside',
    textfont=dict(color='#c9d1d9', size=11),
))

fig_tornado.update_layout(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    height=350,
    xaxis_title="Change in Optimal Cost (₹)",
    margin=dict(t=20, b=40, l=150),
)
fig_tornado.add_vline(x=0, line_color="rgba(255,255,255,0.3)")

st.plotly_chart(fig_tornado, use_container_width=True)

# ─────────────────────────────────────────────
# Regional Comparison Table
# ─────────────────────────────────────────────
st.markdown("---")
st.markdown("""<div style="color: #FFB74D; font-size: 0.8rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 10px;
    padding-bottom: 6px; border-bottom: 1px solid rgba(255,183,77,0.2);">
    Cross-Regional Comparison
</div>""", unsafe_allow_html=True)

region_data = []
for city, profile in CLIMATE_PROFILES.items():
    regional_features = {
        "wc_ratio": wc_ratio,
        "ambient_temp": profile["ambient_temp_c"],
        "ambient_rh_pct": profile["ambient_rh_pct"],
        "curing_method": base_curing,
        "cement_type": cement_type,
        "admixture": admixture,
        "admixture_dose_pct": admixture_dose,
    }
    _, regional_best = optimizer.optimize(
        regional_features, required_strength, yard_day_cost, rework_cost,
        steam_cost if base_curing == "Steam" else 0, base_curing,
    )
    region_data.append({
        "Region": f"{profile['icon']} {city}",
        "Climate": profile['label'],
        "Temp (°C)": profile['ambient_temp_c'],
        "RH (%)": profile['ambient_rh_pct'],
        "Optimal Time (h)": regional_best['time_h'],
        "Total Cost (₹)": f"₹{regional_best['total_cost']:,.0f}",
        "Risk (%)": f"{regional_best['risk_pct']:.2f}%",
        "Strength (MPa)": f"{regional_best['mean_strength']:.1f}",
    })

st.dataframe(pd.DataFrame(region_data), use_container_width=True, hide_index=True)
