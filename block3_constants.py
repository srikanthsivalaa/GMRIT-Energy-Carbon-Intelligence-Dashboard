import os
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

from block3_constants import (
    CAMPUS_LOAD_KW,
    BLOCK3_LOAD_KW,
    BLOCK3_SHARE,
    GRID_KVAH_11M,
    SOLAR_GEN_11M,
    SOLAR_EXP_11M,
    PF,
    MONTHS_IN_AUDIT,
    SOLAR_USED_11M,
    CAMPUS_ANNUAL_KWH,
    SOLAR_USED_KWH,
    ANNUAL_ANCHOR_KWH,
    SOLAR_FRACTION,
    BLOCK3_WEEKLY_KWH,
    CAMPUS_DIESEL_L,
    BLOCK3_DIESEL_L,
    DIESEL_KGCO2_PER_L,
    INCLUDE_DIESEL,
    EMISSION_FACTOR,
    BLOCK3_SQM,
    REFERENCE_YEAR,
    RAW_ANNUAL_KWH,
    FLOOR_WEEKLY_KWH,
    MODEL_METRICS,
    SCALING_FACTOR,
)

# ============================================================
# PAGE CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="Block 3 Energy Intelligence",
    layout="wide",
    page_icon="⚡",
    initial_sidebar_state="expanded"
)

# Dashboard presentation metadata (not audit-derived constants)
BLOCK3_FLOORS_DESC = "G+2 (3 levels)"
BLOCK3_YEARBUILT = 1998
DIESEL_LITRES_YR = CAMPUS_DIESEL_L

# ============================================================
# DESIGN TOKENS
# ============================================================
PAPER = "#ECEBE6"
INK = "#1B2421"
INK2 = "#4A5753"
INK3 = "#5A6561"
RULE = "#C9C8C0"
GRID = "#D9D8D1"
GREEN = "#1F4E45"
GREEN2 = "#5E8F84"
GREEN3 = "#A9C4BC"
SOLAR = "#C98A1B"
STEEL = "#5B6B73"
BRICK = "#A5442F"
FONT = "Public Sans, Helvetica Neue, Arial, sans-serif"

# ============================================================
# STYLING
# ============================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@75..125,300..700&family=Public+Sans:wght@400;500;600&display=swap');

:root {
    --paper:#ECEBE6;
    --ink:#1B2421;
    --ink2:#4A5753;
    --ink3:#5A6561;
    --rule:#C9C8C0;
    --green:#1F4E45;
    --solar:#C98A1B;
    --brick:#A5442F;
    --steel:#5B6B73;
}

.stApp {
    background: var(--paper);
    color: var(--ink);
    font-family: 'Public Sans', 'Helvetica Neue', Arial, sans-serif;
    font-size: 13px;
    line-height: 1.5;
}

header[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer { visibility: hidden; }

.block-container, [data-testid="stMainBlockContainer"] {
    max-width: 1200px !important;
    margin: 0 auto;
    padding: 1.5rem 2rem 3rem 2rem;
}

.stApp p, .stApp li, .stApp label, .stApp span {
    color: var(--ink);
    font-size: 13px;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #E1DFD8;
    border-right: 1px solid var(--rule);
}
[data-testid="stSidebar"][aria-expanded="true"] {
    width: 268px !important;
    min-width: 268px !important;
    max-width: 268px !important;
}
[data-testid="stSidebar"] h2 {
    font-family: 'Archivo', sans-serif;
    font-weight: 600;
    font-size: 16px;
}
[data-testid="stSidebar"] hr {
    border-color: var(--rule);
    margin: 12px 0;
}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
    color: var(--ink3);
    font-size: 10px;
}

/* Masthead */
.masthead-title {
    font-family: 'Archivo', sans-serif;
    font-stretch: 85%;
    font-weight: 600;
    font-size: 24px;
    letter-spacing: -0.01em;
    line-height: 1.15;
    color: var(--ink);
}
.masthead-sub {
    margin-top: 4px;
    color: var(--ink2);
    font-size: 13px;
    max-width: 72ch;
    line-height: 1.45;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 24px;
    border-bottom: 1px solid var(--rule);
    margin-top: 16px;
}
.stTabs [data-baseweb="tab"] {
    background: transparent;
    padding: 8px 0;
    height: auto;
    color: var(--ink2);
    font-size: 13px;
    font-weight: 500;
}
.stTabs [aria-selected="true"] {
    color: var(--ink) !important;
    font-weight: 600;
}
.stTabs [data-baseweb="tab-highlight"] {
    background: var(--green) !important;
    height: 2px;
}
.stTabs [data-baseweb="tab-border"] { display: none; }
.stTabs [data-baseweb="tab-panel"] { padding-top: 16px; }

/* Hero numbers */
.hero {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 32px;
    margin: 36px 0 28px 0;
    align-items: baseline;
}
.hero-num {
    font-family: 'Archivo', sans-serif;
    font-stretch: 80%;
    font-weight: 300;
    font-size: 42px;
    line-height: 1.0;
    letter-spacing: -0.02em;
    font-variant-numeric: tabular-nums;
    color: var(--ink);
    white-space: nowrap;
}
.hero-num.lead { font-size: 44px; color: var(--green); }
.hero-unit {
    font-family: 'Public Sans', sans-serif;
    font-size: 16px;
    font-weight: 400;
    color: var(--ink2);
    margin-left: 6px;
}
.hero-label {
    margin-top: 8px;
    font-size: 13px;
    font-weight: 600;
    color: var(--ink);
    line-height: 1.2;
}
.hero-note {
    margin-top: 4px;
    font-size: 10.5px;
    line-height: 1.4;
    color: var(--ink3);
    max-width: 32ch;
}

/* Section titles */
.sec {
    font-family: 'Archivo', sans-serif;
    font-stretch: 90%;
    font-weight: 600;
    font-size: 16px;
    letter-spacing: -0.005em;
    margin: 24px 0 4px 0;
    color: var(--ink);
}
.sec.first { margin-top: 12px; }
.sec-sub {
    color: var(--ink2);
    font-size: 12px;
    line-height: 1.45;
    max-width: 72ch;
    margin-bottom: 12px;
}
.fig-title {
    font-size: 13px;
    font-weight: 600;
    color: var(--ink);
    margin: 12px 0 2px 0;
}
.fig-sub {
    font-size: 11px;
    color: var(--ink3);
    margin-bottom: 4px;
}

/* Prose and notes */
.prose2 {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 32px;
    margin: 14px 0 0 0;
}
.prose2 p {
    font-size: 13px;
    line-height: 1.55;
    color: var(--ink);
    margin: 0 0 8px 0;
    max-width: 62ch;
}
.prose2 b { font-weight: 600; }
.note {
    font-size: 10.5px;
    line-height: 1.45;
    color: var(--ink3);
    margin: 6px 0 0 0;
    max-width: 120ch;
}
.body {
    font-size: 13px;
    line-height: 1.55;
    color: var(--ink);
    max-width: 64ch;
}

/* Ledger */
.group-title {
    font-size: 13px;
    font-weight: 600;
    margin: 0 0 4px 0;
    color: var(--ink);
}
.ledger {
    display: grid;
    grid-template-columns: 1fr auto;
    column-gap: 20px;
}
.ledger .k {
    padding: 10px 0;
    border-bottom: 1px solid var(--rule);
    font-size: 12.5px;
    color: var(--ink2);
    line-height: 1.3;
}
.ledger .k small {
    display: block;
    font-size: 10.5px;
    color: var(--ink3);
    margin-top: 1px;
}
.ledger .v {
    padding: 10px 0;
    border-bottom: 1px solid var(--rule);
    font-size: 13px;
    font-weight: 600;
    color: var(--ink);
    text-align: right;
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
    line-height: 1.3;
}
.ledger-cols {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 32px;
    margin-top: 8px;
}
.ledger-cols.three {
    grid-template-columns: 1fr 1fr 1fr;
    gap: 24px;
}

/* Caveats */
.caveat {
    border-left: 3px solid var(--solar);
    padding: 2px 0 2px 12px;
    margin: 16px 0;
    max-width: 120ch;
}
.caveat.brick { border-left-color: var(--brick); }
.caveat-title {
    font-size: 13px;
    font-weight: 600;
    color: var(--ink);
    margin-bottom: 2px;
}
.caveat-body {
    font-size: 12px;
    line-height: 1.5;
    color: var(--ink2);
}

/* Big stat */
.stat-num {
    font-family: 'Archivo', sans-serif;
    font-stretch: 85%;
    font-weight: 300;
    font-size: 38px;
    letter-spacing: -0.02em;
    line-height: 1.05;
    color: var(--green);
    font-variant-numeric: tabular-nums;
}
.stat-sub {
    font-size: 12.5px;
    color: var(--ink2);
    margin-top: 4px;
}
.legend-row {
    display: flex;
    flex-wrap: wrap;
    gap: 8px 24px;
    font-size: 12px;
    color: var(--ink);
    margin: 4px 0 10px 0;
}
.sw {
    display: inline-block;
    width: 10px;
    height: 10px;
    margin-right: 6px;
    vertical-align: -1px;
}

/* Widgets */
.stRadio [data-testid="stWidgetLabel"] p {
    font-size: 13px;
    font-weight: 600;
    color: var(--ink) !important;
}
.stRadio div[role="radiogroup"] { gap: 18px; }
.stRadio div[role="radiogroup"] label p {
    font-size: 13px;
    font-weight: 500;
    color: var(--ink) !important;
}
[data-testid="stExpander"] {
    border: none;
    border-top: 1px solid var(--rule);
    border-bottom: 1px solid var(--rule);
    border-radius: 0;
    background: transparent;
}
[data-testid="stExpander"] summary p {
    font-weight: 600;
    font-size: 13px;
}
:focus-visible {
    outline: 2px solid var(--green);
    outline-offset: 2px;
}

@media (max-width: 860px) {
    .hero, .prose2, .ledger-cols, .ledger-cols.three {
        grid-template-columns: 1fr;
        gap: 20px;
    }
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# SMALL DESIGN HELPERS
# ============================================================
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
    st.markdown(
        f"<div class='{cls}'>"
        f"<div class='caveat-title'>{title}</div>"
        f"<div class='caveat-body'>{body}</div>"
        f"</div>",
        unsafe_allow_html=True
    )


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
        height=height,
        template="simple_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT, color=INK, size=11.5),
        margin=margin or dict(l=0, r=0, t=10, b=0),
        showlegend=legend,
        legend=dict(
            orientation="h",
            y=1.12,
            x=0,
            font=dict(color=INK, size=11)
        ),
        hoverlabel=dict(
            bgcolor=INK,
            font_color="#FFFFFF",
            font_family=FONT
        )
    )
    fig.update_xaxes(
        showgrid=False,
        linecolor=RULE,
        tickcolor=RULE,
        ticks="outside",
        tickfont=dict(color=INK2, size=11)
    )
    fig.update_yaxes(
        gridcolor=GRID,
        zeroline=False,
        showline=False,
        tickfont=dict(color=INK2, size=11)
    )
    return fig


def show(fig):
    st.plotly_chart(
        fig,
        use_container_width=True,
        theme=None,
        config={"displayModeBar": False}
    )


def fmt_energy(kwh):
    return (f"{kwh / 1e6:,.2f}", "GWh") if kwh >= 1e6 else (f"{kwh / 1e3:,.1f}", "MWh")


# ============================================================
# LOAD DATA & CORE CALCULATIONS
# ============================================================
predictions_path = "block3_predictions_full_year.csv"

if not os.path.exists(predictions_path):
    st.error(
        f"Required prediction CSV '{predictions_path}' not found in working directory."
    )
    st.stop()

df = pd.read_csv(predictions_path)

required_columns = [
    "timestamp",
    "predicted_electricity_kwh",
    "temperature_C"
]
missing_columns = [c for c in required_columns if c not in df.columns]

if missing_columns:
    st.error(f"Missing required CSV columns: {', '.join(missing_columns)}")
    st.stop()

df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
df["predicted_electricity_kwh"] = pd.to_numeric(
    df["predicted_electricity_kwh"], errors="coerce"
)
df["temperature_C"] = pd.to_numeric(df["temperature_C"], errors="coerce")
df = df.dropna(subset=required_columns).copy()

if df.empty:
    st.error("The prediction CSV contains no usable records.")
    st.stop()

# Standardized calculation block
total_kwh = df["predicted_electricity_kwh"].sum()

solar_offset_kwh = min(
    SOLAR_USED_KWH * BLOCK3_SHARE,
    total_kwh
)
net_grid_kwh = max(total_kwh - solar_offset_kwh, 0)

solar_pct = (
    solar_offset_kwh / total_kwh * 100
    if total_kwh > 0 else 0.0
)

co2_gross = total_kwh / 1000 * EMISSION_FACTOR
co2_solar = solar_offset_kwh / 1000 * EMISSION_FACTOR
co2_net = net_grid_kwh / 1000 * EMISSION_FACTOR

eui_gross = total_kwh / BLOCK3_SQM
eui_net = net_grid_kwh / BLOCK3_SQM
co2_m2 = co2_net * 1000 / BLOCK3_SQM

fl_tot = sum(FLOOR_WEEKLY_KWH.values())
fl_share = {
    k: v / fl_tot
    for k, v in FLOOR_WEEKLY_KWH.items()
}

# ============================================================
# SIDEBAR CONTROLS
# ============================================================
st.sidebar.header("Model controls")

emission_factor_input = st.sidebar.slider(
    "CEA Grid Emission Factor (tCO2/MWh)",
    0.65, 0.80,
    float(EMISSION_FACTOR),
    0.001
)

usage_growth = st.sidebar.slider(
    "Annual usage growth (%)",
    0.0, 5.0, 2.0, 0.5
)

climate_trend = st.sidebar.slider(
    "Climate warming trend (%)",
    0.0, 2.0, 0.5, 0.1
)

st.sidebar.markdown("---")

show_solar = st.sidebar.checkbox(
    "Include solar PV offset",
    value=True
)

st.sidebar.caption(
    f"Estimated Block 3 Solar Allocation — based on {BLOCK3_SHARE:.2%} "
    f"connected-load share; Block 3-specific solar metering unavailable. "
    f"Campus solar used on site ({SOLAR_USED_KWH:,.0f} kWh/yr, annualised "
    f"from 11 audit months) is from the audit; the Block 3 share is a "
    f"scenario allocation, not a measured quantity."
)

st.sidebar.markdown("---")

projection_years = st.sidebar.slider(
    "Projection horizon (years)",
    1, 10, 3
)

st.sidebar.markdown("---")

month_range = st.sidebar.select_slider(
    "Month range (monthly chart)",
    options=[
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
    ],
    value=("Jan", "Dec")
)

# Dynamic emission adjustments
active_solar_offset = solar_offset_kwh if show_solar else 0.0
active_net_grid = max(total_kwh - active_solar_offset, 0.0)

active_co2_net = (
    active_net_grid / 1000
) * emission_factor_input

active_co2_solar = (
    active_solar_offset / 1000
) * emission_factor_input

active_solar_pct = (
    active_solar_offset / total_kwh * 100
    if total_kwh > 0 else 0.0
)

active_carbon_m2 = (
    active_co2_net * 1000
) / BLOCK3_SQM

active_eui_net = active_net_grid / BLOCK3_SQM

avg_weekly_kwh = total_kwh / (len(df) / 168)

FLOOR_COLORS = [GREEN, GREEN2, GREEN3]

raw_annual_kwh = RAW_ANNUAL_KWH
diff_before_pct = (
    (raw_annual_kwh - ANNUAL_ANCHOR_KWH)
    / ANNUAL_ANCHOR_KWH
) * 100

# ============================================================
# HEADER
# ============================================================
st.markdown(
    "<div class='masthead-title'>Block 3 energy intelligence</div>",
    unsafe_allow_html=True
)

st.caption(
    f"GMRIT, Rajam. Scaled to Block 3's {BLOCK3_SHARE:.2%} "
    f"connected-load share ({BLOCK3_LOAD_KW} of {CAMPUS_LOAD_KW} kW) "
    f"of the audited campus consumption."
)

# ============================================================
# TABS
# ============================================================
tab_exec, tab_bim, tab_flow, tab_floor, tab_proj, tab_scaling, tab_audit = st.tabs([
    "Overview",
    "Building",
    "Energy flow",
    "Floors and carbon",
    "Forecast",
    "Scaling",
    "Audit and retrofits"
])

# ============================================================
# TAB 1: OVERVIEW
# ============================================================
with tab_exec:
    demand_val, demand_unit = fmt_energy(total_kwh)

    solar_note = (
        "Of modelled demand, from an allocated share of campus solar"
        if show_solar
        else "Solar offset is switched off in the sidebar"
    )

    st.markdown(f"""
    <div class='hero'>
        <div>
            <div class='hero-num lead'>
                {demand_val}<span class='hero-unit'>{demand_unit}/yr</span>
            </div>
            <div class='hero-label'>Annual electricity demand</div>
            <div class='hero-note'>
                Model estimate, scaled to Block 3's {BLOCK3_SHARE:.2%}
                share of the campus audit. Not a meter reading.
            </div>
        </div>
        <div>
            <div class='hero-num'>
                {active_co2_net:,.1f}<span class='hero-unit'>tCO₂/yr</span>
            </div>
            <div class='hero-label'>Annual electricity-related carbon emissions</div>
            <div class='hero-note'>
                Grid electricity after solar, at {emission_factor_input:.3f}
                tCO₂/MWh. Diesel excluded.
            </div>
        </div>
        <div>
            <div class='hero-num'>{active_solar_pct:.1f}<span class='hero-unit'>%</span></div>
            <div class='hero-label'>Solar contribution</div>
            <div class='hero-note'>{solar_note}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.write(
        f"Total modelled demand is {total_kwh:,.0f} kWh. "
        f"Solar offsets {active_solar_pct:.1f}% "
        f"({active_solar_offset:,.0f} kWh), leaving "
        f"{active_net_grid:,.0f} kWh on the grid."
    )

    st.write(
        f"Net grid EUI is {active_eui_net:.1f} kWh/m²/yr, "
        f"or {eui_gross:.1f} kWh/m²/yr before the solar offset."
    )

    st.caption(
        f"The annual total is scaled to Block 3's {BLOCK3_SHARE:.2%} "
        f"share of the campus audit consumption. EUI is reported as "
        f"a project-level indicator."
    )

    note(
        "Held-out BDG2 reference-dataset R² = 0.892, "
        "which is not a Block 3 validation."
    )

    # Monthly electricity demand — grouped by calendar year and month
    section(
        "Monthly electricity demand",
        "Model-estimated, not metered. Use the month range in the sidebar "
        "to focus on part of the year."
    )

    df["month_period"] = df["timestamp"].dt.to_period("M")

    monthly = (
        df.groupby("month_period")["predicted_electricity_kwh"]
        .sum()
        .reset_index()
    )

    monthly["month_label"] = monthly["month_period"].apply(
        lambda x: x.strftime("%b %Y")
    )
    monthly["month_num"] = monthly["month_period"].apply(
        lambda x: x.month
    )

    month_order = [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
    ]

    start_idx = month_order.index(month_range[0])
    end_idx = month_order.index(month_range[1])

    if start_idx <= end_idx:
        selected_months = month_order[start_idx:end_idx + 1]
    else:
        selected_months = (
            month_order[start_idx:] + month_order[:end_idx + 1]
        )

    monthly_filtered = monthly[
        monthly["month_num"].apply(
            lambda x: month_order[x - 1] in selected_months
        )
    ]

    peak_val = (
        monthly_filtered["predicted_electricity_kwh"].max()
        if len(monthly_filtered) else 0
    )

    bar_colors = [
        INK if v == peak_val else GREEN2
        for v in monthly_filtered["predicted_electricity_kwh"]
    ]

    fig1 = go.Figure(go.Bar(
        x=monthly_filtered["month_label"],
        y=monthly_filtered["predicted_electricity_kwh"],
        marker_color=bar_colors,
        marker_line_width=0,
        text=[
            f"{v:,.0f}"
            for v in monthly_filtered["predicted_electricity_kwh"]
        ],
        textposition="outside",
        cliponaxis=False,
        textfont=dict(size=11, color=INK2),
        hovertemplate="%{x}: %{y:,.0f} kWh<extra></extra>"
    ))

    style_fig(fig1, height=380, margin=dict(l=0, r=0, t=22, b=0))
    fig1.update_layout(bargap=0.38, yaxis_title="kWh")
    show(fig1)

    note(
        "Monthly totals are grouped by calendar year and month. "
        "July 2025 and July 2026 are shown separately. "
        "The first and last months are partial weather-data periods."
    )

    # Supply mix
    fig_title(
        "Where the electricity comes from",
        "Grid versus allocated solar, Block 3 estimate"
    )

    fig_mix = go.Figure()

    fig_mix.add_trace(go.Bar(
        y=[""],
        x=[active_net_grid],
        orientation="h",
        name="Net grid electricity",
        marker_color=STEEL,
        text=[f"Grid  {active_net_grid:,.0f} kWh"],
        textposition="inside",
        insidetextanchor="start",
        textfont=dict(color="#FFFFFF", size=11.5),
        hovertemplate="Net grid: %{x:,.0f} kWh<extra></extra>"
    ))

    fig_mix.add_trace(go.Bar(
        y=[""],
        x=[active_solar_offset],
        orientation="h",
        name="Solar offset (estimated allocation)",
        marker_color=SOLAR,
        text=[
            f"Solar  {active_solar_offset:,.0f} kWh"
            if active_solar_offset > 0 else ""
        ],
        textposition="inside",
        insidetextanchor="start",
        textfont=dict(color=INK, size=11.5),
        hovertemplate="Solar offset: %{x:,.0f} kWh<extra></extra>"
    ))

    style_fig(fig_mix, height=110, margin=dict(l=0, r=0, t=6, b=0))
    fig_mix.update_layout(barmode="stack", bargap=0.1)
    fig_mix.update_xaxes(visible=False)
    fig_mix.update_yaxes(visible=False)
    show(fig_mix)

    note("Diesel is excluded here. Diesel is reported separately in audited litres only.")

    # Supporting figures
    section("Supporting figures")

    left = ledger_html([
        (
            "Solar offset (allocated)",
            f"{active_solar_offset:,.0f} kWh",
            f"{BLOCK3_SHARE:.2%} load share" if show_solar else "Disabled"
        ),
        (
            "CO₂ avoided by solar",
            f"{active_co2_solar:,.1f} tCO₂",
            "Allocated solar share (assumption)"
        ),
        (
            "Campus diesel generator reference",
            f"{DIESEL_LITRES_YR:,.0f} L/yr",
            "Audited campus level, CO₂ excluded"
        ),
    ], "Energy and carbon")

    right = ledger_html([
        (
            "Gross electricity EUI",
            f"{eui_gross:.1f} kWh/m²/yr",
            "Before solar, ML demand / area"
        ),
        (
            "Net grid EUI after solar",
            f"{active_eui_net:.1f} kWh/m²/yr",
            "Grid electricity after active solar setting / area"
        ),
        (
            "Electricity carbon intensity",
            f"{active_carbon_m2:.1f} kgCO₂/m²/yr",
            "Block 3 electricity only"
        ),
        (
            "Built-up area (gbXML/BIM)",
            f"{BLOCK3_SQM:,.2f} m²",
            f"{BLOCK3_FLOORS_DESC}, built {BLOCK3_YEARBUILT}"
        ),
        (
            "ECBC 2017 EPI Ratio",
            "Not computed",
            "Needs a Standard Building simulation."
        ),
    ], "Building performance")

    st.markdown(
        f"<div class='ledger-cols'><div>{left}</div><div>{right}</div></div>",
        unsafe_allow_html=True
    )

# ============================================================
# TAB 2: BUILDING (BIM)
# ============================================================
with tab_bim:
    section(
        "Building and level cutaways",
        "Revit BIM front views linked to the room-level equipment schedule "
        "and load shares.",
        first=True
    )

    floor_views = {
        "Full Building (Front View)": {
            "img": "total block front view.jpeg",
            "share": "100% of Building Demand",
            "weekly_energy": f"{avg_weekly_kwh:,.0f} kWh/wk",
            "description": (
                f"Reinforced concrete institutional frame "
                f"({BLOCK3_FLOORS_DESC} with open central courtyard), "
                f"{BLOCK3_SQM:,.2f} m² built-up area built in "
                f"{BLOCK3_YEARBUILT}."
            )
        },
        "Ground Floor Cut (Front View)": {
            "img": "ground floor cut front view.jpeg",
            "share": f"{fl_share['Ground Floor']:.1%} of Total Load",
            "weekly_energy": (
                f"{avg_weekly_kwh * fl_share['Ground Floor']:,.0f} kWh/wk"
            ),
            "description": (
                "High-draw zone containing Central UPS banks, substation "
                "step-down transformers, and Electrical Machines / "
                "Power Systems lab motors. Weekly energy is an ML estimate "
                "allocated using equipment-schedule floor shares."
            )
        },
        "1st Floor Cut (Front View)": {
            "img": "first floor cut front view.jpeg",
            "share": f"{fl_share['1st Floor']:.1%} of Total Load",
            "weekly_energy": (
                f"{avg_weekly_kwh * fl_share['1st Floor']:,.0f} kWh/wk"
            ),
            "description": (
                "Mid-draw academic zone featuring computer labs, "
                "departmental lecture classrooms, and faculty rooms. "
                "Weekly energy is an ML estimate allocated using "
                "equipment-schedule floor shares."
            )
        },
        "2nd / Top Floor Cut (Front View)": {
            "img": "2nd floor cut front view.jpeg",
            "share": f"{fl_share['Top Floor']:.1%} of Total Load",
            "weekly_energy": (
                f"{avg_weekly_kwh * fl_share['Top Floor']:,.0f} kWh/wk"
            ),
            "description": (
                "Low-draw zone housing seminar halls, department library, "
                "and rooftop solar electrical tie-ins. Weekly energy is an "
                "ML estimate allocated using equipment-schedule floor shares."
            )
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
            st.image(
                view_data["img"],
                caption=f"Revit BIM model, {selected_level}",
                use_container_width=True
            )
        else:
            st.warning(
                f"Image '{view_data['img']}' not found in repository root. "
                "Please ensure the file is present in the GitHub repository."
            )

    with col_meta:
        st.markdown(f"""
        <div style='margin-top:12px;'>
            <div class='stat-num'>{view_data['share']}</div>
            <div class='stat-sub'>{view_data['weekly_energy']}</div>
            <div class='body' style='margin-top:20px;'>
                {view_data['description']}
            </div>
        </div>
        """, unsafe_allow_html=True)

# ============================================================
# TAB 3: ENERGY FLOW (SANKEY)
# ============================================================
with tab_flow:
    section(
        "Energy flow",
        "From supply sources into Block 3 demand, and on to each floor level.",
        first=True
    )

    kwh_ground = total_kwh * fl_share["Ground Floor"]
    kwh_first = total_kwh * fl_share["1st Floor"]
    kwh_top = total_kwh * fl_share["Top Floor"]

    sankey_nodes = [
        "Grid Electricity",
        "Solar PV Offset (Allocated)",
        "Block 3 Total Demand",
        f"Ground Floor ({fl_share['Ground Floor']:.1%})",
        f"1st Floor ({fl_share['1st Floor']:.1%})",
        f"Top Floor ({fl_share['Top Floor']:.1%})"
    ]

    fig_sankey = go.Figure(go.Sankey(
        arrangement="snap",
        node=dict(
            pad=18,
            thickness=12,
            line=dict(color=PAPER, width=0),
            label=sankey_nodes,
            color=[STEEL, SOLAR, INK, GREEN, GREEN2, GREEN3]
        ),
        link=dict(
            source=[0, 1, 2, 2, 2],
            target=[2, 2, 3, 4, 5],
            value=[
                active_net_grid,
                active_solar_offset,
                kwh_ground,
                kwh_first,
                kwh_top
            ],
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

# ============================================================
# TAB 4: FLOORS AND CARBON
# ============================================================
with tab_floor:
    section(
        "Floor-wise electricity",
        "ML-estimated weekly electricity allocated using equipment-schedule "
        "floor shares, not floor-level meter readings.",
        first=True
    )

    col_floor1, col_floor2 = st.columns([1.5, 1], gap="large")

    with col_floor1:
        floor_names = list(fl_share.keys())
        floor_weekly = [
            avg_weekly_kwh * s
            for s in fl_share.values()
        ]

        fig_floor = go.Figure(go.Bar(
            x=floor_weekly,
            y=floor_names,
            orientation="h",
            marker_color=FLOOR_COLORS,
            marker_line_width=0,
            text=[f"{v:,.0f} kWh" for v in floor_weekly],
            textposition="outside",
            cliponaxis=False,
            textfont=dict(color=INK, size=11),
            hovertemplate="%{y}: %{x:,.0f} kWh/week<extra></extra>"
        ))

        style_fig(fig_floor, height=240, margin=dict(l=0, r=80, t=6, b=0))
        fig_floor.update_layout(
            xaxis_title="Estimated kWh per week",
            yaxis=dict(autorange="reversed"),
            bargap=0.4
        )
        fig_floor.update_xaxes(showgrid=True, gridcolor=GRID)
        fig_floor.update_yaxes(showgrid=False)
        show(fig_floor)

    with col_floor2:
        st.markdown(f"""
        <div style='margin-top:4px;'>
            <div class='stat-num'>Ground floor</div>
            <div class='stat-sub'>
                {fl_share['Ground Floor']:.1%} of total load,
                from the equipment schedule
            </div>
            <div class='body' style='margin-top:12px;'>
                Floor split is read directly from the 'Floor Level' column
                of the room-level equipment schedule (rated power ×
                timetable hours), not a BIM-inferred assignment.
                Major ground-floor loads: central UPS banks, substation
                transformers, and Electrical Machines/Power Systems lab motors.
                The displayed weekly electricity is an ML estimate allocated
                using these floor shares.
            </div>
        </div>
        """, unsafe_allow_html=True)

    section(
        "Floor-wise carbon allocation",
        "Electricity only. Diesel is excluded."
    )

    floor_co2 = {
        "Ground Floor": active_co2_net * fl_share["Ground Floor"],
        "1st Floor": active_co2_net * fl_share["1st Floor"],
        "Top Floor": active_co2_net * fl_share["Top Floor"]
    }

    fig_co2_bar = go.Figure(go.Bar(
        x=list(floor_co2.values()),
        y=list(floor_co2.keys()),
        orientation="h",
        marker_color=FLOOR_COLORS,
        marker_line_width=0,
        text=[
            (
                f"{v:.1f} tCO2/yr "
                f"({v / active_co2_net * 100:.0f}%)"
                if active_co2_net > 0
                else f"{v:.1f} tCO2/yr"
            )
            for v in floor_co2.values()
        ],
        textposition="outside",
        cliponaxis=False,
        textfont=dict(color=INK, size=11),
        hovertemplate="%{y}: %{x:.1f} tCO2/yr<extra></extra>"
    ))

    style_fig(fig_co2_bar, height=230, margin=dict(l=0, r=130, t=6, b=0))
    fig_co2_bar.update_layout(
        xaxis_title="tCO2/yr",
        yaxis=dict(autorange="reversed"),
        bargap=0.4
    )
    fig_co2_bar.update_xaxes(showgrid=True, gridcolor=GRID)
    fig_co2_bar.update_yaxes(showgrid=False)
    show(fig_co2_bar)

    note(
        f"Total Block 3 electricity-related footprint: "
        f"{active_co2_net:,.1f} tCO2/yr. Campus diesel "
        f"({DIESEL_LITRES_YR:,.0f} L/yr) is excluded from this figure. "
        "Floor shares are estimates from rated equipment; the Ground "
        "Floor share may be an upper bound."
    )

# ============================================================
# TAB 5: FORECAST
# ============================================================
with tab_proj:
    section(
        "Temperature response",
        "How the trained model's hourly demand changes with outdoor temperature.",
        first=True
    )

    temp_cut = pd.cut(
        df["temperature_C"],
        bins=range(10, 46, 2)
    )

    temp_binned = (
        df.groupby(temp_cut, observed=True)["predicted_electricity_kwh"]
        .mean()
        .reset_index()
    )

    temp_binned["temp_mid"] = [
        interval.mid
        for interval in temp_binned["temperature_C"]
    ]

    fig3 = go.Figure(go.Scatter(
        x=temp_binned["temp_mid"],
        y=temp_binned["predicted_electricity_kwh"],
        mode="lines+markers",
        line=dict(color=GREEN, width=2.5),
        marker=dict(size=5, color=GREEN),
        fill="tozeroy",
        fillcolor="rgba(31,78,69,0.08)",
        hovertemplate="%{x}°C: %{y:,.1f} kWh/h<extra></extra>"
    ))

    style_fig(fig3, height=330, margin=dict(l=0, r=0, t=10, b=0))
    fig3.update_layout(
        xaxis_title="Temperature (°C)",
        yaxis_title="Mean hourly kWh"
    )
    show(fig3)

    section(
        "Scenario projection",
        f"A what-if computed from assumed growth ({usage_growth}%/yr) "
        f"and climate-trend ({climate_trend}%/yr) rates applied to "
        "the ML-estimated base year."
    )

    years = [2026 + i for i in range(projection_years)]

    proj_kwh = [
        total_kwh * (
            (1 + (usage_growth + climate_trend) / 100) ** i
        )
        for i in range(projection_years)
    ]

    proj_net = [
        max(k - active_solar_offset, 0.0)
        for k in proj_kwh
    ]

    proj_co2 = [
        (k / 1000) * emission_factor_input
        for k in proj_net
    ]

    fig4 = go.Figure(go.Bar(
        x=[str(y) for y in years],
        y=proj_co2,
        marker_color=STEEL,
        marker_line_width=0,
        text=[f"{v:,.1f}" for v in proj_co2],
        textposition="outside",
        cliponaxis=False,
        textfont=dict(color=INK2, size=11),
        hovertemplate="%{x}: %{y:,.1f} tCO2<extra></extra>"
    ))

    style_fig(fig4, height=330, margin=dict(l=0, r=0, t=22, b=0))
    fig4.update_layout(yaxis_title="tCO2 / year", bargap=0.45)
    show(fig4)

# ============================================================
# TAB 6: SCALING
# ============================================================
with tab_scaling:
    section(
        "Annual scaling against the campus-share anchor",
        first=True
    )

    caveat(
        "Consistency check, not validation",
        f"The model output is scaled so its annual total equals Block 3's "
        f"share ({BLOCK3_SHARE:.2%}) of the audited campus consumption. "
        "The match is therefore true by construction."
    )

    fig_title(
        "Hourly raw versus scaled prediction",
        "First week of weather data"
    )

    calibrated_week = (
        df["predicted_electricity_kwh"]
        .iloc[:168]
        .reset_index(drop=True)
    )

    raw_week = calibrated_week / SCALING_FACTOR
    hours_axis = list(range(len(calibrated_week)))

    fig_1wk = go.Figure()

    fig_1wk.add_trace(go.Scatter(
        x=hours_axis,
        y=raw_week,
        mode="lines",
        name="Raw XGBoost (ML-derived, pre-scaling)",
        line=dict(color=STEEL, width=1.5, dash="dot")
    ))

    fig_1wk.add_trace(go.Scatter(
        x=hours_axis,
        y=calibrated_week,
        mode="lines",
        name="Scaled XGBoost (scaled ML estimate)",
        line=dict(color=GREEN, width=2.5)
    ))

    style_fig(
        fig_1wk,
        height=360,
        legend=True,
        margin=dict(l=0, r=0, t=28, b=0)
    )
    fig_1wk.update_layout(
        xaxis_title="Hour of week (0-167)",
        yaxis_title="kWh"
    )
    show(fig_1wk)

    section("Summary metrics")

    anchor_col = ledger_html([
        (
            "Audit-share annual anchor",
            f"{ANNUAL_ANCHOR_KWH:,.0f} kWh",
            f"Campus {CAMPUS_ANNUAL_KWH:,.0f} kWh × "
            f"{BLOCK3_SHARE:.2%} connected-load share. "
            "An allocation, not a meter reading."
        ),
        (
            "Raw ML annual total",
            f"{raw_annual_kwh:,.0f} kWh",
            "Pre-scaling"
        ),
    ], "Before")

    mid_col = ledger_html([
        ("Scaled ML annual total", f"{total_kwh:,.0f} kWh"),
        ("Scaling factor", f"{SCALING_FACTOR:.4f}"),
    ], "Scaling")

    after_col = ledger_html([
        ("Difference before scaling", f"{diff_before_pct:+.2f}%"),
        ("Difference after scaling", "0.00%"),
    ], "Difference")

    st.markdown(
        f"<div class='ledger-cols three'>"
        f"<div>{anchor_col}</div>"
        f"<div>{mid_col}</div>"
        f"<div>{after_col}</div>"
        f"</div>",
        unsafe_allow_html=True
    )

    caveat(
        "Why the equipment schedule is not the scaling target",
        f"The equipment schedule (rated power × timetable hours) totals "
        f"{fl_tot:,.2f} kWh/week, about {fl_tot * 52:,.0f} kWh/year, "
        f"which would be {fl_tot * 52 / CAMPUS_ANNUAL_KWH * 100:.0f}% "
        "of the entire campus consumption. It assumes equipment runs "
        "at rated power for all scheduled hours, so it likely overstates "
        "real energy use. It is used only for the floor-wise shares."
    )

    # ML algorithm performance comparison
    section(
        "Machine learning model performance comparison",
        "BDG2 held-out test results using the supplied model metrics. "
        "Random record-level split; not a Block 3 validation."
    )

    models = list(MODEL_METRICS.keys())
    model_colors = [GREEN, GREEN2, STEEL, SOLAR]

    # R² comparison
    fig_r2 = go.Figure(go.Bar(
        x=models,
        y=[MODEL_METRICS[m]["R2"] for m in models],
        marker_color=model_colors,
        text=[f'{MODEL_METRICS[m]["R2"]:.3f}' for m in models],
        textposition="outside",
        cliponaxis=False
    ))

    style_fig(fig_r2, height=340, margin=dict(l=10, r=10, t=35, b=70))
    fig_r2.update_layout(
        title="R² score — Higher is better",
        yaxis_title="R²",
        yaxis=dict(range=[0, 1]),
        xaxis_tickangle=-15
    )
    show(fig_r2)

    # MAE comparison
    fig_mae = go.Figure(go.Bar(
        x=models,
        y=[MODEL_METRICS[m]["MAE"] for m in models],
        marker_color=model_colors,
        text=[f'{MODEL_METRICS[m]["MAE"]:.2f}' for m in models],
        textposition="outside",
        cliponaxis=False
    ))

    style_fig(fig_mae, height=340, margin=dict(l=10, r=10, t=35, b=70))
    fig_mae.update_layout(
        title="Mean Absolute Error (MAE) — Lower is better",
        yaxis_title="MAE",
        xaxis_tickangle=-15
    )
    show(fig_mae)

    # RMSE comparison
    fig_rmse = go.Figure(go.Bar(
        x=models,
        y=[MODEL_METRICS[m]["RMSE"] for m in models],
        marker_color=model_colors,
        text=[f'{MODEL_METRICS[m]["RMSE"]:.2f}' for m in models],
        textposition="outside",
        cliponaxis=False
    ))

    style_fig(fig_rmse, height=340, margin=dict(l=10, r=10, t=35, b=70))
    fig_rmse.update_layout(
        title="Root Mean Squared Error (RMSE) — Lower is better",
        yaxis_title="RMSE",
        xaxis_tickangle=-15
    )
    show(fig_rmse)

    metrics_df = pd.DataFrame([
        {
            "Algorithm": model,
            "R²": MODEL_METRICS[model]["R2"],
            "MAE": MODEL_METRICS[model]["MAE"],
            "RMSE": MODEL_METRICS[model]["RMSE"]
        }
        for model in models
    ])

    st.dataframe(
        metrics_df,
        use_container_width=True,
        hide_index=True
    )

    note(
        "All model metrics are read directly from block3_constants.py. "
        "They represent BDG2 held-out test performance and do not "
        "constitute validation against Block 3 meter readings."
    )

# ============================================================
# TAB 7: AUDIT AND RETROFITS
# ============================================================
with tab_audit:
    section("Data status", first=True)

    st.markdown(f"""
    <div class='legend-row'>
        <span>
            <span class='sw' style='background:{GREEN}'></span>
            <b>Measured / audited:</b> campus electricity (utility and solar
            bills), diesel, solar, Block 3 connected load
            ({BLOCK3_LOAD_KW} of {CAMPUS_LOAD_KW} kW)
        </span>
        <span>
            <span class='sw' style='background:{STEEL}'></span>
            <b>ML-derived:</b> annual and monthly electricity prediction
        </span>
        <span>
            <span class='sw' style='background:{SOLAR}'></span>
            <b>Estimated allocation:</b> Block 3 solar share
            ({BLOCK3_SHARE:.2%}), equipment schedule, floor-wise contribution
            and emissions
        </span>
        <span>
            <span class='sw' style='background:{GREEN3}'></span>
            <b>Assumption / scenario:</b> emission factors, operating hours
            (official timetable, not metered), growth and climate-trend rates,
            future projections
        </span>
    </div>
    """, unsafe_allow_html=True)

    caveat(
        "Temporal scope",
        f"The audit baseline (connected load, diesel, solar generation) is "
        f"<b>Apr 2021–Feb 2022 (11 billed months, annualised ×12/11)</b>. "
        f"The weather dataset used to drive the ML model is "
        f"<b>Jul 2025–Jul 2026</b> (NASA POWER, local solar time). "
        f"These are different periods. The annual Block 3 electricity "
        f"figure on this dashboard is therefore a <b>scaled scenario estimate</b>: "
        f"the model's weather-driven pattern for a recent year, rescaled "
        f"to match Block 3's {BLOCK3_SHARE:.2%} share of the audited campus annual energy."
    )

    with st.expander(
        "Methodology, assumptions and data provenance",
        expanded=False
    ):
        st.markdown(f"""
        **How is Block 3's annual electricity (~{total_kwh/1e3:.0f} MWh)
        derived, and how does it relate to the campus audit total
        ({CAMPUS_ANNUAL_KWH:,.0f} kWh/yr)?**

        - The campus audit figure ({CAMPUS_ANNUAL_KWH:,.0f} kWh/yr,
          Apr 2021–Feb 2022 annualized) is a **measured utility bill total**
          for the entire campus, across all blocks, hostels, and staff quarters.
        - **Block 3 annual anchor = campus total × {BLOCK3_SHARE:.2%}**
          (Block 3's connected-load share: {BLOCK3_LOAD_KW} kW of
          {CAMPUS_LOAD_KW} kW) ≈ {ANNUAL_ANCHOR_KWH:,.0f} kWh.
          This is an **allocation**, not a Block 3 meter reading.
        - An XGBoost model trained on BDG2 (604 education buildings,
          mainly North American and European) supplies the **hourly and
          seasonal shape** from Block 3's weather and physical attributes.
          A single scaling factor sets the annual total equal to the anchor.
        - The connected-load share describes **peak connected capacity**,
          not energy consumed.
        """)

    section(
        "Recommended energy-saving measures",
        "The two retrofits come from the campus audit. "
        "The operational measures are derived from the equipment schedule."
    )

    r1, r2 = st.columns(2, gap="large")

    with r1:
        st.markdown("""
        <div class='stat-num'>67,904<span class='hero-unit'>kWh/yr</span></div>
        <div class='group-title' style='margin-top:8px;'>
            BLDC ceiling fan replacement
        </div>
        <div class='stat-sub'>
            Audited retrofit. Estimated savings, campus-wide.
        </div>
        <div class='body' style='margin-top:8px;'>
            Audit estimate for 2,122 ceiling fans campus-wide
            (80 W to 40 W): investment ₹63.66 lakh, savings
            ₹5.16 lakh/yr, payback 148 months.
        </div>
        """, unsafe_allow_html=True)

    with r2:
        st.markdown("""
        <div class='stat-num'>1,976<span class='hero-unit'>kWh/yr</span></div>
        <div class='group-title' style='margin-top:8px;'>
            SV-to-LED lighting replacement
        </div>
        <div class='stat-sub'>
            Audited retrofit. Estimated savings, campus-wide.
        </div>
        <div class='body' style='margin-top:8px;'>
            Audit estimate for 19 sodium-vapor lamps campus-wide
            (250 W to 150 W): investment ₹19,000, savings
            ₹45,052/yr, payback 5 months.
        </div>
        """, unsafe_allow_html=True)

    # Audited retrofit energy-savings chart
    section(
        "Audited retrofit comparison",
        "Campus-wide audit estimates. These are not Block 3-specific savings."
    )

    retrofit_names = [
        "BLDC ceiling fans",
        "SV-to-LED lighting"
    ]
    retrofit_kwh = [67904, 1976]

    fig_retrofit = go.Figure(go.Bar(
        x=retrofit_names,
        y=retrofit_kwh,
        marker_color=[GREEN, SOLAR],
        text=[f"{v:,.0f} kWh/yr" for v in retrofit_kwh],
        textposition="outside",
        cliponaxis=False
    ))

    style_fig(
        fig_retrofit,
        height=340,
        margin=dict(l=10, r=10, t=35, b=10)
    )
    fig_retrofit.update_layout(
        title="Estimated annual energy savings",
        yaxis_title="Annual electricity savings (kWh)",
        showlegend=False
    )
    show(fig_retrofit)

    # Financial savings and payback charts
    section(
        "Financial performance of audited retrofits",
        "Annual financial savings and payback estimates from the campus audit."
    )

    fin_left, fin_right = st.columns(2, gap="large")

    with fin_left:
        fig_fin = go.Figure(go.Bar(
            x=["BLDC fans", "SV-to-LED"],
            y=[516000, 45052],
            marker_color=[GREEN, SOLAR],
            text=["₹5.16 lakh", "₹45,052"],
            textposition="outside",
            cliponaxis=False
        ))

        style_fig(
            fig_fin,
            height=320,
            margin=dict(l=5, r=10, t=35, b=5)
        )
        fig_fin.update_layout(
            title="Annual financial savings",
            yaxis_title="₹ per year"
        )
        show(fig_fin)

    with fin_right:
        fig_payback = go.Figure(go.Bar(
            x=["BLDC fans", "SV-to-LED"],
            y=[148, 5],
            marker_color=[GREEN, SOLAR],
            text=["148 months", "5 months"],
            textposition="outside",
            cliponaxis=False
        ))

        style_fig(
            fig_payback,
            height=320,
            margin=dict(l=5, r=10, t=35, b=5)
        )
        fig_payback.update_layout(
            title="Estimated payback period",
            yaxis_title="Months"
        )
        show(fig_payback)

    retrofit_finance = pd.DataFrame({
        "Retrofit": [
            "BLDC ceiling fans",
            "SV-to-LED lighting"
        ],
        "Investment": [
            "₹63.66 lakh",
            "₹19,000"
        ],
        "Annual savings": [
            "₹5.16 lakh",
            "₹45,052"
        ],
        "Payback": [
            "148 months",
            "5 months"
        ]
    })

    st.dataframe(
        retrofit_finance,
        use_container_width=True,
        hide_index=True
    )

    st.markdown(
        "<div class='group-title' style='margin-top:28px;'>"
        "No-cost operational measures</div>",
        unsafe_allow_html=True
    )

    st.markdown("""
    - **UPS standby/float-charge audit (Ground Floor):**
      Ground Floor carries 75.5% of Block 3's estimated load, dominated
      by continuous-duty UPS banks. A physical audit of which UPS loads
      genuinely require 24/7 uptime versus which could be scheduled off
      during nights/holidays targets the largest load driver.
    - **Lab/classroom equipment power-down enforcement:**
      Enforcing an equipment shutdown checklist after scheduled lab/class
      hours prevents after-hours idle draw.
    - **Fan/lighting operating-hour review in low-occupancy spaces:**
      Regular checks that spaces like Electrical Labs and Drawing Halls
      are powered off when idle.
    """)

    note(
        "The operational measures are recommendations derived from the "
        "equipment schedule. Their savings have not been quantified or "
        "verified by metering."
    )
