# Source of data
import yfinance as yf
# Data handling using panda
import pandas as pd
# For calculation of weights and returns
import numpy as np
# date management
import datetime as dt
# Chart plotting
import matplotlib.pyplot as plt
# Web app interface
import streamlit as st


def get_user_profile():
    # Header for the page
    st.subheader("Portfolio with Real Data Simulation")

    # Markdown text for aesthetics
    st.markdown("Enter your profile details below:")

    # Prompts user for profile details
    # Dropdown box
    title = st.selectbox("Title:", ["Mr", "Mrs", "Ms"], index=0)
    name = st.text_input("Your Name:", placeholder="Michael Scott")
    balance = st.number_input("Starting Balance (USD):",
                              min_value=1000,
                              max_value=10000000,
                              value=100000,
                              step=1000,
                              help="Min 1000, max 10000000."
                              )
    return title, name, balance


def get_portfolio_allocation():
    # Choosing tickers for simulation
    st.markdown("Ticker Selection")
    st.info("Enter up to 5 tickers and their percentage weights (must total 100%).")

    # Creating 2 columns, for tickers and weightage
    col1, col2 = st.columns(2)
    with col1:
        tickers = [st.text_input(f"Ticker {i + 1}", default)
                   for i, default in enumerate(["AAPL", "TSLA", "AMZN", "NVDA", ""])]

    with col2:
        weights = [st.number_input(f"Weight {i + 1} (%)", min_value=0, max_value=100, value=default)
                   for i, default in enumerate([40, 30, 20, 10, 0])]

    # Convert input into clean dictionary for usage later
    portfolio = {
        t.strip().upper(): w / 100 for t, w in zip(tickers, weights) if t and w > 0
    }

    # Warning prompt if total don't add up to 100%
    total_weight = sum(portfolio.values())

    if total_weight != 1:
        st.warning(f"Your total weights sum to {total_weight * 100:.1f}%. Please adjust to 100%.")
        return
    return portfolio


def fetch_portfolio_data(portfolio, start_date, end_date):
    tickers = list(portfolio.keys())
    st.write(f"Fetching data for: {', '.join(tickers)}...")
    # Download closing prices, yfiance automatically adjusts the historical price
    data = yf.download(tickers, start=start_date, end=end_date)["Close"]
    # Warning message for empty data
    if data.empty:
        st.error("⚠️ No data retrieved. Try adjusting the tickers or date range.")
        return
    return data


def calculate_portfolio_returns(data, portfolio, starting_balance):
    # Panda method to compute daily returns, dropping rows with missing values.
    returns = data.pct_change().dropna()
    # Weighted portfolio daily return
    # Converts the weights into a numpy array
    weights_arr = np.array(list(portfolio.values()))
    # Multiplying stock returns by their weightage and sums across columns to get portfolio returns using numpy.dot
    returns["Portfolio"] = returns[list(portfolio.keys())].dot(weights_arr)
    # Computes cumulative growth factor using .cumprod()
    cumulative = (1 + returns["Portfolio"]).cumprod()
    # Multiply by user’s starting balance to show investment value changes over time
    portfolio_value = starting_balance * cumulative
    return returns, portfolio_value


def display_results(title, name, data, returns, portfolio_value):
    # Display latest stock values from the last 5 days
    st.write("Latest Stock Values")
    st.dataframe(data.tail())

    # Display stock prices over time
    st.subheader("Stock Prices Over Time")
    st.line_chart(data, use_container_width=True)

    # Display daily return percentage over time
    st.subheader("Portfolio Daily Returns")
    st.line_chart(returns["Portfolio"], use_container_width=True)

    # Display portfolio value over time
    st.subheader("Portfolio Value Over Time")
    st.line_chart(portfolio_value, use_container_width=True)

    # Plots a histogram of daily returns, gives a sense of volatility and distribution (bell curve shape).
    st.subheader("Distribution of Portfolio Daily Returns")
    fig, ax = plt.subplots()
    returns["Portfolio"].hist(bins=50, ax=ax)
    ax.set_xlabel("Daily Return")
    ax.set_ylabel("Frequency")
    st.pyplot(fig)

    # Calculating performance metrics
    # Average Daily Return
    avg_return = returns["Portfolio"].mean() * 100
    # How much daily returns fluctuate
    volatility = returns["Portfolio"].std() * 100
    # Overall gain/loss since start date
    total_return = (portfolio_value.iloc[-1] / portfolio_value.iloc[0] - 1) * 100

    # Display performance metrics
    st.metric("Average Daily Return", f"{avg_return:.3f}%")
    st.metric("Volatility (Std Dev)", f"{volatility:.3f}%")
    st.metric("Total Portfolio Return", f"{total_return:.2f}%")
    st.metric("Latest Portfolio Value", f"${portfolio_value[-1]:.2f}")

    # --- User Summary ---
    st.success(f"Simulation complete for {title} {name}.")


def user_portfolio():
    title, name, balance = get_user_profile()
    portfolio = get_portfolio_allocation()
    if not portfolio:
        return

    # Select date range for stock data
    start_date = st.date_input("Start Date", pd.to_datetime("2022-01-01"))
    end_date = st.date_input("End Date", pd.to_datetime("today"))

    # Fetch stock data from Yahoo Finance upon clicking the button
    if st.button("Simulate Portfolio"):
        data = fetch_portfolio_data(portfolio, start_date, end_date)
        if data is not None:
            returns, portfolio_value = calculate_portfolio_returns(data, portfolio, balance)
            display_results(title, name, data, returns, portfolio_value)
