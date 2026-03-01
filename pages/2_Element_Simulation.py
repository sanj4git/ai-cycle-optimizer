import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from src.strength_engine import StrengthEngine, CEMENT_FACTORS, CURING_FACTORS
from src.economic_engine import EconomicEngine
from src.model_loader import load_model
from src.climate_profiles import CLIMATE_PROFILES, get_city_names

st.set_page_config(page_title="Scenario Builder | AI-Cycle", page_icon="🧪", layout="wide")

# ── Header ──
st.markdown("## 🧪 Scenario Builder")
st.caption("Simulate strength development, failure risk, and cost for a specific element configuration")
st.markdown("---")

# ── Sidebar ──
with st.sidebar:
    st.markdown("### Element Configuration")

    cement_type = st.selectbox("Cement Type", list(CEMENT_FACTORS.keys()))
    wc_ratio = st.slider("Water-Cement Ratio", 0.28, 0.60, 0.40, 0.02)
    curing_method = st.selectbox("Curing Method", list(CURING_FACTORS.keys()))
    admixture = st.selectbox("Admixture", ["None", "Plasticizer", "Accelerator", "Retarder"])
    admixture_dose = st.slider("Admixture Dose (%)", 0.0, 3.0, 1.0, 0.1) if admixture != "None" else 0.0

    st.markdown("---")
    st.markdown("**Climate**")
    region = st.selectbox("Region", get_city_names())
    monsoon = st.toggle("Monsoon Season", value=False)
    profile = CLIMATE_PROFILES[region]
    ambient_temp = profile["monsoon_temp_c"] if monsoon else profile["ambient_temp_c"]
    ambient_rh = profile["monsoon_rh_pct"] if monsoon else profile["ambient_rh_pct"]
    st.info(f"{profile['icon']} {ambient_temp}°C • {ambient_rh}% RH")

    st.markdown("---")
    st.markdown("**Targets & Costs**")
    required_strength = st.slider("Required Strength (MPa)", 10, 45, 25)
    yard_day_cost = st.number_input("Yard Cost (₹/day)", 500, 10000, 2000)
    rework_cost = st.number_input("Rework Cost (₹)", 5000, 80000, 25000)
    steam_cost = st.number_input("Steam Cost (₹/hr)", 0, 2000, 200) if curing_method == "Steam" else 0

# ── Compute ──
model = load_model()
engine = StrengthEngine(model)
econ = EconomicEngine()

features = {
    "wc_ratio": wc_ratio, "ambient_temp": ambient_temp, "ambient_rh_pct": ambient_rh,
    "curing_method": curing_method, "cement_type": cement_type,
    "admixture": admixture, "admixture_dose_pct": admixture_dose,
}

time_hours = np.linspace(1, 168, 100)
curve = engine.predict_curve(features, time_hours)

risks, costs = [], []
for t in time_hours:
    m, s = engine.predict(t, features)
    cd = econ.compute(t, m, s, required_strength, yard_day_cost, rework_cost, steam_cost, curing_method)
    risks.append(cd["pfail"] * 100)
    costs.append(cd["total_cost"])
risks = np.array(risks)
costs = np.array(costs)

# Find key points
ready_idx = np.where(curve["means"] >= required_strength)[0]
ready_time = time_hours[ready_idx[0]] if len(ready_idx) > 0 else None
min_cost_idx = np.argmin(costs)
min_cost_time = time_hours[min_cost_idx]

# ── Key Findings ──
f1, f2, f3 = st.columns(3)
f1.metric("Earliest Safe Demould",
          f"{ready_time:.0f}h" if ready_time else ">168h",
          help="When mean strength first exceeds required strength")
f2.metric("Risk at 24h", f"{risks[np.argmin(np.abs(time_hours - 24))]:.1f}%",
          help="Probability of not meeting required strength if demoulded at 24h")
f3.metric("Cost-Optimal Time", f"{min_cost_time:.0f}h — ₹{costs[min_cost_idx]:,.0f}",
          help="Demould time that minimizes total expected cost")

st.markdown("")

# ── Main Chart: 3-panel ──
fig = make_subplots(
    rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.06,
    subplot_titles=("Strength Development (MPa)", "Failure Risk (%)", "Total Expected Cost (₹)"),
    row_heights=[0.40, 0.25, 0.35],
)

# Strength
fig.add_trace(go.Scatter(x=time_hours, y=curve["uppers"], mode='lines', line=dict(width=0),
                         showlegend=False), row=1, col=1)
fig.add_trace(go.Scatter(x=time_hours, y=curve["lowers"], mode='lines', line=dict(width=0),
                         fill='tonexty', fillcolor='rgba(13,110,253,0.1)',
                         name='±1σ band'), row=1, col=1)
fig.add_trace(go.Scatter(x=time_hours, y=curve["means"], mode='lines',
                         line=dict(color='#0d6efd', width=2.5), name='Mean Strength'), row=1, col=1)
fig.add_hline(y=required_strength, line_dash="dash", line_color="#dc3545",
              annotation_text=f"Required: {required_strength} MPa",
              annotation_font_color="#dc3545", row=1, col=1)

# Risk
fig.add_trace(go.Scatter(x=time_hours, y=risks, mode='lines',
                         line=dict(color='#dc3545', width=2),
                         fill='tozeroy', fillcolor='rgba(220,53,69,0.06)',
                         name='Failure Risk'), row=2, col=1)
fig.add_hline(y=5, line_dash="dot", line_color="#198754",
              annotation_text="5% threshold", annotation_font_color="#198754", row=2, col=1)

# Cost
fig.add_trace(go.Scatter(x=time_hours, y=costs, mode='lines',
                         line=dict(color='#212529', width=2), name='Total Cost'), row=3, col=1)
fig.add_trace(go.Scatter(x=[min_cost_time], y=[costs[min_cost_idx]], mode='markers',
                         marker=dict(color='#0d6efd', size=10, symbol='diamond'),
                         name=f'Optimal: {min_cost_time:.0f}h'), row=3, col=1)

fig.update_layout(
    height=700, template="plotly_white", font=dict(family="Inter", size=12),
    margin=dict(t=40, b=30, l=60, r=20),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
)
fig.update_yaxes(title_text="MPa", row=1, col=1)
fig.update_yaxes(title_text="%", row=2, col=1)
fig.update_yaxes(title_text="₹", row=3, col=1)
fig.update_xaxes(title_text="Time (hours)", row=3, col=1)

for ann in fig['layout']['annotations']:
    ann['font'] = dict(size=12, color='#495057', family='Inter')

st.plotly_chart(fig, use_container_width=True)

# ── Milestone Table ──
st.markdown("**Strength at Key Time Points**")
milestones = [12, 24, 36, 48, 72, 96, 168]
rows = []
for t in milestones:
    m, s = engine.predict(t, features)
    cd = econ.compute(t, m, s, required_strength, yard_day_cost, rework_cost, steam_cost, curing_method)
    rows.append({
        "Time (h)": t,
        "Strength (MPa)": f"{m:.1f} ± {s:.1f}",
        "Meets Requirement": "✅ Yes" if m >= required_strength else "❌ No",
        "Failure Risk": f"{cd['pfail']*100:.1f}%",
        "Total Cost (₹)": f"₹{cd['total_cost']:,.0f}",
    })
st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
