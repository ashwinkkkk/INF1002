import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import os

SLOPE_TOL = 1e-4

def parse_mmyy(mmyy: str):
    m = int(mmyy[:2]); y = int(mmyy[2:]); y_full = 2000 + y
    return pd.Timestamp(year=y_full, month=m, day=1)

def load_data_from_local(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        st.error(f"'{path}' not found. Place your CPI file in the same folder and name it 'CPI.txt'."); st.stop()
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line: continue
            parts = [p.strip() for p in line.split(",")]
            if len(parts) != 3: continue
            mmyy, actual, forecast = parts
            try:
                dt = parse_mmyy(mmyy)
                rows.append((dt, float(actual), float(forecast), mmyy))
            except Exception:
                continue
    return pd.DataFrame(rows, columns=["date", "actual", "forecast", "mmyy"]).sort_values("date")

# Calculates the OLS slope (rate of change per step)
def slope_ols(y: np.ndarray) -> float:
    y = np.asarray(y, float); n = len(y)
    if n < 2: return np.nan
    x = np.arange(n, dtype=float)
    xm = x.mean(); ym = y.mean()
    num = np.sum((x - xm) * (y - ym))
    den = np.sum((x - xm)**2)
    return num / den if den != 0 else np.nan

# Classifies slope as Uptrend / Downtrend / Stable
def classify_trend(slope: float, tol: float) -> str:
    if np.isnan(slope): return "Insufficient data"
    if slope > tol: return "Uptrend"
    if slope < -tol: return "Downtrend"
    return "Stable"

def main():
    st.set_page_config(page_title="US Macro Analysis", page_icon="📊", layout="wide")
    st.title("US Inflationary Analyser")

    df = load_data_from_local("CPI.txt")
    if df.empty:
        st.warning("No valid rows parsed from CPI.txt. Ensure each line is 'MMYY,actual,forecast'."); st.stop()

    df["month"] = df["date"].dt.strftime("%b %Y")
    y = df["actual"].values

    horizons = [3, 6, 12]
    cards = []

    for h in horizons:
        if len(y) >= 2:
            h_use = min(h, len(y))
            slope = slope_ols(y[-h_use:])
            verdict = classify_trend(slope, SLOPE_TOL)
        else:
            h_use = len(y); slope = np.nan; verdict = "Insufficient data"
        cards.append((h_use, slope, verdict))

    cols = st.columns(len(cards))
    for col, (h_use, slope, verdict) in zip(cols, cards):
        if verdict == "Uptrend":
            col.success(f"Last {h_use} months: Uptrend  \nSlope: {slope:+.4f} pp/month")
        elif verdict == "Downtrend":
            col.error(f"Last {h_use} months: Downtrend  \nSlope: {slope:+.4f} pp/month")
        elif verdict == "Stable":
            col.info(f"Last {h_use} months: Stable  \nSlope: {slope:+.4f} pp/month")
        else:
            col.warning(f"Last {h_use} months: Insufficient data")

    base = alt.Chart(df).encode(
        x=alt.X("month:N", sort=list(df["month"]), title="Month"),
        tooltip=[
            alt.Tooltip("month:N", title="Month"),
            alt.Tooltip("actual:Q", title="Actual MoM (%)", format=".2f"),
            alt.Tooltip("forecast:Q", title="Forecast MoM (%)", format=".2f"),
        ]
    )

    bars = base.mark_bar().encode(y=alt.Y("actual:Q", title="CPI MoM (%)"))
    dots = alt.Chart(df).mark_point(filled=True, size=90, color="orange").encode(
        x=alt.X("month:N", sort=list(df["month"])),
        y=alt.Y("forecast:Q")
    )
    chart = (bars + dots).properties(height=420)
    st.altair_chart(chart, use_container_width=True)

if __name__ == "__main__":
    main()
