import streamlit as st
import yfinance as yf
import pandas as pd
from ta.trend import MACD
import lxml


def get_sp500_tickers():
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    table = pd.read_html(url, header=0)[0]
    tickers = table['Symbol'].tolist()
    return tickers

def calculate_moving_average(stock_ticker, period='20d', interval='1d', window=20):
    data = yf.download(tickers=stock_ticker, period=period, interval=interval)
    data['MovingAverage'] = data['Close'].rolling(window=window).mean()
    return data

def calculate_macd(data, window_fast=12, window_slow=26, window_sign=9):
    macd_indicator = MACD(data['Close'], window_slow=window_slow, window_fast=window_fast, window_sign=window_sign)
    data[f'MACD_{window_fast}_{window_slow}_{window_sign}'] = macd_indicator.macd()
    return data

def find_stocks_above_conditions(stock_list):
    stocks_above_conditions = []

    for stock in stock_list:
        try:
            data = calculate_moving_average(stock)
            data = calculate_macd(data, window_fast=5)
            data = calculate_macd(data)

            if (not data.empty and
                data.iloc[-1]['Close'] > data.iloc[-1]['MovingAverage'] and
                data.iloc[-1]['Close'] > data.iloc[-1]['MACD_5_26_9']
            ):
                stocks_above_conditions.append(stock)
        except Exception as e:
            st.warning(f"Error processing stock {stock}: {e}")

    return stocks_above_conditions





st.title("Stocks with the Current Price Above the 20-Day Moving Average and 5-Day MACD Line")

st.write("Fetching S&P 500 stock tickers...")
sp500_tickers = get_sp500_tickers()

st.write("Analyzing stocks...")
stocks_above_conditions = find_stocks_above_conditions(sp500_tickers)

st.header("Stocks with the current price above the 20-day moving average and 5-day MACD line:")
st.write(stocks_above_conditions)

