import streamlit as st

# Set up the page configuration
st.set_page_config(page_title="Stock Analysis", page_icon=":chart_with_upwards_trend:", layout="wide")

# Navigation
st.sidebar.title("Navigation")
options = st.sidebar.radio("Go to", ["Portfolio", "SMA", "Upward/Downward", "Best Buy", "Inflation analyzer"])

# Load the corresponding page based on the selection
if options == "SMA":
    import sma
    sma.show_sma()
elif options == "Upward/Downward":
    import upward_downward
    upward_downward.show_trend_analysis()
elif options == "Best Buy":
    import best_buy
    best_buy.show_best_buy()
elif options == "Portfolio":
    import portfolio_sim
    portfolio_sim.user_portfolio()
elif options == "Inflation analyzer":
    import us_inflation
    us_inflation.main()    
