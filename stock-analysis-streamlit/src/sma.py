# sma.py
# Drop this file alongside your main app.py.
# Your app can call:  
#   elif options == "SMA":
#       import sma
#       sma.show_sma()
#
# This module uses a manual sliding-window SMA (no pandas.rolling) and
# robustly handles yfinance's MultiIndex columns to avoid errors like
# "[('Close','AAPL') ('SMA_5','')] not in index".

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf
import plotly.express as px


# ----------------------------
# Core SMA (O(n), no rolling)
# ----------------------------

def sma_sliding(values: np.ndarray, window: int) -> np.ndarray:
    """Compute SMA with a sliding window.
    Returns array same length as `values`, with NaN for the first window-1 entries.
    """
    values = np.asarray(values, dtype=np.float64)
    if values.ndim != 1:
        values = values.reshape(-1)

    n = values.shape[0]
    if window <= 0:
        raise ValueError("window must be positive")
    if window > n:
        raise ValueError("window cannot exceed the number of observations")
    if not np.isfinite(values).all():
        raise ValueError("Input contains NaN/Inf. Clean your data before computing SMA.")

    out = np.empty(n, dtype=np.float64)
    out[: window - 1] = np.nan

    s = float(values[:window].sum(dtype=np.float64))
    inv_w = 1.0 / window
    out[window - 1] = s * inv_w

    for i in range(window, n):
        s += values[i] - values[i - window]
        out[i] = s * inv_w

    return out

# ----------------------------
# Helpers
# ----------------------------

def _normalize_yf_df(df: pd.DataFrame, ticker: str | None) -> pd.DataFrame:
    """Return a single-level OHLCV DataFrame for the chosen ticker.
    Handles yfinance's MultiIndex columns when a list of tickers is fetched.
    Ensures a 'Close' column exists (falls back to 'Adj Close' if needed).
    """
    if isinstance(df.columns, pd.MultiIndex):
        # yfinance default: level 0 = fields (Open/High/Low/Close/Adj Close/Volume), level 1 = tickers
        tick_level = 1
        fields_level = 0
        tickers = [t for t in df.columns.get_level_values(tick_level).unique() if str(t) != ""]
        chosen = None
        if ticker and ticker in tickers:
            chosen = ticker
        elif len(tickers) == 1:
            chosen = tickers[0]
        else:
            # If multiple tickers but no match, pick the first to keep app usable
            chosen = tickers[0]
        df = df.xs(chosen, axis=1, level=tick_level)

    # Ensure a Close column exists
    if "Close" not in df.columns and "Adj Close" in df.columns:
        df = df.copy()
        df["Close"] = df["Adj Close"]

    return df

# ----------------------------
# Public entry point used by your main app
# ----------------------------

def show_sma():
    st.header("📈 Simple Moving Average")

    # Controls (kept inside a form to avoid repeated downloads on every widget change)
    with st.form("sma_form"):
        col1, col2, col3, col4 = st.columns([1.2, 1, 1, 1])
        with col1:
            ticker = st.text_input("Ticker", value="AAPL", help="e.g., AAPL, MSFT, TSLA, ^GSPC")
        with col2:
            period = st.selectbox("Period", ["20d", "1mo", "3mo", "6mo", "1y", "3y", "5y"], index=0)
        with col3:
            window = st.number_input("SMA window", min_value=2, max_value=252, value=5, step=1)
        with col4:
            auto_adjust = st.checkbox("Auto-adjust", value=True, help="Adjust OHLC for splits/dividends")
        submitted = st.form_submit_button("Fetch & Plot")

    if not submitted:
        st.info("Enter settings and click **Fetch & Plot**.")
        return

    # Download
    try:
        df = yf.download(
            ticker,
            period=period,
            interval="1d",
            auto_adjust=auto_adjust,
            progress=False,
        )
    except Exception as e:
        st.error(f"Download error: {e}")
        return

    if df is None or df.empty:
        st.warning("No data returned — check the ticker or period.")
        return

    # Normalize columns to avoid MultiIndex selection errors
    df = _normalize_yf_df(df, ticker)

    if "Close" not in df.columns:
        st.error("No 'Close' column found, even after normalization.")
        return

    # Compute SMA
    try:
        close = df["Close"].to_numpy(dtype=np.float64)
        df[f"SMA_{window}"] = sma_sliding(close, window)
    except Exception as e:
        st.error(f"SMA computation error: {e}")
        return

    # Plot & table
    fig = px.line(
    df.reset_index(),
    x="Date", y=["Close", f"SMA_{window}"],
    color_discrete_map={"Close": "#1f77b4", f"SMA_{window}": "#ff7f0e"}
)
    st.plotly_chart(fig, use_container_width=True)
    st.subheader("Latest values")
    st.dataframe(df[["Close", f"SMA_{window}"]].tail(15))

    # Quick metrics
    latest_close = float(df["Close"].iloc[-1])
    latest_sma = float(df[f"SMA_{window}"] .iloc[-1]) if np.isfinite(df[f"SMA_{window}"] .iloc[-1]) else np.nan
    st.metric(
        label=f"Latest SMA ({window})",
        value=f"{latest_sma:,.4f}" if np.isfinite(latest_sma) else "NaN",
        delta=(f"Close - SMA: {latest_close - latest_sma:,.4f}" if np.isfinite(latest_sma) else None),
    )
