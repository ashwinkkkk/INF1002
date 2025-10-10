import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import datetime
from pprint import pprint


def getTrends(key_name:str, stock_symbol:str, df:pd.DataFrame)->dict:
    #df = pd.DataFrame({"price": values}, index=letters)
    #print(type(df[key_name,stock_symbol]))

    trends = []
    direction = None
    curr_val = [float(df[key_name,stock_symbol][0])]
    start_idx = df.index[0]
    prev_val = float(df[key_name,stock_symbol][0])
    prev_idx = df.index[0]

    for idx, val in zip(df.index[1:], df[key_name,stock_symbol][1:]):
        print(val)
        if val > prev_val: new_dir = 'UP'
        elif val < prev_val: new_dir = 'DOWN'
        else: new_dir = direction

        if direction and new_dir != direction:
            trends.append({
                "direction": direction,
                "start": start_idx,
                "end": idx,
                "values": curr_val
            })
            start_idx = prev_idx
            curr_val = [prev_val]

        direction = new_dir
        prev_val = val
        prev_idx = idx
        curr_val.append(val)


    trends.append({
        "direction": direction,
        "start": start_idx,
        "end": df.index[-1],
        "values": curr_val        
    })
    
    #pprint(trends)
    return trends






def processTrendData(data:list):
    #[Highest Up Trend Dic, Highest Down Trend Dic, Total amount of up trends, Total amount of downtrend]
    up , down = 0,0
    hUp,hDown = {'values':[]}, {'values':[]}
    for d in data:
        if(d["direction"] == 'UP'):
            up += 1
            hUp = d if len(hUp['values']) < len(d['values']) else hUp
        else:
            down += 1
            hDown = d if len(hDown['values']) < len(d['values']) else hDown

    print('\n\nhighest up trend:')
    pprint(hUp)

    print('\n\nhighest down trend:')
    pprint(hDown)

    print(f'\n\ntotal up trends:{up}')
    print(f'total down trends:{down}')

    return (hUp,hDown,up,down)





def downloadTicker(ticker:str,start:datetime,end:datetime,interval:str) -> pd.DataFrame:
    try:
        ticker_df = yf.download(ticker,
                                start=start,
                                end=end,
                                interval=interval)
        print(f"Successfully downloaded {ticker}")
    except ValueError:
        print('Ticker Does not exist')
        print(ValueError)
    return ticker_df

def show_trend_analysis():
    st.title("Upward/Downward Stock Analysis")

    st.subheader("Trending Stocks")
    col1, col2, col3 = st.columns(3)
    with col1:
        # Placeholder for user input
        stock_symbol = st.text_input("Enter Stock Symbol:", "").upper()

    with col2:
        today = datetime.date.today()
        one_week_ago = today - datetime.timedelta(days=7)

        # user selects a range
        try:
            start_date, end_date = st.date_input(
                "Select a date range",
                value=(one_week_ago, today),  # default range
                max_value=datetime.date.today() + datetime.timedelta(1)    
            )
        except ValueError:
            st.warning('Select Start & End Date', icon="⚠️")
            return

        st.write("Start:", start_date, " End:", end_date)     

    with col3:
        intervals = {"Daily":"1d","weekly":"1wk","Monthly":"1mo"}
        option = st.selectbox(
            "Choose an Interval",
            list(intervals.keys()),
            index=0,
            accept_new_options=False
        )        

    
        
    if stock_symbol:
        # Placeholder for analysis logic        
        print(intervals[option])
        print(f"start_date:{start_date}, end_date:{end_date}")        
        ticker_df = downloadTicker(stock_symbol,start_date,end_date,intervals[option])
        if ticker_df.empty:
            st.warning(f'Stock: {stock_symbol} does not exist', icon="⚠️")
            return
        print(f'Open:{ticker_df["Open"]}')
        print(f'High:{ticker_df["High"]}')
        print(f'Low:{ticker_df["Low"]}')
        print(f'Open:{ticker_df["Close"]}')

        trends = getTrends('Close',stock_symbol,ticker_df)
        highest_up,highest_down,total_up,total_down = processTrendData(trends)

        colUp , colDw = st.columns(2)

        with colUp:
            st.markdown(
            f"<a href='#longest-trends-table' style='color:inherit;text-decoration:none;'>"
            f"<div style='text-align:center;'>"
            f"<h1 style='color:green;font-size:80px;margin-bottom:0'>{total_up}</h1>"
            f"<p style='font-size:20px;margin-top:0'>"
            f"Consecutive Upward Trends</p>"
            f"</div></a>", unsafe_allow_html=True
        )

        with colDw:
            st.markdown(
            f"<a href='#longest-trends-table' style='color:inherit;text-decoration:none;'>"
            f"<div style='text-align:center;'>"
            f"<h1 style='color:red;font-size:80px;margin-bottom:0'>{total_down}</h1>"
            f"<p style='font-size:20px;margin-top:0'>Consecutive Downward Trends</p>"
            f"</div></a>", unsafe_allow_html=True
        )
        
        
        # Placeholder for visualizations
        fig = go.Figure(data=[go.Candlestick(
            x=ticker_df.index,
            open=ticker_df['Open',stock_symbol],
            high=ticker_df['High',stock_symbol],
            low=ticker_df['Low',stock_symbol],
            close=ticker_df['Close',stock_symbol]
        )])

        fig.update_layout(
            title='Candlestick Chart',
            xaxis_title='Date',
            yaxis_title='Price',
            xaxis_rangeslider_visible=False
        )

        st.plotly_chart(fig)

        fig2 = go.Figure()

        for i in range(1,len(ticker_df.index)):
            color = "red"

            if(ticker_df['Close',stock_symbol][i] >= ticker_df['Close',stock_symbol][i-1]):
                color = "green"
            fig2.add_trace(go.Scatter(
                x=ticker_df.index[i-1:i+1],
                y=ticker_df['Close',stock_symbol][i-1:i+1],
                mode='lines+markers',
                line=dict(color=color,width=3),
                showlegend=False
            ))
        fig2.update_layout(
            title="Time Series (Close)",
            xaxis_title="Date",
            yaxis_title="Price",
            yaxis=dict(range=[ticker_df['Close',stock_symbol].min()-5,ticker_df['Close',stock_symbol].max()+5])
        )
        st.plotly_chart(fig2,use_container_width=True)

        print(f'\n\nhighest_up:')
        pprint(ticker_df.loc[highest_up['start']:highest_up['end']])
        print(f'\n\n{type(ticker_df.index[0])}')

            
        st.markdown("<a name='longest-trends-table'></a>", unsafe_allow_html=True)
        st.subheader(":green[Longest Upward Trends]",divider='green')
        st.dataframe(
            ticker_df.loc[highest_up['start']:highest_up['end']],
            use_container_width=True
        ) 
                #print(ticker_df['Close','AAPL'].iloc[0:-1])

        st.subheader(":red[Longest Downwards Trends]",divider='red')
        st.dataframe(
            ticker_df.loc[highest_down['start']:highest_down['end']],
            use_container_width=True
        ) 
       