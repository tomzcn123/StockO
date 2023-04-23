import streamlit as st
import yfinance as yf
import pandas as pd
from ta.trend import MACD
import lxml
from collections import defaultdict
import plotly.graph_objects as go




def get_sp500_tickers():
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    table = pd.read_html(url, header=0)[0]
    tickers = table[['Symbol', 'GICS Sector']].to_dict('records')
    return tickers

def get_stock_sector(stock_ticker):
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    table = pd.read_html(url, header=0)[0]
    sector = table.loc[table['Symbol'] == stock_ticker, 'GICS Sector'].iloc[0]
    return sector

@st.cache
def calculate_moving_average(stock_ticker, period='100d', interval='1d', window=20):
    data = yf.download(tickers=stock_ticker, period=period, interval=interval)
    data['MovingAverage'] = data['Close'].rolling(window=window).mean()
    return data

def calculate_macd(stock_ticker, window_fast=12, window_slow=26, window_sign=9):
    data = yf.download(tickers=stock_ticker, period='1y', interval='1d')
    macd_indicator = MACD(data['Close'], window_slow=window_slow, window_fast=window_fast, window_sign=window_sign)
    data[f'MACD_{window_fast}_{window_slow}_{window_sign}'] = macd_indicator.macd()
    return data

@st.cache(suppress_st_warning=True)
def find_stocks_above_conditions(stock_list):
    stocks_above_conditions = defaultdict(list)
    for stock in stock_list:
        try:
            stock_ticker = stock['Symbol']
            data = (calculate_moving_average(stock_ticker)
                    .pipe(calculate_macd, stock_ticker, window_fast=5, window_slow=20, window_sign=5)
                    .pipe(calculate_macd, stock_ticker))
            if (not data.empty and
                data.iloc[-1]['Close'] > data.iloc[-1]['MovingAverage'] and
                data.iloc[-1]['Close'] > data.iloc[-1]['MACD_5_20_5']
            ):
                sector = get_stock_sector(stock_ticker)
                stocks_above_conditions[sector].append(stock_ticker)
                print(f"Stock {stock_ticker} in sector {sector} meets the conditions.")
        except Exception as e:
            st.warning(f"Error processing stock {stock_ticker}: {e}")
    return stocks_above_conditions




@st.cache
def plot_candlestick_chart(stock_ticker, period='3mo', interval='1d', window_fast=12, window_slow=26, window_sign=9):
    data = yf.download(tickers=stock_ticker, period=period, interval=interval)
    macd_data_20 = calculate_macd(stock_ticker)
    macd_data_5 = calculate_macd(stock_ticker, window_fast=5, window_slow=20, window_sign=5)
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=data.index,
                                  open=data['Open'],
                                  high=data['High'],
                                  low=data['Low'],
                                  close=data['Close'],
                                  name='Candlestick'))
    fig.add_trace(go.Scatter(x=macd_data_20.index,
                             y=macd_data_20[f'MACD_12_26_9'],
                             mode='lines',
                             line=dict(color='green', width=1),
                             name='20-day MACD'))
    fig.add_trace(go.Scatter(x=macd_data_5.index,
                             y=macd_data_5[f'MACD_5_20_5'],
                             mode='lines',
                             line=dict(color='blue', width=1),
                             name='5-day MACD'))
    fig.update_layout(title=f'{stock_ticker} Candlestick Chart with 20-day and 5-day MACD',
                      xaxis_title='Date',
                      yaxis_title='Price',
                      xaxis_rangeslider_visible=False)
    return fig

st.title("Stock Opportunity")
st.write("Fetching S&P 500 stock tickers...")
sp500_tickers = get_sp500_tickers()
st.write("Analyzing stocks...")
stocks_above_conditions = find_stocks_above_conditions(sp500_tickers)
st.header("Stocks with the current price above the 20-day moving average and 5-day MACD line:")
for sector, stocks in stocks_above_conditions.items():
    st.subheader(sector)
    selected_stock = st.selectbox(f"Select a stock from {sector}", stocks)
    candlestick_chart = plot_candlestick_chart(selected_stock)
    st.plotly_chart(candlestick_chart)


