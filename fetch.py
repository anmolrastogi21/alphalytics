import yfinance as yf
import pandas as pd
import time
import streamlit as st

@st.cache_data(ttl=300, show_spinner=False)
def get_stock_data(ticker, period="6mo"):
    for attempt in range(3):
        try:
            if period == "1d":
                df = yf.Ticker(ticker).history(period="1d", interval="5m")
            elif period == "5d":
                df = yf.Ticker(ticker).history(period="5d", interval="15m")
            else:
                df = yf.Ticker(ticker).history(period=period)

            df.reset_index(inplace=True)
            if 'Datetime' in df.columns:
                df.rename(columns={'Datetime': 'Date'}, inplace=True)
            df = df.dropna(subset=['Close']).reset_index(drop=True)

            if len(df) > 0:
                return df
        except Exception as e:
            if attempt < 2:
                time.sleep(2 ** attempt)
            else:
                st.warning(f"Couldn't fetch data for {ticker} — Yahoo Finance may be rate limiting. Try again shortly.")
                return pd.DataFrame()
    return pd.DataFrame()