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

def find_stocks_above_moving_average(stock_list):
    stocks_above_moving_average = []

    for stock in stock_list:
        try:
            data = calculate_moving_average(stock)

            if not data.empty and data.iloc[-1]['Close'] > data.iloc[-1]['MovingAverage']:
                stocks_above_moving_average.append(stock)
        except Exception as e:
            st.warning(f"Error processing stock {stock}: {e}")

    return stocks_above_moving_average




st.title("Stocks with the Current Price Above the 20-Day Moving Average")

st.write("Fetching S&P 500 stock tickers...")
sp500_tickers = get_sp500_tickers()

st.write("Analyzing stocks...")
stocks_above_moving_average = find_stocks_above_moving_average(sp500_tickers)

st.header("Stocks with the current price above the 20-day moving average:")
st.write(stocks_above_moving_average)
