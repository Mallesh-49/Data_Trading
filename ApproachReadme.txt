# -----------Crypto Trading Backtest and Visualization--------

#----This Assignment is a Flask web application that performs backtesting on cryptocurrency trading data using Bollinger Bands.
#-----It allows users to analyze trading performance and visualize trades for specific tokens.
#-------------------------Features:-----------------------------
- Fetches cryptocurrency market data using the **ccxt** library.
- Implements Bollinger Bands strategy for **buy** and **sell** decisions.
- Stores trade details (e.g., token, date, trade type, price, profit percentage) in an SQLite database.
- Provides a user-friendly interface to view and analyze trade data.
- Visualizes buy/sell trades for specific tokens using matplotlib.

# ------------the work flow of this Assignment-----------------

#----------------- 1.Fetching Data-----------------
- The program fetches cryptocurrency data (e.g., BTC/USDT) from Binance using the **ccxt** library.
- Data includes **open, high, low, close, and volume** for each trading day.

#-----------------2.Backtesting------------------
----A custom `Backtest` class processes the data:
  Calculates Bollinger Bands.
  Executes trades based on Bollinger Band breakouts:
    **Buy:** When the price drops below the lower band.
    **Sell:** When the price reaches or exceeds the upper band.
  Tracks profit and updates account balance.

#------------------3.Data Storage-------------------------------
- All trade details are stored in an SQLite database named `backtest_results.db`.

#-----------------4.Visualization-------------------------------------
- can view all trade data on the homepage (`/`).
- can view specific token trade visualizations at `/visualize/<id>`.
- The visualizations include:
  - **Price trends** for the selected token.
  - **Buy/Sell markers** to highlight trading activity.
#---Running the project-------
#---------------------------------How to Run the Project------------------------
requirements:-
- Python 3.x
- Required Python libraries: Flask, ccxt, pandas, matplotlib, sqlite3.

#-----------------------Installation--------------------
Install the required libraries:
   pip install flask
   pip install ccxt
   pip install pandas
   pip install matplotlib
