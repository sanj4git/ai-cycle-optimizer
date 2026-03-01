import streamlit as st
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from src.strength_engine import StrengthEngine, CEMENT_FACTORS, CURING_FACTORS
from src.economic_engine import EconomicEngine
from src.model_loader import load_model
from src.climate_profiles import CLIMATE_PROFILES, get_city_names

st.set_page_config(page_title="Element Simulation | AI-Cycle", page_icon="", layout="wide")

# ─────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────
st.markdown("""
<h1 style="background: linear-gradient(90deg, #FFB74D, #FF9800, #F57C00);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; font-size: 2rem; margin-bottom: 0;">
    Element Strength Simulation
</h1>
<p style="color: #8b949e; font-size: 0.95rem; margin-top: 4px;">
    Scenario builder — simulate strength gain, risk, and cost over time for any element configuration
</p>
""", unsafe_allow_html=True)

st.markdown("---")

# ─────────────────────────────────────────────
# Sidebar: Element Configuration
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Element Configuration")

    # Mix Design
    st.markdown("**Mix Design**")
    cement_type = st.selectbox("Cement Type", list(CEMENT_FACTORS.keys()), index=0)
    wc_ratio = st.slider("Water-Cement Ratio (w/c)", 0.28, 0.60, 0.40, 0.02)
    admixture = st.selectbox("Admixture", ["None", "Plasticizer", "Accelerator", "Retarder"])
    admixture_dose = st.slider("Admixture Dose (%)", 0.0, 3.0, 1.0, 0.1) if admixture != "None" else 0.0

    st.markdown("---")

    # Curing
    st.markdown("**Curing Method**")
    curing_method = st.selectbox("Method", list(CURING_FACTORS.keys()), index=0)

    st.markdown("---")

    # Climate
    st.markdown("**Climate Conditions**")
    use_preset = st.toggle("Use Regional Preset", value=True)

    if use_preset:
        region = st.selectbox("Region", get_city_names())
        monsoon = st.toggle("Monsoon Season", value=False)
        profile = CLIMATE_PROFILES[region]
        ambient_temp = profile["monsoon_temp_c"] if monsoon else profile["ambient_temp_c"]
        ambient_rh = profile["monsoon_rh_pct"] if monsoon else profile["ambient_rh_pct"]
        st.markdown(f"**{ambient_temp}°C** &nbsp; **{ambient_rh}%** RH")
    else:
        ambient_temp = st.slider("Ambient Temperature (°C)", 10, 48, 30)
        ambient_rh = st.slider("Relative Humidity (%)", 20, 100, 65)

    st.markdown("---")

    # Strength requirement
    st.markdown("**Target**")
    required_strength = st.slider("Required Demould Strength (MPa)", 10, 45, 25)

    st.markdown("---")

    # Cost parameters
    st.markdown("**Cost Parameters**")
    yard_day_cost = st.number_input("Yard Cost (₹/day)", 500, 10000, 2000)
    rework_cost = st.number_input("Rework Cost (₹)", 5000, 80000, 25000)
    steam_cost = st.number_input("Steam Cost (₹/hr)", 0, 2000, 200) if curing_method == "Steam" else 0

# ─────────────────────────────────────────────
# Engine Setup
# ─────────────────────────────────────────────
model = load_model()
engine = StrengthEngine(model)
econ = EconomicEngine()

features = {
    "wc_ratio": wc_ratio,
    "ambient_temp": ambient_temp,
    "ambient_rh_pct": ambient_rh,
    "curing_method": curing_method,
    "cement_type": cement_type,
    "admixture": admixture,
    "admixture_dose_pct": admixture_dose,
}

# ─────────────────────────────────────────────
# Compute Curves
# ─────────────────────────────────────────────
time_hours = np.linspace(1, 168, 120)
curve = engine.predict_curve(features, time_hours)

# Risk and cost curves
risks = []
costs = []
cost_breakdowns = []

for t in time_hours:
    mean, std = engine.predict(t, features)
    cost_data = econ.compute(
        t, mean, std, required_strength,
        yard_day_cost, rework_cost, steam_cost, curing_method
    )
    risks.append(cost_data["pfail"] * 100)
    costs.append(cost_data["total_cost"])
    cost_breakdowns.append(cost_data)

risks = np.array(risks)
costs = np.array(costs)

# Demould readiness: when mean strength first exceeds required
readiness_idx = np.where(curve["means"] >= required_strength)[0]
readiness_time = time_hours[readiness_idx[0]] if len(readiness_idx) > 0 else None

# ─────────────────────────────────────────────
# Demould Readiness Badge
# ─────────────────────────────────────────────
badge_col1, badge_col2, badge_col3 = st.columns(3)

with badge_col1:
    if readiness_time is not None and readiness_time <= 24:
        st.markdown(f"""
        <div style="background: rgba(46,204,113,0.12); border: 1px solid rgba(46,204,113,0.3);
            border-radius: 10px; padding: 14px 18px; text-align: center;">
            <div style="color: #2ecc71; font-size: 1.8rem; font-weight: 700;">{readiness_time:.0f}h</div>
            <div style="color: #2ecc71; font-size: 0.8rem; font-weight: 500;">🟢 Early Demould Ready</div>
        </div>""", unsafe_allow_html=True)
    elif readiness_time is not None and readiness_time <= 72:
        st.markdown(f"""
        <div style="background: rgba(255,183,77,0.12); border: 1px solid rgba(255,183,77,0.3);
            border-radius: 10px; padding: 14px 18px; text-align: center;">
            <div style="color: #FFB74D; font-size: 1.8rem; font-weight: 700;">{readiness_time:.0f}h</div>
            <div style="color: #FFB74D; font-size: 0.8rem; font-weight: 500;">🟡 Standard Demould</div>
        </div>""", unsafe_allow_html=True)
    else:
        rt_text = f"{readiness_time:.0f}h" if readiness_time else ">168h"
        st.markdown(f"""
        <div style="background: rgba(231,76,60,0.12); border: 1px solid rgba(231,76,60,0.3);
            border-radius: 10px; padding: 14px 18px; text-align: center;">
            <div style="color: #e74c3c; font-size: 1.8rem; font-weight: 700;">{rt_text}</div>
            <div style="color: #e74c3c; font-size: 0.8rem; font-weight: 500;">🔴 Slow Strength Gain</div>
        </div>""", unsafe_allow_html=True)

with badge_col2:
    # Risk at 24h
    risk_24 = risks[np.argmin(np.abs(time_hours - 24))]
    rc = "#2ecc71" if risk_24 < 5 else ("#FFB74D" if risk_24 < 20 else "#e74c3c")
    st.markdown(f"""
    <div style="background: rgba(0,0,0,0.2); border: 1px solid rgba(255,183,77,0.15);
        border-radius: 10px; padding: 14px 18px; text-align: center;">
        <div style="color: {rc}; font-size: 1.8rem; font-weight: 700;">{risk_24:.1f}%</div>
        <div style="color: #8b949e; font-size: 0.8rem; font-weight: 500;">Risk at 24h</div>
    </div>""", unsafe_allow_html=True)

with badge_col3:
    # Min cost point
    min_cost_idx = np.argmin(costs)
    min_cost_time = time_hours[min_cost_idx]
    st.markdown(f"""
    <div style="background: rgba(0,0,0,0.2); border: 1px solid rgba(255,183,77,0.15);
        border-radius: 10px; padding: 14px 18px; text-align: center;">
        <div style="color: #4FC3F7; font-size: 1.8rem; font-weight: 700;">₹{costs[min_cost_idx]:,.0f}</div>
        <div style="color: #8b949e; font-size: 0.8rem; font-weight: 500;">Min Cost @ {min_cost_time:.0f}h</div>
    </div>""", unsafe_allow_html=True)

st.markdown("")

# ─────────────────────────────────────────────
# 3-Panel Plot
# ─────────────────────────────────────────────
fig = make_subplots(
    rows=3, cols=1,
    shared_xaxes=True,
    vertical_spacing=0.08,
    subplot_titles=("Strength vs Time", "Failure Risk vs Time", "Expected Cost vs Time"),
    row_heights=[0.38, 0.28, 0.34],
)

# Panel 1: Strength
fig.add_trace(go.Scatter(
    x=time_hours, y=curve["uppers"], mode='lines',
    line=dict(width=0), showlegend=False, name='Upper',
), row=1, col=1)
fig.add_trace(go.Scatter(
    x=time_hours, y=curve["lowers"], mode='lines',
    line=dict(width=0), fill='tonexty', fillcolor='rgba(255,183,77,0.15)',
    showlegend=True, name='±1σ Confidence',
), row=1, col=1)
fig.add_trace(go.Scatter(
    x=time_hours, y=curve["means"], mode='lines',
    line=dict(color='#FFB74D', width=3), name='Mean Strength',
), row=1, col=1)
# Required strength line
fig.add_hline(
    y=required_strength, line_dash="dash", line_color="#e74c3c", line_width=2,
    annotation_text=f"Required: {required_strength} MPa",
    annotation_font_color="#e74c3c", annotation_font_size=11,
    row=1, col=1,
)

# Panel 2: Risk
fig.add_trace(go.Scatter(
    x=time_hours, y=risks, mode='lines',
    line=dict(color='#e74c3c', width=2.5),
    fill='tozeroy', fillcolor='rgba(231,76,60,0.1)',
    name='Failure Risk %',
), row=2, col=1)
fig.add_hline(y=5, line_dash="dot", line_color="rgba(46,204,113,0.5)",
              annotation_text="5% threshold", annotation_font_color="#2ecc71",
              annotation_font_size=10, row=2, col=1)

# Panel 3: Cost
fig.add_trace(go.Scatter(
    x=time_hours, y=costs, mode='lines',
    line=dict(color='#4FC3F7', width=2.5), name='Total Expected Cost',
), row=3, col=1)
# Yard cost
yard_costs = [cb["yard_cost"] for cb in cost_breakdowns]
fig.add_trace(go.Scatter(
    x=time_hours, y=yard_costs, mode='lines',
    line=dict(color='#81C784', width=1.5, dash='dot'), name='Yard Cost',
), row=3, col=1)
# Rework expected
rework_costs = [cb["rework_expected"] for cb in cost_breakdowns]
fig.add_trace(go.Scatter(
    x=time_hours, y=rework_costs, mode='lines',
    line=dict(color='#e74c3c', width=1.5, dash='dot'), name='Expected Rework',
), row=3, col=1)

# Optimal point marker
fig.add_trace(go.Scatter(
    x=[min_cost_time], y=[costs[min_cost_idx]],
    mode='markers+text', name='Optimal',
    marker=dict(color='#FFB74D', size=12, symbol='star', line=dict(color='white', width=1.5)),
    text=[f"Optimal: {min_cost_time:.0f}h"], textposition='top center',
    textfont=dict(color='#FFB74D', size=11),
), row=3, col=1)

# Layout
fig.update_layout(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    height=850,
    margin=dict(t=40, b=30, l=60, r=30),
    legend=dict(
        orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5,
        font=dict(size=11),
    ),
    font=dict(family="Inter"),
)

fig.update_yaxes(title_text="Strength (MPa)", row=1, col=1)
fig.update_yaxes(title_text="Risk (%)", row=2, col=1, range=[0, max(100, max(risks) * 1.1)])
fig.update_yaxes(title_text="Cost (₹)", row=3, col=1)
fig.update_xaxes(title_text="Time (hours)", row=3, col=1)

# Annotation styling
for annotation in fig['layout']['annotations']:
    annotation['font'] = dict(size=13, color='#c9d1d9', family='Inter')

st.plotly_chart(fig, use_container_width=True)

# ─────────────────────────────────────────────
# Strength at Key Milestones
# ─────────────────────────────────────────────
st.markdown("---")
st.markdown("""<div style="color: #FFB74D; font-size: 0.8rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 10px;
    padding-bottom: 6px; border-bottom: 1px solid rgba(255,183,77,0.2);">
    Strength at Key Milestones
</div>""", unsafe_allow_html=True)

milestones = [12, 24, 36, 48, 72, 96, 168]
ms_cols = st.columns(len(milestones))

for i, t in enumerate(milestones):
    m, s = engine.predict(t, features)
    meets = m >= required_strength
    color = "#2ecc71" if meets else "#e74c3c"
    icon = "PASS" if meets else "FAIL"
    ms_cols[i].markdown(f"""
    <div style="text-align: center; background: rgba(0,0,0,0.2);
        border: 1px solid {'rgba(46,204,113,0.3)' if meets else 'rgba(231,76,60,0.2)'};
        border-radius: 8px; padding: 10px 6px;">
        <div style="color: #8b949e; font-size: 0.7rem; font-weight: 500;">{t}h</div>
        <div style="color: {color}; font-size: 1.2rem; font-weight: 700;">{m:.1f}</div>
        <div style="color: #8b949e; font-size: 0.65rem;">±{s:.1f} MPa</div>
        <div style="font-size: 0.8rem;">{icon}</div>
    </div>
    """, unsafe_allow_html=True)