import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
import os

st.set_page_config(
    page_title="Block 3 Energy & Carbon Intelligence Dashboard",
    layout="wide",
    page_icon="⚡",
    initial_sidebar_state="expanded"
)

# ============ STYLING ============
st.markdown("""
<style>
    .stApp { background-color: #0B0E14; }
    .metric-card { 
        background: linear-gradient(135deg, rgba(23, 27, 38, 0.85) 0%, rgba(31, 36, 51, 0.85) 100%); 
        border: 1px solid #2A3040; 
        border-radius: 12px; 
        padding: 16px; 
        box-shadow: 0 4px 20px rgba(0,0,0,0.25);
    }
    .metric-label { font-size: 11px; color: #9BA3B8; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; }
    .metric-value { font-size: clamp(16px, 3.2vw, 24px); font-weight: 700; color: #F5F7FA; margin-top: 5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .metric-sub { font-size: 11px; color: #4ADE80; margin-top: 4px; font-weight: 500; }
    .section-header { color: #E5E9F0; font-size: 14px; text-transform: uppercase; letter-spacing: 1.5px; margin-top: 18px; margin-bottom: 12px; font-weight: 700; border-left: 3px solid #378ADD; padding-left: 10px; }
    .desc-text { color: #C4CAD9 !important; font-size: 13.5px; line-height: 1.6; }
    .note-text { color: #8B93A8 !important; font-size: 12px; font-style: italic; }
    .badge-pass { background: #14352A; color: #4ADE80; padding: 5px 12px; border-radius: 16px; font-size: 12px; font-weight: 600; display: inline-block; margin-right: 6px; border: 1px solid #2A5A45;}
    .badge-info { background: #1A2A3D; color: #60A5FA; padding: 5px 12px; border-radius: 16px; font-size: 12px; font-weight: 600; display: inline-block; margin-right: 6px; border: 1px solid #2A4A6A;}
    .badge-warn { background: #3D1F1F; color: #F87171; padding: 5px 12px; border-radius: 16px; font-size: 12px; font-weight: 600; display: inline-block; margin-right: 6px; border: 1px solid #5A2A2A;}
    h1, h2, h3, h4 { color: #F5F7FA !important; }
    [data-testid="stSidebar"] { background-color: #12151F; }
    [data-testid="stSidebar"] * { color: #E5E9F0 !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #171B26;
        border-radius: 8px 8px 0px 0px;
        padding: 8px 18px;
        color: #9BA3B8;
        font-weight: 600;
        font-size: 13px;
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
st.markdown("<span class='badge-info'>Held-out BDG2 Reference-Dataset R² = 0.898 (NOT Block 3 validation)</span><span class='badge-info'>Calibrated to Campus Annual Audit (11.15% Block 3 share)</span><span class='badge-info'>EUI benchmarked vs ECBC reference</span>", unsafe_allow_html=True)

# ============ SIDEBAR CONTROLS ============
st.sidebar.header("🎛️ Model Controls")
emission_factor = st.sidebar.slider("CEA Grid Emission Factor (tCO2/MWh)", 0.65, 0.80, 0.710, 0.001)
usage_growth = st.sidebar.slider("Annual usage growth (%)", 0.0, 5.0, 2.0, 0.5)
climate_trend = st.sidebar.slider("Climate warming trend (%)", 0.0, 2.0, 0.5, 0.1)
st.sidebar.markdown("---")
show_solar = st.sidebar.checkbox("Include solar PV offset", value=True)
st.sidebar.caption("Estimated Block 3 Solar Allocation — based on 11.15% connected-load share; Block 3-specific solar metering unavailable. Campus solar used on site (867,317 generated − 261,417 exported = 605,900 kWh/yr) is from the audit; the Block 3 share is a scenario allocation, not a measured Block 3 quantity.")
st.sidebar.markdown("---")
projection_years = st.sidebar.slider("Projection horizon (years)", 1, 10, 3)
st.sidebar.markdown("---")
month_range = st.sidebar.select_slider(
    "Month range (monthly chart)",
    options=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'],
    value=('Jan','Dec')
)

# ============ CORE DATA & CALCULATIONS ============
predictions = pd.read_csv('block3_predictions_full_year.csv')
predictions['timestamp'] = pd.to_datetime(predictions['timestamp'])

block3_sqm = 2594.7391499
block3_floors_desc = "G+2 (3 levels)"
block3_yearbuilt = 1998

campus_load_kw = 2494
block3_load_kw = 278
block3_share = block3_load_kw / campus_load_kw  # 11.15%

campus_solar_generated_kwh = 867317
campus_solar_exported_kwh = 261417
campus_solar_used_kwh = campus_solar_generated_kwh - campus_solar_exported_kwh  # 605,900 kWh/yr used on campus
block3_solar_offset_kwh = (campus_solar_used_kwh * block3_share) if show_solar else 0.0

total_kwh = predictions['predicted_electricity_kwh'].sum()
block3_solar_offset_kwh = min(block3_solar_offset_kwh, total_kwh)
net_grid_kwh = max(total_kwh - block3_solar_offset_kwh, 0.0)

total_co2_gross = (total_kwh / 1000) * emission_factor
total_co2_net_grid = (net_grid_kwh / 1000) * emission_factor
solar_co2_avoided = (block3_solar_offset_kwh / 1000) * emission_factor

annual_diesel_liters = 18650  # audited campus DG diesel consumption, L/year
campus_diesel_co2 = (annual_diesel_liters * 2.68) / 1000  # tCO2/year (assumption: 2.68 kg CO2/L diesel)
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

carbon_intensity = (total_co2_block3_electricity * 1000) / block3_sqm  # kgCO2/sqm/yr

# Calibration Metrics (annual campus-share anchor)
CAMPUS_ANNUAL_KWH = 1524486  # audit, Apr 2021-Mar 2022 (kVAh ~ kWh, PF ~0.99)
ANNUAL_ANCHOR_KWH = CAMPUS_ANNUAL_KWH * block3_share  # Block 3 share of campus annual consumption
EQUIP_SCHEDULE_WEEKLY = 23839.90  # nameplate x scheduled hours; used ONLY for the floor-wise split
avg_weekly_kwh = total_kwh / (len(predictions) / 168)
nmbe = ((total_kwh - ANNUAL_ANCHOR_KWH) / ANNUAL_ANCHOR_KWH) * 100  # ~0 by construction


floor_shares = {'Ground Floor': 0.75501, '1st Floor': 0.18176, 'Top Floor': 0.06323}


# Calibration factor and first-week view
SCALING_FACTOR = 0.271081  # raw XGBoost -> annual anchor
calibrated_week = predictions['predicted_electricity_kwh'].iloc[:168].reset_index(drop=True)
raw_week = calibrated_week / SCALING_FACTOR
hours_axis = list(range(168))
raw_weekly_total = raw_week.sum()
calibrated_weekly_total = calibrated_week.sum()
raw_annual_kwh = total_kwh / SCALING_FACTOR
diff_before_pct = ((raw_annual_kwh - ANNUAL_ANCHOR_KWH) / ANNUAL_ANCHOR_KWH) * 100
diff_after_pct = nmbe


# ============ EXECUTIVE SUMMARY BANNER ============
solar_pct = (block3_solar_offset_kwh / total_kwh) * 100 if total_kwh > 0 else 0
with st.container():
    st.markdown(f"""
    <div style='background: linear-gradient(90deg, #162438 0%, #1A1F2C 100%); border: 1px solid #2B4B70; border-radius: 12px; padding: 14px 18px; margin: 16px 0 20px 0;'>
        <div style='font-size: 12px; color: #60A5FA; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px;'>
            🤖 Executive Summary & High-Level Insights
        </div>
        <div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; color: #D8DFEE; font-size: 13px;'>
            <div>⚡ <b>Energy Sourcing:</b> Total ML demand is <b>{total_kwh:,.0f} kWh</b>. Solar offsets <b>{solar_pct:.1f}%</b> ({block3_solar_offset_kwh:,.0f} kWh), leaving <b>{net_grid_kwh:,.0f} kWh</b> on grid.</div>
            <div>🌱 <b>Carbon Footprint:</b> Solar avoids <b>{solar_co2_avoided:,.1f} tCO₂/yr</b>. Electricity emissions stand at <b>{total_co2_block3_electricity:,.1f} tCO₂/yr</b> ({carbon_intensity:.1f} kgCO₂/m²).</div>
            <div>🏢 <b>Primary Load Node:</b> Ground Floor accounts for <b>75.5%</b> of weekly load ({avg_weekly_kwh * floor_shares['Ground Floor']:,.0f} kWh/wk) driven by central UPS banks.</div>
            <div>📊 <b>Building Index:</b> Net Grid EUI is <b>{eui_net:.1f} kWh/m²/yr</b> ({ecbc_rating}).</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ============ TABBED INTERFACE ============
tab_exec, tab_bim, tab_flow, tab_floor, tab_proj, tab_calib, tab_audit = st.tabs([
    "📊 Executive Summary",
    "🏗️ 3D BIM Architecture",
    "🔀 Energy Flow (Sankey)",
    "🏢 Floor Breakdown & Carbon",
    "📈 Forecast & Patterns",
    "🔍 Calibration Analysis",
    "📋 Audit, ML & Retrofits"
])

# ----------------- TAB 1: EXECUTIVE SUMMARY -----------------
with tab_exec:
    st.markdown("<div class='section-header'>Key Metrics</div>", unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    cards = [
        (c1, "ML-Estimated Demand", f"{total_kwh:,.0f} kWh", "Model output, not a meter reading"),
        (c2, "Solar Offset (Allocated)", f"{block3_solar_offset_kwh:,.0f} kWh", "11.15% load share" if show_solar else "Disabled"),
        (c3, "CO₂ Avoided (Solar)", f"{solar_co2_avoided:,.1f} tCO2", "Allocated solar share (assumption)"),
        (c4, "Campus DG Diesel Ref.", f"{campus_diesel_co2:,.1f} tCO2", f"{annual_diesel_liters:,.0f} L/yr audited campus-level"),
        (c5, "Electricity Carbon Footprint", f"{total_co2_block3_electricity:,.1f} tCO2/yr", "Net grid (post-solar allocation)"),
    ]
    for col, label, val, sub in cards:
        with col:
            st.markdown(f"<div class='metric-card'><div class='metric-label'>{label}</div><div class='metric-value'>{val}</div><div class='metric-sub'>{sub}</div></div>", unsafe_allow_html=True)

    st.markdown("<div class='section-header'>Building Sustainability Scorecard</div>", unsafe_allow_html=True)
    s1, s2, s3, s4, s5 = st.columns(5)
    score_cards = [
        (s1, "Gross Electricity EUI", f"{eui_gross:.1f} kWh/m²/yr", "Before solar (ML demand / area)"),
        (s2, "Net Grid EUI post Solar", f"{eui_net:.1f} kWh/m²/yr", ecbc_rating),
        (s3, "Electricity Carbon Intensity", f"{carbon_intensity:.1f} kgCO2/m²/yr", "From Block 3 electricity only"),
        (s4, "Built-up Area (gbXML/BIM)", f"{block3_sqm:,.0f} m²", f"{block3_floors_desc}, built {block3_yearbuilt}"),
        (s5, "ECBC / BEE Ref. Range", f"{ecbc_benchmark_best}-{ecbc_benchmark_normal} kWh/m²/yr", "Warm & Humid daytime institutional"),
    ]
    for col, label, val, sub in score_cards:
        with col:
            st.markdown(f"<div class='metric-card'><div class='metric-label'>{label}</div><div class='metric-value'>{val}</div><div class='metric-sub'>{sub}</div></div>", unsafe_allow_html=True)

    st.markdown("<p class='note-text'>Both EUI figures use ML-derived annual electricity divided by verified built-up area. This is a Reference EUI Comparison against ECBC/BEE ranges, not a formal ECBC compliance certification.</p>", unsafe_allow_html=True)

    col_pie, col_gauge = st.columns([1.2, 1])
    with col_pie:
        fig2 = go.Figure(go.Pie(
            labels=['Net Grid Electricity', 'Solar Offset (Estimated Allocation)'],
            values=[net_grid_kwh, block3_solar_offset_kwh],
            marker_colors=['#378ADD', '#4ADE80'],
            hole=0.45
        ))
        fig2.update_layout(
            title="Electricity Supply Mix (Grid vs Solar, Block 3 Estimate)",
            template='plotly_dark', height=310,
            paper_bgcolor='rgba(0,0,0,0)', font_color='#E5E9F0', legend=dict(font=dict(color='#E5E9F0')),
            margin=dict(t=40, b=10, l=10, r=10)
        )
        st.plotly_chart(fig2, use_container_width=True)
        st.caption("Diesel is excluded here: diesel-to-kWh conversion factor was not verified against genset specs. Diesel is reported separately in audited litres and CO2 only.")

    with col_gauge:
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number", value=abs(nmbe),
            title={'text': "NMBE (%) — Annual Calibration Consistency (Threshold ±10%)", 'font': {'color': '#E5E9F0', 'size': 12}},
            number={'font': {'color': '#F5F7FA', 'size': 26}, 'suffix': '%'},
            gauge={
                'axis': {'range': [0, 20], 'tickcolor': '#9BA3B8', 'tickfont': {'color': '#9BA3B8'}},
                'bar': {'color': '#4ADE80' if abs(nmbe) <= 10 else '#F87171'},
                'steps': [{'range': [0, 10], 'color': '#14352A'}, {'range': [10, 20], 'color': '#3D1F1F'}],
                'threshold': {'line': {'color': '#F5F7FA', 'width': 3}, 'value': 10}
            }
        ))
        fig_gauge.update_layout(height=310, paper_bgcolor='rgba(0,0,0,0)', margin=dict(t=50, b=10, l=20, r=20))
        st.plotly_chart(fig_gauge, use_container_width=True)
        status = "✓ Within ±10% annual calibration consistency band" if abs(nmbe) <= 10 else "✗ Outside annual calibration consistency band"
        st.markdown(f"<p class='desc-text' style='text-align:center; font-weight:600; color:{'#4ADE80' if abs(nmbe)<=10 else '#F87171'};'>{status}</p>", unsafe_allow_html=True)

# ----------------- TAB 2: 3D BIM ARCHITECTURE -----------------
with tab_bim:
    st.markdown("<div class='section-header'>BIM Architecture & Level-by-Level Cutaways</div>", unsafe_allow_html=True)
    st.markdown("<p class='desc-text'>Interactive Revit BIM architectural front-view representations linked directly to the room-level equipment schedule and load shares.</p>", unsafe_allow_html=True)

    floor_views = {
        "Full Building (Front View)": {
            "img": "total block front view.jpeg",
            "share": "100% of Building Demand",
            "weekly_energy": f"{avg_weekly_kwh:,.0f} kWh/wk",
            "description": "Reinforced concrete institutional frame (G+2 levels with open central courtyard), 2,594.7 m² built-up area built in 1998."
        },
        "Ground Floor Cut (Front View)": {
            "img": "ground floor cut front view.jpeg",
            "share": "75.5% of Total Load",
            "weekly_energy": f"{avg_weekly_kwh * floor_shares['Ground Floor']:,.0f} kWh/wk",
            "description": "High-draw zone containing Central UPS banks (36 kW, 54 kW continuous draw), substation step-down transformers, and Electrical Machines / Power Systems lab motors."
        },
        "1st Floor Cut (Front View)": {
            "img": "first floor cut front view.jpeg",
            "share": "18.2% of Total Load",
            "weekly_energy": f"{avg_weekly_kwh * floor_shares['1st Floor']:,.0f} kWh/wk",
            "description": "Mid-draw academic zone featuring computer labs, departmental lecture classrooms, and faculty rooms."
        },
        "2nd / Top Floor Cut (Front View)": {
            "img": "2nd floor cut front view.jpeg",
            "share": "6.3% of Total Load",
            "weekly_energy": f"{avg_weekly_kwh * floor_shares['Top Floor']:,.0f} kWh/wk",
            "description": "Low-draw zone housing seminar halls, department library, and rooftop solar electrical tie-ins."
        }
    }

    selected_level = st.radio(
        "Select Revit Cut Section / Level to Inspect:",
        options=list(floor_views.keys()),
        horizontal=True
    )

    col_view, col_meta = st.columns([1.6, 1])
    with col_view:
        view_data = floor_views[selected_level]
        if os.path.exists(view_data["img"]):
            st.image(view_data["img"], caption=f"Revit BIM Model — {selected_level}", use_container_width=True)
        else:
            st.warning(f"Image `{view_data['img']}` not found in repository root. Please ensure the file is present in the GitHub repository.")

    with col_meta:
        st.markdown(f"""
        <div class='metric-card' style='margin-bottom: 12px;'>
            <div class='metric-label'>Floor Consumption Share</div>
            <div class='metric-value' style='color:#60A5FA; font-size:20px;'>{view_data['share']}</div>
            <div class='metric-sub'>{view_data['weekly_energy']}</div>
        </div>
        <div class='metric-card'>
            <div class='metric-label'>Architectural & Functional Profile</div>
            <p class='desc-text' style='margin-top: 8px;'>{view_data['description']}</p>
        </div>
        """, unsafe_allow_html=True)

# ----------------- TAB 3: ENERGY FLOW (SANKEY) -----------------
with tab_flow:
    st.markdown("<div class='section-header'>Interactive Energy Flow Mapping</div>", unsafe_allow_html=True)
    st.markdown("<p class='desc-text'>Visualizing energy flow from generation sources into Block 3 demand and distribution across floor levels.</p>", unsafe_allow_html=True)

    kwh_ground = total_kwh * floor_shares['Ground Floor']
    kwh_first = total_kwh * floor_shares['1st Floor']
    kwh_top = total_kwh * floor_shares['Top Floor']

    sankey_nodes = [
        "Grid Electricity",
        "Solar PV Offset (Allocated)",
        "Block 3 Total Demand",
        "Ground Floor (75.5%)",
        "1st Floor (18.2%)",
        "Top Floor (6.3%)"
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
        height=420,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='#171B26',
        font=dict(color='#E5E9F0', size=12),
        margin=dict(t=20, b=20, l=10, r=10)
    )
    st.plotly_chart(fig_sankey, use_container_width=True)

# ----------------- TAB 4: FLOOR BREAKDOWN & EMISSIONS -----------------
with tab_floor:
    st.markdown("<div class='section-header'>Estimated Floor-wise Electricity Contribution</div>", unsafe_allow_html=True)
    st.markdown("<p class='note-text'>Derived from the audited equipment schedule and its operating-hour assumptions, not from floor-level electricity meters.</p>", unsafe_allow_html=True)
    col_floor1, col_floor2 = st.columns([1.3, 1])

    with col_floor1:
        floor_names = list(floor_shares.keys())
        floor_weekly = [avg_weekly_kwh * s for s in floor_shares.values()]
        fig_floor = go.Figure(go.Bar(
            x=floor_weekly, y=floor_names, orientation='h',
            marker_color=['#F87171', '#FB923C', '#FBBF24'],
            text=[f"{v:,.0f} kWh" for v in floor_weekly],
            textposition='outside',
        ))
        fig_floor.update_layout(
            title="Estimated Weekly Electricity Contribution by Floor (kWh)",
            template='plotly_dark', height=300,
            margin=dict(l=10, r=70, t=50, b=10),
            plot_bgcolor='#171B26', paper_bgcolor='rgba(0,0,0,0)', font_color='#E5E9F0',
            xaxis_title="kWh/week", yaxis=dict(autorange="reversed")
        )
        st.plotly_chart(fig_floor, use_container_width=True)

    with col_floor2:
        st.markdown("""<div class='metric-card'>
            <div class='metric-label'>Highest Consuming Level</div>
            <div class='metric-value' style='font-size:20px;'>Ground Floor</div>
            <div class='metric-sub' style='color:#F87171;'>75.5% of Total Load (from equipment schedule)</div>
            <p class='desc-text' style='margin-top:12px;'>Floor split is read directly from the 'Floor Level' column of the audited room-level equipment schedule (not a BIM-inferred assignment). Major ground-floor loads: Central UPS banks (36 kW, 54 kW), substation transformers, and Electrical Machines/Power Systems lab motors.</p>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div class='section-header'>Estimated Floor-wise Carbon Allocation (Electricity Only)</div>", unsafe_allow_html=True)
    floor_co2 = {
        'Ground Floor': total_co2_block3_electricity * floor_shares['Ground Floor'],
        '1st Floor': total_co2_block3_electricity * floor_shares['1st Floor'],
        'Top Floor': total_co2_block3_electricity * floor_shares['Top Floor'],
    }

    fig_co2_bar = go.Figure(go.Bar(
        x=list(floor_co2.values()),
        y=list(floor_co2.keys()),
        orientation='h',
        marker_color=['#F87171', '#FB923C', '#FBBF24'],
        text=[f"{v:.1f} tCO2/yr ({v/total_co2_block3_electricity*100:.0f}%)" for v in floor_co2.values()],
        textposition='outside',
    ))
    fig_co2_bar.update_layout(
        title="Estimated Floor-wise Carbon Allocation (Block 3 Electricity Only, Diesel Excluded)",
        template='plotly_dark', height=260, margin=dict(l=10, r=80, t=50, b=10),
        plot_bgcolor='#171B26', paper_bgcolor='rgba(0,0,0,0)', font_color='#E5E9F0',
        xaxis_title="tCO2/yr", yaxis=dict(autorange="reversed")
    )
    st.plotly_chart(fig_co2_bar, use_container_width=True)
    st.markdown(f"<p class='note-text'>Total Block 3 electricity-related footprint: {total_co2_block3_electricity:,.1f} tCO2/yr. Floor split computed directly from the 'Floor Level' column in the audited room-level equipment schedule (626 rows) and operating-hour assumptions, not inferred from the BIM model. Campus diesel CO2 ({campus_diesel_co2:,.1f} tCO2/yr) is excluded from this figure and from the floor split, since it cannot be defensibly allocated to Block 3 or to individual floors.</p>", unsafe_allow_html=True)

# ----------------- TAB 5: FORECAST & PATTERNS -----------------
with tab_proj:
    st.markdown("<div class='section-header'>Consumption Patterns & Temperature Response</div>", unsafe_allow_html=True)
    
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

    col_pat1, col_pat2 = st.columns(2)
    with col_pat1:
        fig1 = go.Figure(go.Bar(x=monthly_filtered['month'], y=monthly_filtered['predicted_electricity_kwh'], marker_color='#378ADD'))
        fig1.update_layout(title="Model-Estimated Monthly Electricity Consumption (kWh)", template='plotly_dark', height=320,
            plot_bgcolor='#171B26', paper_bgcolor='rgba(0,0,0,0)', font_color='#E5E9F0')
        st.plotly_chart(fig1, use_container_width=True)

    with col_pat2:
        temp_cut = pd.cut(predictions['temperature_C'], bins=range(10,46,2))
        temp_binned = predictions.groupby(temp_cut, observed=True)['predicted_electricity_kwh'].mean().reset_index()
        temp_binned['temp_mid'] = [interval.mid for interval in temp_binned['temperature_C']]
        fig3 = go.Figure(go.Scatter(x=temp_binned['temp_mid'], y=temp_binned['predicted_electricity_kwh'], mode='lines+markers',
            line_color='#4ADE80', fill='tozeroy', fillcolor='rgba(74,222,128,0.1)'))
        fig3.update_layout(title="Model-Derived Temperature Response", template='plotly_dark', height=320,
            margin=dict(l=10, r=10, t=50, b=40),
            plot_bgcolor='#171B26', paper_bgcolor='rgba(0,0,0,0)', font_color='#E5E9F0')
        st.plotly_chart(fig3, use_container_width=True)
        st.caption("Not measured Block 3 behavior — reflects the trained model's general temperature response.")

    st.markdown("<div class='section-header'>Scenario-Based Future Projection (Not an ML Forecast)</div>", unsafe_allow_html=True)
    st.markdown("<p class='note-text'>This is a what-if scenario computed from assumed growth/climate-trend rates applied to the ML-estimated base year - it is not a model forecast or prediction of future years.</p>", unsafe_allow_html=True)
    
    years = [2026 + i for i in range(projection_years)]
    proj_kwh = [total_kwh * ((1 + (usage_growth + climate_trend)/100)**i) for i in range(projection_years)]
    proj_net = [max(k - block3_solar_offset_kwh, 0.0) for k in proj_kwh]
    proj_co2 = [(k/1000)*emission_factor for k in proj_net]

    fig4 = go.Figure(go.Bar(x=[str(y) for y in years], y=proj_co2, marker_color='#A78BFA'))
    fig4.update_layout(title=f"Scenario-Based Projected Block 3 Electricity CO2 ({years[0]} – {years[-1]})", template='plotly_dark', height=320,
        plot_bgcolor='#171B26', paper_bgcolor='rgba(0,0,0,0)', font_color='#E5E9F0', yaxis_title="tCO2 / year")
    st.plotly_chart(fig4, use_container_width=True)
    st.markdown(f"<p class='note-text'>Scenario projection under assumed future usage growth ({usage_growth}%/yr) and climate trend ({climate_trend}%/yr), not a measured or guaranteed forecast. Excludes diesel (campus-level, held constant, not projected here). Audit baseline year: Apr 2021–Mar 2022. Weather data reference period differs from the audit year.</p>", unsafe_allow_html=True)

# ----------------- TAB 6: CALIBRATION ANALYSIS -----------------
with tab_calib:
    st.markdown("<div class='section-header'>Annual Calibration Analysis — Campus-Share Anchor</div>", unsafe_allow_html=True)
    st.info("**Important:** The model output is scaled so its annual total equals Block 3's share (11.15%) of the audited campus consumption. The match is therefore true by construction — a consistency check, not independent validation.")

    fig_1wk = go.Figure()
    fig_1wk.add_trace(go.Scatter(
        x=hours_axis, y=raw_week, mode='lines', name='Raw XGBoost (ML-derived, pre-calibration)',
        line=dict(color='#9BA3B8', width=1.5, dash='dot')
    ))
    fig_1wk.add_trace(go.Scatter(
        x=hours_axis, y=calibrated_week, mode='lines', name='Calibrated XGBoost (calibrated ML estimate)',
        line=dict(color='#378ADD', width=2)
    ))
    fig_1wk.update_layout(
        title="Hourly Raw vs Calibrated Prediction — First Week of Weather Data",
        template='plotly_dark', height=360,
        margin=dict(l=10, r=10, t=50, b=40),
        plot_bgcolor='#171B26', paper_bgcolor='rgba(0,0,0,0)', font_color='#E5E9F0',
        xaxis_title="Hour of week (0-167)", yaxis_title="kWh", legend=dict(font=dict(color='#E5E9F0'))
    )
    st.plotly_chart(fig_1wk, use_container_width=True)

    st.markdown(f"""<div class='metric-card' style='margin-top:4px;'>
    <div class='metric-label'>Audit-Share Annual Anchor (Estimated Allocation)</div>
    <div class='metric-value' style='font-size:24px;'>{ANNUAL_ANCHOR_KWH:,.0f} kWh</div>
    <div class='metric-sub'>Campus consumption {CAMPUS_ANNUAL_KWH:,.0f} kWh × {block3_share*100:.2f}% Block 3 connected-load share. This is an allocation, not a Block 3 meter reading.</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("<p style='margin-top:14px; margin-bottom:8px;' class='desc-text'><b>Summary Metrics</b></p>", unsafe_allow_html=True)
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(f"<div class='metric-card'><div class='metric-label'>Audit-Share Annual Anchor</div><div class='metric-value' style='font-size:20px;'>{ANNUAL_ANCHOR_KWH:,.0f} kWh</div></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-card' style='margin-top:8px;'><div class='metric-label'>Raw ML Annual Total (pre-calibration)</div><div class='metric-value' style='font-size:20px;'>{raw_annual_kwh:,.0f} kWh</div></div>", unsafe_allow_html=True)
    with m2:
        st.markdown(f"<div class='metric-card'><div class='metric-label'>Calibrated ML Annual Total</div><div class='metric-value' style='font-size:20px;'>{total_kwh:,.0f} kWh</div></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-card' style='margin-top:8px;'><div class='metric-label'>Calibration Factor</div><div class='metric-value' style='font-size:20px;'>{SCALING_FACTOR}</div></div>", unsafe_allow_html=True)
    with m3:
        st.markdown(f"<div class='metric-card'><div class='metric-label'>Difference Before Calibration</div><div class='metric-value' style='font-size:20px;'>{diff_before_pct:+.2f}%</div></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-card' style='margin-top:8px;'><div class='metric-label'>Difference After Calibration (NMBE)</div><div class='metric-value' style='font-size:20px;'>{diff_after_pct:+.2f}%</div></div>", unsafe_allow_html=True)

    st.markdown(f"""<div class='metric-card' style='margin-top:14px; border-left:3px solid #FBBF24;'>
    <div class='metric-label' style='color:#FBBF24;'>Why the equipment schedule is not the calibration target</div>
    <p class='desc-text' style='margin-top:6px;'>The audited equipment schedule (rated power × scheduled hours) totals {EQUIP_SCHEDULE_WEEKLY:,.2f} kWh/week, about {EQUIP_SCHEDULE_WEEKLY*52:,.0f} kWh/year, which would be {EQUIP_SCHEDULE_WEEKLY*52/CAMPUS_ANNUAL_KWH*100:.0f}% of the entire campus consumption. It assumes equipment runs at rated power for all scheduled hours, so it overstates real energy use. It is used only for the floor-wise shares.</p>
    </div>""", unsafe_allow_html=True)

    st.caption("CV(RMSE) is not reported: there is no measured Block 3 hourly or monthly electricity series to pair with the predictions, so it cannot be correctly calculated and is not fabricated here.")
    st.markdown("<p class='note-text' style='margin-top:10px;'>The calibrated annual total equals the audit-share anchor because the model was scaled to it. This demonstrates calibration consistency, not independent model validation. Absolute values depend on the 11.15% load-share assumption and carry roughly ±10% uncertainty from the campus audit figures.</p>", unsafe_allow_html=True)

# ----------------- TAB 7: AUDIT, ML & RETROFITS -----------------
with tab_audit:
    st.markdown("""<div class='metric-card' style='margin-bottom:14px;'>
    <div class='metric-label' style='margin-bottom:6px;'>Data Status Legend</div>
    <p class='desc-text' style='margin:0;'>
    🟢 <b>Measured/Audited</b>: campus electricity, diesel, solar, Block 3 connected load, equipment inventory &nbsp;|&nbsp;
    🔵 <b>ML-Derived</b>: annual/monthly electricity prediction &nbsp;|&nbsp;
    🟠 <b>Estimated Allocation</b>: Block 3 solar share, floor-wise contribution/emissions &nbsp;|&nbsp;
    ⚪ <b>Assumption/Scenario</b>: emission factors, operating hours, future growth/climate-trend rates, future projections
    </p></div>""", unsafe_allow_html=True)

    st.markdown("""<div class='metric-card' style='margin-bottom:14px; border-left:3px solid #FBBF24;'>
    <div class='metric-label' style='color:#FBBF24;'>Temporal Scope Note</div>
    <p class='desc-text' style='margin-top:6px;'>The audit baseline (connected load, diesel, solar generation) is <b>Apr 2021–Mar 2022</b>.
    The weather dataset used to drive the ML model is <b>Jul 2025–Jul 2026</b> (NASA POWER, local coordinates).
    These are different periods. The annual Block 3 electricity figure on this dashboard is therefore a
    <b>calibrated scenario estimate</b> — the model's weather-driven pattern for a recent year, rescaled to match
    Block 3's share of the audited campus annual energy — and should not be read as a reconstruction of actual Apr 2021–Mar 2022
    Block 3 consumption.</p>
    </div>""", unsafe_allow_html=True)

    with st.expander("📋 Methodology & Data Provenance — read before presenting", expanded=False):
        st.markdown("""
**How is Block 3's annual electricity (~170 MWh) derived, and how does it relate to the campus audit total (1,524,486 kVAh/yr)?**

- The campus audit figure (1,524,486 kVAh/yr, Apr 2021–Mar 2022) is a **measured utility bill total** for the entire campus, across all blocks, hostels, and staff quarters.
- **Block 3 annual anchor = campus total × 11.15%** (Block 3's connected-load share: 278 kW of 2,494 kW) ≈ 169,931 kWh. This is an **allocation**, not a Block 3 meter reading.
- An XGBoost model trained on BDG2 (604 education buildings, US-based archetypes) supplies the **hourly and seasonal shape** from Block 3's weather and physical attributes. A single scaling factor (0.271) sets the annual total equal to the anchor.
- The connected-load share describes **peak connected capacity**, not energy consumed. If Block 3 runs more hours than other blocks its true share could be higher; totals scale linearly with the share (for example 15% would give about 229 MWh). The campus source figures also differ by about 10% (grid + solar used + diesel = 1.67M vs 1.52M kWh reported), so treat the anchor as roughly ±10%.
- The audited equipment schedule (23,840 kWh/week, rated power × scheduled hours) would imply Block 3 uses about 81% of campus energy, so it overstates real use and is used **only for the floor-wise split**.

**Units — kVAh vs kWh**

The audit reports campus electricity in kVAh, not kWh. Per the audit, average campus power factor ≈ 0.99, so kVAh ≈ kWh at this site to within ~1%. All Block 3 figures in this dashboard are computed and reported directly in kWh.
        """)

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
        st.info("model_metrics.json not found in repository root. Run block3_model_training.py (Cells 10-10d) to generate it.")
    else:
        st.markdown("**Input features used by the XGBoost model:**")
        st.code(", ".join(model_metrics["features_used"]), language="text")

        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.markdown("**XGBoost vs. Linear Regression baseline** (BDG2 held-out test set)")
            xgb_m, base_m = model_metrics["xgboost"], model_metrics["baseline_linear_regression"]
            fig_metrics = go.Figure()
            metric_names = ['R²', 'MAE (kWh)', 'RMSE (kWh)']
            fig_metrics.add_trace(go.Bar(name='XGBoost', x=metric_names,
                y=[xgb_m['r2'], xgb_m['mae_kwh'], xgb_m['rmse_kwh']], marker_color='#378ADD'))
            fig_metrics.add_trace(go.Bar(name='Linear Regression (baseline)', x=metric_names,
                y=[base_m['r2'], base_m['mae_kwh'], base_m['rmse_kwh']], marker_color='#9BA3B8'))
            fig_metrics.update_layout(template='plotly_dark', height=260, barmode='group',
                plot_bgcolor='#171B26', paper_bgcolor='rgba(0,0,0,0)', font_color='#E5E9F0',
                legend=dict(font=dict(color='#E5E9F0')))
            st.plotly_chart(fig_metrics, use_container_width=True)

        with col_m2:
            st.markdown("**XGBoost feature importance** (gain-based)")
            importances = model_metrics["feature_importance"]
            fig_imp = go.Figure(go.Bar(
                x=list(importances.values()), y=list(importances.keys()), orientation='h',
                marker_color='#4ADE80'
            ))
            fig_imp.update_layout(template='plotly_dark', height=260, margin=dict(l=10, r=20, t=10, b=10),
                plot_bgcolor='#171B26', paper_bgcolor='rgba(0,0,0,0)', font_color='#E5E9F0',
                yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_imp, use_container_width=True)

    st.markdown("""<div class='metric-card' style='margin-top:14px; border-left:3px solid #F87171;'>
    <div class='metric-label' style='color:#F87171;'>Domain Limitation</div>
    <p class='desc-text' style='margin-top:8px;'>The XGBoost model is trained entirely on the BDG2 dataset (604 education buildings, predominantly North American/European campuses). Block 3 (GMRIT, Rajam - Warm & Humid climate) is <b>not represented in the training data</b>. The campus annual audit share (11.15% of 1,524,486 kWh) is used only to <i>calibrate</i> output magnitude. BDG2 performance (R²=0.898) reflects generalization across BDG2 buildings, not direct Block 3 out-of-sample accuracy.</p>
    </div>""", unsafe_allow_html=True)

    st.markdown("""<div class='metric-card' style='margin-top:14px; border-left:3px solid #F87171;'>
    <div class='metric-label' style='color:#F87171;'>Data Boundary & Limitations</div>
    <p class='desc-text' style='margin-top:8px;'>
    No Block 3-specific electricity meter series, solar generation meter, or diesel generator (DG) meter was available for this project. All Block 3-level figures are produced by ML predictions or allocation methods. <b>Independent building-level validation of Block 3's electricity, solar, or diesel figures is not claimed.</b>
    </p>
    </div>""", unsafe_allow_html=True)

    st.markdown("<div class='section-header'>Recommended Energy-Saving Measures</div>", unsafe_allow_html=True)
    r1, r2 = st.columns(2)
    with r1:
        st.markdown("""<div class='metric-card' style='height:100%;'>
        <div class='metric-label'>🟢 Audited Retrofit — BLDC Ceiling Fan Replacement</div>
        <div class='metric-value' style='font-size:20px;'>67,904 kWh/yr</div>
        <div class='metric-sub'>Estimated savings, campus-wide</div>
        <p class='desc-text' style='margin-top:10px;'>Replacing standard induction ceiling fans with BLDC fans (East Coast Sustainable Pvt. Ltd., Apr 2022). Low unit cost, no operational cost increase, typically &lt;2 year payback at scale.</p>
        </div>""", unsafe_allow_html=True)

    with r2:
        st.markdown("""<div class='metric-card' style='height:100%;'>
        <div class='metric-label'>🟢 Audited Retrofit — SV-to-LED Lighting Replacement</div>
        <div class='metric-value' style='font-size:20px;'>1,976 kWh/yr</div>
        <div class='metric-sub'>Estimated savings, campus-wide</div>
        <p class='desc-text' style='margin-top:10px;'>Replacing sodium-vapor/CFL fixtures with LED, same campus audit source. Zero recurring cost once installed, immediate effect, no scheduling or behavioral dependency.</p>
        </div>""", unsafe_allow_html=True)

    st.markdown("""<div class='metric-card' style='margin-top:14px;'>
    <div class='metric-label'>⚪ No-Cost Operational Measures (Derived from Equipment Schedule)</div>
    <ul class='desc-text' style='margin-top:8px;'>
    <li><b>UPS standby/float-charge audit (Ground Floor):</b> Ground Floor carries 75.5% of Block 3's estimated load, dominated by continuous-duty UPS banks (36 kW, 54 kW). A physical audit of which UPS loads genuinely require 24/7 uptime versus which could be scheduled off during nights/holidays targets the largest load driver.</li>
    <li><b>Lab/classroom equipment power-down enforcement:</b> Enforcing an equipment shutdown checklist after scheduled lab/class hours prevents after-hours idle draw.</li>
    <li><b>Fan/lighting operating-hour review in low-occupancy spaces:</b> Regular checks that spaces like Electrical Labs and Drawing Halls (scheduled ~8 hrs/week) are powered off when idle.</li>
    </ul>
    </div>""", unsafe_allow_html=True)
