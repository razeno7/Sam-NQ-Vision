import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

# --- SAM TERMINAL ELITE V3 ---
# CONFIGURATION D'INTERFACE DENSE BLOOMBERG
st.set_page_config(
    page_title="SAM TERMINAL PRO",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# INJECTION CSS POUR SUPPRIMER TOUS LES ESPACES INUTILES
st.markdown("""
<style>
    /* Global Styles */
    .stApp { background-color: #000000; color: #d1d1d1; font-family: 'Courier New', monospace; }
    header, footer { visibility: hidden !important; }
    .main .block-container { padding: 0.5rem 1rem !important; max-width: 100% !important; }
    
    /* Bloomberg Aesthetics */
    div[data-testid="stMetric"] {
        background-color: #050505;
        border: 1px solid #222;
        border-left: 4px solid #ffb000;
        padding: 4px 10px;
        margin: 2px 0;
    }
    div[data-testid="stMetricValue"] { font-size: 1.1rem !important; color: #ffffff !important; font-weight: bold; }
    div[data-testid="stMetricLabel"] { font-size: 0.7rem !important; color: #888 !important; }

    /* Input Styling */
    .stTextInput input {
        background-color: #000 !important;
        color: #ffb000 !important;
        border: 1px solid #333 !important;
        font-family: 'Courier New', monospace;
    }
    
    /* Tables */
    .stDataFrame { border: 1px solid #111; }
    thead th { background-color: #111 !important; color: #555 !important; font-size: 10px !important; }
</style>
""", unsafe_allow_html=True)

# --- ENGINE: DATA & ANALYTICS ---
@st.cache_data(ttl=60)
def fetch_ticker_data(symbol, range="1mo", interval="1h"):
    try:
        data = yf.download(symbol, period=range, interval=interval, progress=False)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        return data
    except Exception as e:
        return None

def compute_technicals(df):
    # RSI (14)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # Bollinger Bands
    df['MA20'] = df['Close'].rolling(20).mean()
    df['STD20'] = df['Close'].rolling(20).std()
    df['Upper'] = df['MA20'] + (df['STD20'] * 2)
    df['Lower'] = df['MA20'] - (df['STD20'] * 2)
    
    # Simple Sentiment Logic
    df['Sentiment'] = np.where(df['Close'] > df['MA20'], 0.7, 0.3)
    return df

# --- UI: HEADER COMMAND ---
c_cmd, c_info = st.columns([5, 1])
with c_cmd:
    target = st.text_input("COMMAND", value="NQ=F", help="Enter Ticker (e.g. AAPL, BTC-USD)").upper()
with c_info:
    st.markdown(f"**SAM TERMINAL V3**\n{datetime.now().strftime('%H:%M:%S')}")

# --- UI: MAIN GRID ---
col_side, col_main = st.columns([1, 4])

# WATCHLIST LATERALE
with col_side:
    st.caption("WATCHLIST / MACD")
    watchlist = {"NQ1!": "NQ=F", "DXY": "DX-Y.NYB", "VIX": "^VIX", "BTC": "BTC-USD"}
    for label, sym in watchlist.items():
        d = fetch_ticker_data(sym, "1d", "1h")
        if d is not None:
            last = d['Close'].iloc[-1]
            chg = ((last - d['Close'].iloc[0]) / d['Close'].iloc[0]) * 100
            st.metric(label, f"{last:,.2f}", f"{chg:.2f}%")

    st.divider()
    st.caption("SENTIMENT ENGINE")
    st.progress(0.72, text="Market Greed: 72%")

# GRAPHIQUE CENTRAL COMPOSITE
with col_main:
    df = fetch_ticker_data(target, "1mo", "1h")
    if df is not None:
        df = compute_technicals(df)
        
        # Subplots
        fig = make_subplots(rows=3, cols=1, shared_xaxes=True, 
                           vertical_spacing=0.03, row_heights=[0.6, 0.2, 0.2])
        
        # 1. Price + Bollinger
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], 
                                   low=df['Low'], close=df['Close'], name="Price"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['Upper'], line=dict(color='gray', width=1, dash='dot'), name="Upper BB"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['Lower'], line=dict(color='gray', width=1, dash='dot'), name="Lower BB"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], line=dict(color='orange', width=1), name="MA20"), row=1, col=1)
        
        # 2. Volume
        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name="Vol"), row=2, col=1)
        
        # 3. RSI
        fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='cyan', width=1.5), name="RSI"), row=3, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)

        fig.update_layout(template='plotly_dark', height=700, margin=dict(l=0,r=0,t=0,b=0),
                         xaxis_rangeslider_visible=False, paper_bgcolor='black', plot_bgcolor='black')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("TICKER_NOT_FOUND // CHECK_CONNECTION")

# FOOTER LOGS
st.markdown("---")
st.caption("SYSTEMS ACTIVE // GIP: ENABLED // TERMINAL_ID: SNV_ELITE_01")
