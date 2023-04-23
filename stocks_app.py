import streamlit as st
import yfinance as yf
import pandas as pd
from ta.trend import MACD
import lxml
from collections import defaultdict
import plotly.graph_objects as go
import copy



def get_sp500_tickers():
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    table = pd.read_html(url, header=0)[0]
    tickers = table[['Symbol', 'GICS Sector']].to_dict('records')
    return tickers

@st.cache
def calculate_moving_average(stock_ticker, period='100d', interval='1d', window=20):
    data = yf.download(tickers=stock_ticker, period=period, interval=interval)
    data['MovingAverage'] = data['Close'].rolling(window=window).mean()
    return copy.deepcopy(data)

@st.cache
def calculate_macd(data, window_fast=12, window_slow=26, window_sign=9, macd_ma_window=5):
    macd_indicator = MACD(data['Close'], window_slow=window_slow, window_fast=window_fast, window_sign=window_sign)
    data[f'MACD_{window_fast}_{window_slow}_{window_sign}'] = macd_indicator.macd()
    data[f'MACD_{window_fast}_{window_slow}_{window_sign}_MA_{macd_ma_window}'] = data[f'MACD_{window_fast}_{window_slow}_{window_sign}'].rolling(window=macd_ma_window).mean()
    return copy.deepcopy(data)


@st.cache
def find_stocks_above_conditions(stock_list):
    stocks_above_conditions = defaultdict(list)

    for stock_info in stock_list:
        stock = stock_info['Symbol']
        sector = stock_info['GICS Sector']
        try:
            data = calculate_moving_average(stock)
            data = calculate_macd(data, window_fast=5, macd_ma_window=5)
            data = calculate_macd(data)

            if (not data.empty and
                data.iloc[-1]['Close'] > data.iloc[-1]['MovingAverage'] and
                data.iloc[-1][f'MACD_5_26_9_MA_5'] > data.iloc[-1]['MACD_5_26_9']
            ):
                stocks_above_conditions[sector].append(stock)
        except Exception as e:
            st.warning(f"Error processing stock {stock}: {e}")

    return stocks_above_conditions


def plot_candlestick_chart(stock_ticker, period='3mo', interval='1d'):
    data = yf.download(tickers=stock_ticker, period=period, interval=interval)

    macd_data_20 = calculate_macd(stock_ticker, period=period, interval=interval)
    macd_data_5 = calculate_macd(stock_ticker, period=period, interval=interval, window_fast=5, window_slow=20, window_sign=5)

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


