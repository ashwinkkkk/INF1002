import streamlit as st
import yfinance as yf
import pandas
from datetime import date, timedelta
import streamlit as st

#Set Global Variables
target_stocks = ["MSFT","ABNB","AMZN","AAPL","TSLA"]

def LevenshteinDistance(compared_stock, input_stock):
  distance = [[0] * (len(compared_stock) + 1) for _ in range(len(input_stock)+1)]

  #Map out the distance of input stock to an empty string in 2D Array
  for i in range(len(input_stock)+1):
    distance[i][0]=i
  #Map out the distance of compared stock to an empty string in 2D Array 
  for j in range(len(compared_stock)+1):
    distance[0][j]=j

  #Map through array to compare how many operations are needed from the compared stock to input string
  for i in range(1,len(input_stock)+1):
    for j in range(1,len(compared_stock)+1):
      #If the character of the strings are the same, then no oepration is needed, so the distance is the same
      if input_stock[i-1] == compared_stock[j-1]:
        distance[i][j] = distance[i-1][j-1]
      #Else you will need to add, delete or replace the character from the previous fastest distance, so the distance will always add 1
      else:
       distance[i][j] = min(distance[i-1][j],distance[i][j-1],distance[i-1][j-1]) + 1

  #At the end of the 2D array, the shortest distance will always be at the end of the 2D array
  return distance[-1][-1]

def Profit(prices,dates):
  total_profit = 0
  i = 0
  profit_information = []
  #Loop through prices to check the price
  while i < len(prices) - 1: 
      #Find if there are any prices better to buy than the current day
      while i < len(prices) - 1 and prices[i] >= prices[i + 1]:
          #If the price of the next day is higher, skip it
          i += 1
          
      if i == len(prices)-1:
         break
      #Assign the current price to be the lowest price to buy at
      lowest_price = prices[i]
      lowprice_date = dates[i]
      #Find if there are any prices to sell at
      while i < len(prices) - 1 and prices[i] <= prices[i + 1]:
          #If the price of the next day is lower, skip it
          i += 1
      #Assign the current price to be the best price to sell at
      highest_price = prices[i]
      highprice_date = dates[i]

      #If theres any profit made, the lowest and highest price wont be the same
      if highest_price != lowest_price:
        total_profit += (highest_price - lowest_price)
        profit_information.append(f"Buy at {lowest_price} on {lowprice_date}, Sell at {highest_price} on {highprice_date}")
  return total_profit, profit_information

def SearchStock(stock_name,start_date,end_date,main_container):
    col1,col2,col3= main_container.columns([3,2,1])
    dates = ""
    prices = []
    try:
      #Search for stock with yf ticker with user start and end dates
      stock = yf.Ticker(stock_name)
      stock_history = stock.history(start=start_date,end=end_date)
      
      #Get Close values as prices and format to 2dp
      prices = pandas.DataFrame(stock_history).get("Close").tolist()
      prices = [round(float(i), 2) for i in prices]

      #Set Date as a column instead of a index when retrieved from yfinance
      stock_history.reset_index(inplace=True)
      dates = pandas.DataFrame(stock_history)["Date"].dt.strftime('%Y/%m/%d')

      #Invoke profit function
      total_profit, profit_information = Profit(prices,dates)

      #Display graph in column 1
      graph_data = pandas.DataFrame({"price": prices,"date": dates})
      with col1:
        st.line_chart(data=graph_data,x_label="Date", y_label="Price",x="date",y="price")
      #Display stock table in col 2
      with col2:
        #If theres any profit made
        if total_profit:
          #Write the maximum profit
          st.write("Maximum Profit " + str(round(total_profit,2)))
          #Write the best days to buy and sell
          for i in range(len(profit_information)):
            st.write(profit_information[i])
        else:
          st.write("No profit")

    except AttributeError:
      recommended_search = []
        #Compare the in put stock with the 5 set of stocks
      for i in range(len(target_stocks)):
        dist = LevenshteinDistance(target_stocks[i], stock_name.upper())
        #If the distance is less than (set 3 as of now)
        maximum_distance_difference = 3
        if dist < maximum_distance_difference:
            recommended_search.append(target_stocks[i])

      output = ""
      #Formatting the output
      for i in range (len(recommended_search)):
          output += f"{recommended_search[i]}?"
          if i < (len(recommended_search)-1):
               output+=" or "
      with col2:
        if output:
            st.write(f"Maybe you meant {output}")
        else:
            st.write("No Stock Ticker Found!")
    except:
        with col2: 
            st.write("Invalid Stock Ticker!")
            
def show_best_buy():
    main_container = st.container(border=True)
    main_container.title("Best Buy And Sell Timings")
    col1,col2,col3= main_container.columns([3,2,1])
    stock_name=""
    #Col 1 used to select date input range
    with col1:
        #Setting max date as today and selecting it will give error, so i added +1 day 
        selected_date = st.date_input("Select Date Range",(),max_value=date.today() + timedelta(days=1),width="stretch")
  
    #Col 2 for selecting which stock to search
    with col2:
        stock_name = st.text_input("Stock Ticker",placeholder="MSFT, ABNB, AMZN, AAPL, TSLA")

    #Col 3 for search button
    with col3:
        #Just for padding
        st.write("")

        #On button press, search stock with start and end date
        if st.button("Search",):
                try:
                    end_date = selected_date[1].strftime("%Y-%m-%d")
                    start_date = selected_date[0].strftime("%Y-%m-%d") 
                    #Only accepts input of more than 4 days
                    if (selected_date[1] - selected_date[0]).days > 4:
                        SearchStock(stock_name,start_date,end_date,main_container)
                    else:
                        with col1:
                            st.write("Please enter a date range of more than 4 days")    
                except IndexError:
                    with col1:
                        st.write("Invalid Date Input")