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
INK3 = "#5A6561"       # tertiary text
RULE = "#C9C8C0"       # hairlines
GRID = "#D9D8D1"       # chart gridlines
GREEN = "#1F4E45"      # oxidised-copper dark
GREEN2 = "#5E8F84"
GREEN3 = "#A9C4BC"
SOLAR = "#C98A1B"      # solar amber
STEEL = "#5B6B73"      # grid electricity
BRICK = "#A5442F"      # warnings / limitations
FONT = "Public Sans, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"

# ============ REVISED STYLING ============
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Archivo:wght@400;600;700&family=Public+Sans:wght@400;500;600;700&display=swap');

:root {
  --paper:#ECEBE6; --ink:#1B2421; --ink2:#4A5753; --ink3:#5A6561; --rule:#C9C8C0;
  --green:#1F4E45; --solar:#C98A1B; --brick:#A5442F; --steel:#5B6B73;
}

/* Background & Main App */
.stApp {
    background: var(--paper);
    color: var(--ink);
    font-family: 'Public Sans', sans-serif;
}

header[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer { visibility: hidden; }

/* Responsive Container Layout */
.block-container, [data-testid="stMainBlockContainer"] { 
    max-width: 1400px !important;
    width: 95% !important;
    margin: 0 auto !important; 
    padding: 1.5rem 2rem 3rem 2rem !important; 
}

/* Sidebar Fixes */
[data-testid="stSidebar"] {
    background: #E1DFD8 !important;
    border-right: 1px solid var(--rule);
}
[data-testid="stSidebar"] .stMarkdown p, 
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] span {
    font-size: 13px !important;
    color: var(--ink) !important;
}

/* Masthead Header */
.masthead-title { 
    font-family: 'Archivo', sans-serif; 
    font-weight: 700; 
    font-size: 28px !important; 
    letter-spacing: -0.02em; 
    line-height: 1.2 !important; 
    color: var(--ink); 
    margin-bottom: 4px;
}

.masthead-sub { 
    color: var(--ink2); 
    font-size: 14px !important; 
    max-width: 850px !important; 
    line-height: 1.5 !important; 
    margin-bottom: 16px;
}

/* Tabs Styling */
.stTabs [data-baseweb="tab-list"] { gap: 16px; border-bottom: 1px solid var(--rule); }
.stTabs [data-baseweb="tab"] { background: transparent; padding: 10px 14px; height: auto; color: var(--ink2); font-size: 14px !important; font-weight: 500; }
.stTabs [aria-selected="true"] { color: var(--ink) !important; font-weight: 700; }
.stTabs [data-baseweb="tab-highlight"] { background: var(--green) !important; height: 3px; }
.stTabs [data-baseweb="tab-panel"] { padding-top: 20px; }

/* Hero KPIs */
.hero { 
    display: flex !important; 
    flex-direction: row !important;
    gap: 32px !important; 
    max-width: 100% !important; 
    margin: 16px 0 24px 0 !important; 
    background: rgba(255,255,255,0.4);
    padding: 20px 24px;
    border-radius: 8px;
    border: 1px solid var(--rule);
}

.hero > div { flex: 1; }

.hero-num { 
    font-family: 'Archivo', sans-serif; 
    font-weight: 700; 
    font-size: 36px !important; 
    line-height: 1.1 !important; 
    color: var(--ink); 
}

.hero-num.lead { color: var(--green); }
.hero-unit { font-family: 'Public Sans', sans-serif; font-size: 16px !important; font-weight: 500; color: var(--ink2); margin-left: 4px; }
.hero-label { margin-top: 6px; font-size: 14px !important; font-weight: 700; color: var(--ink); }
.hero-note { margin-top: 4px; font-size: 12px !important; line-height: 1.4 !important; color: var(--ink3); }

/* Typography Rules for Body & Prose */
p, li, label, span {
    font-size: 14px !important;
    line-height: 1.6 !important;
    color: var(--ink);
}

.sec { font-family: 'Archivo', sans-serif; font-weight: 700; font-size: 18px !important; margin: 24px 0 6px 0; color: var(--ink); }
.sec-sub { color: var(--ink2); font-size: 13px !important; line-height: 1.45 !important; margin-bottom: 12px; }
.fig-title { font-size: 14px !important; font-weight: 700; color: var(--ink); margin: 12px 0 4px 0; }
.fig-sub { font-size: 12px !important; color: var(--ink3); margin-bottom: 8px; }

.prose2 { display: flex !important; flex-direction: row !important; gap: 32px !important; margin: 16px 0 !important; }
.prose2 > div { flex: 1; }
.prose2 p { font-size: 14px !important; line-height: 1.6 !important; color: var(--ink); }

.note { font-size: 12px !important; line-height: 1.5 !important; color: var(--ink3); margin-top: 8px; }
.body { font-size: 14px !important; line-height: 1.6 !important; color: var(--ink); }

/* Ledgers & Tables */
.group-title { font-size: 14px !important; font-weight: 700; margin-bottom: 8px; color: var(--ink); }
.ledger { display: grid; grid-template-columns: 1fr auto; column-gap: 16px; width: 100%; }
.ledger .k { padding: 8px 0; border-bottom: 1px solid var(--rule); font-size: 13px !important; color: var(--ink2); }
.ledger .k small { display: block; font-size: 11px !important; color: var(--ink3); }
.ledger .v { padding: 8px 0; border-bottom: 1px solid var(--rule); font-size: 13px !important; font-weight: 700; color: var(--ink); text-align: right; }
.ledger-cols { display: flex !important; flex-direction: row !important; gap: 32px !important; margin-top: 12px !important; }
.ledger-cols > div { flex: 1; }

/* Caveats */
.caveat { border-left: 4px solid var(--solar); background: rgba(201, 138, 27, 0.08); padding: 12px 16px; margin: 16px 0; border-radius: 0 4px 4px 0; }
.caveat.brick { border-left-color: var(--brick); background: rgba(165, 68, 47, 0.08); }
.caveat-title { font-size: 14px !important; font-weight: 700; color: var(--ink); margin-bottom: 4px; }
.caveat-body { font-size: 13px !important; line-height: 1.5 !important; color: var(--ink2); }

/* Big Stat Numbers */
.stat-num { font-family: 'Archivo', sans-serif; font-weight: 700; font-size: 32px !important; color: var(--green); }
.stat-sub { font-size: 13px !important; color: var(--ink2); margin-top: 2px; }

/* Legend Row */
.legend-row { display: flex; flex-wrap: wrap; gap: 12px 24px; font-size: 13px !important; color: var(--ink); margin: 8px 0 16px 0; }
.sw { display: inline-block; width: 12px; height: 12px; margin-right: 6px; vertical-align: -1px; border-radius: 2px; }

/* Expanders */
[data-testid="stExpander"] { border: 1px solid var(--rule); border-radius: 4px; background: rgba(255,255,255,0.3); }

@media (max-width: 900px) {
  .hero, .prose2, .ledger-cols { flex-direction: column !important; gap: 16px !important; }
}
</style>
""", unsafe_allow_html=True)

# ============ SMALL HELPER FUNCTIONS ============
def section(title, sub=None):
    html = f"<div class='sec'>{title}</div>"
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

def style_fig(fig, height=350, legend=False, margin=None):
    fig.update_layout(
        height=height, template="simple_white",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT, color=INK, size=12),
        margin=margin or dict(l=0, r=0, t=20, b=10),
        showlegend=legend,
        legend=dict(orientation="h", y=1.12, x=0, font=dict(color=INK, size=12)),
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
st.sidebar.caption("Estimated Block 3 Solar Allocation based on 11.15% connected-load share.")
st.sidebar.markdown("---")
projection_years = st.sidebar.slider("Projection horizon (years)", 1, 10, 3)
st.sidebar.markdown("---")
month_range = st.sidebar.select_slider(
    "Month range (monthly chart)",
    options=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
    value=('Jan', 'Dec')
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
campus_solar_used_kwh = campus_solar_generated_kwh - campus_solar_exported_kwh
block3_solar_offset_kwh = (campus_solar_used_kwh * block3_share) if show_solar else 0.0

total_kwh = predictions['predicted_electricity_kwh'].sum()
block3_solar_offset_kwh = min(block3_solar_offset_kwh, total_kwh)
net_grid_kwh = max(total_kwh - block3_solar_offset_kwh, 0.0)

total_co2_gross = (total_kwh / 1000) * emission_factor
total_co2_net_grid = (net_grid_kwh / 1000) * emission_factor
solar_co2_avoided = (block3_solar_offset_kwh / 1000) * emission_factor

annual_diesel_liters = 18650
campus_diesel_co2 = (annual_diesel_liters * 2.68) / 1000
total_co2_block3_electricity = total_co2_net_grid

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

CAMPUS_ANNUAL_KWH = 1524486
ANNUAL_ANCHOR_KWH = CAMPUS_ANNUAL_KWH * block3_share
avg_weekly_kwh = total_kwh / (len(predictions) / 168)
nmbe = ((total_kwh - ANNUAL_ANCHOR_KWH) / ANNUAL_ANCHOR_KWH) * 100

floor_shares = {'Ground Floor': 0.75501, '1st Floor': 0.18176, 'Top Floor': 0.06323}
FLOOR_COLORS = [GREEN, GREEN2, GREEN3]

SCALING_FACTOR = 0.271081
calibrated_week = predictions['predicted_electricity_kwh'].iloc[:168].reset_index(drop=True)
raw_week = calibrated_week / SCALING_FACTOR
hours_axis = list(range(168))
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
    solar_note = ("Allocated share of campus solar" if show_solar else "Solar offset disabled")

    st.markdown(f"""
<div class='hero'>
<div>
<div class='hero-num lead'>{demand_val}<span class='hero-unit'>{demand_unit}/yr</span></div>
<div class='hero-label'>Annual electricity demand</div>
<div class='hero-note'>Calibrated to Block 3's share of the campus energy audit.</div>
</div>
<div>
<div class='hero-num'>{total_co2_block3_electricity:,.1f}<span class='hero-unit'>tCO₂/yr</span></div>
<div class='hero-label'>Annual carbon footprint</div>
<div class='hero-note'>Grid electricity after solar at {emission_factor:.3f} tCO₂/MWh.</div>
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
</div>
<div>
<p>The ground floor carries <b>75.5%</b> of weekly load ({avg_weekly_kwh * floor_shares['Ground Floor']:,.0f} kWh/wk), driven by central UPS banks.</p>
</div>
</div>
""", unsafe_allow_html=True)

    section("Monthly electricity demand", "Model-estimated demand by month.")

    predictions['month'] = predictions['timestamp'].dt.strftime('%b')
    predictions['month_num'] = predictions['timestamp'].dt.month
    monthly = predictions.groupby(['month_num', 'month'])['predicted_electricity_kwh'].sum().reset_index().sort_values('month_num')

    month_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    start_idx, end_idx = month_order.index(month_range[0]), month_order.index(month_range[1])
    selected_months = month_order[start_idx:end_idx + 1] if start_idx <= end_idx else month_order[start_idx:] + month_order[:end_idx + 1]
    monthly_filtered = monthly[monthly['month'].isin(selected_months)]

    peak_val = monthly_filtered['predicted_electricity_kwh'].max() if len(monthly_filtered) else 0
    bar_colors = [INK if v == peak_val else GREEN2 for v in monthly_filtered['predicted_electricity_kwh']]
    fig1 = go.Figure(go.Bar(
        x=monthly_filtered['month'], y=monthly_filtered['predicted_electricity_kwh'],
        marker_color=bar_colors,
        text=[f"{v:,.0f}" for v in monthly_filtered['predicted_electricity_kwh']],
        textposition="outside", cliponaxis=False, textfont=dict(size=12, color=INK2),
        hovertemplate="%{x}: %{y:,.0f} kWh<extra></extra>"
    ))
    style_fig(fig1, height=360)
    fig1.update_layout(bargap=0.35, yaxis_title="kWh")
    show(fig1)

# ----------------- TAB 7: AUDIT AND RETROFITS -----------------
with tab_audit:
    section("Data status")
    st.markdown("""
<div class='legend-row'>
<span><span class='sw' style='background:#1F4E45'></span><b>Measured / audited:</b> campus electricity, diesel, solar, connected load</span><br>
<span><span class='sw' style='background:#5B6B73'></span><b>ML-derived:</b> annual and monthly electricity prediction</span><br>
<span><span class='sw' style='background:#C98A1B'></span><b>Estimated allocation:</b> Block 3 solar share, floor-wise contribution</span>
</div>
""", unsafe_allow_html=True)

    caveat("Temporal scope",
           "The audit baseline (connected load, diesel, solar) is <b>Apr 2021–Mar 2022</b>. Weather data driving the ML model is <b>Jul 2025–Jul 2026</b>.")

    with st.expander("Methodology and data provenance", expanded=False):
        st.markdown("""
- **Block 3 annual anchor = campus total × 11.15%** (278 kW / 2,494 kW) ≈ 169,931 kWh.
- An XGBoost model trained on BDG2 supplies hourly shapes, scaled by factor 0.271 to match the anchor.
        """)

    section("Model inputs and evaluation")
    metrics_path = "model_metrics.json"
    model_metrics = None
    if os.path.exists(metrics_path):
        try:
            with open(metrics_path) as f:
                model_metrics = json.load(f)
        except Exception:
            model_metrics = None

    if model_metrics:
        st.markdown("<div class='fig-title'>Input features used by XGBoost</div>", unsafe_allow_html=True)
        st.code(", ".join(model_metrics["features_used"]), language="text")

        col_m1, col_m2 = st.columns(2, gap="large")
        with col_m1:
            fig_title("XGBoost vs linear regression baseline", "BDG2 held-out test set")
            xgb_m, base_m = model_metrics["xgboost"], model_metrics["baseline_linear_regression"]
            fig_metrics = go.Figure()
            metric_names = ['R²', 'MAE (kWh)', 'RMSE (kWh)']
            fig_metrics.add_trace(go.Bar(name='XGBoost', x=metric_names, y=[xgb_m['r2'], xgb_m['mae_kwh'], xgb_m['rmse_kwh']], marker_color=GREEN))
            fig_metrics.add_trace(go.Bar(name='Linear Regression', x=metric_names, y=[base_m['r2'], base_m['mae_kwh'], base_m['rmse_kwh']], marker_color=GREEN3))
            style_fig(fig_metrics, height=280, legend=True)
            fig_metrics.update_layout(barmode='group', bargap=0.3)
            show(fig_metrics)

        with col_m2:
            fig_title("XGBoost feature importance", "Gain-based")
            importances = model_metrics["feature_importance"]
            fig_imp = go.Figure(go.Bar(x=list(importances.values()), y=list(importances.keys()), orientation='h', marker_color=GREEN2))
            style_fig(fig_imp, height=280)
            fig_imp.update_layout(yaxis=dict(autorange="reversed"), bargap=0.3)
            show(fig_imp)

    caveat("Data boundary and limitations",
           "No Block 3-specific meter series was available. Figures are generated by ML predictions calibrated to campus totals.",
           tone="brick")

    section("Recommended energy-saving measures")
    r1, r2 = st.columns(2, gap="large")
    with r1:
        st.markdown("""
<div class='stat-num'>67,904<span class='hero-unit'>kWh/yr</span></div>
<div class='group-title' style='margin-top:6px;'>BLDC ceiling fan replacement</div>
<div class='body'>Audited campus retrofit. Replacing standard induction fans with BLDC fans.</div>
""", unsafe_allow_html=True)

    with r2:
        st.markdown("""
<div class='stat-num'>1,976<span class='hero-unit'>kWh/yr</span></div>
<div class='group-title' style='margin-top:6px;'>SV-to-LED lighting replacement</div>
<div class='body'>Audited campus retrofit. Replacing sodium-vapor/CFL fixtures with LEDs.</div>
""", unsafe_allow_html=True)
