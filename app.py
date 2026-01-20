import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

# --- BLOOMBERG COMMAND CENTER V7 ---
st.set_page_config(page_title="BLOOMBERG NQ PRO", layout="wide", initial_sidebar_state="collapsed")

# 1. CSS INJECTION (FORCE ZERO MARGINS & BLOOMBERG COLORS)
st.markdown("""
<style>
    /* Kill Streamlit Defaults */
    .stApp { background-color: #000000; color: #d1d1d1; font-family: 'JetBrains Mono', monospace; }
    [data-testid="stHeader"] { display: none; }
    .main .block-container { 
        padding-top: 0.5rem !important; 
        padding-bottom: 0rem !important; 
        padding-left: 0.5rem !important; 
        padding-right: 0.5rem !important; 
        max-width: 100% !important; 
    }
    
    /* Metrics High Density */
    div[data-testid="stMetric"] {
        background-color: #050505;
        border: 1px solid #222;
        border-left: 3px solid #ffb000;
        padding: 4px 10px;
        margin-bottom: 0px;
    }
    div[data-testid="stMetricValue"] { font-size: 1.1rem !important; color: #ffffff !important; font-weight: 700; }
    div[data-testid="stMetricLabel"] { font-size: 0.65rem !important; color: #888 !important; text-transform: uppercase; }
    
    /* Sidebar Table Look */
    .stDataFrame { border: 1px solid #222 !important; }
    
    /* Input Style */
    .stTextInput input {
        background-color: #0a0a0a !important;
        color: #00f0ff !important;
        border: 1px solid #333 !important;
        border-radius: 2px;
        font-family: 'JetBrains Mono', monospace;
    }
</style>
""", unsafe_allow_html=True)

# 2. DATA ENGINE
@st.cache_data(ttl=60)
def fetch_terminal_data(ticker, period="1mo"):
    try:
        data = yf.download(ticker, period=period, interval="1h", progress=False)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        
        # Technicals
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data['RSI'] = 100 - (100 / (1 + rs))
        
        high_low = data['High'] - data['Low']
        high_cp = np.abs(data['High'] - data['Close'].shift())
        low_cp = np.abs(data['Low'] - data['Close'].shift())
        tr = pd.concat([high_low, high_cp, low_cp], axis=1).max(axis=1)
        data['ATR'] = tr.rolling(14).mean()
        
        return data
    except:
        return pd.DataFrame()

# 3. TOP TICKER TAPE (5 COLUMNS)
tape_cols = st.columns(5)
tickers = {"NQ=F": "Nasdaq", "ES=F": "S&P 500", "BTC-USD": "Bitcoin", "DX-Y.NYB": "DXY", "^TNX": "US10Y"}

for i, (sym, label) in enumerate(tickers.items()):
    with tape_cols[i]:
        d = yf.download(sym, period="1d", progress=False)
        if not d.empty:
            if isinstance(d.columns, pd.MultiIndex): d.columns = d.columns.get_level_values(0)
            price = d['Close'].iloc[-1]
            change = ((price / d['Open'].iloc[0]) - 1) * 100
            st.metric(label, f"{price:,.2f}", f"{change:+.2f}%")

# 4. MAIN WORKSPACE (75/25 SPLIT)
col_main, col_side = st.columns([3, 1])

with col_main:
    # Header & Command
    c_cmd, c_info = st.columns([1, 2])
    with c_cmd:
        target = st.text_input("COMMAND", value="NVDA").upper()
    
    df = fetch_terminal_data(target)
    
    if not df.empty:
        # MAIN CHART
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                           vertical_spacing=0.03, row_heights=[0.8, 0.2])
        
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], 
                                   low=df['Low'], close=df['Close'], name="Price"), row=1, col=1)
        
        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name="Vol", marker_color='#333'), row=2, col=1)
        
        fig.update_layout(template='plotly_dark', height=550, 
                         margin=dict(l=0,r=0,t=10,b=0),
                         xaxis_rangeslider_visible=False,
                         paper_bgcolor='black', plot_bgcolor='black')
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        # LOWER STATUS CARDS
        st.markdown("<br>", unsafe_allow_html=True)
        sc1, sc2, sc3 = st.columns(3)
        with sc1:
            st.metric("Total Vol (1H)", f"{df['Volume'].iloc[-1]:,.0f}", "Live Data")
        with sc2:
            rsi_val = df['RSI'].iloc[-1]
            color = "Normal"
            if rsi_val > 70: color = "Overbought"
            elif rsi_val < 30: color = "Oversold"
            st.metric("RSI (14)", f"{rsi_val:.2f}", color)
        with sc3:
            st.metric("ATR (Volatility)", f"{df['ATR'].iloc[-1]:.2f}", "Trailing 14")
    else:
        st.error(f"INVALID TICKER: {target}")

with col_side:
    st.markdown("<h4 style='color:#ffb000; font-size: 10px; border-bottom:1px solid #333;'>MARKET MOVERS (TECH)</h4>", unsafe_allow_html=True)
    movers = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA"]
    mover_data = []
    for m in movers:
        tick = yf.Ticker(m)
        price = tick.fast_info['last_price']
        change = (tick.fast_info['last_price'] / tick.fast_info['open'] - 1) * 100
        mover_data.append({"Ticker": m, "Price": f"{price:.2f}", "Chg %": f"{change:+.2f}%"})
    
    st.table(pd.DataFrame(mover_data))
    
    st.markdown("<br><h4 style='color:#ffb000; font-size: 10px; border-bottom:1px solid #333;'>LAST NEWS</h4>", unsafe_allow_html=True)
    news_ticker = yf.Ticker(target)
    for n in news_ticker.news[:5]:
        st.markdown(f"**[{n['publisher']}]** {n['title'][:60]}...")
        st.markdown(f"<p style='color:#555; font-size: 9px;'>{datetime.fromtimestamp(n['providerPublishTime']).strftime('%H:%M')}</p>", unsafe_allow_html=True)
