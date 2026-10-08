import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
import os

st.set_page_config(
    page_title="Block 3 Energy Intelligence",
    layout="wide",
    page_icon="⚡",
    initial_sidebar_state="expanded"
)

# ============ DESIGN TOKENS ============
PAPER = "#ECEBE6"      # concrete / drafting paper
INK = "#1B2421"        # primary text
INK2 = "#4A5753"       # secondary text
INK3 = "#5A6561"       # tertiary text (>= 4.5:1 on paper)
RULE = "#C9C8C0"       # hairlines
GRID = "#D9D8D1"       # chart gridlines
GREEN = "#1F4E45"      # oxidised-copper dark: building / primary data
GREEN2 = "#5E8F84"
GREEN3 = "#A9C4BC"
SOLAR = "#C98A1B"      # solar amber: only ever means solar or caution
STEEL = "#5B6B73"      # grid electricity
BRICK = "#A5442F"      # warnings / limitations
FONT = "Public Sans, Helvetica Neue, Arial, sans-serif"

# ============ STYLING ============
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@75..125,300..700&family=Public+Sans:wght@400;500;600&display=swap');

:root {
  --paper:#ECEBE6; --ink:#1B2421; --ink2:#4A5753; --ink3:#5A6561; --rule:#C9C8C0;
  --green:#1F4E45; --solar:#C98A1B; --brick:#A5442F; --steel:#5B6B73;
}
.stApp { background: var(--paper); color: var(--ink); font-family: 'Public Sans', 'Helvetica Neue', Arial, sans-serif; font-size: 13px; line-height: 1.5; }
header[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer { visibility: hidden; }
.block-container, [data-testid="stMainBlockContainer"] {
    max-width: 1200px !important;
    margin: 0 auto;
    padding: 1.5rem 2rem 3rem 2rem;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    justify-content: center;
}
.stApp p, .stApp li, .stApp label, .stApp span { color: var(--ink); font-size: 13px; }

/* ---- sidebar ---- */
[data-testid="stSidebar"] { background: #E1DFD8; border-right: 1px solid var(--rule); }
[data-testid="stSidebar"][aria-expanded="true"] { width: 268px !important; min-width: 268px !important; max-width: 268px !important; }
[data-testid="stSidebar"] h2 { font-family: 'Archivo', sans-serif; font-weight: 600; font-size: 16px; letter-spacing: 0; }
[data-testid="stSidebar"] hr { border-color: var(--rule); margin: 12px 0; }
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] { color: var(--ink3); font-size: 10px; }

/* ---- masthead ---- */
.masthead-title { font-family: 'Archivo', sans-serif; font-stretch: 85%; font-weight: 600; font-size: 24px; letter-spacing: -0.01em; line-height: 1.15; color: var(--ink); }
.masthead-sub { margin-top: 4px; color: var(--ink2); font-size: 13px; max-width: 72ch; line-height: 1.45; }

/* ---- tabs: text only, one underline ---- */
.stTabs [data-baseweb="tab-list"] { gap: 24px; border-bottom: 1px solid var(--rule); margin-top: 16px; }
.stTabs [data-baseweb="tab"] { background: transparent; padding: 8px 0; height: auto; color: var(--ink2); font-size: 13px; font-weight: 500; }
.stTabs [aria-selected="true"] { color: var(--ink) !important; font-weight: 600; }
.stTabs [data-baseweb="tab-highlight"] { background: var(--green) !important; height: 2px; }
.stTabs [data-baseweb="tab-border"] { display: none; }
.stTabs [data-baseweb="tab-panel"] { padding-top: 16px; }

/* ---- hero numbers ---- */
.hero { display: grid; grid-template-columns: repeat(3, 1fr); gap: 32px; margin: 36px 0 28px 0; align-items: baseline; }
.hero-num { font-family: 'Archivo', sans-serif; font-stretch: 80%; font-weight: 300; font-size: 42px; line-height: 1.0; letter-spacing: -0.02em; font-variant-numeric: tabular-nums; color: var(--ink); white-space: nowrap; }
.hero-num.lead { font-size: 44px; color: var(--green); }
.hero-unit { font-family: 'Public Sans', sans-serif; font-stretch: 100%; font-size: 16px; font-weight: 400; letter-spacing: 0; color: var(--ink2); margin-left: 6px; }
.hero-label { margin-top: 8px; font-size: 13px; font-weight: 600; color: var(--ink); line-height: 1.2; }
.hero-note { margin-top: 4px; font-size: 10.5px; line-height: 1.4; color: var(--ink3); max-width: 32ch; }

/* ---- section titles ---- */
.sec { font-family: 'Archivo', sans-serif; font-stretch: 90%; font-weight: 600; font-size: 16px; letter-spacing: -0.005em; margin: 24px 0 4px 0; color: var(--ink); }
.sec.first { margin-top: 12px; }
.sec-sub { color: var(--ink2); font-size: 12px; line-height: 1.45; max-width: 72ch; margin-bottom: 12px; }
.fig-title { font-size: 13px; font-weight: 600; color: var(--ink); margin: 12px 0 2px 0; }
.fig-sub { font-size: 11px; color: var(--ink3); margin-bottom: 4px; }

/* ---- prose and notes ---- */
.prose2 { display: grid; grid-template-columns: 1fr 1fr; gap: 32px; margin: 14px 0 0 0; }
.prose2 p { font-size: 13px; line-height: 1.55; color: var(--ink); margin: 0 0 8px 0; max-width: 62ch; }
.prose2 b { font-weight: 600; }
.note { font-size: 10.5px; line-height: 1.45; color: var(--ink3); margin: 6px 0 0 0; max-width: 120ch; }
.body { font-size: 13px; line-height: 1.55; color: var(--ink); max-width: 64ch; }

/* ---- ledger: label left, value right, hairline rows ---- */
.group-title { font-size: 13px; font-weight: 600; margin: 0 0 4px 0; color: var(--ink); }
.ledger { display: grid; grid-template-columns: 1fr auto; column-gap: 20px; }
.ledger .k { padding: 10px 0; border-bottom: 1px solid var(--rule); font-size: 12.5px; color: var(--ink2); line-height: 1.3; }
.ledger .k small { display: block; font-size: 10.5px; color: var(--ink3); margin-top: 1px; }
.ledger .v { padding: 10px 0; border-bottom: 1px solid var(--rule); font-size: 13px; font-weight: 600; color: var(--ink); text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; line-height: 1.3; }
.ledger-cols { display: grid; grid-template-columns: 1fr 1fr; gap: 32px; margin-top: 8px; }
.ledger-cols.three { grid-template-columns: 1fr 1fr 1fr; gap: 24px; }

/* ---- caveats: the only place a rule line is used on a block ---- */
.caveat { border-left: 3px solid var(--solar); padding: 2px 0 2px 12px; margin: 16px 0; max-width: 120ch; }
.caveat.brick { border-left-color: var(--brick); }
.caveat-title { font-size: 13px; font-weight: 600; color: var(--ink); margin-bottom: 2px; }
.caveat-body { font-size: 12px; line-height: 1.5; color: var(--ink2); }

/* ---- big stat (BIM / retrofits) ---- */
.stat-num { font-family: 'Archivo', sans-serif; font-stretch: 85%; font-weight: 300; font-size: 38px; letter-spacing: -0.02em; line-height: 1.05; color: var(--green); font-variant-numeric: tabular-nums; }
.stat-sub { font-size: 12.5px; color: var(--ink2); margin-top: 4px; }
.legend-row { display: flex; flex-wrap: wrap; gap: 8px 24px; font-size: 12px; color: var(--ink); margin: 4px 0 10px 0; }
.sw { display: inline-block; width: 10px; height: 10px; margin-right: 6px; vertical-align: -1px; }

/* ---- widgets ---- */
.stRadio [data-testid="stWidgetLabel"] p { font-size: 13px; font-weight: 600; color: var(--ink) !important; }
.stRadio div[role="radiogroup"] { gap: 18px; }
.stRadio div[role="radiogroup"] label p { font-size: 13px; font-weight: 500; color: var(--ink) !important; }
[data-testid="stExpander"] { border: none; border-top: 1px solid var(--rule); border-bottom: 1px solid var(--rule); border-radius: 0; background: transparent; }
[data-testid="stExpander"] summary p { font-weight: 600; font-size: 13px; }
:focus-visible { outline: 2px solid var(--green); outline-offset: 2px; }

@media (max-width: 860px) {
  .hero, .prose2, .ledger-cols, .ledger-cols.three { grid-template-columns: 1fr; gap: 20px; }
}
</style>
""", unsafe_allow_html=True)


# ============ SMALL DESIGN HELPERS ============
def section(title, sub=None, first=False):
    cls = "sec first" if first else "sec"
    html = f"<div class='{cls}'>{title}</div>"
    if sub:
        html += f"<div class='sec-sub'>{sub}</div>"
    st.markdown(html, unsafe_allow_html=True)


def fig_title(title, sub=None):
    html = f"<div class='fig-title'>{title}</div>"
    if sub:
        html += f"<div class='fig-sub'>{sub}</div>"
    st.markdown(html, unsafe_allow_html=True)


def note(text):
    st.markdown(f"<p class='note'>{text}</p>", unsafe_allow_html=True)


def caveat(title, body, tone="solar"):
    cls = "caveat brick" if tone == "brick" else "caveat"
    st.markdown(f"<div class='{cls}'><div class='caveat-title'>{title}</div><div class='caveat-body'>{body}</div></div>", unsafe_allow_html=True)


def ledger_html(rows, title=None):
    out = f"<div class='group-title'>{title}</div>" if title else ""
    out += "<div class='ledger'>"
    for r in rows:
        label, value = r[0], r[1]
        sub = f"<small>{r[2]}</small>" if len(r) > 2 and r[2] else ""
        out += f"<div class='k'>{label}{sub}</div><div class='v'>{value}</div>"
    out += "</div>"
    return out


def style_fig(fig, height=300, legend=False, margin=None):
    fig.update_layout(
        height=height, template="simple_white",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT, color=INK, size=11.5),
        margin=margin or dict(l=0, r=0, t=10, b=0),
        showlegend=legend,
        legend=dict(orientation="h", y=1.12, x=0, font=dict(color=INK, size=11)),
        hoverlabel=dict(bgcolor=INK, font_color="#FFFFFF", font_family=FONT),
    )
    fig.update_xaxes(showgrid=False, linecolor=RULE, tickcolor=RULE, ticks="outside", tickfont=dict(color=INK2, size=11))
    fig.update_yaxes(gridcolor=GRID, zeroline=False, showline=False, tickfont=dict(color=INK2, size=11))
    return fig


def show(fig):
    st.plotly_chart(fig, use_container_width=True, theme=None, config={"displayModeBar": False})


def fmt_energy(kwh):
    return (f"{kwh / 1e6:,.2f}", "GWh") if kwh >= 1e6 else (f"{kwh / 1e3:,.1f}", "MWh")


# ============ HEADER ============
st.markdown("""
<div class='masthead-title'>Block 3 energy intelligence</div>
<div class='masthead-sub'>GMRIT, Rajam. Electricity demand and carbon footprint from an XGBoost model calibrated to the campus energy audit.</div>
""", unsafe_allow_html=True)

# ============ SIDEBAR CONTROLS ============
st.sidebar.header("Model controls")
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
    options=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
    value=('Jan', 'Dec')
)

# ============ CORE DATA & CALCULATIONS (unchanged) ============
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
FLOOR_COLORS = [GREEN, GREEN2, GREEN3]

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

solar_pct = (block3_solar_offset_kwh / total_kwh) * 100 if total_kwh > 0 else 0

# ============ TABS ============
tab_exec, tab_bim, tab_flow, tab_floor, tab_proj, tab_calib, tab_audit = st.tabs([
    "Overview",
    "Building",
    "Energy flow",
    "Floors and carbon",
    "Forecast",
    "Calibration",
    "Audit and retrofits"
])

# ----------------- TAB 1: OVERVIEW -----------------
with tab_exec:
    demand_val, demand_unit = fmt_energy(total_kwh)
    solar_note = ("Of modelled demand, from an allocated share of campus solar"
                  if show_solar else "Solar offset is switched off in the sidebar")

    st.markdown(f"""
<div class='hero'>
<div>
<div class='hero-num lead'>{demand_val}<span class='hero-unit'>{demand_unit}/yr</span></div>
<div class='hero-label'>Annual electricity demand</div>
<div class='hero-note'>Model estimate, calibrated to Block 3's share of the campus audit. Not a meter reading.</div>
</div>
<div>
<div class='hero-num'>{total_co2_block3_electricity:,.1f}<span class='hero-unit'>tCO₂/yr</span></div>
<div class='hero-label'>Annual carbon footprint</div>
<div class='hero-note'>Grid electricity after solar, at {emission_factor:.3f} tCO₂/MWh. Diesel excluded.</div>
</div>
<div>
<div class='hero-num'>{solar_pct:.1f}<span class='hero-unit'>%</span></div>
<div class='hero-label'>Solar contribution</div>
<div class='hero-note'>{solar_note}</div>
</div>
</div>
""", unsafe_allow_html=True)

    st.markdown(f"""
<div class='prose2'>
<div>
<p>Total modelled demand is <b>{total_kwh:,.0f} kWh</b>. Solar offsets <b>{solar_pct:.1f}%</b> of it ({block3_solar_offset_kwh:,.0f} kWh), leaving <b>{net_grid_kwh:,.0f} kWh</b> on the grid.</p>
<p>Solar avoids <b>{solar_co2_avoided:,.1f} tCO₂/yr</b>. Electricity emissions stand at <b>{total_co2_block3_electricity:,.1f} tCO₂/yr</b>, or {carbon_intensity:.1f} kgCO₂/m².</p>
</div>
<div>
<p>The ground floor carries <b>75.5%</b> of weekly load ({avg_weekly_kwh * floor_shares['Ground Floor']:,.0f} kWh/wk), driven by the central UPS banks.</p>
<p>Net grid EUI is <b>{eui_net:.1f} kWh/m²/yr</b>: {ecbc_rating.lower()}.</p>
</div>
</div>
""", unsafe_allow_html=True)
    note("Held-out BDG2 reference-dataset R² = 0.898, which is not a Block 3 validation. The annual total is calibrated to Block 3's 11.15% connected-load share of the campus audit. EUI is compared against ECBC reference ranges.")

    # ---- primary visualisation ----
    section("Monthly electricity demand", "Model-estimated, not metered. Use the month range in the sidebar to focus on part of the year.")

    predictions['month'] = predictions['timestamp'].dt.strftime('%b')
    predictions['month_num'] = predictions['timestamp'].dt.month
    monthly = predictions.groupby(['month_num', 'month'])['predicted_electricity_kwh'].sum().reset_index().sort_values('month_num')

    month_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    start_idx, end_idx = month_order.index(month_range[0]), month_order.index(month_range[1])
    if start_idx <= end_idx:
        selected_months = month_order[start_idx:end_idx + 1]
    else:
        selected_months = month_order[start_idx:] + month_order[:end_idx + 1]
    monthly_filtered = monthly[monthly['month'].isin(selected_months)]

    peak_val = monthly_filtered['predicted_electricity_kwh'].max() if len(monthly_filtered) else 0
    bar_colors = [INK if v == peak_val else GREEN2 for v in monthly_filtered['predicted_electricity_kwh']]
    fig1 = go.Figure(go.Bar(
        x=monthly_filtered['month'], y=monthly_filtered['predicted_electricity_kwh'],
        marker_color=bar_colors, marker_line_width=0,
        text=[f"{v:,.0f}" for v in monthly_filtered['predicted_electricity_kwh']],
        textposition="outside", cliponaxis=False, textfont=dict(size=11, color=INK2),
        hovertemplate="%{x}: %{y:,.0f} kWh<extra></extra>"
    ))
    style_fig(fig1, height=380, margin=dict(l=0, r=0, t=22, b=0))
    fig1.update_layout(bargap=0.38, yaxis_title="kWh")
    show(fig1)
    note("The darkest bar marks the peak month in the selected range.")

    # ---- supporting: supply mix + calibration consistency ----
    c_mix, c_cal = st.columns([1.5, 1], gap="large")
    with c_mix:
        fig_title("Where the electricity comes from", "Grid versus allocated solar, Block 3 estimate")
        fig_mix = go.Figure()
        fig_mix.add_trace(go.Bar(
            y=[""], x=[net_grid_kwh], orientation="h", name="Net grid electricity",
            marker_color=STEEL, text=[f"Grid  {net_grid_kwh:,.0f} kWh"], textposition="inside",
            insidetextanchor="start", textfont=dict(color="#FFFFFF", size=11.5),
            hovertemplate="Net grid: %{x:,.0f} kWh<extra></extra>"
        ))
        fig_mix.add_trace(go.Bar(
            y=[""], x=[block3_solar_offset_kwh], orientation="h", name="Solar offset (estimated allocation)",
            marker_color=SOLAR, text=[f"Solar  {block3_solar_offset_kwh:,.0f} kWh" if block3_solar_offset_kwh > 0 else ""],
            textposition="inside", insidetextanchor="start", textfont=dict(color=INK, size=11.5),
            hovertemplate="Solar offset: %{x:,.0f} kWh<extra></extra>"
        ))
        style_fig(fig_mix, height=110, margin=dict(l=0, r=0, t=6, b=0))
        fig_mix.update_layout(barmode="stack", bargap=0.1)
        fig_mix.update_xaxes(visible=False)
        fig_mix.update_yaxes(visible=False)
        show(fig_mix)
        note("Diesel is excluded here: the diesel-to-kWh conversion factor was not verified against genset specs. Diesel is reported separately in audited litres and CO2 only.")

    with c_cal:
        fig_title("Annual calibration consistency", "NMBE against the ±10% band")
        ok = abs(nmbe) <= 10
        st.markdown(
            f"<div class='stat-num' style='color:{GREEN if ok else BRICK}'>{abs(nmbe):.2f}%</div>"
            f"<div class='stat-sub'>{'Within the ±10% band' if ok else 'Outside the ±10% band'}</div>",
            unsafe_allow_html=True)
        fig_n = go.Figure()
        fig_n.add_vrect(x0=0, x1=10, fillcolor=GREEN3, opacity=0.35, line_width=0)
        fig_n.add_vrect(x0=10, x1=20, fillcolor=BRICK, opacity=0.18, line_width=0)
        fig_n.add_trace(go.Scatter(x=[min(abs(nmbe), 20)], y=[0], mode="markers",
                                   marker=dict(symbol="diamond", size=12, color=INK), hoverinfo="skip"))
        style_fig(fig_n, height=80, margin=dict(l=0, r=0, t=4, b=0))
        fig_n.update_xaxes(range=[0, 20], tickvals=[0, 10, 20], ticksuffix="%", showline=False)
        fig_n.update_yaxes(visible=False, range=[-1, 1])
        show(fig_n)

    # ---- ledger ----
    section("Supporting figures")
    left = ledger_html([
        ("Solar offset (allocated)", f"{block3_solar_offset_kwh:,.0f} kWh", "11.15% load share" if show_solar else "Disabled"),
        ("CO₂ avoided by solar", f"{solar_co2_avoided:,.1f} tCO₂", "Allocated solar share (assumption)"),
        ("Campus diesel generator reference", f"{campus_diesel_co2:,.1f} tCO₂", f"{annual_diesel_liters:,.0f} L/yr, audited campus level"),
    ], "Energy and carbon")
    right = ledger_html([
        ("Gross electricity EUI", f"{eui_gross:.1f} kWh/m²/yr", "Before solar, ML demand / area"),
        ("Net grid EUI after solar", f"{eui_net:.1f} kWh/m²/yr", ecbc_rating),
        ("Electricity carbon intensity", f"{carbon_intensity:.1f} kgCO₂/m²/yr", "Block 3 electricity only"),
        ("Built-up area (gbXML/BIM)", f"{block3_sqm:,.0f} m²", f"{block3_floors_desc}, built {block3_yearbuilt}"),
        ("ECBC / BEE reference range", f"{ecbc_benchmark_best}–{ecbc_benchmark_normal} kWh/m²/yr", "Warm & humid, daytime institutional"),
    ], "Building performance")
    st.markdown(f"<div class='ledger-cols'><div>{left}</div><div>{right}</div></div>", unsafe_allow_html=True)
    note("Both EUI figures use ML-derived annual electricity divided by verified built-up area. This is a reference EUI comparison against ECBC/BEE ranges, not a formal ECBC compliance certification.")

# ----------------- TAB 2: BUILDING (BIM) -----------------
with tab_bim:
    section("Building and level cutaways", "Revit BIM front views linked to the room-level equipment schedule and load shares.", first=True)

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
        "Select Revit cut section / level to inspect",
        options=list(floor_views.keys()),
        horizontal=True
    )

    col_view, col_meta = st.columns([1.8, 1], gap="large")
    with col_view:
        view_data = floor_views[selected_level]
        if os.path.exists(view_data["img"]):
            st.image(view_data["img"], caption=f"Revit BIM model, {selected_level}", use_container_width=True)
        else:
            st.warning(f"Image `{view_data['img']}` not found in repository root. Please ensure the file is present in the GitHub repository.")

    with col_meta:
        st.markdown(f"""
<div style='margin-top:12px;'>
<div class='stat-num'>{view_data['share']}</div>
<div class='stat-sub'>{view_data['weekly_energy']}</div>
<div class='body' style='margin-top:20px;'>{view_data['description']}</div>
</div>
""", unsafe_allow_html=True)

# ----------------- TAB 3: ENERGY FLOW (SANKEY) -----------------
with tab_flow:
    section("Energy flow", "From supply sources into Block 3 demand, and on to each floor level.", first=True)

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
        arrangement="snap",
        node=dict(
            pad=18, thickness=12,
            line=dict(color=PAPER, width=0),
            label=sankey_nodes,
            color=[STEEL, SOLAR, INK, GREEN, GREEN2, GREEN3]
        ),
        link=dict(
            source=[0, 1, 2, 2, 2],
            target=[2, 2, 3, 4, 5],
            value=[net_grid_kwh, block3_solar_offset_kwh, kwh_ground, kwh_first, kwh_top],
            color=[
                "rgba(91, 107, 115, 0.35)",
                "rgba(201, 138, 27, 0.40)",
                "rgba(31, 78, 69, 0.35)",
                "rgba(94, 143, 132, 0.40)",
                "rgba(169, 196, 188, 0.60)"
            ]
        )
    ))
    style_fig(fig_sankey, height=440, margin=dict(l=0, r=0, t=10, b=10))
    show(fig_sankey)

# ----------------- TAB 4: FLOORS AND CARBON -----------------
with tab_floor:
    section("Floor-wise electricity", "Derived from the audited equipment schedule and its operating-hour assumptions, not from floor-level electricity meters.", first=True)

    col_floor1, col_floor2 = st.columns([1.5, 1], gap="large")
    with col_floor1:
        floor_names = list(floor_shares.keys())
        floor_weekly = [avg_weekly_kwh * s for s in floor_shares.values()]
        fig_floor = go.Figure(go.Bar(
            x=floor_weekly, y=floor_names, orientation='h',
            marker_color=FLOOR_COLORS, marker_line_width=0,
            text=[f"{v:,.0f} kWh" for v in floor_weekly],
            textposition='outside', cliponaxis=False, textfont=dict(color=INK, size=11),
            hovertemplate="%{y}: %{x:,.0f} kWh/week<extra></extra>"
        ))
        style_fig(fig_floor, height=240, margin=dict(l=0, r=80, t=6, b=0))
        fig_floor.update_layout(xaxis_title="Estimated kWh per week", yaxis=dict(autorange="reversed"), bargap=0.4)
        fig_floor.update_xaxes(showgrid=True, gridcolor=GRID)
        fig_floor.update_yaxes(showgrid=False)
        show(fig_floor)

    with col_floor2:
        st.markdown(f"""
<div style='margin-top:4px;'>
<div class='stat-num'>Ground floor</div>
<div class='stat-sub'>75.5% of total load, from the equipment schedule</div>
<div class='body' style='margin-top:12px;'>Floor split is read directly from the 'Floor Level' column of the audited room-level equipment schedule, not a BIM-inferred assignment. Major ground-floor loads: central UPS banks (36 kW, 54 kW), substation transformers, and Electrical Machines/Power Systems lab motors.</div>
</div>
""", unsafe_allow_html=True)

    section("Floor-wise carbon allocation", "Electricity only. Diesel is excluded.")
    floor_co2 = {
        'Ground Floor': total_co2_block3_electricity * floor_shares['Ground Floor'],
        '1st Floor': total_co2_block3_electricity * floor_shares['1st Floor'],
        'Top Floor': total_co2_block3_electricity * floor_shares['Top Floor'],
    }

    fig_co2_bar = go.Figure(go.Bar(
        x=list(floor_co2.values()),
        y=list(floor_co2.keys()),
        orientation='h',
        marker_color=FLOOR_COLORS, marker_line_width=0,
        text=[f"{v:.1f} tCO2/yr ({v / total_co2_block3_electricity * 100:.0f}%)" if total_co2_block3_electricity > 0 else f"{v:.1f} tCO2/yr" for v in floor_co2.values()],
        textposition='outside', cliponaxis=False, textfont=dict(color=INK, size=11),
        hovertemplate="%{y}: %{x:.1f} tCO2/yr<extra></extra>"
    ))
    style_fig(fig_co2_bar, height=230, margin=dict(l=0, r=130, t=6, b=0))
    fig_co2_bar.update_layout(xaxis_title="tCO2/yr", yaxis=dict(autorange="reversed"), bargap=0.4)
    fig_co2_bar.update_xaxes(showgrid=True, gridcolor=GRID)
    fig_co2_bar.update_yaxes(showgrid=False)
    show(fig_co2_bar)
    note(f"Total Block 3 electricity-related footprint: {total_co2_block3_electricity:,.1f} tCO2/yr. Floor split computed directly from the 'Floor Level' column in the audited room-level equipment schedule (626 rows) and operating-hour assumptions, not inferred from the BIM model. Campus diesel CO2 ({campus_diesel_co2:,.1f} tCO2/yr) is excluded from this figure and from the floor split, since it cannot be defensibly allocated to Block 3 or to individual floors.")

# ----------------- TAB 5: FORECAST -----------------
with tab_proj:
    section("Temperature response", "How the trained model's hourly demand changes with outdoor temperature.", first=True)

    temp_cut = pd.cut(predictions['temperature_C'], bins=range(10, 46, 2))
    temp_binned = predictions.groupby(temp_cut, observed=True)['predicted_electricity_kwh'].mean().reset_index()
    temp_binned['temp_mid'] = [interval.mid for interval in temp_binned['temperature_C']]
    fig3 = go.Figure(go.Scatter(
        x=temp_binned['temp_mid'], y=temp_binned['predicted_electricity_kwh'], mode='lines+markers',
        line=dict(color=GREEN, width=2.5), marker=dict(size=5, color=GREEN),
        fill='tozeroy', fillcolor='rgba(31,78,69,0.08)',
        hovertemplate="%{x}°C: %{y:,.1f} kWh/h<extra></extra>"
    ))
    style_fig(fig3, height=330, margin=dict(l=0, r=0, t=10, b=0))
    fig3.update_layout(xaxis_title="Temperature (°C)", yaxis_title="Mean hourly kWh")
    show(fig3)
    note("Not measured Block 3 behavior. This reflects the trained model's general temperature response.")

    section("Scenario projection", "A what-if computed from assumed growth and climate-trend rates applied to the ML-estimated base year. It is not a model forecast or prediction of future years.")

    years = [2026 + i for i in range(projection_years)]
    proj_kwh = [total_kwh * ((1 + (usage_growth + climate_trend) / 100) ** i) for i in range(projection_years)]
    proj_net = [max(k - block3_solar_offset_kwh, 0.0) for k in proj_kwh]
    proj_co2 = [(k / 1000) * emission_factor for k in proj_net]

    fig4 = go.Figure(go.Bar(
        x=[str(y) for y in years], y=proj_co2, marker_color=STEEL, marker_line_width=0,
        text=[f"{v:,.1f}" for v in proj_co2], textposition="outside", cliponaxis=False,
        textfont=dict(color=INK2, size=11),
        hovertemplate="%{x}: %{y:,.1f} tCO2<extra></extra>"
    ))
    style_fig(fig4, height=330, margin=dict(l=0, r=0, t=22, b=0))
    fig4.update_layout(yaxis_title="tCO2 / year", bargap=0.45)
    show(fig4)
    note(f"Scenario-based projected Block 3 electricity CO2, {years[0]} to {years[-1]}, under assumed usage growth ({usage_growth}%/yr) and climate trend ({climate_trend}%/yr). Not a measured or guaranteed forecast. Excludes diesel (campus-level, held constant, not projected here). Audit baseline year: Apr 2021–Mar 2022. Weather data reference period differs from the audit year.")

# ----------------- TAB 6: CALIBRATION -----------------
with tab_calib:
    section("Annual calibration against the campus-share anchor", first=True)
    caveat("Consistency check, not validation",
           "The model output is scaled so its annual total equals Block 3's share (11.15%) of the audited campus consumption. The match is therefore true by construction.")

    fig_title("Hourly raw versus calibrated prediction", "First week of weather data")
    fig_1wk = go.Figure()
    fig_1wk.add_trace(go.Scatter(
        x=hours_axis, y=raw_week, mode='lines', name='Raw XGBoost (ML-derived, pre-calibration)',
        line=dict(color=STEEL, width=1.5, dash='dot')
    ))
    fig_1wk.add_trace(go.Scatter(
        x=hours_axis, y=calibrated_week, mode='lines', name='Calibrated XGBoost (calibrated ML estimate)',
        line=dict(color=GREEN, width=2.5)
    ))
    style_fig(fig_1wk, height=360, legend=True, margin=dict(l=0, r=0, t=28, b=0))
    fig_1wk.update_layout(xaxis_title="Hour of week (0-167)", yaxis_title="kWh")
    show(fig_1wk)

    section("Summary metrics")
    anchor_col = ledger_html([
        ("Audit-share annual anchor", f"{ANNUAL_ANCHOR_KWH:,.0f} kWh", f"Campus {CAMPUS_ANNUAL_KWH:,.0f} kWh × {block3_share * 100:.2f}% connected-load share. An allocation, not a meter reading."),
        ("Raw ML annual total", f"{raw_annual_kwh:,.0f} kWh", "Pre-calibration"),
    ], "Before")
    mid_col = ledger_html([
        ("Calibrated ML annual total", f"{total_kwh:,.0f} kWh"),
        ("Calibration factor", f"{SCALING_FACTOR}"),
    ], "Calibration")
    after_col = ledger_html([
        ("Difference before calibration", f"{diff_before_pct:+.2f}%"),
        ("Difference after calibration (NMBE)", f"{diff_after_pct:+.2f}%"),
    ], "Difference")
    st.markdown(f"<div class='ledger-cols three'><div>{anchor_col}</div><div>{mid_col}</div><div>{after_col}</div></div>", unsafe_allow_html=True)

    caveat("Why the equipment schedule is not the calibration target",
           f"The audited equipment schedule (rated power × scheduled hours) totals {EQUIP_SCHEDULE_WEEKLY:,.2f} kWh/week, about {EQUIP_SCHEDULE_WEEKLY * 52:,.0f} kWh/year, which would be {EQUIP_SCHEDULE_WEEKLY * 52 / CAMPUS_ANNUAL_KWH * 100:.0f}% of the entire campus consumption. It assumes equipment runs at rated power for all scheduled hours, so it overstates real energy use. It is used only for the floor-wise shares.")

    note("CV(RMSE) is not reported: there is no measured Block 3 hourly or monthly electricity series to pair with the predictions, so it cannot be correctly calculated and is not fabricated here.")
    note("The calibrated annual total equals the audit-share anchor because the model was scaled to it. This demonstrates calibration consistency, not independent model validation. Absolute values depend on the 11.15% load-share assumption and carry roughly ±10% uncertainty from the campus audit figures.")

section("Model inputs and evaluation")

metrics_path = "model_metrics.json"
model_metrics = None

if os.path.exists(metrics_path):
    try:
        with open(metrics_path) as f:
            model_metrics = json.load(f)
    except Exception:
        model_metrics = None

if model_metrics is None:
    st.info(
        "model_metrics.json not found in repository root. "
        "Run block3_model_training.py to generate it."
    )
else:

    # ---------------- MODEL INPUTS ----------------
    st.markdown(
        "<div class='fig-title'>Input features used by the selected XGBoost model</div>",
        unsafe_allow_html=True
    )

    st.code(
        ", ".join(model_metrics["features_used"]),
        language="text"
    )

    # ---------------- SELECTED MODEL ----------------
    selected_model = model_metrics.get("selected_model", "xgboost").upper()

    st.markdown(
        f"""
        <div class='group-title' style='margin-top:18px;'>
        Selected prediction model: <b>{selected_model}</b>
        </div>
        """,
        unsafe_allow_html=True
    )

    # ---------------- MODEL COMPARISON ----------------
    fig_title(
        "Model performance comparison",
        "BDG2 held-out test set"
    )

    model_names = [
        "XGBoost",
        "Random Forest",
        "Gradient Boosting",
        "Linear Regression"
    ]

    model_keys = [
        "xgboost",
        "random_forest",
        "gradient_boosting",
        "baseline_linear_regression"
    ]

    r2_values = [
        model_metrics[k]["r2"] for k in model_keys
    ]

    mae_values = [
        model_metrics[k]["mae_kwh"] for k in model_keys
    ]

    rmse_values = [
        model_metrics[k]["rmse_kwh"] for k in model_keys
    ]

    fig_model = go.Figure()

    fig_model.add_trace(
        go.Bar(
            name="R²",
            x=model_names,
            y=r2_values,
            marker_color=GREEN
        )
    )

    fig_model.add_trace(
        go.Bar(
            name="MAE (kWh)",
            x=model_names,
            y=mae_values,
            marker_color=GREEN2
        )
    )

    fig_model.add_trace(
        go.Bar(
            name="RMSE (kWh)",
            x=model_names,
            y=rmse_values,
            marker_color=GREEN3
        )
    )

    style_fig(
        fig_model,
        height=340,
        legend=True,
        margin=dict(l=0, r=0, t=30, b=0)
    )

    fig_model.update_layout(
        barmode="group",
        bargap=0.25
    )

    show(fig_model)

    # ---------------- METRICS TABLE ----------------
    st.markdown(
        "<div class='fig-title' style='margin-top:20px;'>Detailed model metrics</div>",
        unsafe_allow_html=True
    )

    metrics_df = pd.DataFrame({
        "Model": model_names,
        "R²": [
            round(model_metrics[k]["r2"], 3)
            for k in model_keys
        ],
        "MAE (kWh)": [
            round(model_metrics[k]["mae_kwh"], 2)
            for k in model_keys
        ],
        "RMSE (kWh)": [
            round(model_metrics[k]["rmse_kwh"], 2)
            for k in model_keys
        ]
    })

    st.dataframe(
        metrics_df,
        use_container_width=True,
        hide_index=True
    )

    # ---------------- FEATURE IMPORTANCE ----------------
    col_m1, col_m2 = st.columns(2, gap="large")

    with col_m1:

        fig_title(
            "XGBoost feature importance",
            "Gain-based"
        )

        importances = model_metrics["feature_importance"]

        # Sort from most important to least important
        sorted_importances = dict(
            sorted(
                importances.items(),
                key=lambda x: x[1],
                reverse=True
            )
        )

        fig_imp = go.Figure(
            go.Bar(
                x=list(sorted_importances.values()),
                y=list(sorted_importances.keys()),
                orientation="h",
                marker_color=GREEN2,
                marker_line_width=0
            )
        )

        style_fig(
            fig_imp,
            height=300,
            margin=dict(l=0, r=10, t=10, b=0)
        )

        fig_imp.update_layout(
            yaxis=dict(autorange="reversed"),
            bargap=0.35
        )

        fig_imp.update_xaxes(
            showgrid=True,
            gridcolor=GRID
        )

        fig_imp.update_yaxes(
            showgrid=False
        )

        show(fig_imp)

    # ---------------- MODEL SELECTION NOTE ----------------
    with col_m2:

        st.markdown(
            "<div class='fig-title'>Selected model rationale</div>",
            unsafe_allow_html=True
        )

        st.markdown(
            f"""
<div class='body' style='margin-top:12px;'>
The final prediction model used in this dashboard is
<b>{selected_model}</b>.
<br><br>
XGBoost achieved an R² of
<b>{model_metrics["xgboost"]["r2"]:.3f}</b>
with an MAE of
<b>{model_metrics["xgboost"]["mae_kwh"]:.2f} kWh</b>
and RMSE of
<b>{model_metrics["xgboost"]["rmse_kwh"]:.2f} kWh</b>
on the held-out BDG2 test set.
<br><br>
The model uses building characteristics together with
weather and temporal features to estimate electricity demand.
</div>
""",
            unsafe_allow_html=True
        )
