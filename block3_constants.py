"""Single source of truth for Block 3 numbers.
Used by BOTH the notebook and the dashboard, so they can never disagree.
Change a value here once; re-run the notebook; push to GitHub.

RULE: the audit values below are CAMPUS totals. Block 3 values are always
derived from them with BLOCK3_SHARE. Never type Block 3 numbers in these lines."""

# ---- Audit: East Coast Sustainable Pvt. Ltd., April 2022 (Tables 3, 5, 8, 11) ----
CAMPUS_LOAD_KW  = 2494          # Table 8 total
BLOCK3_LOAD_KW  = 279.624       # Table 11 (appliance list); Table 8 summary rounds to 278
BLOCK3_SHARE    = BLOCK3_LOAD_KW / CAMPUS_LOAD_KW        # 0.112119

GRID_KVAH_11M   = 949_365       # Table 5, CAMPUS utility energy (kVAh), Apr 2021 - Feb 2022
SOLAR_GEN_11M   = 867_317       # Table 5, CAMPUS solar generated (kWh)
SOLAR_EXP_11M   = 292_196       # Table 5, CAMPUS solar exported, monthly entries summed (printed total 261,417 is wrong)
PF              = 0.99          # audit average power factor
MONTHS_IN_AUDIT = 11            # March 2022 row is blank in the audit

SOLAR_USED_11M    = SOLAR_GEN_11M - SOLAR_EXP_11M                                  # 575,121
CAMPUS_ANNUAL_KWH = (GRID_KVAH_11M * PF + SOLAR_USED_11M) * 12 / MONTHS_IN_AUDIT   # 1,652,719
SOLAR_USED_KWH    = SOLAR_USED_11M * 12 / MONTHS_IN_AUDIT                          # 627,405 (campus)
ANNUAL_ANCHOR_KWH = CAMPUS_ANNUAL_KWH * BLOCK3_SHARE                               # 185,301 (Block 3)
SOLAR_FRACTION    = SOLAR_USED_KWH / CAMPUS_ANNUAL_KWH                             # 0.380
BLOCK3_WEEKLY_KWH = ANNUAL_ANCHOR_KWH / 52                                         # 3,563.5

# ---- Diesel (Table 3: campus 18,650 L/yr) ----
CAMPUS_DIESEL_L    = 18_650
BLOCK3_DIESEL_L    = 2051       # SDG 7 allocation (about 11% of campus); NOT metered at Block 3
DIESEL_KGCO2_PER_L = 2.68       # add a source before publishing
INCLUDE_DIESEL     = False      # False = electricity-only net carbon (paper, notebook and dashboard). Diesel is shown separately.

# ---- Other inputs ----
EMISSION_FACTOR = 0.71          # tCO2/MWh, CEA CO2 Baseline Database v19.0 (verify the table value)
BLOCK3_SQM      = 2594.74       # BIM (Revit/gbXML)
REFERENCE_YEAR  = 2024          # building age = REFERENCE_YEAR - year built, in training AND for Block 3

# ---- Latest notebook run (BDG2 sample 500,000 rows: 400,000 train / 100,000 test) ----
RAW_ANNUAL_KWH  = 925_209       # raw XGBoost total, Jul 2025 - Jul 2026 weather (final notebook run, REFERENCE_YEAR 2024)

# Weekly equipment-schedule energy by floor (kWh/week) - printed by the notebook
FLOOR_WEEKLY_KWH = {"Ground Floor": 17_999.291, "1st Floor": 4_333.170, "Top Floor": 1_507.440}

# BDG2 held-out test results (random record-level split, NOT a Block 3 validation)
MODEL_METRICS = {
    "XGBoost (selected)":           {"R2": 0.892, "MAE": 42.92,  "RMSE": 101.40},
    "Random Forest":                {"R2": 0.886, "MAE": 53.53,  "RMSE": 104.31},
    "Gradient Boosting":            {"R2": 0.912, "MAE": 47.10,  "RMSE": 91.41},
    "Linear Regression (baseline)": {"R2": 0.388, "MAE": 120.43, "RMSE": 241.64},
}

SCALING_FACTOR = ANNUAL_ANCHOR_KWH / RAW_ANNUAL_KWH     # 0.0975

# ---- Guard: stops campus and Block 3 numbers being mixed up ----
assert SOLAR_GEN_11M > SOLAR_EXP_11M > 100_000, "SOLAR_* must be CAMPUS totals (867,317 and 292,196), not Block 3 values"
assert round(ANNUAL_ANCHOR_KWH) == 185_301, f"Anchor is {ANNUAL_ANCHOR_KWH:,.0f}; expected 185,301 - check the audit lines above"

if __name__ == "__main__":
    print(f"share {BLOCK3_SHARE:.6f}  campus annual {CAMPUS_ANNUAL_KWH:,.0f}  campus solar used {SOLAR_USED_KWH:,.0f}")
    print(f"anchor {ANNUAL_ANCHOR_KWH:,.0f}  weekly {BLOCK3_WEEKLY_KWH:,.1f}  scaling {SCALING_FACTOR:.4f}")
