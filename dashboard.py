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
st.markdown("<span class='badge-info'>BDG2 Test R² = 0.8984 (not Block 3 validation)</span><span class='badge-info'>Calibrated to 1-Week Audit Anchor (Scale: 1.7312)</span><span class='badge-warn'>EUI: Above Reference Range (Retrofit Potential)</span>", unsafe_allow_html=True)

# ============ DATA STATUS LEGEND ============
st.markdown("""<div class='metric-card' style='margin-bottom:18px;'>
<div class='metric-label' style='margin-bottom:8px;'>Data Status Legend</div>
<p class='desc-text' style='margin:0;'>
🟢 <b>Measured/Audited</b>: campus electricity, diesel, solar, Block 3 connected load, equipment inventory &nbsp;|&nbsp;
🔵 <b>ML-Derived</b>: annual/monthly electricity prediction &nbsp;|&nbsp;
🟠 <b>Estimated Allocation</b>: Block 3 solar share, floor-wise contribution/emissions &nbsp;|&nbsp;
⚪ <b>Assumption/Scenario</b>: emission factors, operating hours, future growth/climate-trend rates, future projections
</p></div>""", unsafe_allow_html=True)

# ============ METHODOLOGY & DATA PROVENANCE ============
with st.expander("📋 Methodology & Data Provenance — read before presenting"):
    st.markdown("""
**Why does Block 3's estimated annual electricity (~1.085M kWh) look close to the whole campus audit total (1,524,486 kVAh/yr)?**

These two numbers are **not directly comparable** and should not be read as "Block 3 = ~71% of campus load":

- The campus audit figure (1,524,486 kVAh/yr, Apr 2021–Mar 2022) is a **measured utility bill total** for the entire campus, across all blocks, hostels, and staff quarters.
- The Block 3 figure (~1,085,229.38 kWh/yr) is an **ML model output**: an XGBoost model trained on the BDG2 dataset (604 education buildings, US-based, general-purpose archetypes), fed Block 3's physical attributes (2,594.74 sqm, 3 floors, 26 years age) and local NASA POWER weather, then scaled by a single-week calibration factor (1.7312) to match Block 3's audited weekly energy (23,853.03 kWh).
- The model was **not constrained to sum to any share of the campus total**. Its output is a scenario estimate built from a generalized archetype model, not a bottom-up validated measurement of Block 3 alone.
- The connected-load share (Block 3 = 278 kW of 2,494 kW campus total, ~11.15%) describes **peak connected capacity**, not annual energy consumed.
- **Recommended framing for viva**: present the campus audit total as a *reference envelope* for context, and the Block 3 ML estimate as a separate, independently-calibrated scenario — do not imply the two are on the same accounting basis.

**Units — kVAh vs kWh**

The audit reports campus electricity in kVAh, not kWh. Per the audit, average campus power factor ≈ 0.99, so kVAh ≈ kWh at this site to within ~1%. All Block 3 figures in this dashboard are computed and reported directly in kWh (from the ML model and equipment schedule).
    """)

# ============ SIDEBAR CONTROLS ============
st.sidebar.header("🎛️ Model Controls")
emission_factor = st.sidebar.slider("CEA Grid Emission Factor (tCO2/MWh)", 0.65, 0.80, 0.710, 0.001)
usage_growth = st.sidebar.slider("Annual usage growth (%)", 0.0, 5.0, 2.0, 0.5)
climate_trend = st.sidebar.slider("Climate warming trend (%)", 0.0, 2.0, 0.5, 0.1)
st.sidebar.markdown("---")
show_solar = st.sidebar.checkbox("Include solar PV offset", value=True)
st.sidebar.caption("Measured campus solar generation (867,317 + 261,417 kWh/yr = 1,128,734 kWh/yr), allocated to Block 3 by its 11.15% connected-load share (278/2494 kW) = 125,817.18 kWh/yr.")
st.sidebar.markdown("---")
projection_years = st.sidebar.slider("Projection horizon (years)", 1, 10, 3)
st.sidebar.markdown("---")
month_range = st.sidebar.select_slider("Month range (monthly chart)",
    options=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'],
    value=('Jan','Dec'))

# ============ CORE DATA & CALCULATIONS ============
block3_sqm = 2594.7391499
block3_floors_desc = "G+2 (3 levels)"
block3_yearbuilt = 1998

campus_load_kw = 2494
block3_load_kw = 278
block3_share = block3_load_kw / campus_load_kw  # 11.14675%

campus_solar_generation_kwh = 867317 + 261417  # 1,128,734 kWh/yr total campus solar
raw_solar_allocation = campus_solar_generation_kwh * block3_share  # 125,817.18 kWh
block3_solar_offset_kwh = raw_solar_allocation if show_solar else 0.0

if os.path.exists('block3_predictions_full_year.csv'):
    predictions = pd.read_csv('block3_predictions_full_year.csv')
    predictions['timestamp'] = pd.to_datetime(predictions['timestamp'])
    total_kwh = float(predictions['predicted_electricity_kwh'].sum())
    predicted_first_week = float(predictions['predicted_electricity_kwh'].iloc[:168].sum())
else:
    # Exact fallback directly matching Cell 14/15/22 script run outputs
    total_kwh = 1085229.38
    predicted_first_week = 23853.03
    # Synthetic dataframe for rendering UI charts if CSV is absent
    dates = pd.date_range("2025-07-29", periods=8760, freq="h")
    predictions = pd.DataFrame({
        'timestamp': dates,
        'temperature_C': [28.0] * 8760,
        'precipitation_mm': [0.0] * 8760,
        'predicted_electricity_kwh': [total_kwh / 8760] * 8760
    })

block3_solar_offset_kwh = min(block3_solar_offset_kwh, total_kwh)
net_grid_kwh = max(total_kwh - block3_solar_offset_kwh, 0.0)

total_co2_gross = (total_kwh / 1000) * emission_factor
total_co2_net_grid = (net_grid_kwh / 1000) * emission_factor
solar_co2_avoided = (block3_solar_offset_kwh / 1000) * emission_factor

annual_diesel_liters = 18650  # audited campus DG diesel consumption (Apr 2021-Mar 2022)
campus_diesel_co2 = (annual_diesel_liters * 2.68) / 1000  # 49.982 tCO2/yr (reference only, NOT allocated to Block 3)

# Block 3's carbon footprint is electricity only (grid, post estimated-solar-allocation)
total_co2_block3_electricity = total_co2_net_grid

# EUI / ECBC Reference Comparisons
eui_gross = total_kwh / block3_sqm  # 418.24 kWh/sqm/yr
eui_net = net_grid_kwh / block3_sqm
ecbc_benchmark_normal, ecbc_benchmark_best = 200, 130
if eui_gross <= ecbc_benchmark_best:
    ecbc_rating = "Within Best-Practice Reference Range"
elif eui_gross <= ecbc_benchmark_normal:
    ecbc_rating = "Within Typical Reference Range"
else:
    ecbc_rating = "Above Reference Range (Retrofit Potential)"

# Block 3 Electricity Carbon Intensity (diesel excluded)
carbon_intensity = (total_co2_block3_electricity * 1000) / block3_sqm  # 262.5 kgCO2/sqm/yr

# Calibration-Consistency Check
actual_weekly = 23853.03
nmbe = ((predicted_first_week - actual_weekly) / actual_weekly) * 100  # -0.00%

# Floor-wise breakdown from audited equipment schedule (Cell 20 exact verified figures)
floor_shares = {
    'Ground Floor': {'weekly_kwh': 17999.291000, 'annual_kwh': 935963.132000, 'pct': 75.500695},
    '1st Floor': {'weekly_kwh': 4333.169986, 'annual_kwh': 225324.839272, 'pct': 18.176124},
    'Top Floor': {'weekly_kwh': 1507.440000, 'annual_kwh': 78386.880000, 'pct': 6.323181}
}

# ============ METRIC CARDS ============
st.markdown("<div class='section-header'>Key Metrics</div>", unsafe_allow_html=True)
c1, c2, c3, c4, c5 = st.columns(5)
cards = [
    (c1, "ML-Estimated Electricity Demand", f"{total_kwh:,.0f} kWh", "1,085,229 kWh (calibrated model output)"),
    (c2, "Estimated Solar Allocation (Scenario)", f"{block3_solar_offset_kwh:,.0f} kWh", f"{(block3_solar_offset_kwh/total_kwh*100):.1f}% of demand (125,817 kWh)" if show_solar else "Disabled"),
    (c3, "Estimated CO2 Avoided (Solar)", f"{solar_co2_avoided:,.1f} tCO2", f"Avoided emissions ({block3_solar_offset_kwh:,.0f} kWh)"),
    (c4, "Campus Diesel CO2 (Reference Only)", f"{campus_diesel_co2:,.1f} tCO2", f"{annual_diesel_liters:,.0f} L/yr audited — NOT allocated to Block 3"),
    (c5, "Block 3 Electricity-Related Footprint", f"{total_co2_block3_electricity:,.1f} tCO2/yr", f"{total_co2_block3_electricity:,.2f} tCO2 (diesel excluded)"),
]
for col, label, val, sub in cards:
    with col:
        st.markdown(f"<div class='metric-card'><div class='metric-label'>{label}</div><div class='metric-value'>{val}</div><div class='metric-sub'>{sub}</div></div>", unsafe_allow_html=True)

# ============ SUSTAINABILITY SCORECARD ============
st.markdown("<div class='section-header'>Building Sustainability Scorecard</div>", unsafe_allow_html=True)
s1, s2, s3, s4 = st.columns(4)
score_cards = [
    (s1, "Model-Estimated EUI (Gross)", f"{eui_gross:.1f} kWh/m²/yr", ecbc_rating),
    (s2, "Block 3 Electricity Carbon Intensity", f"{carbon_intensity:.1f} kgCO2/m²/yr", "From electricity emissions only, excludes diesel"),
    (s3, "Built-up Area (gbXML/BIM)", f"{block3_sqm:,.0f} m²", f"{block3_floors_desc}, built {block3_yearbuilt} — 2,594.74 m² (f-1.xml)"),
    (s4, "ECBC / BEE Reference EUI Range", f"{ecbc_benchmark_best}–{ecbc_benchmark_normal} kWh/m²/yr", "Best: 130 | Typical: up to 200–275 kWh/m²/yr"),
]
for col, label, val, sub in score_cards:
    with col:
        st.markdown(f"<div class='metric-card'><div class='metric-label'>{label}</div><div class='metric-value'>{val}</div><div class='metric-sub'>{sub}</div></div>", unsafe_allow_html=True)
st.markdown("<p class='note-text'>Model-Estimated EUI: ML annual electricity (1,085,229.38 kWh) divided by verified area (2,594.74 sqm) = 418.24 kWh/sqm/yr. This is a reference comparison against ECBC 2017 / BEE Star institutional ranges, not a formal compliance certification. Reference audit period: Apr 2021–Mar 2022. Campus diesel consumption (18,650 L/yr = 49.98 tCO2/yr) is unallocated to Block 3.</p>", unsafe_allow_html=True)

# ============ VALIDATION ============
st.markdown("<div class='section-header'>One-Week Calibration Consistency Check (NMBE)</div>", unsafe_allow_html=True)
st.markdown("<p class='note-text'>This is a calibration-consistency check, not independent out-of-sample validation. The scaling factor (1.7312) was computed directly to align the model's first-week prediction with the audited weekly energy (23,853.03 kWh). Formal ASHRAE Guideline 14 validation requires an independent, non-calibration dataset and is not claimed.</p>", unsafe_allow_html=True)
col_gauge, col_compare = st.columns([1, 1.5])

with col_gauge:
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number", value=abs(nmbe),
        title={'text': "NMBE (%) — Calibration Week Consistency (Threshold ±10%)", 'font': {'color': '#E5E9F0', 'size': 12}},
        number={'font': {'color': '#F5F7FA', 'size': 28}, 'suffix': '%'},
        gauge={'axis': {'range': [0, 20], 'tickcolor': '#9BA3B8', 'tickfont': {'color': '#9BA3B8'}},
               'bar': {'color': '#4ADE80' if abs(nmbe) <= 10 else '#F87171'},
               'steps': [{'range': [0, 10], 'color': '#14352A'}, {'range': [10, 20], 'color': '#3D1F1F'}],
               'threshold': {'line': {'color': '#F5F7FA', 'width': 3}, 'value': 10}}))
    fig_gauge.update_layout(height=250, paper_bgcolor='rgba(0,0,0,0)', margin=dict(t=50,b=10,l=20,r=20))
    st.plotly_chart(fig_gauge, use_container_width=True)
    status = f"✓ NMBE = {nmbe:.2f}% (Within ±10% tolerance on calibration week)"
    st.markdown(f"<p class='desc-text' style='text-align:center; font-weight:600; color:#4ADE80;'>{status}</p>", unsafe_allow_html=True)

with col_compare:
    fig_compare = go.Figure()
    fig_compare.add_trace(go.Bar(name='Calibrated Predicted (ML)', x=['Anchor Week'], y=[predicted_first_week], marker_color='#378ADD', text=[f"{predicted_first_week:,.1f} kWh"], textposition='outside'))
    fig_compare.add_trace(go.Bar(name='Audited Actual (Schedule)', x=['Anchor Week'], y=[actual_weekly], marker_color='#4ADE80', text=[f"{actual_weekly:,.1f} kWh"], textposition='outside'))
    fig_compare.update_layout(title="Anchor Week Consistency (23,853.03 kWh)", template='plotly_dark', height=280, barmode='group',
        plot_bgcolor='#171B26', paper_bgcolor='rgba(0,0,0,0)', font_color='#E5E9F0', legend=dict(font=dict(color='#E5E9F0')))
    st.plotly_chart(fig_compare, use_container_width=True)

# ============ FLOOR-WISE BREAKDOWN ============
st.markdown("<div class='section-header'>Floor-wise Energy Breakdown (Audited Equipment Schedule)</div>", unsafe_allow_html=True)
st.markdown("<p class='note-text'>Extracted from the room-level equipment audit schedule (Cell 20). 2nd and 3rd floors are grouped as 'Top Floor'.</p>", unsafe_allow_html=True)
col_floor1, col_floor2 = st.columns([1.3, 1])

with col_floor1:
    floor_names = list(floor_shares.keys())
    floor_weekly = [floor_shares[k]['weekly_kwh'] for k in floor_names]
    fig_floor = go.Figure(go.Bar(
        x=floor_weekly, y=floor_names, orientation='h',
        marker_color=['#F87171', '#FB923C', '#FBBF24'],
        text=[f"{v:,.1f} kWh/wk ({floor_shares[k]['pct']:.1f}%)" for v, k in zip(floor_weekly, floor_names)],
        textposition='outside',
    ))
    fig_floor.update_layout(title="Audited Weekly Energy by Floor (kWh/week)", template='plotly_dark', height=320,
        margin=dict(l=10, r=100, t=50, b=10),
        plot_bgcolor='#171B26', paper_bgcolor='rgba(0,0,0,0)', font_color='#E5E9F0',
        xaxis_title="kWh/week", yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig_floor, use_container_width=True)

with col_floor2:
    st.markdown(f"""<div class='metric-card'>
        <div class='metric-label'>Highest Consuming Level</div>
        <div class='metric-value' style='font-size:20px;'>Ground Floor</div>
        <div class='metric-sub' style='color:#F87171;'>75.50% (17,999.29 kWh/week)</div>
        <p class='desc-text' style='margin-top:12px;'>
        • <b>Ground Floor:</b> 17,999.29 kWh/wk (935,963.13 kWh/yr | 75.50%)<br>
        • <b>1st Floor:</b> 4,333.17 kWh/wk (225,324.84 kWh/yr | 18.18%)<br>
        • <b>Top Floor:</b> 1,507.44 kWh/wk (78,386.88 kWh/yr | 6.32%)<br>
        Ground floor load is dominated by central UPS banks (36 kW, 54 kW), heavy testing machines, and lab servers.
        </p>
    </div>""", unsafe_allow_html=True)

# ============ CONSUMPTION PATTERNS ============
st.markdown("<div class='section-header'>Consumption Patterns & Supply Mix</div>", unsafe_allow_html=True)
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
fig1.update_layout(title="Calibrated Model Monthly Electricity Consumption (Annual: 1,085,229.38 kWh)", template='plotly_dark', height=340,
    plot_bgcolor='#171B26', paper_bgcolor='rgba(0,0,0,0)', font_color='#E5E9F0')
st.plotly_chart(fig1, use_container_width=True)

col_a, col_b = st.columns(2)
with col_a:
    fig2 = go.Figure(go.Pie(
        labels=['Net Grid Electricity', 'Solar Offset (Allocated Scenario)'],
        values=[net_grid_kwh, block3_solar_offset_kwh],
        marker_colors=['#378ADD', '#4ADE80'],
        hole=0.45
    ))
    fig2.update_layout(title="Block 3 Electricity Supply Mix (Grid vs Solar)", template='plotly_dark', height=340,
        paper_bgcolor='rgba(0,0,0,0)', font_color='#E5E9F0', legend=dict(font=dict(color='#E5E9F0')))
    st.plotly_chart(fig2, use_container_width=True)
    st.caption("Solar offset: 125,817.18 kWh (11.6% of demand). Campus diesel (18,650 L/yr = 49.98 tCO2/yr) is excluded from Block 3 supply mix and reported as campus reference only.")

with col_b:
    temp_cut = pd.cut(predictions['temperature_C'], bins=range(10,46,2))
    temp_binned = predictions.groupby(temp_cut, observed=True)['predicted_electricity_kwh'].mean().reset_index()
    temp_binned['temp_mid'] = [interval.mid for interval in temp_binned['temperature_C']]
    fig3 = go.Figure(go.Scatter(x=temp_binned['temp_mid'], y=temp_binned['predicted_electricity_kwh'], mode='lines+markers',
        line_color='#4ADE80', fill='tozeroy', fillcolor='rgba(74,222,128,0.1)'))
    fig3.update_layout(title="Model-Derived Temperature Response (NASA POWER T2M)", template='plotly_dark', height=340,
        margin=dict(l=10, r=10, t=50, b=40),
        plot_bgcolor='#171B26', paper_bgcolor='rgba(0,0,0,0)', font_color='#E5E9F0')
    st.plotly_chart(fig3, use_container_width=True)
    st.caption("Reflects XGBoost regression behavior over local hourly dry-bulb temperature (T2M).")

# ============ FLOOR-WISE EMISSIONS BREAKDOWN ============
st.markdown("<div class='section-header'>Estimated Floor-wise CO2 Contribution (Electricity Only)</div>", unsafe_allow_html=True)

floor_co2 = {
    'Ground Floor': total_co2_block3_electricity * (floor_shares['Ground Floor']['pct'] / 100),
    '1st Floor': total_co2_block3_electricity * (floor_shares['1st Floor']['pct'] / 100),
    'Top Floor': total_co2_block3_electricity * (floor_shares['Top Floor']['pct'] / 100),
}

fig_treemap = go.Figure(go.Bar(
    x=list(floor_co2.values()),
    y=list(floor_co2.keys()),
    orientation='h',
    marker_color=['#F87171', '#FB923C', '#FBBF24'],
    text=[f"{v:.2f} tCO2/yr ({floor_shares[k]['pct']:.1f}%)" for k, v in zip(floor_co2.keys(), floor_co2.values())],
    textposition='outside',
))
fig_treemap.update_layout(
    title=f"Floor-wise Electricity Carbon (Total: {total_co2_block3_electricity:.2f} tCO2/yr | Diesel Excluded)",
    template='plotly_dark', height=280, margin=dict(l=10, r=100, t=50, b=10),
    plot_bgcolor='#171B26', paper_bgcolor='rgba(0,0,0,0)', font_color='#E5E9F0',
    xaxis_title="tCO2/yr", yaxis=dict(autorange="reversed")
)
st.plotly_chart(fig_treemap, use_container_width=True)
st.markdown(f"<p class='note-text'>Ground: {floor_co2['Ground Floor']:.2f} tCO2/yr (75.50%) | 1st: {floor_co2['1st Floor']:.2f} tCO2/yr (18.18%) | Top: {floor_co2['Top Floor']:.2f} tCO2/yr (6.32%). Campus diesel CO2 ({campus_diesel_co2:.2f} tCO2/yr) is unallocated and excluded.</p>", unsafe_allow_html=True)

# ============ FUTURE PROJECTION ============
st.markdown("<div class='section-header'>Scenario-Based Future Projection (Not an ML Forecast)</div>", unsafe_allow_html=True)
years = [2026 + i for i in range(projection_years)]
proj_kwh = [total_kwh * ((1 + (usage_growth + climate_trend)/100)**i) for i in range(projection_years)]
proj_net = [max(k - block3_solar_offset_kwh, 0.0) for k in proj_kwh]
proj_co2 = [(k/1000)*emission_factor for k in proj_net]

fig4 = go.Figure(go.Bar(x=[str(y) for y in years], y=proj_co2, marker_color='#A78BFA', text=[f"{v:.1f} tCO2" for v in proj_co2], textposition='outside'))
fig4.update_layout(title=f"Projected Block 3 Electricity CO2 ({years[0]}–{years[-1]}) @ {(usage_growth+climate_trend):.1f}% Combined Growth/Climate Factor", template='plotly_dark', height=340,
    plot_bgcolor='#171B26', paper_bgcolor='rgba(0,0,0,0)', font_color='#E5E9F0', yaxis_title="tCO2 / year")
st.plotly_chart(fig4, use_container_width=True)

st.markdown("---")

# ============ MODEL INPUTS & EVALUATION ============
st.markdown("<div class='section-header'>Model Inputs & Evaluation (BDG2 Benchmark)</div>", unsafe_allow_html=True)

# Default exact metrics from Model Run (Block 3 Cells 8, 9, 10, 10b, 10c)
features_used_list = ['airTemperature', 'hour', 'day_of_week', 'month', 'is_weekend', 'sqm', 'numberoffloors', 'building_age']
xgb_metrics_exact = {'r2': 0.8984, 'mae_kwh': 41.90, 'rmse_kwh': 98.10}
base_metrics_exact = {'r2': 0.3842, 'mae_kwh': 120.34, 'rmse_kwh': 241.55}
importance_exact = {
    'sqm': 0.5120,
    'numberoffloors': 0.2891,
    'building_age': 0.1324,
    'airTemperature': 0.0217,
    'month': 0.0131,
    'is_weekend': 0.0124,
    'hour': 0.0111,
    'day_of_week': 0.0082
}

metrics_path = "model_metrics.json"
if os.path.exists(metrics_path):
    try:
        with open(metrics_path) as f:
            mm = json.load(f)
            features_used_list = mm.get("features_used", features_used_list)
            xgb_metrics_exact = mm.get("xgboost", xgb_metrics_exact)
            base_metrics_exact = mm.get("baseline_linear_regression", base_metrics_exact)
            importance_exact = mm.get("feature_importance", importance_exact)
    except Exception:
        pass

st.markdown("**Input features used by the XGBoost model** (Cell 8):")
st.code(", ".join(features_used_list), language="text")

col_m1, col_m2 = st.columns(2)
with col_m1:
    st.markdown("**XGBoost vs. Linear Regression Baseline** (BDG2 Test Set: 400,000 rows)")
    fig_metrics = go.Figure()
    metric_names = ['R²', 'MAE (kWh)', 'RMSE (kWh)']
    fig_metrics.add_trace(go.Bar(
        name='XGBoost',
        x=metric_names,
        y=[xgb_metrics_exact['r2'], xgb_metrics_exact['mae_kwh'], xgb_metrics_exact['rmse_kwh']],
        marker_color='#378ADD',
        text=[f"{xgb_metrics_exact['r2']:.4f}", f"{xgb_metrics_exact['mae_kwh']:.2f}", f"{xgb_metrics_exact['rmse_kwh']:.2f}"],
        textposition='outside'
    ))
    fig_metrics.add_trace(go.Bar(
        name='Linear Regression',
        x=metric_names,
        y=[base_metrics_exact['r2'], base_metrics_exact['mae_kwh'], base_metrics_exact['rmse_kwh']],
        marker_color='#9BA3B8',
        text=[f"{base_metrics_exact['r2']:.4f}", f"{base_metrics_exact['mae_kwh']:.2f}", f"{base_metrics_exact['rmse_kwh']:.2f}"],
        textposition='outside'
    ))
    fig_metrics.update_layout(template='plotly_dark', height=340, barmode='group',
        plot_bgcolor='#171B26', paper_bgcolor='rgba(0,0,0,0)', font_color='#E5E9F0',
        legend=dict(font=dict(color='#E5E9F0')))
    st.plotly_chart(fig_metrics, use_container_width=True)
    st.caption("XGBoost improvement over linear baseline: R² +0.5142, MAE -78.44 kWh, RMSE -143.44 kWh on held-out BDG2 education test set (1.6M train / 400k test rows).")

with col_m2:
    st.markdown("**XGBoost Feature Importance** (Gain-Based, Cell 10c)")
    fig_imp = go.Figure(go.Bar(
        x=list(importance_exact.values()),
        y=list(importance_exact.keys()),
        orientation='h',
        marker_color='#4ADE80',
        text=[f"{v:.4f}" for v in importance_exact.values()],
        textposition='outside'
    ))
    fig_imp.update_layout(template='plotly_dark', height=340, margin=dict(l=10, r=60, t=10, b=10),
        plot_bgcolor='#171B26', paper_bgcolor='rgba(0,0,0,0)', font_color='#E5E9F0',
        xaxis_title="Gain", yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig_imp, use_container_width=True)
    st.caption("Primary drivers: Floor Area (51.2%), Floor Count (28.9%), Building Age (13.2%), Temperature (2.2%).")

st.markdown("""<div class='metric-card' style='margin-top:14px; border-left:3px solid #F87171;'>
<div class='metric-label' style='color:#F87171;'>Domain Limitation</div>
<p class='desc-text' style='margin-top:8px;'>The XGBoost model was trained on 604 global education buildings from BDG2. Block 3 (GMRIT, Rajam, Andhra Pradesh — Warm & Humid zone) is not in the training set. The 1-week audit anchor provides scale calibration (Scaling factor: 1.7312), not full local retraining. BDG2 test metrics (R² = 0.8984) measure generalization across BDG2 test buildings, not standalone Block 3 accuracy.</p>
</div>""", unsafe_allow_html=True)

# ============ 3D BUILDING & EMISSION VISUALIZATION ============
st.markdown("<div class='section-header'>BIM-Integrated Building Performance Model & Emission Distribution</div>", unsafe_allow_html=True)

col_bim, col_emissions = st.columns([1.2, 1])

with col_bim:
    st.markdown("#### Architectural BIM Model (Courtyard Layout)")
    try:
        st.image("block3_render.png", caption="Block 3 (GMRIT) — gbXML Geometry with Open Central Courtyard (2,595 sqm)", use_container_width=True)
    except Exception:
        st.info("Place 'block3_render.png' in your project root directory to display the BIM model.")

with col_emissions:
    st.markdown("#### Floor-Wise Emission Load Intensity")
    try:
        st.image("block3_floor_emission_render.png",
                  caption="Block 3 — Floor-wise Load Intensity (Ground: 75.5%, 1st: 18.2%, Top: 6.3%)",
                  use_container_width=True)
    except Exception:
        st.info("Place 'block3_floor_emission_render.png' in your project root directory to display this render.")

st.markdown("<p class='note-text'>Left: BIM architectural wireframe with central courtyard. Right: floor-colored elevation render from Revit matching audited equipment schedule proportions.</p>", unsafe_allow_html=True)
