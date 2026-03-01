import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from src.strength_engine import StrengthEngine, CEMENT_FACTORS, CURING_FACTORS
from src.economic_engine import EconomicEngine
from src.optimization_engine import OptimizationEngine
from src.model_loader import load_model
from src.climate_profiles import CLIMATE_PROFILES, get_city_names

st.set_page_config(page_title="Optimizer | AI-Cycle", page_icon="🎯", layout="wide")

# ── Header ──
st.markdown("## 🎯 Optimization Dashboard")
st.caption("Multi-objective optimization — find the best demoulding time balancing cost, risk, and cycle time")
st.markdown("---")

# ── Sidebar ──
with st.sidebar:
    st.markdown("### Optimization Parameters")
    cement_type = st.selectbox("Cement Type", list(CEMENT_FACTORS.keys()))
    wc_ratio = st.slider("W/C Ratio", 0.28, 0.60, 0.40, 0.02)
    curing_method = st.selectbox("Curing Method", list(CURING_FACTORS.keys()))
    admixture = st.selectbox("Admixture", ["None", "Plasticizer", "Accelerator", "Retarder"])
    admixture_dose = st.slider("Dose (%)", 0.0, 3.0, 1.0, 0.1) if admixture != "None" else 0.0

    st.markdown("---")
    region = st.selectbox("Region", get_city_names())
    monsoon = st.toggle("Monsoon", value=False)
    profile = CLIMATE_PROFILES[region]
    ambient_temp = profile["monsoon_temp_c"] if monsoon else profile["ambient_temp_c"]
    ambient_rh = profile["monsoon_rh_pct"] if monsoon else profile["ambient_rh_pct"]

    st.markdown("---")
    required_strength = st.slider("Required Strength (MPa)", 10, 45, 25)
    yard_day_cost = st.number_input("Yard Cost (₹/day)", 500, 10000, 2000)
    rework_cost = st.number_input("Rework Cost (₹)", 5000, 80000, 25000)
    steam_cost = st.number_input("Steam Cost (₹/hr)", 0, 2000, 200) if curing_method == "Steam" else 0

# ── Run Optimization ──
model = load_model()
strength_engine = StrengthEngine(model)
economic_engine = EconomicEngine()
optimizer = OptimizationEngine(strength_engine, economic_engine)

features = {
    "wc_ratio": wc_ratio, "ambient_temp": ambient_temp, "ambient_rh_pct": ambient_rh,
    "curing_method": curing_method, "cement_type": cement_type,
    "admixture": admixture, "admixture_dose_pct": admixture_dose,
}

results, best = optimizer.optimize(
    features, required_strength, yard_day_cost, rework_cost, steam_cost, curing_method,
)
pareto = optimizer.pareto_front(results)

# ── Recommendation ──
st.markdown("#### Recommended Strategy")
r1, r2, r3, r4 = st.columns(4)
r1.metric("Demould Time", f"{best['time_h']}h")
r2.metric("Total Cost", f"₹{best['total_cost']:,.0f}")
r3.metric("Failure Risk", f"{best['risk_pct']:.2f}%")
r4.metric("Strength", f"{best['mean_strength']:.1f} MPa",
          delta="✅ Meets target" if best['meets_strength'] else "❌ Below target",
          delta_color="normal" if best['meets_strength'] else "inverse")

st.markdown("")

# ── Two charts side by side ──
ch1, ch2 = st.columns(2)

with ch1:
    st.markdown("**Cost vs Risk Trade-off (Pareto Front)**")
    df_r = pd.DataFrame(results)

    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(
        x=df_r['risk_pct'], y=df_r['total_cost'], mode='markers+text',
        marker=dict(size=df_r['time_h'] / 4 + 6, color='#6c757d',
                    line=dict(width=1, color='#fff')),
        text=[f"{r['time_h']}h" for r in results],
        textposition='top center', textfont=dict(size=10, color='#495057'),
        name='Candidates',
    ))
    # Pareto line
    if len(pareto) > 1:
        p = sorted(pareto, key=lambda x: x['risk_pct'])
        fig1.add_trace(go.Scatter(
            x=[r['risk_pct'] for r in p], y=[r['total_cost'] for r in p],
            mode='lines', line=dict(color='#0d6efd', width=1.5, dash='dash'),
            name='Pareto Front',
        ))
    # Best
    fig1.add_trace(go.Scatter(
        x=[best['risk_pct']], y=[best['total_cost']], mode='markers',
        marker=dict(size=14, color='#0d6efd', symbol='diamond',
                    line=dict(width=2, color='#fff')),
        name='Recommended',
    ))
    fig1.update_layout(
        template="plotly_white", height=380, font=dict(family="Inter"),
        xaxis_title="Failure Risk (%)", yaxis_title="Total Cost (₹)",
        margin=dict(t=20, b=40), showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig1, use_container_width=True)

with ch2:
    st.markdown("**Cost Breakdown by Demould Time**")
    fig2 = go.Figure()
    labels = [f"{r['time_h']}h" for r in results]
    fig2.add_trace(go.Bar(x=labels, y=[r['yard_cost'] for r in results],
                          name='Yard Holding', marker_color='#0d6efd'))
    fig2.add_trace(go.Bar(x=labels, y=[r['treatment_cost'] for r in results],
                          name='Steam Treatment', marker_color='#198754'))
    fig2.add_trace(go.Bar(x=labels, y=[r['rework_expected'] for r in results],
                          name='Expected Rework', marker_color='#dc3545'))
    fig2.update_layout(
        barmode='stack', template="plotly_white", height=380,
        font=dict(family="Inter"),
        xaxis_title="Demould Time", yaxis_title="Cost (₹)",
        margin=dict(t=20, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig2, use_container_width=True)

# ── Results Table ──
st.markdown("---")
st.markdown("**All Candidate Results**")

table_data = []
for r in results:
    table_data.append({
        "Time (h)": r['time_h'],
        "Strength (MPa)": f"{r['mean_strength']:.1f} ± {r['std_strength']:.1f}",
        "Risk (%)": f"{r['risk_pct']:.2f}",
        "Yard Cost (₹)": f"{r['yard_cost']:,.0f}",
        "Treatment (₹)": f"{r['treatment_cost']:,.0f}",
        "Rework Risk (₹)": f"{r['rework_expected']:,.0f}",
        "Total Cost (₹)": f"{r['total_cost']:,.0f}",
        "Meets Strength": "✅" if r['meets_strength'] else "❌",
    })
st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)