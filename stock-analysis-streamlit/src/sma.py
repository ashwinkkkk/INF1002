from __future__ import annotations

import re
import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf
import plotly.express as px

# ----------------------------
# Core SMA Function using sliding window approach.
# Returns array same length as `values`, with NaN for the first window-1 entries
# ----------------------------
def sma_sliding(values: np.ndarray, window: int) -> np.ndarray:
    # Input normalisation and shape safety
    values = np.asarray(values, dtype=np.float64)
    # Safer shape handling: only auto-fix (n,1); reject wider shapes
    if values.ndim == 2 and values.shape[1] == 1:
        values = values[:, 0]
    elif values.ndim != 1:
        raise ValueError(f"Expected a single series (1-D), got shape {values.shape}")

    n = values.shape[0]
    # Ensure window is valid.
    if window <= 0:
        raise ValueError("window must be positive")
    if window > n:
        raise ValueError("window cannot exceed the number of observations")
    if not np.isfinite(values).all():
        raise ValueError("Input contains NaN/Inf. Clean your data before computing SMA.")

    out = np.empty(n, dtype=np.float64)
    # Input NaN for the first window - 1 coloumns. Since you can't comput avergae for them.
    out[:window - 1] = np.nan

    # Compute initial window sum.
    s = float(values[:window].sum(dtype=np.float64))
    inv_w = 1.0 / window
    # Store first SMA.
    out[window - 1] = s * inv_w

    for i in range(window, n):
        # Add new element entering window and subtract the element leaving the window.
        s += values[i] - values[i - window]
        out[i] = s * inv_w

    return out

# ----------------------------
# Helper functions
# ----------------------------


# Sanitise user input of Ticker symbol.
# Return exactly one clean ticker (warn if more than one).
def parse_single_ticker(raw: str) -> str:
    #Check if user input more than 1 ticker and seperate them. 
    syms = [s for s in re.split(r"[, \t]+", (raw or "").strip()) if s]
    if not syms:
        raise ValueError("Please enter a ticker symbol.")
    if len(syms) > 1:
        st.warning(f"Multiple tickers detected {syms}; using the first: {syms[0]}")
    t = syms[0].upper()
    #Accept only Alphabets, Carets, Hyphens and dots.
    if not re.fullmatch(r"[A-Z\.\-\^]+", t):
        raise ValueError("Ticker contains invalid characters.")
    return t

#Return a single ticker, single level Data Frame that has a Close Column.
def _normalize_yf_df(df: pd.DataFrame, ticker: str | None) -> pd.DataFrame:
    if isinstance(df.columns, pd.MultiIndex):
        known_fields = {"Open", "High", "Low", "Close", "Adj Close", "Volume"}
        lvl0 = set(map(str, df.columns.get_level_values(0)))
        lvl1 = set(map(str, df.columns.get_level_values(1)))
        # Which level holds fields vs tickers?
        tick_level = 1 if len(known_fields & lvl0) > len(known_fields & lvl1) else 0
        # In the case Yahoo Finance retreived dataset of multiple tickers.
        tickers = [t for t in df.columns.get_level_values(tick_level).unique() if str(t)]
        if not tickers:
            raise ValueError("Could not detect tickers in MultiIndex columns.")
        if ticker and ticker in tickers:
            chosen = ticker
        elif len(tickers) == 1:
            chosen = tickers[0]
        else:
            chosen = tickers[0]
            st.warning(f"Multiple tickers in data {tickers}; defaulting to {chosen}.")
        df = df.xs(chosen, axis=1, level=tick_level)

    # Ensure a Close column exists
    if "Close" not in df.columns and "Adj Close" in df.columns:
        df = df.copy()
        df["Close"] = df["Adj Close"]

    return df

#Return a 1-D float64 numpy array of Close prices from a normalized DF
def get_close_1d(df: pd.DataFrame) -> np.ndarray:
    s = df.get("Close")
    if s is None:
        raise ValueError("No 'Close' column after normalization.")
    if isinstance(s, pd.DataFrame):
        # Still wide? (e.g., multiple tickers) — refuse.
        raise ValueError(f"Multiple 'Close' series detected: {list(s.columns)}. Pick one ticker.")
    # Convert series to Numeric float 64. Turns any non-parsable values into NaN.
    arr = np.asarray(pd.to_numeric(s, errors="coerce"), dtype=np.float64)
    if arr.ndim == 2 and arr.shape[1] == 1:
        arr = arr[:, 0]
    elif arr.ndim != 1:
        raise ValueError(f"Expected a single series, got shape {arr.shape}")
    return arr

# ----------------------------
# Public entry point used by your main app
# ----------------------------
def show_sma():
    st.header("📈 Simple Moving Average")

    # Getting user input from form.
    with st.form("sma_form"):
        col1, col2, col3, col4 = st.columns([1.2, 1, 1, 1])
        with col1:
            ticker_in = st.text_input("Ticker", value="AAPL", help="e.g., AAPL, MSFT, TSLA, ^GSPC")
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

    # Call function to sanitise ticker input.
    try:
        ticker = parse_single_ticker(ticker_in)
    except Exception as e:
        st.error(str(e))
        return

    # Download Data using Yfinance API
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
    # Clean index: drop dupes, sort
    df = df[~df.index.duplicated(keep="last")].sort_index()
    # Normalize columns to avoid MultiIndex selection errors
    try:
        df = _normalize_yf_df(df, ticker)
    except Exception as e:
        st.error(str(e))
        return

    # Ensure there is a close column.
    if "Close" not in df.columns:
        st.error("No 'Close' column found, even after normalization.")
        return

    # Extract 1-D close and handle leading NaNs
    try:
        close = get_close_1d(df)
    except Exception as e:
        st.error(str(e))
        return

    #Ensure valid data (Not all Inf or NaN)
    finite_mask = np.isfinite(close)
    if not finite_mask.any():
        st.error("All Close values are NaN/Inf; cannot compute SMA.")
        return

    # In the case of IPOs or when the period starts before data exists, this ensures invalid data is dropped.
    start = int(np.argmax(finite_mask))  # first finite index
    close_trim = close[start:]
    if close_trim.size < window: 
        st.warning("Not enough valid closes to compute SMA after trimming missing values.")
        return

    # Compute SMA on trimmed series and align back
    sma_vals = sma_sliding(close_trim, window)
    sma_col = f"SMA_{window}"
    df[sma_col] = np.nan
    df.loc[df.index[start]:, sma_col] = sma_vals

    # Validate result with trusted function.
    dates_trim = df.index[start:]
    s = pd.Series(close_trim, dtype="float64", index=dates_trim)
    sma = s.rolling(window=window, min_periods=window).mean().round(4)
    sma_txt = sma.to_string(max_rows=None)
    with open('validateResults.txt', 'w') as file:
        file.write(str(sma_txt))
    

    # Prepare plot DataFrame with explicit Date column
    df_plot = df.reset_index()
    date_col = df_plot.columns[0]
    if date_col != "Date":
        df_plot = df_plot.rename(columns={date_col: "Date"})

    # Drop rows where both series are NaN
    plot_cols = ["Close", sma_col]
    df_plot_nonan = df_plot.dropna(how="all", subset=plot_cols)
    if df_plot_nonan.empty:
        st.warning("No rows with data to plot after cleaning.")
        return

    # Plot
    fig = px.line(
        df_plot_nonan,
        x="Date",
        y=plot_cols,
        color_discrete_map={"Close": "#1f77b4", sma_col: "#ff7f0e"},
    )
    st.plotly_chart(fig, use_container_width=True)

    # Plotting latest values chart for easy reference.
    st.subheader("Latest values")
    st.dataframe(df[["Close", sma_col]].tail(15), use_container_width=True)

    # Metrics
    latest_close = float(df["Close"].iloc[-1])
    last_sma_val = df[sma_col].iloc[-1]
    latest_sma = float(last_sma_val) if np.isfinite(last_sma_val) else np.nan
    st.metric(
        label=f"Latest SMA ({window})",
        value=f"{latest_sma:,.4f}" if np.isfinite(latest_sma) else "NaN",
        delta=(f"Close - SMA: {latest_close - latest_sma:,.4f}" if np.isfinite(latest_sma) else None),
    )

