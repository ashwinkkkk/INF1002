import yfinance as yf
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

def display_dashboard():
    st.title("Stock Dashboard")
    st.subheader("Key Stock Metrics")
    
    # Placeholder for stock metrics
    st.write("Displaying key metrics for selected stocks...")
    
    # Example metrics (these would be replaced with actual data)
    st.metric(label="Stock Price", value="$150.00")
    st.metric(label="Market Cap", value="$1.5 Trillion")
    st.metric(label="P/E Ratio", value="25.4")
    
    # Placeholder for visualizations
    st.write("Visualizations will be displayed here.")
    
    # Example chart (this would be replaced with actual data)
    st.line_chart([1, 2, 3, 4, 5])

def daily_returns():
    st.subheader("Stock Daily Return")
    # Prompt for stock ticker
    ticker = st.text_input("Enter Stock Ticker (e.g. AAPL, MSFT, TSLA)", "AAPL")

    # Ask for time range of data
    start_date = st.date_input("Start Date", pd.to_datetime("2022-01-01"))
    end_date = st.date_input("End Date", pd.to_datetime("today"))

    # Only display after clicking the button
    if st.button("Fetch Data"):
        try:
            # Download stock data
            data = yf.download(ticker, start=start_date, end=end_date)

            if data.empty:
                st.error("No data found for this ticker and date range.")
            else:
                # Panda method to compute daily returns
                data["Daily Return"] = data["Close"].pct_change()

                # Show dataframe
                st.subheader(f"{ticker} Stock Data")
                st.dataframe(data.tail())

                # Line chart for price
                st.subheader(f"{ticker} Closing Price")
                st.line_chart(data["Close"])

                # Line chart for daily return
                st.subheader(f"{ticker} Daily Returns")
                st.line_chart(data["Daily Return"])

                # Histogram of returns
                st.subheader("Distribution of Daily Returns")
                fig, ax = plt.subplots()
                data["Daily Return"].hist(bins=50, ax=ax)
                ax.set_xlabel("Daily Return")
                ax.set_ylabel("Frequency")
                st.pyplot(fig)

        except Exception as e:
            st.error(f"Error: {e}")
    pass


if __name__ == "__main__":
    display_dashboard()
    daily_returns()
