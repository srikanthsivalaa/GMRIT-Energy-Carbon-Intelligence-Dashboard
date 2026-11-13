import pathlib
import numpy as np
import pandas as pd
import streamlit as st
from block3_constants import *

st.set_page_config(page_title="Block 3 energy intelligence", layout="wide")
CSV = pathlib.Path(__file__).parent / "block3_predictions_full_year.csv"

@st.cache_data
def load(path):
    df = pd.read_csv(path)
    tcol = next((c for c in df.columns if c.lower() in ("timestamp", "datetime", "time", "date", "hour_timestamp")), df.columns[0])
    df["ts"] = pd.to_datetime(df[tcol])
    pcol = next((c for c in df.columns if "predicted" in c.lower() and "raw" not in c.lower()), None)
    if pcol is None:
        pcol = [c for c in df.select_dtypes("number").columns][-1]
    df["kwh"] = df[pcol].astype(float)
    return df[["ts", "kwh"]]

try:
    df = load(CSV)
except Exception as e:
    st.error(f"Could not read {CSV.name}: {e}")
    st.stop()

# ---------- core numbers (all derived from block3_constants and the CSV) ----------
total_kwh        = df["kwh"].sum()
solar_offset_kwh = min(SOLAR_USED_KWH * BLOCK3_SHARE, total_kwh)
net_grid_kwh     = max(total_kwh - solar_offset_kwh, 0)
solar_pct        = solar_offset_kwh / total_kwh * 100
co2_gross = total_kwh / 1000 * EMISSION_FACTOR
co2_solar = solar_offset_kwh / 1000 * EMISSION_FACTOR
co2_net   = net_grid_kwh / 1000 * EMISSION_FACTOR
eui_gross = total_kwh / BLOCK3_SQM
eui_net   = net_grid_kwh / BLOCK3_SQM
co2_m2    = co2_net * 1000 / BLOCK3_SQM
fl_tot    = sum(FLOOR_WEEKLY_KWH.values())
fl_share  = {k: v / fl_tot for k, v in FLOOR_WEEKLY_KWH.items()}
weekly_total = total_kwh / (len(df) / 168)

st.title("Block 3 energy intelligence")
st.caption(f"GMRIT, Rajam. XGBoost demand shape scaled to Block 3's {BLOCK3_SHARE:.2%} connected-load share "
           f"({BLOCK3_LOAD_KW} of {CAMPUS_LOAD_KW} kW) of the audited campus consumption. "
           "These are scenario estimates, not measurements.")

tabs = st.tabs(["Overview", "Monthly demand", "Floors and carbon", "Scaling", "Sensitivity", "Audit data"])

# ---------- Overview ----------
with tabs[0]:
    c1, c2, c3 = st.columns(3)
    c1.metric("Annual electricity demand", f"{total_kwh/1000:,.1f} MWh/yr")
    c2.metric("Net grid carbon", f"{co2_net:,.1f} tCO\u2082/yr")
    c3.metric("Solar contribution (allocated)", f"{solar_pct:.1f} %")
    st.write(f"Total modelled demand is {total_kwh:,.0f} kWh. Allocated solar offsets {solar_offset_kwh:,.0f} kWh "
             f"({solar_pct:.1f}%), leaving {net_grid_kwh:,.0f} kWh on the grid.")
    st.write(f"Net grid EUI is {eui_net:.1f} kWh/m\u00b2/yr, or {eui_gross:.1f} kWh/m\u00b2/yr before the solar offset.")
    st.write(f"BDG2 held-out R\u00b2 = {MODEL_METRICS['XGBoost (selected)']['R2']:.3f}. This is not a Block 3 validation; "
             f"the annual total is set by the {BLOCK3_SHARE:.2%} allocation and the model supplies only the hourly and seasonal shape.")
    t = pd.DataFrame({"Quantity": ["Gross CO\u2082 (before solar)", "CO\u2082 avoided by allocated solar", "Net grid CO\u2082",
                                   "Gross EUI", "Net EUI", "Net carbon intensity"],
                      "Value": [f"{co2_gross:.1f} tCO\u2082/yr", f"{co2_solar:.1f} tCO\u2082/yr", f"{co2_net:.1f} tCO\u2082/yr",
                                f"{eui_gross:.1f} kWh/m\u00b2/yr", f"{eui_net:.1f} kWh/m\u00b2/yr", f"{co2_m2:.1f} kgCO\u2082/m\u00b2/yr"]})
    st.table(t)
    diesel_t = BLOCK3_DIESEL_L * DIESEL_KGCO2_PER_L / 1000
    st.caption(f"Campus diesel is {CAMPUS_DIESEL_L:,} L/yr in the audit. An allocated {BLOCK3_DIESEL_L:,} L for Block 3 "
               f"(SDG 7 allocation, not metered) would be about {diesel_t:.1f} tCO\u2082; it is shown here only and is not "
               "included in net grid carbon. EUI is a project-level indicator, not an ECBC compliance result.")

# ---------- Monthly ----------
with tabs[1]:
    m = df.assign(month=df["ts"].dt.month, day=df["ts"].dt.date).groupby("month").agg(kwh=("kwh", "sum"), days=("day", "nunique"))
    m["kWh per day"] = m["kwh"] / m["days"]
    m.index = [pd.Timestamp(2000, i, 1).strftime("%b") for i in m.index]
    per_day = st.checkbox("Show kWh per day (July has 32 days in this weather window)", value=False)
    st.bar_chart(m["kWh per day"] if per_day else m["kwh"])
    st.dataframe(m.rename(columns={"kwh": "kWh", "days": "Days in window"}).round(1))
    st.caption("Model-estimated, not metered. The pattern is a weather-driven trend learned from BDG2 buildings.")

# ---------- Floors ----------
with tabs[2]:
    fl = pd.DataFrame({"Share of demand": {k: s * 100 for k, s in fl_share.items()},
                       "Weekly demand (kWh/wk)": {k: s * weekly_total for k, s in fl_share.items()},
                       "Annual carbon (tCO\u2082/yr)": {k: s * co2_net for k, s in fl_share.items()}})
    st.dataframe(fl.round(1))
    st.bar_chart(fl["Weekly demand (kWh/wk)"])
    st.bar_chart(fl["Annual carbon (tCO\u2082/yr)"])
    st.caption("Floor shares come from the project's equipment schedule (rated power x timetable hours). "
               "They are estimates, not floor-level measurements; the Ground Floor share may be an upper bound.")

# ---------- Scaling ----------
with tabs[3]:
    st.subheader("How the annual total is set")
    st.table(pd.DataFrame({"Step": ["Utility energy, 11 months", "Converted at PF 0.99", "On-site solar use, 11 months",
                                    "Campus use, 11 months", "Annualised (x 12/11)", f"Block 3 share ({BLOCK3_SHARE:.2%})",
                                    "Allocated annual demand (anchor)", "Raw model total", "Scaling factor"],
                           "Value": [f"{GRID_KVAH_11M:,} kVAh", f"{GRID_KVAH_11M*PF:,.0f} kWh", f"{SOLAR_USED_11M:,} kWh",
                                     f"{GRID_KVAH_11M*PF+SOLAR_USED_11M:,.0f} kWh", f"{CAMPUS_ANNUAL_KWH:,.0f} kWh",
                                     f"{BLOCK3_LOAD_KW} / {CAMPUS_LOAD_KW} kW", f"{ANNUAL_ANCHOR_KWH:,.0f} kWh",
                                     f"{RAW_ANNUAL_KWH:,} kWh", f"{SCALING_FACTOR:.4f}"]}))
    st.warning("The annual total equals the anchor by construction. This is a scaling step, not a validation of Block 3 demand.")
    st.table(pd.DataFrame(MODEL_METRICS).T.rename(columns={"R2": "R\u00b2", "MAE": "MAE (kWh)", "RMSE": "RMSE (kWh)"}))
    st.caption("BDG2 held-out scores (random record-level split). They do not measure performance on a new building.")

# ---------- Sensitivity ----------
with tabs[4]:
    rows = []
    for s in (0.08, 0.10, BLOCK3_SHARE, 0.13, 0.15):
        d = CAMPUS_ANNUAL_KWH * s; so = SOLAR_USED_KWH * s; n = d - so
        rows.append({"Share": f"{s:.2%}" + (" (adopted)" if abs(s - BLOCK3_SHARE) < 1e-9 else ""),
                     "Annual demand (kWh)": round(d), "Net grid CO\u2082 (t/yr)": round(n / 1000 * EMISSION_FACTOR, 1),
                     "Gross EUI": round(d / BLOCK3_SQM, 1), "Net EUI": round(n / BLOCK3_SQM, 1)})
    st.table(pd.DataFrame(rows))
    st.caption("The connected-load share is not necessarily the energy share; results scale almost linearly with it.")

# ---------- Audit data ----------
with tabs[5]:
    st.table(pd.DataFrame({
        "Item": ["Campus connected load", "Block 3 connected load", "Utility energy (11 months)", "Solar generated (11 months)",
                 "Solar exported (11 months)", "Campus use (11 months)", "Diesel"],
        "Value": [f"{CAMPUS_LOAD_KW} kW", f"{BLOCK3_LOAD_KW} kW", f"{GRID_KVAH_11M:,} kVAh", f"{SOLAR_GEN_11M:,} kWh",
                  f"{SOLAR_EXP_11M:,} kWh", f"{GRID_KVAH_11M+SOLAR_GEN_11M-SOLAR_EXP_11M:,}", f"{CAMPUS_DIESEL_L:,} L/yr (campus)"],
        "Note": ["Audit Table 8", "Audit Table 11 (summary shows 278 kW)", "Audit Tables 5 and 6",
                 "Audit Table 5", "Monthly sum; the audit's printed total (261,417) does not add up",
                 "Audit table covers April 2021 to February 2022; March is blank", "Campus total; Block 3 allocation is shown separately"]}))
