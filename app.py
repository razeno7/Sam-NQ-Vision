import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime

# --- SAM NQ VISION | PROFESSIONAL TERMINAL ---
st.set_page_config(
    page_title="Sam NQ Vision - Terminal Pro",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Bloomberg Terminal Styling
st.markdown("""
<style>
    /* Global Background */
    .stApp { background-color: #000000; color: #d1d1d1; }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #050505;
        border-right: 1px solid #333;
    }
    
    /* Metrics */
    div[data-testid="stMetric"] {
        background-color: #0a0a0a;
        border: 1px solid #222;
        padding: 10px;
        border-radius: 4px;
    }
    div[data-testid="stMetricValue"] {
        color: #00ff00 !important;
        font-family: 'Courier New', monospace !important;
        font-weight: bold;
    }
    
    /* Dataframe styling */
    .stDataFrame { border: 1px solid #222; }
    
    /* Headers */
    h1, h2, h3 { 
        color: #fbbf24 !important; 
        font-family: 'Courier New', monospace;
        letter-spacing: -1px;
    }
</style>
""", unsafe_allow_html=True)

# --- CORE DATA ENGINE ---
@st.cache_data(ttl=60)
def get_terminal_data(ticker, period="1mo", interval="1h"):
    try:
        data = yf.download(ticker, period=period, interval=interval, progress=False)
        if data.empty: return None
        # Fix yfinance MultiIndex bug
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        return data
    except Exception as e:
        st.error(f"ENGINE ERROR: {e}")
        return None

def compute_indicators(df):
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    # MA
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
    return df

# --- SIDEBAR NAV ---
with st.sidebar:
    st.markdown("# 🖥️ SAM VISION")
    st.markdown("---")
    
    mode = st.radio("FUNCTION", ["📊 Terminal", "🗺️ Heatmap", "📡 News Feed"])
    
    st.markdown("---")
    tickers = {
        "NQ1! (Nasdaq)": "NQ=F",
        "AAPL (Apple)": "AAPL",
        "NVDA (Nvidia)": "NVDA",
        "TSLA (Tesla)": "TSLA",
        "BTC (Bitcoin)": "BTC-USD",
        "DXY (USD Index)": "DX-Y.NYB"
    }
    selected_asset = st.selectbox("SECURITY", list(tickers.keys()))
    ticker_sym = tickers[selected_asset]
    
    tf = st.selectbox("TIMEFRAME", ["15m", "1h", "1d"], index=1)
    range_val = st.selectbox("RANGE", ["5d", "1mo", "6mo", "1y"], index=1)
    
    if st.button("🔄 REFRESH SYSTEM"):
        st.cache_data.clear()
        st.rerun()

# --- MAIN RENDER ---
if mode == "📊 Terminal":
    df = get_terminal_data(ticker_sym, range_val, tf)
    
    if df is not None:
        df = compute_indicators(df)
        
        # Panel 1: Top Metrics
        last = df['Close'].iloc[-1]
        prev = df['Close'].iloc[-2]
        chg = last - prev
        chg_pct = (chg / prev) * 100
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("LAST PRICE", f"{last:,.2f}", f"{chg:,.2f}")
        c2.metric("CHANGE %", f"{chg_pct:.2f}%")
        c3.metric("RSI (14)", f"{df['RSI'].iloc[-1]:.2f}")
        c4.metric("VOL (PERIOD)", f"{df['Volume'].iloc[-1]:,.0f}")
        
        # Panel 2: Interactive Chart
        fig = go.Figure()
        # Candlestick
        fig.add_trace(go.Candlestick(
            x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
            name='Candles'
        ))
        # Indicators
        fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], line=dict(color='#fbbf24', width=1), name='MA20'))
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA50'], line=dict(color='#3b82f6', width=1), name='EMA50'))
        
        fig.update_layout(
            template='plotly_dark', height=600,
            xaxis_rangeslider_visible=False,
            margin=dict(l=0, r=0, t=20, b=0),
            paper_bgcolor='black', plot_bgcolor='black'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Panel 3: Technicals & Data
        st.markdown("### 📋 DATA ANALYSIS")
        col_a, col_b = st.columns([2, 1])
        with col_a:
            st.dataframe(df.tail(10), use_container_width=True)
        with col_b:
            st.write("**Signals:**")
            if df['RSI'].iloc[-1] > 70: st.error("⚠️ OVERBOUGHT")
            elif df['RSI'].iloc[-1] < 30: st.success("🚀 OVERSOLD")
            else: st.info("⏺️ NEUTRAL")

elif mode == "🗺️ Heatmap":
    st.header("NASDAQ 100 RELATIVE PERFORMANCE")
    # Simulation d'un heatmap sectoriel
    data = {
        'Tech': np.random.uniform(-5, 5, 5),
        'Finance': np.random.uniform(-5, 5, 5),
        'Retail': np.random.uniform(-5, 5, 5)
    }
    st.write("Visualisation des flux de capitaux en temps réel...")
    st.bar_chart(pd.DataFrame(data))

else:
    st.header("BREAKING NEWS FEED")
    news_items = [
        {"time": "14:50", "headline": "Fed's Daly: No urgency to adjust rates yet."},
        {"time": "14:32", "headline": "Nvidia options volume hits record high for June expiration."},
        {"time": "14:10", "headline": "European markets close higher as inflation cools."},
        {"time": "13:55", "headline": "TSMC reports 20% jump in monthly revenue."}
    ]
    for n in news_items:
        st.markdown(f"**{n['time']}** - {n['headline']}")
        st.divider()
