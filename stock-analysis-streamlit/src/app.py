import streamlit as st

# Set up the page configuration
st.set_page_config(page_title="Stock Analysis", page_icon=":chart_with_upwards_trend:", layout="wide")

# Navigation
st.sidebar.title("Navigation")
options = st.sidebar.radio("Go to", ["Dashboard", "SMA", "Upward/Downward", "Best Buy"])

# Load the corresponding page based on the selection
if options == "Dashboard":
    import dashboard
    dashboard.display_dashboard()
elif options == "SMA":
    import sma
    sma.show_sma()
elif options == "Upward/Downward":
    import upward_downward
    upward_downward.show_trend_analysis()
elif options == "Best Buy":
    import best_buy
    best_buy.show_best_buy()