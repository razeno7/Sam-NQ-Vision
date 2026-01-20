import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# --- SAM TERMINAL PRO CONFIG ---
st.set_page_config(page_title="SAM TERMINAL PRO", layout="wide", initial_sidebar_state="collapsed")

# CSS INJECTION POUR LOOK BLOOMBERG RETRO-MODERNE
st.markdown("""
<style>
    .stApp { background-color: #000000; color: #d1d1d1; font-family: 'Courier New', monospace; }
    [data-testid="stHeader"] { background: #000000; }
    .main .block-container { padding: 1rem; max-width: 100%; }
    
    /* Metrics Bloomberg Style */
    div[data-testid="stMetric"] {
        background-color: #050505;
        border-left: 3px solid #fbbf24;
        padding: 5px 10px;
        margin-bottom: 5px;
    }
    div[data-testid="stMetricValue"] { font-size: 1.2rem !important; color: #fbbf24 !important; }
    div[data-testid="stMetricDelta"] { font-size: 0.8rem !important; }

    /* Tables */
    .stDataFrame { border: 1px solid #222; font-size: 0.8rem; }
    
    /* Input */
    .stTextInput input {
        background-color: #0a0a0a !important;
        color: #00ff00 !important;
        border: 1px solid #333 !important;
        font-family: 'Courier New', monospace !important;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #050505; border-right: 1px solid #222; }
</style>
""", unsafe_allow_html=True)

# --- DATA ENGINE ---
@st.cache_data(ttl=60)
def fetch_data(ticker, period="1mo", interval="1h"):
    try:
        data = yf.download(ticker, period=period, interval=interval, progress=False)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        return data
    except: return None

def add_indicators(df):
    # Bollinger Bands
    df['MA20'] = df['Close'].rolling(20).mean()
    df['STD20'] = df['Close'].rolling(20).std()
    df['Upper'] = df['MA20'] + (df['STD20'] * 2)
    df['Lower'] = df['MA20'] - (df['STD20'] * 2)
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain/loss)))
    # MACD
    df['EMA12'] = df['Close'].ewm(span=12).mean()
    df['EMA26'] = df['Close'].ewm(span=26).mean()
    df['MACD'] = df['EMA12'] - df['EMA26']
    df['Signal'] = df['MACD'].ewm(span=9).mean()
    return df

# --- HEADER / COMMAND BAR ---
col_cmd, col_time = st.columns([4, 1])
with col_cmd:
    cmd = st.text_input("COMMAND", value="NQ=F", help="Enter Ticker (e.g. AAPL, NVDA, BTC-USD)")
with col_time:
    st.write(f"**SYSTEM TIME**\n{datetime.now().strftime('%H:%M:%S')}")

# --- MAIN INTERFACE ---
c_left, c_main, c_right = st.columns([1.5, 5, 1.5])

# LEFT: MARKET WATCH
with c_left:
    st.caption("WATCHLIST")
    watch_tickers = {"NQ": "NQ=F", "ES": "ES=F", "DXY": "DX-Y.NYB", "VIX": "^VIX", "10Y": "^TNX"}
    for label, sym in watch_tickers.items():
        d = fetch_data(sym, "2d", "1h")
        if d is not None:
            last = d['Close'].iloc[-1]
            chg = ((last - d['Close'].iloc[0]) / d['Close'].iloc[0]) * 100
            st.metric(label, f"{last:,.2f}", f"{chg:.2f}%")

# CENTER: ADVANCED CHARTING
with c_main:
    df = fetch_data(cmd, "1mo", "1h")
    if df is not None:
        df = add_indicators(df)
        
        fig = make_subplots(rows=3, cols=1, shared_xaxes=True, 
                           vertical_spacing=0.05, row_heights=[0.6, 0.2, 0.2])
        
        # Price & Bollinger
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], 
                                   low=df['Low'], close=df['Close'], name="Price"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['Upper'], line=dict(color='gray', width=1, dash='dot'), name="Upper BB"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['Lower'], line=dict(color='gray', width=1, dash='dot'), name="Lower BB"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], line=dict(color='orange', width=1.5), name="MA20"), row=1, col=1)
        
        # Volume
        colors = ['red' if row['Open'] - row['Close'] > 0 else 'green' for index, row in df.iterrows()]
        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors, name="Volume"), row=2, col=1)
        
        # RSI
        fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='#00ff00', width=1.5), name="RSI"), row=3, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)

        fig.update_layout(template='plotly_dark', height=750, margin=dict(l=0,r=0,t=10,b=0),
                         xaxis_rangeslider_visible=False, paper_bgcolor='black', plot_bgcolor='black')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("INVALID TICKER OR ENGINE TIMEOUT")

# RIGHT: TECHNICAL SUMMARY & MACRO
with c_right:
    st.caption("TECH SUMMARY")
    if df is not None:
        curr_rsi = df['RSI'].iloc[-1]
        st.write(f"RSI: {curr_rsi:.1f}")
        if curr_rsi > 70: st.error("OVERBOUGHT")
        elif curr_rsi < 30: st.success("OVERSOLD")
        else: st.info("NEUTRAL")
        
        st.divider()
        st.caption("MAG 7 SNAPSHOT")
        mag7 = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA"]
        m7_data = []
        for s in mag7:
            tmp = fetch_data(s, "1d", "1d")
            if tmp is not None:
                m7_data.append({"Sym": s, "Price": f"{tmp['Close'].iloc[-1]:.2f}"})
        st.table(pd.DataFrame(m7_data))

# FOOTER
st.markdown("---")
st.caption("SAM TERMINAL V2.5 // DATA DELAYED 15M (FREE TIER) // [F1] HELP [F2] NEWS [F3] CHAT")
