import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

# --- SAM TERMINAL PRO V4.0 ---
st.set_page_config(page_title="SAM TERMINAL ELITE", layout="wide", initial_sidebar_state="collapsed")

# BLOOMBERG BRUTALIST CSS
st.markdown("""
<style>
    .stApp { background-color: #000000; color: #d1d1d1; font-family: 'Courier New', monospace; }
    [data-testid="stHeader"] { display: none; }
    .main .block-container { padding: 0.5rem !important; max-width: 100% !important; }
    
    /* Metrics High Density */
    div[data-testid="stMetric"] {
        background-color: #050505;
        border: 1px solid #222;
        border-left: 3px solid #ffb000;
        padding: 5px 10px;
        margin: 2px 0;
    }
    div[data-testid="stMetricValue"] { font-size: 1.1rem !important; color: #ffffff !important; }
    div[data-testid="stMetricLabel"] { font-size: 0.7rem !important; color: #666 !important; }
    
    /* Input */
    .stTextInput input {
        background-color: #000 !important;
        color: #00f0ff !important;
        border: 1px solid #333 !important;
        font-family: 'Courier New', monospace !important;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ENGINE: DATA FETCHING
@st.cache_data(ttl=60)
def get_data(ticker, period="1mo"):
    data = yf.download(ticker, period=period, interval="1h", progress=False)
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    return data

# UI: TOP BAR
c1, c2 = st.columns([5, 1])
with c1:
    ticker = st.text_input("COMMAND", value="NQ=F").upper()
with c2:
    st.markdown(f"**V4.0 PRO**\n{datetime.now().strftime('%H:%M:%S')}")

# UI: MAIN QUADRANTS
col_side, col_main = st.columns([1, 4])

with col_side:
    st.caption("WATCHLIST")
    for s in ["NQ=F", "DX-Y.NYB", "^VIX", "BTC-USD"]:
        d = get_data(s, "1d")
        if not d.empty:
            st.metric(s.split('=')[0], f"{d['Close'].iloc[-1]:.2f}", f"{((d['Close'].iloc[-1]/d['Close'].iloc[0])-1)*100:.2f}%")

with col_main:
    df = get_data(ticker)
    if not df.empty:
        # COMPLEX SUBPLOTS
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                           vertical_spacing=0.02, row_heights=[0.8, 0.2])
        
        # Price & MA
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], 
                                   low=df['Low'], close=df['Close'], name="Price"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['Close'].rolling(20).mean(), line=dict(color='orange', width=1), name="MA20"), row=1, col=1)
        
        # Vol
        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name="Vol", marker_color='gray'), row=2, col=1)
        
        fig.update_layout(template='plotly_dark', height=700, margin=dict(l=0,r=0,t=0,b=0),
                         xaxis_rangeslider_visible=False, paper_bgcolor='black', plot_bgcolor='black')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("TICKER ERROR")
