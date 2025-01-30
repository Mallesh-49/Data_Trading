# --------- Importing Libraries for Data Trading ---------
import pandas as pd
import sqlite3
import ccxt
import matplotlib.pyplot as plt
from flask import Flask, render_template
#--------------------step1:data ingestion--------------------------
# ---------------------- Backtest Class -------------------
class Backtest:
    def __init__(self, data, initial_capital=100000):
        self.data = data
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.trades = []
        self.token_balance = {}
    #-----------creating a function for calculating the lower band and upper band using bollinger band technique----------
    def bollinger_bands(self, df, window=20):
        #-----Calculate Bollinger Bands for the given dataframe.-------------------
        df['SMA'] = df['close'].rolling(window).mean()
        df['StdDev'] = df['close'].rolling(window).std()
        df['UpperBand'] = df['SMA'] + (2 * df['StdDev'])
        df['LowerBand'] = df['SMA'] - (2 * df['StdDev'])
        return df
    #----------- Execute a trade (Buy or Sell) and update account balance and token holdings.---------
    def execute_trade(self, token, date, trade_type, price):
        if trade_type == 'BUY':
            #----------- Fixed amount per trade-------------
            self.capital -= 100
            quantity = 100 / price
            self.token_balance[token] = self.token_balance.get(token, 0) + quantity
        elif trade_type == 'SELL':
            if token in self.token_balance and self.token_balance[token] > 0:
                quantity = self.token_balance[token]
                self.capital += quantity * price
                self.token_balance[token] = 0
        profit_percentage = ((self.capital - self.initial_capital) / self.initial_capital) * 100
        self.trades.append({
            'token': token,
            'date': date.strftime('%Y-%m-%d %H:%M:%S'),
            'trade_type': trade_type,
            'price': price,
            'profit_percentage': profit_percentage
        })
    #-----------Run the backtesting strategy on all tokens using Bollinger Band breakouts---------------
    def run(self):
        for token, df in self.data.items():
            df = self.bollinger_bands(df)
            for i in range(len(df)):
                date = df.index[i]
                price = df['close'].iloc[i]
                lower_band = df['LowerBand'].iloc[i]
                upper_band = df['UpperBand'].iloc[i]
                #-----------condition for buy-------
                if price < lower_band * 0.97:
                    self.execute_trade(token, date, 'BUY', price)
                #-----------condition for sell-------
                elif price >= upper_band:
                    self.execute_trade(token, date, 'SELL', price)
    #-----------Save trade results into an SQLite database.----------------------
    def save_to_db(self, db_name="backtest_results.db"):
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token TEXT,
                date TEXT,
                trade_type TEXT,
                price REAL,
                profit_percentage REAL
            )
        ''')
        for trade in self.trades:
            cursor.execute('''
                INSERT INTO trades (token, date, trade_type, price, profit_percentage)
                VALUES (?, ?, ?, ?, ?)
            ''', (trade['token'], trade['date'], trade['trade_type'], trade['price'], trade['profit_percentage']))
        conn.commit()
        conn.close()
#------------Fetch historical market data using the ccxt library.-----------------
def fetch_data_with_ccxt(symbols, timeframe='1d', since=None, limit=365):
    exchange = ccxt.binance()
    data = {}
    for symbol in symbols:
        try:
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, since=since, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            data[symbol] = df
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
    return data

app = Flask(__name__)
#---------------Fetch trade data from the SQLite database.-----------
def fetch_data_from_db(db_name="backtest_results.db"):
    conn = sqlite3.connect(db_name)
    query = "SELECT * FROM trades"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def initialize_token_mapping(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS token_mapping (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token TEXT UNIQUE
        )
    ''')
    conn.commit()

def populate_token_mapping(symbols, conn):
    cursor = conn.cursor()
    for symbol in symbols:
        cursor.execute('INSERT OR IGNORE INTO token_mapping (token) VALUES (?)', (symbol,))
    conn.commit()

@app.route('/')
def index():
    df = fetch_data_from_db()
    df = df.applymap(lambda x: x.replace("\n", "").strip() if isinstance(x, str) else x)
    return render_template(
        'index.html',
        tables=[df.to_html(classes='data', index=False, escape=False)],
        titles=df.columns.values
    )

@app.route('/visualize/<int:token_id>')
def visualize(token_id):
    conn = sqlite3.connect("backtest_results.db")
    token_query = "SELECT token FROM token_mapping WHERE id = ?"
    token_row = pd.read_sql_query(token_query, conn, params=(token_id,))
    if token_row.empty:
        return f"No token found for ID: {token_id}"

    token = token_row['token'].iloc[0]
    trades_query = "SELECT date, trade_type, price FROM trades WHERE token = ?"
    df = pd.read_sql_query(trades_query, conn, params=(token,))
    conn.close()

    if df.empty:
        return f"No trades found for token: {token}. Available tokens are: {', '.join(get_available_tokens())}"

    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df.dropna(subset=['date'], inplace=True)
    df.sort_values(by='date', inplace=True)

    df.set_index('date', inplace=True)
    df_buy = df[df['trade_type'] == 'BUY']
    df_sell = df[df['trade_type'] == 'SELL']

    plt.figure(figsize=(10, 6))
    plt.plot(df.index, df['price'], label=f'{token} Price')
    plt.scatter(df_buy.index, df_buy['price'], color='green', label='Buy', marker='^')
    plt.scatter(df_sell.index, df_sell['price'], color='red', label='Sell', marker='v')
    plt.title(f"Trades for {token}")
    plt.legend()
    plt.savefig('static/trades_plot.png')
    plt.close()

    return render_template('visualize.html', token=token)

def get_available_tokens():
    conn = sqlite3.connect("backtest_results.db")
    tokens = pd.read_sql_query("SELECT id, token FROM token_mapping", conn)
    conn.close()
    return tokens.apply(lambda row: f"{row['id']}: {row['token']}", axis=1).tolist()

if __name__ == "__main__":
    symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'XRP/USDT', 'ADA/USDT']
    conn = sqlite3.connect("backtest_results.db")
    initialize_token_mapping(conn)
    populate_token_mapping(symbols, conn)
    conn.close()

    data = fetch_data_with_ccxt(symbols, timeframe='1d')
    backtester = Backtest(data)
    backtester.run()
    backtester.save_to_db()

    app.run(debug=True)
