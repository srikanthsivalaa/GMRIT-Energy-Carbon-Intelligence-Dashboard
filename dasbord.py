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

# ============ CONSTANTS & AUDIT PARAMETERS ============
CAMPUS_LOAD_KW  = 2494
BLOCK3_LOAD_KW  = 279.624
BLOCK3_SHARE    = BLOCK3_LOAD_KW / CAMPUS_LOAD_KW            # 0.1121186848436247 (~11.21%)

GRID_KVAH_11M   = 949_365
SOLAR_GEN_11M   = 867_317
SOLAR_EXP_11M   = 292_196
PF              = 0.99

SOLAR_USED_11M    = SOLAR_GEN_11M - SOLAR_EXP_11M               # 575,121 kWh
CAMPUS_ANNUAL_KWH = (GRID_KVAH_11M * PF + SOLAR_USED_11M) * 12 / 11  # 1,652,719 kWh
SOLAR_USED_KWH    = SOLAR_USED_11M * 12 / 11                    # 627,405 kWh
ANNUAL_ANCHOR_KWH = CAMPUS_ANNUAL_KWH * BLOCK3_SHARE          # 185,301 kWh

# Final notebook run (REFERENCE_YEAR 2024, 500,000-row BDG2 sample)
RAW_ANNUAL_KWH    = 925_209                                    # raw XGBoost total before scaling
SCALING_FACTOR    = ANNUAL_ANCHOR_KWH / RAW_ANNUAL_KWH         # 0.2003

EMISSION_FACTOR   = 0.71                                       # tCO2/MWh
BLOCK3_SQM        = 2594.74
BLOCK3_FLOORS_DESC = "G+2 (3 levels)"
BLOCK3_YEARBUILT   = 1998
DIESEL_LITRES_YR   = 18_650                                    # campus total (audit Table 3)

FLOOR_WEEKLY_KWH  = {"Ground Floor": 17_999.291, "1st Floor": 4_333.170, "Top Floor": 1_507.440}


# ============ DESIGN TOKENS ============
PAPER = "#ECEBE6"      # concrete / drafting paper
INK   = "#1B2421"      # primary text
INK2  = "#4A5753"      # secondary text
INK3  = "#5A6561"      # tertiary text (>= 4.5:1 on paper)
RULE  = "#C9C8C0"      # hairlines
GRID  = "#D9D8D1"      # chart gridlines
GREEN = "#1F4E45"      # oxidised-copper dark: building / primary data
GREEN2 = "#5E8F84"
GREEN3 = "#A9C4BC"
SOLAR = "#C98A1B"      # solar amber: only ever means solar or caution
STEEL = "#5B6B73"      # grid electricity
BRICK = "#A5442F"      # warnings / limitations
FONT  = "Public Sans, Helvetica Neue, Arial, sans-serif"

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

/* FIX: content now starts at the top (removed min-height:100vh + vertical centering) */
.block-container, [data-testid="stMainBlockContainer"] {
    max-width: 1200px !important;
    margin: 0 auto;
    padding: 1.5rem 2rem 3rem 2rem;
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

/* ---- caveats ---- */
.caveat { border-left: 3px solid var(--solar); padding: 2px 0 2px 12px; margin: 16px 0; max-width: 120ch; }
.caveat.brick { border-left-color: var(--brick); }
.caveat-title { font-size: 13px; font-weight: 600; color: var(--ink); margin-bottom: 2px; }
.caveat-body { font-size: 12px; line-height: 1.5; color: var(--ink2); }

/* ---- big stat ---- */
.stat-num { font-family: 'Archivo', sans-serif; font-stretch: 85%; font-weight: 300; font-size: 38px; letter-spacing: -0.02em; line-height: 1.05; color: var(--green); font-variant-numeric: tabular-nums; }
.stat-sub { font-size: 12.5px; color: var(--ink2); margin-top: 4px; }

/* FIX: legend is a 2-column grid instead of an uneven flex-wrap row */
.legend-row { display: grid; grid-template-columns: 1fr 1fr; gap: 8px 32px; font-size: 12px; color: var(--ink); margin: 4px 0 10px 0; }
.legend-row > span { display: block; position: relative; padding-left: 18px; line-height: 1.45; }
.sw { position: absolute; left: 0; top: 4px; width: 10px; height: 10px; margin: 0; }

/* tidy bullet lists so they align with the rest of the page */
[data-testid="stMarkdownContainer"] ul { padding-left: 1.1rem; margin: 4px 0 0 0; }
[data-testid="stMarkdownContainer"] li { margin-bottom: 4px; }

/* ---- widgets ---- */
.stRadio [data-testid="stWidgetLabel"] p { font-size: 13px; font-weight: 600; color: var(--ink) !important; }
.stRadio div[role="radiogroup"] { gap: 18px; }
.stRadio div[role="radiogroup"] label p { font-size: 13px; font-weight: 500; color: var(--ink) !important; }

/* FIX: expander. Newer Streamlit draws the border/background on the inner <details>,
   so both the wrapper and <details> must be overridden. */
[data-testid="stExpander"],
[data-testid="stExpander"] details {
    border: none !important;
    border-radius: 0 !important;
    background: transparent !important;
    box-shadow: none !important;
}
[data-testid="stExpander"] details {
    border-top: 1px solid var(--rule) !important;
    border-bottom: 1px solid var(--rule) !important;
}
[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary:hover,
[data-testid="stExpander"] summary:focus,
[data-testid="stExpander"] summary:active {
    background: transparent !important;
    outline: none !important;
    box-shadow: none !important;
}
[data-testid="stExpander"] summary p { font-weight: 600; font-size: 13px; }
[data-testid="stExpander"] summary:hover p { color: var(--green); }

/* FIX: global focus ring no longer hits the expander header */
:focus-visible { outline: 2px solid var(--green); outline-offset: 2px; }
[data-testid="stExpander"] summary:focus-visible { outline: none !important; }

@media (max-width: 860px) {
  .hero, .prose2, .ledger-cols, .ledger-cols.three, .legend-row { grid-template-columns: 1fr; gap: 20px; }
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


# ============ LOAD DATA & CORE CALCULATIONS ============
predictions_path = 'block3_predictions_full_year.csv'
if not os.path.exists(predictions_path):
    st.error(f"Required prediction CSV '{predictions_path}' not found in working directory.")
    st.stop()

df = pd.read_csv(predictions_path)
df['timestamp'] = pd.to_datetime(df['timestamp'])

# Standardized Calculation Block
total_kwh        = df["predicted_electricity_kwh"].sum()
solar_offset_kwh = min(SOLAR_USED_KWH * BLOCK3_SHARE, total_kwh)    # 70,344 kWh
net_grid_kwh     = max(total_kwh - solar_offset_kwh, 0)             # 114,957 kWh
solar_pct        = solar_offset_kwh / total_kwh * 100               # 38.0%

co2_gross = total_kwh / 1000 * EMISSION_FACTOR                        # 131.6 tCO2
co2_solar = solar_offset_kwh / 1000 * EMISSION_FACTOR                 # 49.9 tCO2
co2_net   = net_grid_kwh / 1000 * EMISSION_FACTOR                     # 81.6 tCO2

eui_gross = total_kwh / BLOCK3_SQM                                  # 71.4 kWh/m2
eui_net   = net_grid_kwh / BLOCK3_SQM                               # 44.3 kWh/m2
co2_m2    = co2_net * 1000 / BLOCK3_SQM                              # 31.5 kgCO2/m2

fl_tot   = sum(FLOOR_WEEKLY_KWH.values())
fl_share = {k: v / fl_tot for k, v in FLOOR_WEEKLY_KWH.items()}      # Ground: 75.5%, 1st: 18.2%, Top: 6.3%


# ============ SIDEBAR CONTROLS ============
st.sidebar.header("Model controls")
emission_factor_input = st.sidebar.slider("CEA Grid Emission Factor (tCO2/MWh)", 0.65, 0.80, float(EMISSION_FACTOR), 0.001)
usage_growth = st.sidebar.slider("Annual usage growth (%)", 0.0, 5.0, 2.0, 0.5)
climate_trend = st.sidebar.slider("Climate warming trend (%)", 0.0, 2.0, 0.5, 0.1)
st.sidebar.markdown("---")
show_solar = st.sidebar.checkbox("Include solar PV offset", value=True)
st.sidebar.caption(
    f"Estimated Block 3 Solar Allocation — based on {BLOCK3_SHARE:.2%} connected-load share; "
    f"Block 3-specific solar metering unavailable. Campus solar used on site ({SOLAR_USED_KWH:,.0f} kWh/yr, "
    f"annualised from 11 audit months) is from the audit; the Block 3 share is a scenario allocation, not a measured quantity."
)
st.sidebar.markdown("---")
projection_years = st.sidebar.slider("Projection horizon (years)", 1, 10, 3)
st.sidebar.markdown("---")
month_range = st.sidebar.select_slider(
    "Month range (monthly chart)",
    options=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
    value=('Jan', 'Dec')
)

# Sidebar dynamic emission adjustments
active_solar_offset = solar_offset_kwh if show_solar else 0.0
active_net_grid     = max(total_kwh - active_solar_offset, 0.0)
active_co2_net      = (active_net_grid / 1000) * emission_factor_input
active_co2_solar    = (active_solar_offset / 1000) * emission_factor_input
active_solar_pct    = (active_solar_offset / total_kwh * 100) if total_kwh > 0 else 0.0
active_carbon_m2    = (active_co2_net * 1000) / BLOCK3_SQM

avg_weekly_kwh      = total_kwh / (len(df) / 168)
FLOOR_COLORS        = [GREEN, GREEN2, GREEN3]

raw_annual_kwh      = RAW_ANNUAL_KWH
diff_before_pct     = ((raw_annual_kwh - ANNUAL_ANCHOR_KWH) / ANNUAL_ANCHOR_KWH) * 100   # +399.3%


# ============ HEADER ============
st.markdown(f"""
<div class='masthead-title'>Block 3 energy intelligence</div>
""", unsafe_allow_html=True)
st.caption(
    f"GMRIT, Rajam. Scaled to Block 3's {BLOCK3_SHARE:.2%} connected-load share "
    f"({BLOCK3_LOAD_KW} of {CAMPUS_LOAD_KW} kW) of the audited campus consumption."
)

# ============ TABS ============
tab_exec, tab_bim, tab_flow, tab_floor, tab_proj, tab_scaling, tab_audit = st.tabs([
    "Overview",
    "Building",
    "Energy flow",
    "Floors and carbon",
    "Forecast",
    "Scaling",
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
<div class='hero-note'>Model estimate, scaled to Block 3's {BLOCK3_SHARE:.2%} share of the campus audit. Not a meter reading.</div>
</div>
<div>
<div class='hero-num'>{active_co2_net:,.1f}<span class='hero-unit'>tCO₂/yr</span></div>
<div class='hero-label'>Annual carbon footprint</div>
<div class='hero-note'>Grid electricity after solar, at {emission_factor_input:.3f} tCO₂/MWh. Diesel excluded.</div>
</div>
<div>
<div class='hero-num'>{active_solar_pct:.1f}<span class='hero-unit'>%</span></div>
<div class='hero-label'>Solar contribution</div>
<div class='hero-note'>{solar_note}</div>
</div>
</div>
""", unsafe_allow_html=True)

    st.write(
        f"Total modelled demand is {total_kwh:,.0f} kWh. Solar offsets {active_solar_pct:.1f}% "
        f"({active_solar_offset:,.0f} kWh), leaving {active_net_grid:,.0f} kWh on the grid."
    )
    st.write(
        f"Net grid EUI is {eui_net:.1f} kWh/m²/yr, or {eui_gross:.1f} kWh/m²/yr before the solar offset."
    )

    st.caption(
        f"The annual total is scaled to Block 3's {BLOCK3_SHARE:.2%} share of the campus audit "
        f"consumption. EUI is reported as a project-level indicator."
    )

    note("Held-out BDG2 reference-dataset R² = 0.892, which is not a Block 3 validation.")

    # ---- primary visualisation ----
    section("Monthly electricity demand", "Model-estimated, not metered. Use the month range in the sidebar to focus on part of the year.")

    df['month'] = df['timestamp'].dt.strftime('%b')
    df['month_num'] = df['timestamp'].dt.month
    monthly = df.groupby(['month_num', 'month'])['predicted_electricity_kwh'].sum().reset_index().sort_values('month_num')

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
    note("The darkest bar marks the peak month in the selected range. July has 32 days in the weather window "
         "(29 Jul 2025 to 29 Jul 2026), so its total is slightly inflated.")

    # ---- supply mix ----
    fig_title("Where the electricity comes from", "Grid versus allocated solar, Block 3 estimate")
    fig_mix = go.Figure()
    fig_mix.add_trace(go.Bar(
        y=[""], x=[active_net_grid], orientation="h", name="Net grid electricity",
        marker_color=STEEL, text=[f"Grid  {active_net_grid:,.0f} kWh"], textposition="inside",
        insidetextanchor="start", textfont=dict(color="#FFFFFF", size=11.5),
        hovertemplate="Net grid: %{x:,.0f} kWh<extra></extra>"
    ))
    fig_mix.add_trace(go.Bar(
        y=[""], x=[active_solar_offset], orientation="h", name="Solar offset (estimated allocation)",
        marker_color=SOLAR, text=[f"Solar  {active_solar_offset:,.0f} kWh" if active_solar_offset > 0 else ""],
        textposition="inside", insidetextanchor="start", textfont=dict(color=INK, size=11.5),
        hovertemplate="Solar offset: %{x:,.0f} kWh<extra></extra>"
    ))
    style_fig(fig_mix, height=110, margin=dict(l=0, r=0, t=6, b=0))
    fig_mix.update_layout(barmode="stack", bargap=0.1)
    fig_mix.update_xaxes(visible=False)
    fig_mix.update_yaxes(visible=False)
    show(fig_mix)
    note("Diesel is excluded here. Diesel is reported separately in audited litres only.")

    # ---- ledger ----
    section("Supporting figures")
    left = ledger_html([
        ("Solar offset (allocated)", f"{active_solar_offset:,.0f} kWh", f"{BLOCK3_SHARE:.2%} load share" if show_solar else "Disabled"),
        ("CO₂ avoided by solar", f"{active_co2_solar:,.1f} tCO₂", "Allocated solar share (assumption)"),
        ("Campus diesel generator reference", f"{DIESEL_LITRES_YR:,.0f} L/yr", "Audited campus level, CO₂ excluded"),
    ], "Energy and carbon")
    right = ledger_html([
        ("Gross electricity EUI", f"{eui_gross:.1f} kWh/m²/yr", "Before solar, ML demand / area"),
        ("Net grid EUI after solar", f"{eui_net:.1f} kWh/m²/yr", "Grid electricity after solar offset / area"),
        ("Electricity carbon intensity", f"{active_carbon_m2:.1f} kgCO₂/m²/yr", "Block 3 electricity only"),
        ("Built-up area (gbXML/BIM)", f"{BLOCK3_SQM:,.2f} m²", f"{BLOCK3_FLOORS_DESC}, built {BLOCK3_YEARBUILT}"),
        ("ECBC 2017 EPI Ratio", "Not computed", "Needs a Standard Building simulation."),
    ], "Building performance")
    st.markdown(f"<div class='ledger-cols'><div>{left}</div><div>{right}</div></div>", unsafe_allow_html=True)


# ----------------- TAB 2: BUILDING (BIM) -----------------
with tab_bim:
    section("Building and level cutaways", "Revit BIM front views linked to the room-level equipment schedule and load shares.", first=True)

    floor_views = {
        "Full Building (Front View)": {
            "img": "total block front view.jpeg",
            "share": "100% of Building Demand",
            "weekly_energy": f"{avg_weekly_kwh:,.0f} kWh/wk",
            "description": f"Reinforced concrete institutional frame ({BLOCK3_FLOORS_DESC} with open central courtyard), {BLOCK3_SQM:,.2f} m² built-up area built in {BLOCK3_YEARBUILT}."
        },
        "Ground Floor Cut (Front View)": {
            "img": "ground floor cut front view.jpeg",
            "share": f"{fl_share['Ground Floor']:.1%} of Total Load",
            "weekly_energy": f"{avg_weekly_kwh * fl_share['Ground Floor']:,.0f} kWh/wk",
            "description": "High-draw zone containing Central UPS banks, substation step-down transformers, and Electrical Machines / Power Systems lab motors."
        },
        "1st Floor Cut (Front View)": {
            "img": "first floor cut front view.jpeg",
            "share": f"{fl_share['1st Floor']:.1%} of Total Load",
            "weekly_energy": f"{avg_weekly_kwh * fl_share['1st Floor']:,.0f} kWh/wk",
            "description": "Mid-draw academic zone featuring computer labs, departmental lecture classrooms, and faculty rooms."
        },
        "2nd / Top Floor Cut (Front View)": {
            "img": "2nd floor cut front view.jpeg",
            "share": f"{fl_share['Top Floor']:.1%} of Total Load",
            "weekly_energy": f"{avg_weekly_kwh * fl_share['Top Floor']:,.0f} kWh/wk",
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

    kwh_ground = total_kwh * fl_share['Ground Floor']
    kwh_first  = total_kwh * fl_share['1st Floor']
    kwh_top    = total_kwh * fl_share['Top Floor']

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
            pad=18, thickness=12,
            line=dict(color=PAPER, width=0),
            label=sankey_nodes,
            color=[STEEL, SOLAR, INK, GREEN, GREEN2, GREEN3]
        ),
        link=dict(
            source=[0, 1, 2, 2, 2],
            target=[2, 2, 3, 4, 5],
            value=[active_net_grid, active_solar_offset, kwh_ground, kwh_first, kwh_top],
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
    section("Floor-wise electricity", "Derived from the equipment schedule (rated power × timetable hours), not from floor-level electricity meters.", first=True)

    col_floor1, col_floor2 = st.columns([1.5, 1], gap="large")
    with col_floor1:
        floor_names = list(fl_share.keys())
        floor_weekly = [avg_weekly_kwh * s for s in fl_share.values()]
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
<div class='stat-sub'>{fl_share['Ground Floor']:.1%} of total load, from the equipment schedule</div>
<div class='body' style='margin-top:12px;'>Floor split is read directly from the 'Floor Level' column of the room-level equipment schedule (rated power × timetable hours), not a BIM-inferred assignment. Major ground-floor loads: central UPS banks, substation transformers, and Electrical Machines/Power Systems lab motors.</div>
</div>
""", unsafe_allow_html=True)

    section("Floor-wise carbon allocation", "Electricity only. Diesel is excluded.")
    floor_co2 = {
        'Ground Floor': active_co2_net * fl_share['Ground Floor'],
        '1st Floor': active_co2_net * fl_share['1st Floor'],
        'Top Floor': active_co2_net * fl_share['Top Floor'],
    }

    fig_co2_bar = go.Figure(go.Bar(
        x=list(floor_co2.values()),
        y=list(floor_co2.keys()),
        orientation='h',
        marker_color=FLOOR_COLORS, marker_line_width=0,
        text=[f"{v:.1f} tCO2/yr ({v / active_co2_net * 100:.0f}%)" if active_co2_net > 0 else f"{v:.1f} tCO2/yr" for v in floor_co2.values()],
        textposition='outside', cliponaxis=False, textfont=dict(color=INK, size=11),
        hovertemplate="%{y}: %{x:.1f} tCO2/yr<extra></extra>"
    ))
    style_fig(fig_co2_bar, height=230, margin=dict(l=0, r=130, t=6, b=0))
    fig_co2_bar.update_layout(xaxis_title="tCO2/yr", yaxis=dict(autorange="reversed"), bargap=0.4)
    fig_co2_bar.update_xaxes(showgrid=True, gridcolor=GRID)
    fig_co2_bar.update_yaxes(showgrid=False)
    show(fig_co2_bar)
    note(f"Total Block 3 electricity-related footprint: {active_co2_net:,.1f} tCO2/yr. Campus diesel ({DIESEL_LITRES_YR:,.0f} L/yr) is excluded from this figure. "
         "Floor shares are estimates from rated equipment; the Ground Floor share may be an upper bound.")


# ----------------- TAB 5: FORECAST -----------------
with tab_proj:
    section("Temperature response", "How the trained model's hourly demand changes with outdoor temperature.", first=True)

    temp_cut = pd.cut(df['temperature_C'], bins=range(10, 46, 2))
    temp_binned = df.groupby(temp_cut, observed=True)['predicted_electricity_kwh'].mean().reset_index()
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

    section("Scenario projection", f"A what-if computed from assumed growth ({usage_growth}%/yr) and climate-trend ({climate_trend}%/yr) rates applied to the ML-estimated base year.")

    years = [2026 + i for i in range(projection_years)]
    proj_kwh = [total_kwh * ((1 + (usage_growth + climate_trend) / 100) ** i) for i in range(projection_years)]
    proj_net = [max(k - active_solar_offset, 0.0) for k in proj_kwh]
    proj_co2 = [(k / 1000) * emission_factor_input for k in proj_net]

    fig4 = go.Figure(go.Bar(
        x=[str(y) for y in years], y=proj_co2, marker_color=STEEL, marker_line_width=0,
        text=[f"{v:,.1f}" for v in proj_co2], textposition="outside", cliponaxis=False,
        textfont=dict(color=INK2, size=11),
        hovertemplate="%{x}: %{y:,.1f} tCO2<extra></extra>"
    ))
    style_fig(fig4, height=330, margin=dict(l=0, r=0, t=22, b=0))
    fig4.update_layout(yaxis_title="tCO2 / year", bargap=0.45)
    show(fig4)


# ----------------- TAB 6: SCALING -----------------
with tab_scaling:
    section("Annual scaling against the campus-share anchor", first=True)

    caveat(
        f"Consistency check, not validation",
        f"The model output is scaled so its annual total equals Block 3's share ({BLOCK3_SHARE:.2%}) of the audited campus consumption. The match is therefore true by construction."
    )

    fig_title("Hourly raw versus scaled prediction", "First week of weather data")
    calibrated_week = df['predicted_electricity_kwh'].iloc[:168].reset_index(drop=True)
    raw_week = calibrated_week / SCALING_FACTOR
    hours_axis = list(range(168))

    fig_1wk = go.Figure()
    fig_1wk.add_trace(go.Scatter(
        x=hours_axis, y=raw_week, mode='lines', name='Raw XGBoost (ML-derived, pre-scaling)',
        line=dict(color=STEEL, width=1.5, dash='dot')
    ))
    fig_1wk.add_trace(go.Scatter(
        x=hours_axis, y=calibrated_week, mode='lines', name='Scaled XGBoost (scaled ML estimate)',
        line=dict(color=GREEN, width=2.5)
    ))
    style_fig(fig_1wk, height=360, legend=True, margin=dict(l=0, r=0, t=28, b=0))
    fig_1wk.update_layout(xaxis_title="Hour of week (0-167)", yaxis_title="kWh")
    show(fig_1wk)

    section("Summary metrics")
    anchor_col = ledger_html([
        ("Audit-share annual anchor", f"{ANNUAL_ANCHOR_KWH:,.0f} kWh", f"Campus {CAMPUS_ANNUAL_KWH:,.0f} kWh × {BLOCK3_SHARE:.2%} connected-load share. An allocation, not a meter reading."),
        ("Raw ML annual total", f"{raw_annual_kwh:,.0f} kWh", "Pre-scaling"),
    ], "Before")
    mid_col = ledger_html([
        ("Scaled ML annual total", f"{total_kwh:,.0f} kWh"),
        ("Scaling factor", f"{SCALING_FACTOR:.4f}"),
    ], "Scaling")
    after_col = ledger_html([
        ("Difference before scaling", f"{diff_before_pct:+.2f}%"),
        ("Difference after scaling", "0.00%"),
    ], "Difference")
    st.markdown(f"<div class='ledger-cols three'><div>{anchor_col}</div><div>{mid_col}</div><div>{after_col}</div></div>", unsafe_allow_html=True)

    caveat("Why the equipment schedule is not the scaling target",
           f"The equipment schedule (rated power × timetable hours) totals {fl_tot:,.2f} kWh/week, about {fl_tot * 52:,.0f} kWh/year, which would be {fl_tot * 52 / CAMPUS_ANNUAL_KWH * 100:.0f}% of the entire campus consumption. It assumes equipment runs at rated power for all scheduled hours, so it likely overstates real energy use. It is used only for the floor-wise shares.")


# ----------------- TAB 7: AUDIT AND RETROFITS -----------------
with tab_audit:
    section("Data status", first=True)
    st.markdown(f"""
<div class='legend-row'>
<span><span class='sw' style='background:{GREEN}'></span><b>Measured / audited:</b> campus electricity (utility and solar bills), diesel, solar, Block 3 connected load ({BLOCK3_LOAD_KW} of {CAMPUS_LOAD_KW} kW)</span>
<span><span class='sw' style='background:{STEEL}'></span><b>ML-derived:</b> annual and monthly electricity prediction</span>
<span><span class='sw' style='background:{SOLAR}'></span><b>Estimated allocation:</b> Block 3 solar share ({BLOCK3_SHARE:.2%}), equipment schedule, floor-wise contribution and emissions</span>
<span><span class='sw' style='background:{GREEN3}'></span><b>Assumption / scenario:</b> emission factors, operating hours (official timetable, not metered), growth and climate-trend rates, future projections</span>
</div>
""", unsafe_allow_html=True)

    caveat("Temporal scope",
           f"The audit baseline (connected load, diesel, solar generation) is <b>Apr 2021–Feb 2022 (11 billed months, annualised ×12/11)</b>. The weather dataset used to drive the ML model is <b>Jul 2025–Jul 2026</b> (NASA POWER, local solar time). These are different periods. The annual Block 3 electricity figure on this dashboard is therefore a <b>scaled scenario estimate</b>: the model's weather-driven pattern for a recent year, rescaled to match Block 3's {BLOCK3_SHARE:.2%} share of the audited campus annual energy.")

    with st.expander("Methodology and data provenance (read before presenting)", expanded=False):
        st.markdown(f"""
**How is Block 3's annual electricity (~{total_kwh/1e3:.0f} MWh) derived, and how does it relate to the campus audit total ({CAMPUS_ANNUAL_KWH:,.0f} kWh/yr)?**

- The campus audit figure ({CAMPUS_ANNUAL_KWH:,.0f} kWh/yr, Apr 2021–Feb 2022 annualized) is a **measured utility bill total** for the entire campus, across all blocks, hostels, and staff quarters.
- **Block 3 annual anchor = campus total × {BLOCK3_SHARE:.2%}** (Block 3's connected-load share: {BLOCK3_LOAD_KW} kW of {CAMPUS_LOAD_KW} kW) ≈ {ANNUAL_ANCHOR_KWH:,.0f} kWh. This is an **allocation**, not a Block 3 meter reading.
- An XGBoost model trained on BDG2 (604 education buildings, mainly North American and European) supplies the **hourly and seasonal shape** from Block 3's weather and physical attributes. A single scaling factor sets the annual total equal to the anchor.
- The connected-load share describes **peak connected capacity**, not energy consumed.
        """)

    section("Recommended energy-saving measures", "The two retrofits come from the campus audit. The operational measures are derived from the equipment schedule.")
    r1, r2 = st.columns(2, gap="large")
    with r1:
        st.markdown("""
<div class='stat-num'>67,904<span class='hero-unit'>kWh/yr</span></div>
<div class='group-title' style='margin-top:8px;'>BLDC ceiling fan replacement</div>
<div class='stat-sub'>Audited retrofit. Estimated savings, campus-wide.</div>
<div class='body' style='margin-top:8px;'>Audit estimate for 2,122 ceiling fans campus-wide (80 W to 40 W): investment ₹63.66 lakh, savings ₹5.16 lakh/yr, payback 148 months.</div>
""", unsafe_allow_html=True)

    with r2:
        st.markdown("""
<div class='stat-num'>1,976<span class='hero-unit'>kWh/yr</span></div>
<div class='group-title' style='margin-top:8px;'>SV-to-LED lighting replacement</div>
<div class='stat-sub'>Audited retrofit. Estimated savings, campus-wide.</div>
<div class='body' style='margin-top:8px;'>Audit estimate for 19 sodium-vapor lamps campus-wide (250 W to 150 W): investment ₹19,000, savings ₹45,052/yr, payback 5 months.</div>
""", unsafe_allow_html=True)

    st.markdown("<div class='group-title' style='margin-top:28px;'>No-cost operational measures</div>", unsafe_allow_html=True)
    st.markdown("""
- **UPS standby/float-charge audit (Ground Floor):** Ground Floor carries 75.5% of Block 3's estimated load, dominated by continuous-duty UPS banks. A physical audit of which UPS loads genuinely require 24/7 uptime versus which could be scheduled off during nights/holidays targets the largest load driver.
- **Lab/classroom equipment power-down enforcement:** Enforcing an equipment shutdown checklist after scheduled lab/class hours prevents after-hours idle draw.
- **Fan/lighting operating-hour review in low-occupancy spaces:** Regular checks that spaces like Electrical Labs and Drawing Halls are powered off when idle.
""")
