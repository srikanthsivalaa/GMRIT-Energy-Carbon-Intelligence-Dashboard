import streamlit as st
import pandas as pd
import plotly.graph_objects as go

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
st.markdown("<span class='badge-info'>BDG2 Test R² = 0.898 (not Block 3 validation)</span><span class='badge-info'>Calibrated to 1-Week Audit Anchor</span><span class='badge-warn'>EUI: Retrofit Potential</span>", unsafe_allow_html=True)

# ============ DATA STATUS LEGEND ============
st.markdown("""<div class='metric-card' style='margin-bottom:18px;'>
<div class='metric-label' style='margin-bottom:8px;'>Data Status Legend</div>
<p class='desc-text' style='margin:0;'>
🟢 <b>Measured/Audited</b>: campus electricity, diesel, solar, Block 3 connected load, equipment inventory &nbsp;|&nbsp;
🔵 <b>ML-Derived</b>: annual/monthly electricity prediction, future projections &nbsp;|&nbsp;
🟠 <b>Estimated Allocation</b>: Block 3 solar share, floor-wise emissions &nbsp;|&nbsp;
⚪ <b>Assumption</b>: emission factors, operating hours, future growth rates
</p></div>""", unsafe_allow_html=True)

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
st.sidebar.caption("Measured campus solar generation (867,317 + 261,417 kWh/yr), allocated to Block 3 by its 11.15% connected-load share (estimated allocation — not separately metered).")
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
# NOTE: earlier version of this dashboard divided by 13 and multiplied by 12 assuming
# a 13-month reporting period. There is no audit evidence for a 13-month period -
# the audit explicitly covers 12 months (Apr 2021-Mar 2022). Fixed to use 18,650 L directly.
annual_diesel_liters = 18650  # audited campus DG diesel consumption, L/year
diesel_co2 = (annual_diesel_liters * 2.68) / 1000  # tCO2/year (assumption: 2.68 kg CO2/L diesel)
# kWh-equivalent of diesel generation, for the supply-mix chart only.
# ASSUMPTION: ~6.91 kWh electrical output per liter of diesel (needs verification against
# your genset spec sheet / audit - flag this to your guide before presenting).
diesel_kwh_per_liter_assumption = 6.91
annual_diesel_kwh = annual_diesel_liters * diesel_kwh_per_liter_assumption

total_co2_final = total_co2_net_grid + diesel_co2

# EUI / ECBC Benchmarks
eui_gross = total_kwh / block3_sqm
eui_net = net_grid_kwh / block3_sqm
ecbc_benchmark_normal, ecbc_benchmark_best = 200, 130
if eui_net <= ecbc_benchmark_best:
    ecbc_rating = "ECBC+ Compliant (Excellent)"
elif eui_net <= ecbc_benchmark_normal:
    ecbc_rating = "ECBC Compliant"
else:
    ecbc_rating = "Exceeds ECBC (HVAC/UPS Heavy)"

carbon_intensity = (total_co2_final * 1000) / block3_sqm  # kgCO2/sqm/yr

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
    (c2, "Estimated Solar Allocation", f"{block3_solar_offset_kwh:,.0f} kWh", f"{block3_solar_offset_kwh/total_kwh*100:.1f}% of estimated demand" if show_solar else "Disabled"),
    (c3, "Estimated CO2 Avoided (Solar)", f"{solar_co2_avoided:,.1f} tCO2", "Based on allocated solar share"),
    (c4, "Estimated Diesel CO2", f"{diesel_co2:,.1f} tCO2", f"{annual_diesel_liters:,.0f} L/yr — audited campus-level DG use"),
    (c5, "Estimated Annual Carbon Footprint", f"{total_co2_final:,.1f} tCO2/yr", "Net grid (post-solar) + diesel backup, model-derived"),
]
for col, label, val, sub in cards:
    with col:
        st.markdown(f"<div class='metric-card'><div class='metric-label'>{label}</div><div class='metric-value'>{val}</div><div class='metric-sub'>{sub}</div></div>", unsafe_allow_html=True)

# ============ SUSTAINABILITY SCORECARD ============
st.markdown("<div class='section-header'>Building Sustainability Scorecard</div>", unsafe_allow_html=True)
s1, s2, s3, s4 = st.columns(4)
score_cards = [
    (s1, "Net Electricity Use Intensity", f"{eui_net:.1f} kWh/m²/yr", ecbc_rating),
    (s2, "Estimated Carbon Intensity", f"{carbon_intensity:.1f} kgCO2/m²/yr", "Derived from estimated footprint"),
    (s3, "Built-up Area (gbXML/BIM)", f"{block3_sqm:,.0f} m²", f"{block3_floors_desc}, built {block3_yearbuilt} — verified from f-1.xml"),
    (s4, "ECBC / BEE Institutional Benchmark", f"{ecbc_benchmark_best}-{ecbc_benchmark_normal} kWh/m²/yr", "ECBC 2017 + BEE Star Rating, daytime institutional, Warm & Humid zone"),
]
for col, label, val, sub in score_cards:
    with col:
        st.markdown(f"<div class='metric-card'><div class='metric-label'>{label}</div><div class='metric-value'>{val}</div><div class='metric-sub'>{sub}</div></div>", unsafe_allow_html=True)
st.markdown("<p class='note-text'>Reference audit period: Apr 2021–Mar 2022 (East Coast Sustainable Pvt. Ltd., BEE-format audit). ECBC/BEE benchmark based on ECBC 2017 EPI standards for institutional daytime-use buildings, Warm & Humid climate; unoptimized baselines for comparable buildings typically run 200–275 kWh/m²/yr.</p>", unsafe_allow_html=True)

# ============ VALIDATION ============
st.markdown("<div class='section-header'>Model Calibration Check (NMBE)</div>", unsafe_allow_html=True)
st.markdown("<p class='note-text'>Note: the model's scaling factor was fit using this same one-week audited benchmark, so NMBE here reflects calibration consistency, not independent out-of-sample validation. Formal ASHRAE Guideline 14 compliance is not claimed — the metric is reported for transparency.</p>", unsafe_allow_html=True)
col_gauge, col_compare = st.columns([1, 1.5])

with col_gauge:
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number", value=abs(nmbe),
        title={'text': "NMBE (%) — threshold ±10%", 'font': {'color': '#E5E9F0', 'size': 13}},
        number={'font': {'color': '#F5F7FA', 'size': 28}, 'suffix': '%'},
        gauge={'axis': {'range': [0, 20], 'tickcolor': '#9BA3B8', 'tickfont': {'color': '#9BA3B8'}},
               'bar': {'color': '#4ADE80' if abs(nmbe) <= 10 else '#F87171'},
               'steps': [{'range': [0, 10], 'color': '#14352A'}, {'range': [10, 20], 'color': '#3D1F1F'}],
               'threshold': {'line': {'color': '#F5F7FA', 'width': 3}, 'value': 10}}))
    fig_gauge.update_layout(height=250, paper_bgcolor='rgba(0,0,0,0)', margin=dict(t=50,b=10,l=20,r=20))
    st.plotly_chart(fig_gauge, use_container_width=True)
    status = "✓ Within ±10% calibration-week tolerance" if abs(nmbe) <= 10 else "✗ Outside calibration-week tolerance"
    st.markdown(f"<p class='desc-text' style='text-align:center; font-weight:600; color:{'#4ADE80' if abs(nmbe)<=10 else '#F87171'};'>{status}</p>", unsafe_allow_html=True)

with col_compare:
    fig_compare = go.Figure()
    fig_compare.add_trace(go.Bar(name='Predicted (model)', x=['Weekly kWh'], y=[predicted_weekly], marker_color='#378ADD'))
    fig_compare.add_trace(go.Bar(name='Actual (audit)', x=['Weekly kWh'], y=[actual_weekly], marker_color='#4ADE80'))
    fig_compare.update_layout(title="Predicted vs Audited (1 Week Anchor)", template='plotly_dark', height=280, barmode='group',
        plot_bgcolor='#171B26', paper_bgcolor='rgba(0,0,0,0)', font_color='#E5E9F0', legend=dict(font=dict(color='#E5E9F0')))
    st.plotly_chart(fig_compare, use_container_width=True)

# ============ FLOOR-WISE BREAKDOWN ============
st.markdown("<div class='section-header'>Floor-wise Energy Distribution (Audit Calibrated)</div>", unsafe_allow_html=True)
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
    fig_floor.update_layout(title="Weekly Energy Consumption by Floor (kWh)", template='plotly_dark', height=320,
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
        labels=['Net Grid Electricity', 'Solar Offset', 'Diesel Generation'],
        values=[net_grid_kwh, block3_solar_offset_kwh, annual_diesel_kwh],
        marker_colors=['#378ADD', '#4ADE80', '#F87171'],
        hole=0.45
    ))
    fig2.update_layout(title="Energy Supply Mix (Total Building Demand)", template='plotly_dark', height=340,
        paper_bgcolor='rgba(0,0,0,0)', font_color='#E5E9F0', legend=dict(font=dict(color='#E5E9F0')))
    st.plotly_chart(fig2, use_container_width=True)

with col_b:
    temp_cut = pd.cut(predictions['temperature_C'], bins=range(10,46,2))
    temp_binned = predictions.groupby(temp_cut, observed=True)['predicted_electricity_kwh'].mean().reset_index()
    temp_binned['temp_mid'] = [interval.mid for interval in temp_binned['temperature_C']]
    fig3 = go.Figure(go.Scatter(x=temp_binned['temp_mid'], y=temp_binned['predicted_electricity_kwh'], mode='lines+markers',
        line_color='#4ADE80', fill='tozeroy', fillcolor='rgba(74,222,128,0.1)'))
    fig3.update_layout(title="Temperature Sensitivity (Model-Derived)", template='plotly_dark', height=340,
        margin=dict(l=10, r=10, t=50, b=40),
        plot_bgcolor='#171B26', paper_bgcolor='rgba(0,0,0,0)', font_color='#E5E9F0')
    st.plotly_chart(fig3, use_container_width=True)
    st.caption("Not measured Block 3 behavior — reflects the trained model's general temperature response.")

# ============ FLOOR-WISE EMISSIONS BREAKDOWN ============
st.markdown("<div class='section-header'>Floor-Wise CO2 Emissions Breakdown</div>", unsafe_allow_html=True)

floor_co2 = {
    'Ground Floor': total_co2_net_grid * floor_shares['Ground Floor'],
    '1st Floor': total_co2_net_grid * floor_shares['1st Floor'],
    'Top Floor': total_co2_net_grid * floor_shares['Top Floor'],
}

fig_treemap = go.Figure(go.Bar(
    x=list(floor_co2.values()),
    y=list(floor_co2.keys()),
    orientation='h',
    marker_color=['#F87171', '#FB923C', '#FBBF24'],
    text=[f"{v:.1f} tCO2/yr ({v/total_co2_net_grid*100:.0f}%)" for v in floor_co2.values()],
    textposition='outside',
))
fig_treemap.update_layout(
    title="Estimated CO2 Emissions by Floor (Grid Share Only)",
    template='plotly_dark', height=280, margin=dict(l=10, r=80, t=50, b=10),
    plot_bgcolor='#171B26', paper_bgcolor='rgba(0,0,0,0)', font_color='#E5E9F0',
    xaxis_title="tCO2/yr", yaxis=dict(autorange="reversed")
)
st.plotly_chart(fig_treemap, use_container_width=True)
st.markdown(f"<p class='note-text'>Total net footprint: {total_co2_final:,.1f} tCO2/yr. Floor split computed directly from the 'Floor Level' column in the audited room-level equipment schedule (626 rows), not inferred from the BIM model. Diesel CO2 is campus-level and not separately allocated by floor.</p>", unsafe_allow_html=True)

# ============ FUTURE PROJECTION ============
st.markdown("<div class='section-header'>Future Outlook (Dynamic Projections)</div>", unsafe_allow_html=True)
years = [2026 + i for i in range(projection_years)]
proj_kwh = [total_kwh * ((1 + (usage_growth + climate_trend)/100)**i) for i in range(projection_years)]
proj_net = [max(k - block3_solar_offset_kwh, 0.0) for k in proj_kwh]
proj_co2 = [(k/1000)*emission_factor + diesel_co2 for k in proj_net]

fig4 = go.Figure(go.Bar(x=[str(y) for y in years], y=proj_co2, marker_color='#A78BFA'))
fig4.update_layout(title=f"Projected Net Carbon Footprint — Scenario ({years[0]} – {years[-1]})", template='plotly_dark', height=340,
    plot_bgcolor='#171B26', paper_bgcolor='rgba(0,0,0,0)', font_color='#E5E9F0', yaxis_title="tCO2 / year")
st.plotly_chart(fig4, use_container_width=True)
st.markdown(f"<p class='note-text'>Scenario projection under assumed future usage growth ({usage_growth}%/yr) and climate trend ({climate_trend}%/yr), not a measured or guaranteed forecast. Audit baseline year: Apr 2021–Mar 2022. Weather data reference period differs from the audit year.</p>", unsafe_allow_html=True)

st.markdown("---")
st.markdown(f"<p class='desc-text'>Model: XGBoost (R²=0.898 on held-out BDG2 education-building test data; not a Block 3 validation metric), compared/calibrated against available GMRIT energy-audit data (NMBE={nmbe:.2f}% on the same one-week anchor used for calibration — a consistency check, not independent validation). Campus PV generation ({campus_solar_generation_kwh:,.0f} kWh/yr) is measured; the {block3_share*100:.2f}% Block 3 share is an estimated allocation based on connected-load share, since Block 3-specific solar metering was not available. Diesel: {annual_diesel_liters:,.0f} L/yr is the audited campus-level DG consumption (Apr 2021–Mar 2022); Block 3's share of this is not separately metered.</p>", unsafe_allow_html=True)




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
