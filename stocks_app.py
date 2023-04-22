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


def calculate_macd(stock_ticker, period='20d', interval='1d'):
    data = yf.download(tickers=stock_ticker, period=period, interval=interval)
    macd_indicator = MACD(data['Close'], window_slow=26, window_fast=12, window_sign=9)
    data['MACD'] = macd_indicator.macd()
    return data



def find_stocks_above_macd(stock_list):
    stocks_above_macd = []

    for stock in stock_list:
        try:
            data = calculate_macd(stock)

            if not data.empty and data.iloc[-1]['Close'] > data.iloc[-1]['MACD']:
                stocks_above_macd.append(stock)
        except Exception as e:
            st.warning(f"Error processing stock {stock}: {e}")

    return stocks_above_macd



st.title("Stocks with the Current Price Above the Daily 20 MACD")

st.write("Fetching S&P 500 stock tickers...")
sp500_tickers = get_sp500_tickers()

st.write("Analyzing stocks...")
stocks_above_macd = find_stocks_above_macd(sp500_tickers)

st.header("Stocks with the current price above the daily 20 MACD:")
st.write(stocks_above_macd)
