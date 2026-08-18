import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
import os

st.set_page_config(page_title="Block 3 Energy Dashboard", layout="wide", page_icon="⚡", initial_sidebar_state="expanded")

# ============ STYLING ============
st.markdown("""
<style>
    .stApp { background-color: #0B0E14; }
    .metric-card { background: linear-gradient(135deg, #171B26 0%, #1F2433 100%); border: 1px solid #2A3040; border-radius: 14px; padding: 18px; }
    .metric-label { font-size: 12px; color: #9BA3B8; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; }
    .metric-value { font-size: clamp(18px, 4.5vw, 26px); font-weight: 700; color: #F5F7FA; margin-top: 6px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .metric-sub { font-size: 12px; color: #4ADE80; margin-top: 4px; font-weight: 500; }
    .section-header { color: #E5E9F0; font-size: 15px; text-transform: uppercase; letter-spacing: 1.5px; margin-top: 28px; margin-bottom: 12px; font-weight: 700; border-left: 3px solid #378ADD; padding-left: 10px; }
    .desc-text { color: #C4CAD9 !important; font-size: 14px; line-height: 1.6; }
    .note-text { color: #8B93A8 !important; font-size: 12px; font-style: italic; }
    .badge-pass { background: #14352A; color: #4ADE80; padding: 6px 14px; border-radius: 20px; font-size: 13px; font-weight: 600; display: inline-block; margin-right: 8px; border: 1px solid #2A5A45;}
    .badge-info { background: #1A2A3D; color: #60A5FA; padding: 6px 14px; border-radius: 20px; font-size: 13px; font-weight: 600; display: inline-block; margin-right: 8px; border: 1px solid #2A4A6A;}
    .badge-warn { background: #3D1F1F; color: #F87171; padding: 6px 14px; border-radius: 20px; font-size: 13px; font-weight: 600; display: inline-block; margin-right: 8px; border: 1px solid #5A2A2A;}
    h1, h2, h3 { color: #F5F7FA !important; }
    [data-testid="stSidebar"] { background-color: #12151F; }
    [data-testid="stSidebar"] * { color: #E5E9F0 !important; }
</style>
""", unsafe_allow_html=True)

st.title("⚡ Block 3 — GMRIT Energy & Carbon Intelligence Dashboard")
st.markdown("<p class='desc-text'>ML framework for predicting electricity consumption and carbon footprint | XGBoost calibrated to available GMRIT energy-audit data</p>", unsafe_allow_html=True)
st.markdown("<span class='badge-info'>Held-out BDG2 Reference-Dataset R² = 0.898 (NOT Block 3 validation)</span><span class='badge-info'>Calibrated to 1-Week Audit Anchor</span><span class='badge-warn'>EUI: Retrofit Potential</span>", unsafe_allow_html=True)

# ============ DATA STATUS LEGEND ============
st.markdown("""<div class='metric-card' style='margin-bottom:18px;'>
<div class='metric-label' style='margin-bottom:8px;'>Data Status Legend</div>
<p class='desc-text' style='margin:0;'>
🟢 <b>Measured/Audited</b>: campus electricity, diesel, solar, Block 3 connected load, equipment inventory &nbsp;|&nbsp;
🔵 <b>ML-Derived</b>: annual/monthly electricity prediction &nbsp;|&nbsp;
🟠 <b>Estimated Allocation</b>: Block 3 solar share, floor-wise contribution/emissions &nbsp;|&nbsp;
⚪ <b>Assumption/Scenario</b>: emission factors, operating hours, future growth/climate-trend rates, future projections
</p></div>""", unsafe_allow_html=True)

# ============ TEMPORAL SCOPE NOTICE (prominent, not collapsed) ============
st.markdown("""<div class='metric-card' style='margin-bottom:18px; border-left:3px solid #FBBF24;'>
<div class='metric-label' style='color:#FBBF24;'>Temporal Scope Note</div>
<p class='desc-text' style='margin-top:8px;'>The audit baseline (connected load, diesel, solar generation) is <b>Apr 2021–Mar 2022</b>.
The weather dataset used to drive the ML model is <b>Jul 2025–Jul 2026</b> (NASA POWER, local coordinates).
These are different periods. The annual Block 3 electricity figure on this dashboard is therefore a
<b>calibrated scenario estimate</b> — the model's weather-driven pattern for a recent year, rescaled to match
the audited weekly energy level — and should not be read as a reconstruction of actual Apr 2021–Mar 2022
Block 3 consumption.</p>
</div>""", unsafe_allow_html=True)

# ============ METHODOLOGY & DATA PROVENANCE ============
with st.expander("📋 Methodology & Data Provenance — read before presenting"):
    st.markdown("""
**Why does Block 3's estimated annual electricity (~1.09M kWh) look close to the whole campus audit total (1,524,486 kVAh/yr)?**

These two numbers are **not directly comparable** and should not be read as "Block 3 = ~71% of campus load":

- The campus audit figure (1,524,486 kVAh/yr, Apr 2021–Mar 2022) is a **measured utility bill total** for the entire campus, across all blocks, hostels, and staff quarters.
- The Block 3 figure (~1.09M kWh/yr) is an **ML model output**: an XGBoost model trained on the BDG2 dataset (604 education buildings, US-based, general-purpose archetypes), fed Block 3's physical attributes (area, floors, age) and local weather, then scaled by a single-week calibration factor to match Block 3's audited weekly energy.
- The model was **not constrained to sum to any share of the campus total**. Its output is a scenario estimate built from a generalized archetype model, not a bottom-up validated measurement of Block 3 alone.
- The connected-load share (Block 3 = 278 kW of 2,494 kW campus total, ~11.15%) describes **peak connected capacity**, not annual energy consumed — a building can have a small share of connected load but a large share of actual usage if its equipment runs more hours (Block 3's UPS/lab equipment mostly runs continuously, unlike hostels/staff quarters which are used part of the day).
- **Recommended framing for viva**: present the campus audit total as a *reference envelope* for context, and the Block 3 ML estimate as a separate, independently-calibrated scenario — do not imply the two are on the same accounting basis.

**Units — kVAh vs kWh**

The audit reports campus electricity in kVAh, not kWh. Per the audit, average campus power factor ≈ 0.99, so kVAh ≈ kWh at this site to within ~1%. All Block 3 figures in this dashboard are computed and reported directly in kWh (from the ML model and equipment schedule), so no conversion was applied to those — this note is only to clarify why the audit's campus-level unit differs from the dashboard's building-level unit.
    """)

# ============ SIDEBAR CONTROLS ============
st.sidebar.header("🎛️ Model Controls")
emission_factor = st.sidebar.slider("CEA Grid Emission Factor (tCO2/MWh)", 0.65, 0.80, 0.710, 0.001)
usage_growth = st.sidebar.slider("Annual usage growth (%)", 0.0, 5.0, 2.0, 0.5)
climate_trend = st.sidebar.slider("Climate warming trend (%)", 0.0, 2.0, 0.5, 0.1)
st.sidebar.markdown("---")
show_solar = st.sidebar.checkbox("Include solar PV offset", value=True)
st.sidebar.caption("Estimated Block 3 Solar Allocation — based on 11.15% connected-load share; Block 3-specific solar metering unavailable. Campus total (867,317 + 261,417 kWh/yr) is measured; the Block 3 share is a scenario allocation, not a measured Block 3 quantity.")
st.sidebar.markdown("---")
projection_years = st.sidebar.slider("Projection horizon (years)", 1, 10, 3)
st.sidebar.markdown("---")
month_range = st.sidebar.select_slider("Month range (monthly chart)",
    options=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'],
    value=('Jan','Dec'))

# ============ CORE DATA & CALCULATIONS ============
predictions = pd.read_csv('block3_predictions_full_year.csv')
predictions['timestamp'] = pd.to_datetime(predictions['timestamp'])

block3_sqm = 2594.7391499
block3_floors_desc = "G+2 (3 levels)"
block3_yearbuilt = 1998

campus_load_kw = 2494
block3_load_kw = 278
block3_share = block3_load_kw / campus_load_kw  # 11.15%

campus_solar_generation_kwh = 867317 + 261417  # 1,128,734 kWh/yr total campus solar
block3_solar_offset_kwh = (campus_solar_generation_kwh * block3_share) if show_solar else 0.0

total_kwh = predictions['predicted_electricity_kwh'].sum()
block3_solar_offset_kwh = min(block3_solar_offset_kwh, total_kwh)
net_grid_kwh = max(total_kwh - block3_solar_offset_kwh, 0.0)

total_co2_gross = (total_kwh / 1000) * emission_factor
total_co2_net_grid = (net_grid_kwh / 1000) * emission_factor
solar_co2_avoided = (block3_solar_offset_kwh / 1000) * emission_factor

# Diesel: 18,650 L/year is the audited campus DG consumption (Apr 2021-Mar 2022).
# This is CAMPUS-LEVEL, not Block 3-specific - there is no defensible way to
# allocate it to Block 3 alone (unlike solar/connected-load, there is no
# diesel sub-metering or connected-load-based diesel allocation in the audit).
# Per the correction: diesel CO2 is reported SEPARATELY and is NOT added into
# the Block 3 carbon footprint below.
annual_diesel_liters = 18650  # audited campus DG diesel consumption, L/year
campus_diesel_co2 = (annual_diesel_liters * 2.68) / 1000  # tCO2/year (assumption: 2.68 kg CO2/L diesel)
# NOTE: the diesel-to-kWh conversion (kWh/L) that was previously used to add a
# "Diesel Generation" slice to the energy supply-mix chart has been REMOVED.
# That conversion factor (6.91 kWh/L) was never verified against the actual
# genset spec sheet or audit, so it has been dropped rather than presented as
# fact. The supply-mix chart below now shows only Net Grid vs Solar Offset.

# Block 3's carbon footprint is now electricity-only (grid, post estimated-solar-allocation).
# Diesel is NOT included here - see campus_diesel_co2 above, reported separately.
total_co2_block3_electricity = total_co2_net_grid

# EUI / ECBC Benchmarks
eui_gross = total_kwh / block3_sqm
eui_net = net_grid_kwh / block3_sqm
ecbc_benchmark_normal, ecbc_benchmark_best = 200, 130
if eui_net <= ecbc_benchmark_best:
    ecbc_rating = "Within Best-Practice Reference Range"
elif eui_net <= ecbc_benchmark_normal:
    ecbc_rating = "Within Typical Reference Range"
else:
    ecbc_rating = "Above Reference Range (HVAC/UPS Heavy)"

# Carbon intensity uses Block 3 electricity-related emissions ONLY - diesel excluded
# (diesel is campus-level and not defensibly allocable to Block 3, see above).
carbon_intensity = (total_co2_block3_electricity * 1000) / block3_sqm  # kgCO2/sqm/yr

# ASHRAE Guideline 14 Validation
actual_weekly = 23853.03
predicted_weekly = predictions['predicted_electricity_kwh'].iloc[:168].sum()
nmbe = ((predicted_weekly - actual_weekly) / actual_weekly) * 100

# Computed directly from 'civil block final power and equipment count occupancy.xlsx'
# (626-row Block 3 equipment schedule), grouped by Floor, weekly energy (kWh) basis.
# Ground: 17,999.3 kWh/wk, 1st: 4,333.2 kWh/wk, 2nd: 1,507.4 kWh/wk of 23,839.9 kWh/wk total.
# Verified from actual run of block3_model_training.py Cell 20 (Srikanth's own file):
# Ground 75.500695% (17,999.29 kWh/wk), 1st 18.176124% (4,333.17 kWh/wk),
# Top Floor 6.323181% (1,507.44 kWh/wk), total 23,839.90 kWh/wk.
floor_shares = {'Ground Floor': 0.75501, '1st Floor': 0.18176, 'Top Floor': 0.06323}

# ============ METRIC CARDS ============
st.markdown("<div class='section-header'>Key Metrics</div>", unsafe_allow_html=True)
c1, c2, c3, c4, c5 = st.columns(5)
cards = [
    (c1, "ML-Estimated Electricity Demand", f"{total_kwh:,.0f} kWh", "Model output, not a measured meter reading"),
    (c2, "Estimated Block 3 Solar Allocation", f"{block3_solar_offset_kwh:,.0f} kWh", f"Based on 11.15% connected-load share; Block 3-specific solar metering unavailable" if show_solar else "Disabled"),
    (c3, "Estimated CO2 Avoided (Solar)", f"{solar_co2_avoided:,.1f} tCO2", "Based on allocated solar share (assumption)"),
    (c4, "Campus DG Diesel Reference", f"{campus_diesel_co2:,.1f} tCO2", f"{annual_diesel_liters:,.0f} L/yr audited campus-level — Block 3-specific diesel not metered, NOT allocated to Block 3"),
    (c5, "Block 3 Electricity-Related Carbon Footprint", f"{total_co2_block3_electricity:,.1f} tCO2/yr", "Net grid (post-solar allocation), model-derived — excludes diesel"),
]
for col, label, val, sub in cards:
    with col:
        st.markdown(f"<div class='metric-card'><div class='metric-label'>{label}</div><div class='metric-value'>{val}</div><div class='metric-sub'>{sub}</div></div>", unsafe_allow_html=True)

# ============ SUSTAINABILITY SCORECARD ============
st.markdown("<div class='section-header'>Building Sustainability Scorecard</div>", unsafe_allow_html=True)
s1, s2, s3, s4, s5 = st.columns(5)
score_cards = [
    (s1, "Estimated Gross Electricity Intensity", f"{eui_gross:.1f} kWh/m²/yr", "Before solar allocation (total ML-estimated demand / area)"),
    (s2, "Estimated Grid Electricity Intensity after Solar Allocation", f"{eui_net:.1f} kWh/m²/yr", ecbc_rating),
    (s3, "Block 3 Electricity Carbon Intensity", f"{carbon_intensity:.1f} kgCO2/m²/yr", "From Block 3 electricity emissions only, excludes diesel"),
    (s4, "Built-up Area (gbXML/BIM)", f"{block3_sqm:,.0f} m²", f"{block3_floors_desc}, built {block3_yearbuilt} — verified from f-1.xml"),
    (s5, "ECBC / BEE Reference EUI Range", f"{ecbc_benchmark_best}-{ecbc_benchmark_normal} kWh/m²/yr", "ECBC 2017 + BEE Star Rating, daytime institutional, Warm & Humid zone"),
]
for col, label, val, sub in score_cards:
    with col:
        st.markdown(f"<div class='metric-card'><div class='metric-label'>{label}</div><div class='metric-value'>{val}</div><div class='metric-sub'>{sub}</div></div>", unsafe_allow_html=True)
st.markdown("<p class='note-text'>Both EUI figures use ML-derived annual electricity (not a measured Block 3 meter reading) divided by verified built-up area. This is a Reference EUI Comparison against ECBC/BEE ranges, not a formal ECBC compliance certification — a single EUI value cannot establish compliance, which requires a full building energy simulation and code-compliance audit. Reference audit period: Apr 2021–Mar 2022 (East Coast Sustainable Pvt. Ltd., BEE-format audit). ECBC/BEE benchmark based on ECBC 2017 EPI standards for institutional daytime-use buildings, Warm & Humid climate; unoptimized baselines for comparable buildings typically run 200–275 kWh/m²/yr.</p>", unsafe_allow_html=True)

# ============ VALIDATION ============
st.markdown("<div class='section-header'>One-Week Calibration Consistency Check (NMBE)</div>", unsafe_allow_html=True)
st.markdown("<p class='note-text'>This is NOT independent ML validation. The model's calibration (scaling) factor was derived from this same one-week audited benchmark, so NMBE here can only show whether the calibration is internally consistent — it cannot demonstrate out-of-sample accuracy. Formal ASHRAE Guideline 14 validation (which requires an independent, non-calibration dataset and a full validation procedure) has not been performed and is not claimed.</p>", unsafe_allow_html=True)
col_gauge, col_compare = st.columns([1, 1.5])

with col_gauge:
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number", value=abs(nmbe),
        title={'text': "NMBE (%) — calibration-week consistency, threshold ±10%", 'font': {'color': '#E5E9F0', 'size': 12}},
        number={'font': {'color': '#F5F7FA', 'size': 28}, 'suffix': '%'},
        gauge={'axis': {'range': [0, 20], 'tickcolor': '#9BA3B8', 'tickfont': {'color': '#9BA3B8'}},
               'bar': {'color': '#4ADE80' if abs(nmbe) <= 10 else '#F87171'},
               'steps': [{'range': [0, 10], 'color': '#14352A'}, {'range': [10, 20], 'color': '#3D1F1F'}],
               'threshold': {'line': {'color': '#F5F7FA', 'width': 3}, 'value': 10}}))
    fig_gauge.update_layout(height=250, paper_bgcolor='rgba(0,0,0,0)', margin=dict(t=50,b=10,l=20,r=20))
    st.plotly_chart(fig_gauge, use_container_width=True)
    status = "✓ Within ±10% calibration-week consistency band" if abs(nmbe) <= 10 else "✗ Outside calibration-week consistency band"
    st.markdown(f"<p class='desc-text' style='text-align:center; font-weight:600; color:{'#4ADE80' if abs(nmbe)<=10 else '#F87171'};'>{status}</p>", unsafe_allow_html=True)

with col_compare:
    fig_compare = go.Figure()
    fig_compare.add_trace(go.Bar(name='Predicted (model)', x=['Weekly kWh'], y=[predicted_weekly], marker_color='#378ADD'))
    fig_compare.add_trace(go.Bar(name='Actual (audit)', x=['Weekly kWh'], y=[actual_weekly], marker_color='#4ADE80'))
    fig_compare.update_layout(title="Predicted vs Audited (1 Week Anchor)", template='plotly_dark', height=280, barmode='group',
        plot_bgcolor='#171B26', paper_bgcolor='rgba(0,0,0,0)', font_color='#E5E9F0', legend=dict(font=dict(color='#E5E9F0')))
    st.plotly_chart(fig_compare, use_container_width=True)

# ============ FLOOR-WISE BREAKDOWN ============
st.markdown("<div class='section-header'>Estimated Floor-wise Electricity Contribution</div>", unsafe_allow_html=True)
st.markdown("<p class='note-text'>Derived from the audited equipment schedule and its operating-hour assumptions, not from floor-level electricity meters.</p>", unsafe_allow_html=True)
col_floor1, col_floor2 = st.columns([1.3, 1])

with col_floor1:
    floor_names = list(floor_shares.keys())
    floor_weekly = [actual_weekly * s for s in floor_shares.values()]
    fig_floor = go.Figure(go.Bar(
        x=floor_weekly, y=floor_names, orientation='h',
        marker_color=['#F87171', '#FB923C', '#FBBF24'],
        text=[f"{v:,.0f} kWh" for v in floor_weekly],
        textposition='outside',
    ))
    fig_floor.update_layout(title="Estimated Weekly Electricity Contribution by Floor (kWh)", template='plotly_dark', height=320,
        margin=dict(l=10, r=70, t=50, b=10),
        plot_bgcolor='#171B26', paper_bgcolor='rgba(0,0,0,0)', font_color='#E5E9F0',
        xaxis_title="kWh/week", yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig_floor, use_container_width=True)

with col_floor2:
    st.markdown(f"""<div class='metric-card'>
        <div class='metric-label'>Highest Consuming Level</div>
        <div class='metric-value' style='font-size:20px;'>Ground Floor</div>
        <div class='metric-sub' style='color:#F87171;'>75.5% of Total Load (from equipment schedule)</div>
        <p class='desc-text' style='margin-top:12px;'>Floor split is read directly from the 'Floor Level' column of the audited room-level equipment schedule (not a BIM-inferred assignment). Major ground-floor loads: Central UPS banks (36 kW, 54 kW), substation transformers, and Electrical Machines/Power Systems lab motors.</p>
    </div>""", unsafe_allow_html=True)

# ============ CONSUMPTION PATTERNS ============
st.markdown("<div class='section-header'>Consumption Patterns</div>", unsafe_allow_html=True)
predictions['month'] = predictions['timestamp'].dt.strftime('%b')
predictions['month_num'] = predictions['timestamp'].dt.month
monthly = predictions.groupby(['month_num','month'])['predicted_electricity_kwh'].sum().reset_index().sort_values('month_num')

month_order = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
start_idx, end_idx = month_order.index(month_range[0]), month_order.index(month_range[1])
if start_idx <= end_idx:
    selected_months = month_order[start_idx:end_idx+1]
else:
    selected_months = month_order[start_idx:] + month_order[:end_idx+1]

monthly_filtered = monthly[monthly['month'].isin(selected_months)]

fig1 = go.Figure(go.Bar(x=monthly_filtered['month'], y=monthly_filtered['predicted_electricity_kwh'], marker_color='#378ADD'))
fig1.update_layout(title="Model-Estimated Monthly Electricity Consumption (not metered readings)", template='plotly_dark', height=340,
    plot_bgcolor='#171B26', paper_bgcolor='rgba(0,0,0,0)', font_color='#E5E9F0')
st.plotly_chart(fig1, use_container_width=True)

col_a, col_b = st.columns(2)
with col_a:
    fig2 = go.Figure(go.Pie(
        labels=['Net Grid Electricity', 'Solar Offset (Estimated Allocation)'],
        values=[net_grid_kwh, block3_solar_offset_kwh],
