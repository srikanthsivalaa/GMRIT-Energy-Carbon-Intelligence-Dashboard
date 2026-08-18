import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
import os

st.set_page_config(
    page_title="Block 3 Energy & Carbon Dashboard",
    layout="wide",
    page_icon="⚡",
    initial_sidebar_state="expanded"
)

# ============ STYLING ============
st.markdown("""
<style>
    .stApp { background-color: #0B0E14; }
    .metric-card { 
        background: linear-gradient(135deg, rgba(23, 27, 38, 0.8) 0%, rgba(31, 36, 51, 0.8) 100%); 
        border: 1px solid #2A3040; 
        border-radius: 12px; 
        padding: 16px; 
        box-shadow: 0 4px 20px rgba(0,0,0,0.25);
    }
    .metric-label { font-size: 11px; color: #9BA3B8; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; }
    .metric-value { font-size: clamp(16px, 3.5vw, 24px); font-weight: 700; color: #F5F7FA; margin-top: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .metric-sub { font-size: 11px; color: #4ADE80; margin-top: 4px; font-weight: 500; }
    .section-header { color: #E5E9F0; font-size: 14px; text-transform: uppercase; letter-spacing: 1.5px; margin-top: 14px; margin-bottom: 12px; font-weight: 700; border-left: 3px solid #378ADD; padding-left: 10px; }
    .desc-text { color: #C4CAD9 !important; font-size: 13.5px; line-height: 1.6; }
    .note-text { color: #8B93A8 !important; font-size: 12px; font-style: italic; }
    .badge-pass { background: #14352A; color: #4ADE80; padding: 4px 10px; border-radius: 16px; font-size: 12px; font-weight: 600; display: inline-block; margin-right: 6px; border: 1px solid #2A5A45;}
    .badge-info { background: #1A2A3D; color: #60A5FA; padding: 4px 10px; border-radius: 16px; font-size: 12px; font-weight: 600; display: inline-block; margin-right: 6px; border: 1px solid #2A4A6A;}
    .badge-warn { background: #3D1F1F; color: #F87171; padding: 4px 10px; border-radius: 16px; font-size: 12px; font-weight: 600; display: inline-block; margin-right: 6px; border: 1px solid #5A2A2A;}
    [data-testid="stSidebar"] { background-color: #12151F; }
    [data-testid="stSidebar"] * { color: #E5E9F0 !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #171B26;
        border-radius: 8px 8px 0px 0px;
        padding: 8px 20px;
        color: #9BA3B8;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #242B3D !important;
        color: #60A5FA !important;
        border-bottom: 2px solid #60A5FA !important;
    }
</style>
""", unsafe_allow_html=True)

# ============ HEADER ============
st.title("⚡ Block 3 — GMRIT Energy & Carbon Intelligence Dashboard")
st.markdown("<p class='desc-text'>ML framework for predicting electricity consumption and carbon footprint | XGBoost calibrated to available GMRIT energy-audit data</p>", unsafe_allow_html=True)
st.markdown("<span class='badge-info'>Held-out BDG2 Reference-Dataset R² = 0.898</span><span class='badge-info'>Calibrated to 1-Week Audit Anchor</span><span class='badge-warn'>EUI: Retrofit Potential</span>", unsafe_allow_html=True)

# ============ SIDEBAR CONTROLS ============
st.sidebar.header("🎛️ Model Controls")
emission_factor = st.sidebar.slider("CEA Grid Emission Factor (tCO2/MWh)", 0.65, 0.80, 0.710, 0.001)
usage_growth = st.sidebar.slider("Annual usage growth (%)", 0.0, 5.0, 2.0, 0.5)
climate_trend = st.sidebar.slider("Climate warming trend (%)", 0.0, 2.0, 0.5, 0.1)
st.sidebar.markdown("---")
show_solar = st.sidebar.checkbox("Include solar PV offset", value=True)
st.sidebar.caption("Estimated Block 3 Solar Allocation — based on 11.15% connected-load share; Block 3-specific solar metering unavailable.")
st.sidebar.markdown("---")
projection_years = st.sidebar.slider("Projection horizon (years)", 1, 10, 3)
st.sidebar.markdown("---")
month_range = st.sidebar.select_slider(
    "Month range (monthly chart)",
    options=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'],
    value=('Jan','Dec')
)

# ============ CORE CALCULATIONS (UNCHANGED) ============
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

annual_diesel_liters = 18650
campus_diesel_co2 = (annual_diesel_liters * 2.68) / 1000
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

carbon_intensity = (total_co2_block3_electricity * 1000) / block3_sqm

actual_weekly = 23853.03
predicted_weekly = predictions['predicted_electricity_kwh'].iloc[:168].sum()
nmbe = ((predicted_weekly - actual_weekly) / actual_weekly) * 100

floor_shares = {'Ground Floor': 0.75501, '1st Floor': 0.18176, 'Top Floor': 0.06323}

# ============ DYNAMIC EXECUTIVE SUMMARY BANNER ============
solar_pct = (block3_solar_offset_kwh / total_kwh) * 100 if total_kwh > 0 else 0
with st.container():
    st.markdown(f"""
    <div style='background: linear-gradient(90deg, #162438 0%, #1A1F2C 100%); border: 1px solid #2B4B70; border-radius: 12px; padding: 16px 20px; margin: 16px 0;'>
        <div style='font-size: 13px; color: #60A5FA; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px;'>
            🤖 Executive Intelligence Summary
        </div>
        <div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 14px; color: #D8DFEE; font-size: 13px;'>
            <div>⚡ <b>Demand & Sourcing:</b> Total ML demand is <b>{total_kwh:,.0f} kWh</b>. Solar offsets <b>{solar_pct:.1f}%</b> ({block3_solar_offset_kwh:,.0f} kWh), leaving <b>{net_grid_kwh:,.0f} kWh</b> on the grid.</div>
            <div>🌱 <b>Carbon Impact:</b> Solar saves <b>{solar_co2_avoided:,.1f} tCO₂/yr</b>. Net grid footprint is <b>{total_co2_block3_electricity:,.1f} tCO₂/yr</b> ({carbon_intensity:.1f} kgCO₂/m²).</div>
            <div>🏢 <b>Critical Load Hub:</b> Ground floor accounts for <b>75.5%</b> of weekly load ({actual_weekly * floor_shares['Ground Floor']:,.0f} kWh/wk) driven by central UPS banks.</div>
            <div>📊 <b>EUI Benchmark:</b> Building operates at <b>{eui_net:.1f} kWh/m²/yr</b> ({ecbc_rating}).</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ============ TABBED INTERFACE ============
tab_exec, tab_flow, tab_floor, tab_proj, tab_audit = st.tabs([
    "📊 Executive Summary",
    "🔀 Energy Flow (Sankey)",
    "🏢 Floor Breakdown",
    "📈 Forecast & Patterns",
    "📋 Audit & Methodology"
])

# ----------------- TAB 1: EXECUTIVE SUMMARY -----------------
with tab_exec:
    st.markdown("<div class='section-header'>Key Performance Indicators</div>", unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    cards = [
        (c1, "ML-Estimated Demand", f"{total_kwh:,.0f} kWh", "Annual model output"),
        (c2, "Solar Offset (Allocated)", f"{block3_solar_offset_kwh:,.0f} kWh", "11.15% load share" if show_solar else "Disabled"),
        (c3, "CO₂ Avoided (Solar)", f"{solar_co2_avoided:,.1f} tCO2", "Green energy savings"),
        (c4, "Campus DG Diesel Ref.", f"{campus_diesel_co2:,.1f} tCO2", f"{annual_diesel_liters:,.0f} L/yr (campus-wide)"),
        (c5, "Block 3 Carbon Footprint", f"{total_co2_block3_electricity:,.1f} tCO2/yr", "Net grid electricity"),
    ]
    for col, label, val, sub in cards:
        with col:
            st.markdown(f"<div class='metric-card'><div class='metric-label'>{label}</div><div class='metric-value'>{val}</div><div class='metric-sub'>{sub}</div></div>", unsafe_allow_html=True)

    st.markdown("<div class='section-header'>Building Sustainability Scorecard</div>", unsafe_allow_html=True)
    s1, s2, s3, s4, s5 = st.columns(5)
    score_cards = [
        (s1, "Gross Electricity EUI", f"{eui_gross:.1f} kWh/m²/yr", "Gross ML demand / area"),
        (s2, "Net Grid EUI (Post Solar)", f"{eui_net:.1f} kWh/m²/yr", ecbc_rating),
        (s3, "Electricity Carbon Intensity", f"{carbon_intensity:.1f} kgCO2/m²/yr", "Excludes campus diesel"),
        (s4, "Built-up Area (BIM)", f"{block3_sqm:,.0f} m²", f"{block3_floors_desc}, built {block3_yearbuilt}"),
        (s5, "ECBC Reference Range", f"{ecbc_benchmark_best}-{ecbc_benchmark_normal} kWh/m²/yr", "Warm & Humid daytime"),
    ]
    for col, label, val, sub in score_cards:
        with col:
            st.markdown(f"<div class='metric-card'><div class='metric-label'>{label}</div><div class='metric-value'>{val}</div><div class='metric-sub'>{sub}</div></div>", unsafe_allow_html=True)

    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
    col_pie, col_gauge = st.columns([1.2, 1])
    with col_pie:
        fig_pie = go.Figure(go.Pie(
            labels=['Net Grid Electricity', 'Solar Offset (Estimated)'],
            values=[net_grid_kwh, block3_solar_offset_kwh],
            hole=0.5,
            marker=dict(colors=['#378ADD', '#4ADE80'])
        ))
        fig_pie.update_layout(
            title="Estimated Energy Supply Mix",
            template='plotly_dark',
            height=300,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='#171B26',
            font_color='#E5E9F0',
            margin=dict(t=40, b=10, l=10, r=10)
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_gauge:
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number", value=abs(nmbe),
            title={'text': "NMBE (%) — Calibration Consistency (Target: ±10%)", 'font': {'color': '#E5E9F0', 'size': 12}},
            number={'font': {'color': '#F5F7FA', 'size': 26}, 'suffix': '%'},
            gauge={
                'axis': {'range': [0, 20], 'tickcolor': '#9BA3B8', 'tickfont': {'color': '#9BA3B8'}},
                'bar': {'color': '#4ADE80' if abs(nmbe) <= 10 else '#F87171'},
                'steps': [{'range': [0, 10], 'color': '#14352A'}, {'range': [10, 20], 'color': '#3D1F1F'}],
                'threshold': {'line': {'color': '#F5F7FA', 'width': 3}, 'value': 10}
            }
        ))
        fig_gauge.update_layout(height=300, paper_bgcolor='rgba(0,0,0,0)', margin=dict(t=50, b=10, l=20, r=20))
        st.plotly_chart(fig_gauge, use_container_width=True)

# ----------------- TAB 2: ENERGY FLOW (SANKEY) -----------------
with tab_flow:
    st.markdown("<div class='section-header'>Interactive Energy Flow Mapping</div>", unsafe_allow_html=True)
    st.markdown("<p class='desc-text'>Visualizing energy flow from generation sources into Block 3 demand and distribution across floor levels.</p>", unsafe_allow_html=True)
    
    # Calculate estimated annual floor allocations based on audited floor shares
    kwh_ground = total_kwh * floor_shares['Ground Floor']
    kwh_first = total_kwh * floor_shares['1st Floor']
    kwh_top = total_kwh * floor_shares['Top Floor']

    # Node setup: [0: Grid, 1: Solar, 2: Block 3 Total, 3: Ground Floor, 4: 1st Floor, 5: Top Floor]
    sankey_nodes = [
        "Grid Electricity",                         # 0
        "Solar PV Offset (Allocated)",              # 1
        "Block 3 Total Demand",                     # 2
        f"Ground Floor (75.5%)",                    # 3
        f"1st Floor (18.2%)",                       # 4
        f"Top Floor (6.3%)"                         # 5
    ]
    
    fig_sankey = go.Figure(go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="#2A3040", width=0.5),
            label=sankey_nodes,
            color=["#378ADD", "#4ADE80", "#818CF8", "#F87171", "#FB923C", "#FBBF24"]
        ),
        link=dict(
            source=[0, 1, 2, 2, 2],
            target=[2, 2, 3, 4, 5],
            value=[net_grid_kwh, block3_solar_offset_kwh, kwh_ground, kwh_first, kwh_top],
            color=[
                "rgba(55, 138, 221, 0.4)",
                "rgba(74, 222, 128, 0.4)",
                "rgba(248, 113, 113, 0.4)",
                "rgba(251, 146, 60, 0.4)",
                "rgba(251, 191, 36, 0.4)"
            ]
        )
    ))
    fig_sankey.update_layout(
        template='plotly_dark',
        height=450,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='#171B26',
        font=dict(color='#E5E9F0', size=12),
        margin=dict(t=20, b=20, l=10, r=10)
    )
    st.plotly_chart(fig_sankey, use_container_width=True)

# ----------------- TAB 3: FLOOR BREAKDOWN -----------------
with tab_floor:
    st.markdown("<div class='section-header'>Estimated Floor-Wise Distribution</div>", unsafe_allow_html=True)
    col_floor1, col_floor2 = st.columns([1.3, 1])

    with col_floor1:
        floor_names = list(floor_shares.keys())
        floor_weekly = [actual_weekly * s for s in floor_shares.values()]
        fig_floor = go.Figure(go.Bar(
            x=floor_weekly, y=floor_names, orientation='h',
            marker_color=['#F87171', '#FB923C', '#FBBF24'],
            text=[f"{v:,.0f} kWh/wk" for v in floor_weekly],
            textposition='outside',
        ))
        fig_floor.update_layout(
            title="Estimated Weekly Electricity Contribution by Floor (kWh)", 
            template='plotly_dark', 
            height=320,
            margin=dict(l=10, r=70, t=50, b=10),
            plot_bgcolor='#171B26', 
            paper_bgcolor='rgba(0,0,0,0)', 
            font_color='#E5E9F0',
            xaxis_title="kWh/week", 
            yaxis=dict(autorange="reversed")
        )
        st.plotly_chart(fig_floor, use_container_width=True)

    with col_floor2:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-label'>Highest Consuming Level</div>
            <div class='metric-value' style='font-size:20px;'>Ground Floor</div>
            <div class='metric-sub' style='color:#F87171;'>75.5% of Total Load (Equipment Schedule)</div>
            <p class='desc-text' style='margin-top:12px;'>Derived from the 626-row audited equipment schedule. Primary drivers:</p>
            <ul class='desc-text' style='margin:0; padding-left: 20px;'>
                <li>Central UPS banks (36 kW, 54 kW continuous draw)</li>
                <li>Substation step-down transformers</li>
                <li>Electrical Machines & Power Systems lab motors</li>
            </ul>
        </div>""", unsafe_allow_html=True)

# ----------------- TAB 4: FORECAST & PATTERNS -----------------
with tab_proj:
    st.markdown("<div class='section-header'>Temporal Patterns & Growth Forecast</div>", unsafe_allow_html=True)
    
    # Monthly Consumption Filter
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

    fig_month = go.Figure(go.Bar(x=monthly_filtered['month'], y=monthly_filtered['predicted_electricity_kwh'], marker_color='#378ADD'))
    fig_month.update_layout(
        title="Model-Estimated Monthly Electricity Consumption (kWh)", 
        template='plotly_dark', 
        height=320,
        plot_bgcolor='#171B26', 
        paper_bgcolor='rgba(0,0,0,0)', 
        font_color='#E5E9F0',
        margin=dict(t=40, b=10, l=10, r=10)
    )
    st.plotly_chart(fig_month, use_container_width=True)

    # Multi-Year Projection
    years_proj = [f"+{i} Yr{'s' if i > 1 else ''}" for i in range(1, projection_years + 1)]
    growth_multiplier = (1 + (usage_growth + climate_trend) / 100)
    projected_kwh = [total_kwh * (growth_multiplier ** i) for i in range(1, projection_years + 1)]

    fig_proj = go.Figure(go.Bar(x=years_proj, y=projected_kwh, marker_color='#60A5FA', text=[f"{v/1000:,.1f} MWh" for v in projected_kwh], textposition='auto'))
    fig_proj.update_layout(
        title=f"{projection_years}-Year Growth & Climate Projection (Usage: +{usage_growth}%, Climate: +{climate_trend}%)",
        template='plotly_dark',
        height=320,
        plot_bgcolor='#171B26',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='#E5E9F0',
        margin=dict(t=40, b=10, l=10, r=10)
    )
    st.plotly_chart(fig_proj, use_container_width=True)

# ----------------- TAB 5: AUDIT & METHODOLOGY -----------------
with tab_audit:
    st.markdown("<div class='section-header'>Data Status Legend & Temporal Scope</div>", unsafe_allow_html=True)
    st.markdown("""<div class='metric-card' style='margin-bottom:14px;'>
    <div class='metric-label' style='margin-bottom:6px;'>Data Provenance Matrix</div>
    <p class='desc-text' style='margin:0;'>
    🟢 <b>Measured/Audited</b>: Campus electricity, diesel, solar, Block 3 connected load, equipment inventory<br>
    🔵 <b>ML-Derived</b>: Annual & monthly electricity predictions (XGBoost on NASA POWER weather)<br>
    🟠 <b>Estimated Allocation</b>: Block 3 solar share (11.15%), floor-wise contribution<br>
    ⚪ <b>Assumption/Scenario</b>: CEA emission factor (0.710), operating hours, future growth trends
    </p></div>""", unsafe_allow_html=True)

    st.markdown("""<div class='metric-card' style='margin-bottom:14px; border-left:3px solid #FBBF24;'>
    <div class='metric-label' style='color:#FBBF24;'>Temporal Scope Alignment</div>
    <p class='desc-text' style='margin-top:6px;'>
    The audit baseline (connected load, diesel, solar) reflects <b>Apr 2021–Mar 2022</b>. Weather data driving ML predictions is from <b>Jul 2025–Jul 2026</b> (NASA POWER). Block 3 electricity demand represents a <b>calibrated scenario estimate</b>, not an empirical reconstruction of 2021–2022 consumption.
    </p></div>""", unsafe_allow_html=True)

    col_val1, col_val2 = st.columns([1, 1])
    with col_val1:
        fig_compare = go.Figure()
        fig_compare.add_trace(go.Bar(name='Predicted (Model)', x=['Weekly kWh'], y=[predicted_weekly], marker_color='#378ADD'))
        fig_compare.add_trace(go.Bar(name='Actual (Audit Anchor)', x=['Weekly kWh'], y=[actual_weekly], marker_color='#4ADE80'))
        fig_compare.update_layout(
            title="Predicted vs Audited (1-Week Anchor)", 
            template='plotly_dark', 
            height=260, 
            barmode='group',
            plot_bgcolor='#171B26', 
            paper_bgcolor='rgba(0,0,0,0)', 
            font_color='#E5E9F0'
        )
        st.plotly_chart(fig_compare, use_container_width=True)
        
    with col_val2:
        with st.expander("📋 Methodology Note — kVAh vs kWh & Campus Envelope", expanded=True):
            st.markdown("""
            - **Campus Audit Envelope:** 1,524,486 kVAh/yr (Apr 2021–Mar 2022) measured campus-wide utility total.
            - **Power Factor:** Average ≈ 0.99, meaning kVAh ≈ kWh within ~1%.
            - **Calibration Anchor:** XGBoost model scaled against a single-week audited baseline (23,853.03 kWh/wk).
            - **Connected Load Share:** Block 3 represents 278 kW of 2,494 kW campus capacity (11.15%).
            """)
