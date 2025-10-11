# Stock Analysis Streamlit

This project is a web application built using Streamlit for stock analysis. It provides various tools and visualizations to help users analyze stock performance and make informed investment decisions.

## Project Structure

```
stock-analysis-streamlit
├── src
│   ├── app.py              # Main entry point of the Streamlit application
│   ├── portfolio.py        # Simulate portfolio
│   ├── sma.py              # Simple Moving Average (SMA) analysis section
│   ├── upward_downward.py  # Analysis of stocks trending upward or downward
│   ├── best_buy.py         # Identifies the best buy stocks
│   ├── us_inflation.py     # Track and reflect inflation trends
│   └── utils
│       └── __init__.py     # Utility functions for shared use across the application
├── requirements.txt        # Project dependencies
└── README.md               # Documentation for the project
```

## Features

- **Dashboard**: View key metrics and visualizations for selected stocks.
- **SMA Analysis**: Calculate and visualize the Simple Moving Average for stocks.
- **Upward/Downward Analysis**: Identify stocks that are trending upward or downward.
- **Best Buy Recommendations**: Get insights on the best stocks to buy based on analysis.

## Setup Instructions

1. Clone the repository:
   ```
   git clone <repository-url>
   cd stock-analysis-streamlit
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the Streamlit application:
   ```
   streamlit run src/app.py
   ```

## Usage

Once the application is running, navigate through the different sections using the sidebar to explore stock analysis features. Each section provides unique insights and visualizations to assist in stock market decisions.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue for any suggestions or improvements.