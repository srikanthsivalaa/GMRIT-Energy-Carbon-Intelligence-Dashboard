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
        marker_colors=['#378ADD', '#4ADE80'],
        hole=0.45
    ))
    fig2.update_layout(title="Electricity Supply Mix (Grid vs Solar, Block 3 Estimate)", template='plotly_dark', height=340,
        paper_bgcolor='rgba(0,0,0,0)', font_color='#E5E9F0', legend=dict(font=dict(color='#E5E9F0')))
    st.plotly_chart(fig2, use_container_width=True)
    st.caption("Diesel is excluded here: the diesel-to-kWh conversion factor was not verified against genset specs. Diesel is shown separately (Campus Diesel CO2 card and section below) in audited litres and CO2 only.")

with col_b:
    temp_cut = pd.cut(predictions['temperature_C'], bins=range(10,46,2))
    temp_binned = predictions.groupby(temp_cut, observed=True)['predicted_electricity_kwh'].mean().reset_index()
    temp_binned['temp_mid'] = [interval.mid for interval in temp_binned['temperature_C']]
    fig3 = go.Figure(go.Scatter(x=temp_binned['temp_mid'], y=temp_binned['predicted_electricity_kwh'], mode='lines+markers',
        line_color='#4ADE80', fill='tozeroy', fillcolor='rgba(74,222,128,0.1)'))
    fig3.update_layout(title="Model-Derived Temperature Response", template='plotly_dark', height=340,
        margin=dict(l=10, r=10, t=50, b=40),
        plot_bgcolor='#171B26', paper_bgcolor='rgba(0,0,0,0)', font_color='#E5E9F0')
    st.plotly_chart(fig3, use_container_width=True)
    st.caption("Not measured Block 3 behavior — reflects the trained model's general temperature response.")

# ============ FLOOR-WISE EMISSIONS BREAKDOWN ============
st.markdown("<div class='section-header'>Estimated Floor-wise Carbon Allocation (Electricity Only)</div>", unsafe_allow_html=True)
st.markdown("<p class='note-text'>Floor shares originate from the audited equipment schedule and are allocated proportionally, not individually metered per-floor emissions.</p>", unsafe_allow_html=True)

floor_co2 = {
    'Ground Floor': total_co2_block3_electricity * floor_shares['Ground Floor'],
    '1st Floor': total_co2_block3_electricity * floor_shares['1st Floor'],
    'Top Floor': total_co2_block3_electricity * floor_shares['Top Floor'],
}

fig_treemap = go.Figure(go.Bar(
    x=list(floor_co2.values()),
    y=list(floor_co2.keys()),
    orientation='h',
    marker_color=['#F87171', '#FB923C', '#FBBF24'],
    text=[f"{v:.1f} tCO2/yr ({v/total_co2_block3_electricity*100:.0f}%)" for v in floor_co2.values()],
    textposition='outside',
))
fig_treemap.update_layout(
    title="Estimated Floor-wise Carbon Allocation (Block 3 Electricity Only, Diesel Excluded)",
    template='plotly_dark', height=280, margin=dict(l=10, r=80, t=50, b=10),
    plot_bgcolor='#171B26', paper_bgcolor='rgba(0,0,0,0)', font_color='#E5E9F0',
    xaxis_title="tCO2/yr", yaxis=dict(autorange="reversed")
)
st.plotly_chart(fig_treemap, use_container_width=True)
st.markdown(f"<p class='note-text'>Total Block 3 electricity-related footprint: {total_co2_block3_electricity:,.1f} tCO2/yr. Floor split computed directly from the 'Floor Level' column in the audited room-level equipment schedule (626 rows) and operating-hour assumptions, not inferred from the BIM model. Campus diesel CO2 ({campus_diesel_co2:,.1f} tCO2/yr) is excluded from this figure and from the floor split, since it cannot be defensibly allocated to Block 3 or to individual floors.</p>", unsafe_allow_html=True)

# ============ FUTURE PROJECTION ============
st.markdown("<div class='section-header'>Scenario-Based Future Projection (Not an ML Forecast)</div>", unsafe_allow_html=True)
st.markdown("<p class='note-text'>This is a what-if scenario computed from assumed growth/climate-trend rates applied to the ML-estimated base year - it is not a model forecast or prediction of future years.</p>", unsafe_allow_html=True)
years = [2026 + i for i in range(projection_years)]
proj_kwh = [total_kwh * ((1 + (usage_growth + climate_trend)/100)**i) for i in range(projection_years)]
proj_net = [max(k - block3_solar_offset_kwh, 0.0) for k in proj_kwh]
proj_co2 = [(k/1000)*emission_factor for k in proj_net]  # electricity-only, diesel excluded (see above)

fig4 = go.Figure(go.Bar(x=[str(y) for y in years], y=proj_co2, marker_color='#A78BFA'))
fig4.update_layout(title=f"Scenario-Based Projected Block 3 Electricity CO2 ({years[0]} – {years[-1]})", template='plotly_dark', height=340,
    plot_bgcolor='#171B26', paper_bgcolor='rgba(0,0,0,0)', font_color='#E5E9F0', yaxis_title="tCO2 / year")
st.plotly_chart(fig4, use_container_width=True)
st.markdown(f"<p class='note-text'>Scenario projection under assumed future usage growth ({usage_growth}%/yr) and climate trend ({climate_trend}%/yr), not a measured or guaranteed forecast. Excludes diesel (campus-level, held constant, not projected here). Audit baseline year: Apr 2021–Mar 2022. Weather data reference period differs from the audit year.</p>", unsafe_allow_html=True)

st.markdown("---")
st.markdown(f"<p class='desc-text'>Model: XGBoost (R²=0.898 on held-out BDG2 education-building test data; not a Block 3 validation metric — see Model Inputs & Evaluation and Domain Limitation notes below), compared against available GMRIT energy-audit data via a one-week calibration consistency check (NMBE={nmbe:.2f}% on the same anchor week used to fit the calibration factor — not independent validation). Campus PV generation ({campus_solar_generation_kwh:,.0f} kWh/yr) is measured; the {block3_share*100:.2f}% Block 3 share is an assumption-based scenario allocation using connected-load share, since Block 3-specific solar metering was not available. Diesel: {annual_diesel_liters:,.0f} L/yr is the audited campus-level DG consumption (Apr 2021–Mar 2022); it is reported separately and is NOT included in the Block 3 carbon footprint, since no defensible Block 3-specific diesel allocation exists.</p>", unsafe_allow_html=True)

# ============ MODEL INPUTS & EVALUATION ============
st.markdown("<div class='section-header'>Model Inputs & Evaluation</div>", unsafe_allow_html=True)

metrics_path = "model_metrics.json"
model_metrics = None
if os.path.exists(metrics_path):
    try:
        with open(metrics_path) as f:
            model_metrics = json.load(f)
    except Exception:
        model_metrics = None

if model_metrics is None:
    st.info("model_metrics.json not found in the repo. Run the updated block3_model_training.py "
             "(Cells 10-10d) and copy the generated model_metrics.json into this repo's root folder "
             "to populate this section. No metrics are fabricated here in its absence.")
else:
    st.markdown("**Input features used by the XGBoost model** (exactly as defined in `block3_model_training.py`, Cell 8):")
    st.code(", ".join(model_metrics["features_used"]), language="text")

    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.markdown("**XGBoost vs. Linear Regression baseline** (same BDG2 held-out test set)")
        xgb_m, base_m = model_metrics["xgboost"], model_metrics["baseline_linear_regression"]
        fig_metrics = go.Figure()
        metric_names = ['R²', 'MAE (kWh)', 'RMSE (kWh)']
        fig_metrics.add_trace(go.Bar(name='XGBoost', x=metric_names,
            y=[xgb_m['r2'], xgb_m['mae_kwh'], xgb_m['rmse_kwh']], marker_color='#378ADD'))
        fig_metrics.add_trace(go.Bar(name='Linear Regression (baseline)', x=metric_names,
            y=[base_m['r2'], base_m['mae_kwh'], base_m['rmse_kwh']], marker_color='#9BA3B8'))
        fig_metrics.update_layout(template='plotly_dark', height=320, barmode='group',
            plot_bgcolor='#171B26', paper_bgcolor='rgba(0,0,0,0)', font_color='#E5E9F0',
            legend=dict(font=dict(color='#E5E9F0')))
        st.plotly_chart(fig_metrics, use_container_width=True)
        st.caption(f"Evaluated on: {model_metrics.get('evaluation_dataset', 'BDG2 held-out test set')}. "
                    f"R² is unitless (higher is better); MAE/RMSE are in kWh (lower is better) and are "
                    f"not directly comparable across the two different y-axis scales shown together here — "
                    f"read R² and error metrics as separate comparisons.")

    with col_m2:
        st.markdown("**XGBoost feature importance** (gain-based, from the trained model)")
        importances = model_metrics["feature_importance"]
        fig_imp = go.Figure(go.Bar(
            x=list(importances.values()), y=list(importances.keys()), orientation='h',
            marker_color='#4ADE80'
        ))
        fig_imp.update_layout(template='plotly_dark', height=320, margin=dict(l=10, r=20, t=10, b=10),
            plot_bgcolor='#171B26', paper_bgcolor='rgba(0,0,0,0)', font_color='#E5E9F0',
            yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig_imp, use_container_width=True)
        st.caption("Built-in XGBoost gain-based importance. A full SHAP explanation was not generated "
                    "for this model run (requires the 'shap' package and re-running against the saved "
                    "model) - this chart shows relative feature contribution, not SHAP values.")

st.markdown("""<div class='metric-card' style='margin-top:14px; border-left:3px solid #F87171;'>
<div class='metric-label' style='color:#F87171;'>Domain Limitation</div>
<p class='desc-text' style='margin-top:8px;'>The XGBoost model is trained entirely on the BDG2 (Building Data Genome Project 2) dataset -
604 education buildings, predominantly North American/European campuses, with their own climate zones,
construction practices, and occupancy patterns. Block 3 (GMRIT, Rajam, Andhra Pradesh - a Warm & Humid
climate, Indian institutional construction) is <b>not represented in the training data</b> in any form.
The one-week audit anchor is used only to <i>calibrate</i> (rescale) the model's output magnitude to
Block 3's actual audited weekly energy - it does not retrain the model on Indian/Block-3-specific patterns.
BDG2 performance (R²=0.898) therefore reflects how well the model generalizes across other BDG2 buildings,
not how accurately it captures Block 3's actual behavior. This is a genuine limitation of the current
approach and should be stated as such in the report and viva, not minimized.</p>
</div>""", unsafe_allow_html=True)




# ============ 3D BUILDING & EMISSION VISUALIZATION ============
st.markdown("<div class='section-header'>BIM-Integrated Building Performance Model & Emission Distribution</div>", unsafe_allow_html=True)

col_bim, col_emissions = st.columns([1.2, 1])

with col_bim:
    st.markdown("#### Architectural BIM Model (Courtyard Layout)")
    try:
        st.image("block3_render.png", caption="Block 3 (GMRIT) — gbXML Geometry with Open Central Courtyard", use_container_width=True)
    except Exception:
        st.info("Place 'block3_render.png' in your project root directory to display the BIM model.")

with col_emissions:
    st.markdown("#### Floor-Wise Emission Load Intensity")
    try:
        st.image("block3_floor_emission_render.png",
                  caption="Block 3 — floor-colored elevation render (Ground/1st/Top, from Revit)",
                  use_container_width=True)
    except Exception:
        st.info("Place 'block3_floor_emission_render.png' in your project root directory to display this render. "
                 "In Revit: color each floor by a filter/legend matching the dashboard palette "
                 "(Ground=#F87171 red, 1st=#FB923C orange, Top=#FBBF24 yellow), export an isometric/elevation view as PNG.")

st.markdown("<p class='note-text'>Left: BIM architectural wireframe with central courtyard. Right: floor-colored elevation render from Revit, matching the equipment-schedule-derived load share by floor — not a thermal simulation.</p>", unsafe_allow_html=True)

# ============ DATA BOUNDARY & LIMITATIONS ============
st.markdown("<div class='section-header'>Data Boundary & Limitations</div>", unsafe_allow_html=True)
st.markdown("""<div class='metric-card' style='border-left:3px solid #F87171;'>
<p class='desc-text' style='margin:0;'>
No Block 3-specific electricity meter series, solar generation meter, or diesel generator (DG) meter was
available for this project. All Block 3-level electricity, solar, and floor-wise figures on this dashboard
are therefore produced by one of two methods:
</p>
<ul class='desc-text' style='margin-top:8px; margin-bottom:8px;'>
<li><b>ML prediction</b> (annual/monthly electricity): an XGBoost model trained on the BDG2 reference dataset,
driven by local weather and Block 3's physical attributes, then rescaled using a single-week audited
calibration anchor.</li>
<li><b>Allocation methods</b> (solar share, floor-wise share, EUI, carbon intensity): campus-level or
building-level totals distributed using connected-load share or the audited equipment schedule's
floor/weekly-energy split — not independently measured at the Block 3, floor, or room level.</li>
</ul>
<p class='desc-text' style='margin:0;'>
Consequently, <b>independent building-level validation of Block 3's electricity, solar, or diesel figures is
not claimed anywhere on this dashboard.</b> The one-week NMBE check demonstrates calibration consistency only
(see One-Week Calibration Consistency Check above). Campus-level audited figures (electricity, diesel, solar
generation) are real measurements, but the moment they are allocated or predicted down to Block 3, floor, or
room level, the result becomes an estimate or scenario, not a measurement, and is labeled as such throughout.
</p>
</div>""", unsafe_allow_html=True)

# ============ RECOMMENDED ENERGY-SAVING MEASURES ============
st.markdown("<div class='section-header'>Recommended Energy-Saving Measures</div>", unsafe_allow_html=True)
st.markdown("<p class='note-text'>Two categories below: audited retrofit measures with verified savings figures, and no-cost operational measures derived from this project's own floor-wise and occupancy findings (not independently quantified — see notes).</p>", unsafe_allow_html=True)

r1, r2 = st.columns(2)
with r1:
    st.markdown("""<div class='metric-card' style='height:100%;'>
    <div class='metric-label'>🟢 Audited Retrofit — BLDC Ceiling Fan Replacement</div>
    <div class='metric-value' style='font-size:22px;'>67,904 kWh/yr</div>
    <div class='metric-sub'>Estimated savings, campus-wide</div>
    <p class='desc-text' style='margin-top:10px;'>Replacing standard induction ceiling fans with BLDC (brushless DC) fans, campus equipment
    audit (East Coast Sustainable Pvt. Ltd., Apr 2022). Low unit cost, no operational cost increase, typically
    &lt;2 year payback at scale. Block 3 has ~150+ fan units across classrooms, labs, and staff areas per the
    equipment schedule — a proportional share of this saving is a reasonable, defensible retrofit target,
    though a Block 3-specific fan count and savings split was not separately computed here.</p>
    </div>""", unsafe_allow_html=True)

with r2:
    st.markdown("""<div class='metric-card' style='height:100%;'>
    <div class='metric-label'>🟢 Audited Retrofit — SV-to-LED Lighting Replacement</div>
    <div class='metric-value' style='font-size:22px;'>1,976 kWh/yr</div>
    <div class='metric-sub'>Estimated savings, campus-wide</div>
    <p class='desc-text' style='margin-top:10px;'>Replacing sodium-vapor/CFL fixtures with LED, same campus audit source. Zero recurring
    cost once installed, immediate effect, no scheduling or behavioral dependency. Smaller absolute saving
    than the fan retrofit, but effectively zero-risk and applicable to Block 3's CFL-lit corridors, classrooms,
    and staff rooms per the equipment schedule.</p>
    </div>""", unsafe_allow_html=True)

st.markdown("<p style='margin-top:18px; margin-bottom:8px;' class='desc-text'><b>⚪ No-cost operational measures — derived from this project's own findings, savings not quantified:</b></p>", unsafe_allow_html=True)
st.markdown("""<div class='metric-card'>
<ul class='desc-text' style='margin:0;'>
<li><b>UPS standby/float-charge audit (Ground Floor):</b> Ground Floor carries 75.5% of Block 3's estimated load,
dominated by continuous-duty UPS banks (36 kW, 54 kW per the equipment schedule). UPS units draw float/standby
power even when their connected load is idle. A physical audit of which UPS loads genuinely require 24/7 uptime
versus which could be scheduled off during nights/holidays would directly target the single largest contributor
identified in this study — no capital cost, procedural only.</li>
<li><b>Lab/classroom equipment power-down enforcement:</b> The equipment schedule shows CAD/Sim Labs and
classrooms operating 35–40 hrs/week, but PCs, projectors, and lab equipment are common sources of after-hours
idle draw if not powered down. Enforcing a shutdown checklist after the last scheduled class/lab session is a
zero-cost behavioral measure directly addressing occupancy-linked equipment already inventoried in this study.</li>
<li><b>Fan/lighting operating-hour review in low-occupancy spaces:</b> Electrical Labs and the Drawing Hall
show only 8 hrs/week scheduled occupancy in the equipment schedule; a walk-through check that fans/lighting in
these spaces are not left running outside scheduled hours is a no-cost, low-effort measure.</li>
</ul>
<p class='note-text' style='margin-top:10px; margin-bottom:0;'>These three measures are recommended based on patterns visible in this project's own audited equipment/occupancy data (Data Status: 🟠 Estimated Allocation basis). No kWh or tCO2 savings figure is quoted for them, since no before/after measurement or sub-metering exists to quantify the actual achievable saving — quoting a number here would be fabrication. If pursued, a short before/after spot-metering exercise on the Ground Floor UPS bank would let a future study quantify this with real data.</p>
</div>""", unsafe_allow_html=True)
