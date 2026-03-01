import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from src.strength_engine import StrengthEngine, CEMENT_FACTORS, CURING_FACTORS
from src.economic_engine import EconomicEngine
from src.optimization_engine import OptimizationEngine
from src.model_loader import load_model
from src.climate_profiles import CLIMATE_PROFILES, get_city_names

st.set_page_config(page_title="Optimization Lab | AI-Cycle", page_icon="🎯", layout="wide")

# ─────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────
st.markdown("""
<h1 style="background: linear-gradient(90deg, #FFB74D, #FF9800, #F57C00);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; font-size: 2rem; margin-bottom: 0;">
    🎯 Optimization Dashboard
</h1>
<p style="color: #8b949e; font-size: 0.95rem; margin-top: 4px;">
    Multi-objective optimization — find the optimal demould time balancing cost, risk, and throughput
</p>
""", unsafe_allow_html=True)

st.markdown("---")

# ─────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🎯 Optimization Parameters")

    # Mix design
    st.markdown("**Mix Design**")
    cement_type = st.selectbox("Cement Type", list(CEMENT_FACTORS.keys()))
    wc_ratio = st.slider("W/C Ratio", 0.28, 0.60, 0.40, 0.02)
    admixture = st.selectbox("Admixture", ["None", "Plasticizer", "Accelerator", "Retarder"])
    admixture_dose = st.slider("Dose (%)", 0.0, 3.0, 1.0, 0.1) if admixture != "None" else 0.0

    st.markdown("---")

    # Curing
    curing_method = st.selectbox("Curing Method", list(CURING_FACTORS.keys()))

    # Climate
    st.markdown("---")
    st.markdown("**Climate**")
    region = st.selectbox("Region", get_city_names())
    monsoon = st.toggle("Monsoon", value=False)
    profile = CLIMATE_PROFILES[region]
    ambient_temp = profile["monsoon_temp_c"] if monsoon else profile["ambient_temp_c"]
    ambient_rh = profile["monsoon_rh_pct"] if monsoon else profile["ambient_rh_pct"]

    st.markdown("---")

    # Targets
    st.markdown("**Targets & Costs**")
    required_strength = st.slider("Required Strength (MPa)", 10, 45, 25)
    yard_day_cost = st.number_input("Yard Cost (₹/day)", 500, 10000, 2000)
    rework_cost = st.number_input("Rework Cost (₹)", 5000, 80000, 25000)
    steam_cost = st.number_input("Steam Cost (₹/hr)", 0, 2000, 200) if curing_method == "Steam" else 0
    electricity_cost = st.number_input("Electricity (₹/hr)", 0, 1000, 150)
    labor_cost = st.number_input("Labor (₹/shift)", 0, 30000, 12000)
    mold_opp_cost = st.number_input("Mold Opportunity Cost (₹)", 0, 10000, 2000)

# ─────────────────────────────────────────────
# Run Optimization
# ─────────────────────────────────────────────
model = load_model()
strength_engine = StrengthEngine(model)
economic_engine = EconomicEngine()
optimizer = OptimizationEngine(strength_engine, economic_engine)

features = {
    "wc_ratio": wc_ratio,
    "ambient_temp": ambient_temp,
    "ambient_rh_pct": ambient_rh,
    "curing_method": curing_method,
    "cement_type": cement_type,
    "admixture": admixture,
    "admixture_dose_pct": admixture_dose,
}

results, best = optimizer.optimize(
    features, required_strength, yard_day_cost, rework_cost, steam_cost,
    curing_method, electricity_cost, labor_cost, mold_opp_cost,
)

pareto = optimizer.pareto_front(results)

# ─────────────────────────────────────────────
# Recommendation Card
# ─────────────────────────────────────────────
st.markdown(f"""
<div style="background: linear-gradient(135deg, rgba(46,204,113,0.1) 0%, rgba(46,204,113,0.02) 100%);
    border: 1px solid rgba(46,204,113,0.3); border-radius: 14px; padding: 24px 28px; margin-bottom: 20px;">
    <div style="display: flex; align-items: center; gap: 15px; flex-wrap: wrap;">
        <div style="flex-shrink: 0;">
            <div style="font-size: 2.5rem;">🏆</div>
        </div>
        <div style="flex: 1; min-width: 200px;">
            <div style="color: #2ecc71; font-size: 0.75rem; font-weight: 600;
                text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 4px;">
                Recommended Strategy
            </div>
            <div style="color: #e6edf3; font-size: 1.5rem; font-weight: 700;">
                Demould at {best['time_h']}h &nbsp;
                <span style="color: #2ecc71; font-size: 0.85rem;">
                    {'✅ Meets Strength' if best['meets_strength'] else '⚠️ Below Target'}
                </span>
            </div>
        </div>
        <div style="display: flex; gap: 20px; flex-wrap: wrap;">
            <div style="text-align: center;">
                <div style="color: #8b949e; font-size: 0.7rem; text-transform: uppercase;">Total Cost</div>
                <div style="color: #FFB74D; font-size: 1.3rem; font-weight: 700;">₹{best['total_cost']:,.0f}</div>
            </div>
            <div style="text-align: center;">
                <div style="color: #8b949e; font-size: 0.7rem; text-transform: uppercase;">Risk</div>
                <div style="color: {'#2ecc71' if best['risk_pct'] < 5 else '#e74c3c'}; font-size: 1.3rem; font-weight: 700;">
                    {best['risk_pct']:.1f}%
                </div>
            </div>
            <div style="text-align: center;">
                <div style="color: #8b949e; font-size: 0.7rem; text-transform: uppercase;">Strength</div>
                <div style="color: #4FC3F7; font-size: 1.3rem; font-weight: 700;">{best['mean_strength']:.1f} MPa</div>
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Charts Row
# ─────────────────────────────────────────────
chart1, chart2 = st.columns(2)

with chart1:
    # Pareto Front Scatter
    df_results = pd.DataFrame(results)
    df_pareto = pd.DataFrame(pareto)

    fig_pareto = go.Figure()

    # All candidates
    fig_pareto.add_trace(go.Scatter(
        x=df_results['risk_pct'], y=df_results['total_cost'],
        mode='markers+text',
        marker=dict(
            size=df_results['time_h'] / 3,
            color=df_results['time_h'],
            colorscale=[[0, '#4FC3F7'], [0.5, '#FFB74D'], [1, '#e74c3c']],
            colorbar=dict(title="Time (h)", tickfont=dict(color='#8b949e')),
            line=dict(width=1, color='rgba(255,255,255,0.3)'),
        ),
        text=[f"{r['time_h']}h" for _, r in df_results.iterrows()],
        textposition='top center',
        textfont=dict(size=10, color='#c9d1d9'),
        name='All Candidates',
    ))

    # Pareto front line
    if len(df_pareto) > 1:
        df_pareto_sorted = df_pareto.sort_values('risk_pct')
        fig_pareto.add_trace(go.Scatter(
            x=df_pareto_sorted['risk_pct'], y=df_pareto_sorted['total_cost'],
            mode='lines', name='Pareto Front',
            line=dict(color='#2ecc71', width=2, dash='dash'),
        ))

    # Best point
    fig_pareto.add_trace(go.Scatter(
        x=[best['risk_pct']], y=[best['total_cost']],
        mode='markers', name='Recommended',
        marker=dict(size=16, color='#FFB74D', symbol='star',
                    line=dict(width=2, color='white')),
    ))

    fig_pareto.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        title=dict(text="Pareto Front: Cost vs Risk", font=dict(size=14, color='#c9d1d9')),
        xaxis_title="Failure Risk (%)",
        yaxis_title="Total Expected Cost (₹)",
        height=420,
        margin=dict(t=50, b=40),
    )
    st.plotly_chart(fig_pareto, use_container_width=True)

with chart2:
    # Cost Breakdown Stacked Bar
    fig_cost = go.Figure()

    fig_cost.add_trace(go.Bar(
        x=[f"{r['time_h']}h" for r in results],
        y=[r['yard_cost'] for r in results],
        name='Yard Cost', marker_color='#4FC3F7',
    ))
    fig_cost.add_trace(go.Bar(
        x=[f"{r['time_h']}h" for r in results],
        y=[r['treatment_cost'] for r in results],
        name='Treatment', marker_color='#81C784',
    ))
    fig_cost.add_trace(go.Bar(
        x=[f"{r['time_h']}h" for r in results],
        y=[r['rework_expected'] for r in results],
        name='Expected Rework', marker_color='#e74c3c',
    ))

    fig_cost.update_layout(
        barmode='stack',
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        title=dict(text="Cost Breakdown by Demould Time", font=dict(size=14, color='#c9d1d9')),
        xaxis_title="Demould Time",
        yaxis_title="Cost (₹)",
        height=420,
        margin=dict(t=50, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig_cost, use_container_width=True)

# ─────────────────────────────────────────────
# Risk Gauge Row
# ─────────────────────────────────────────────
st.markdown("---")
st.markdown("""<div style="color: #FFB74D; font-size: 0.8rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 10px;
    padding-bottom: 6px; border-bottom: 1px solid rgba(255,183,77,0.2);">
    ⚠️ Failure Risk by Candidate Time
</div>""", unsafe_allow_html=True)

risk_cols = st.columns(len(results))
for i, r in enumerate(results):
    color = "#2ecc71" if r['risk_pct'] < 5 else ("#FFB74D" if r['risk_pct'] < 20 else "#e74c3c")
    is_best = r.get('recommended', False)
    border = f"2px solid {color}" if is_best else f"1px solid rgba(255,183,77,0.15)"

    risk_cols[i].markdown(f"""
    <div style="text-align: center; background: rgba(0,0,0,0.2); border: {border};
        border-radius: 8px; padding: 10px 4px;">
        <div style="color: #8b949e; font-size: 0.7rem; font-weight: 500;">{r['time_h']}h</div>
        <div style="color: {color}; font-size: 1.3rem; font-weight: 700;">{r['risk_pct']:.1f}%</div>
        <div style="color: #8b949e; font-size: 0.6rem;">{'⭐ Best' if is_best else ''}</div>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Results Table
# ─────────────────────────────────────────────
st.markdown("---")
st.markdown("""<div style="color: #FFB74D; font-size: 0.8rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 10px;
    padding-bottom: 6px; border-bottom: 1px solid rgba(255,183,77,0.2);">
    📊 Full Results Table
</div>""", unsafe_allow_html=True)

display_df = pd.DataFrame(results)
display_df.columns = ['Time (h)', 'Mean Strength (MPa)', 'Std (MPa)', 'Risk (%)',
                       'Yard Cost (₹)', 'Treatment (₹)', 'Rework Expected (₹)',
                       'Total Cost (₹)', 'Meets Strength']
# Format boolean
display_df['Meets Strength'] = display_df['Meets Strength'].map({True: '✅', False: '❌'})

st.dataframe(display_df, use_container_width=True, hide_index=True)