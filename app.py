import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import time

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="VIBE // NQ TERMINAL",
    layout="wide",
    page_icon="💹",
    initial_sidebar_state="collapsed"
)

# --- CUSTOM CSS FOR "BLOOMBERG" NEON LOOK ---
st.markdown("""
    <style>
    /* Main Background */
    .stApp {
        background-color: #050505;
        color: #e0e0e0;
        font-family: 'Courier New', monospace;
    }
    /* Metrics */
    div[data-testid="stMetricValue"] {
        font-size: 1.5rem !important;
        color: #00ff41; /* Neon Green */
        text-shadow: 0 0 5px #00ff41;
    }
    /* Headers */
    h1, h2, h3 {
        color: #ff9500 !important; /* Amber Accent */
        border-bottom: 1px solid #333;
    }
    /* Cards/Containers */
    .css-1r6slb0 {
        border: 1px solid #333;
        background-color: #121212;
        padding: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- HEADER ---
c1, c2 = st.columns([3, 1])
with c1:
    st.title("VIBE // NQ_FUTURES")
with c2:
    if st.button("🔄 REFRESH DATA"):
        st.rerun()

# --- DATA FETCHING ---
@st.cache_data(ttl=60) # Cache data for 60 seconds to prevent API spam
def get_data():
    # NQ=F is Nasdaq 100 Futures, ^VIX is Volatility
    tickers = yf.download(tickers=['NQ=F', '^VIX', 'QQQ'], period='5d', interval='15m', progress=False)
    return tickers

try:
    data = get_data()
    
    # Process NQ Data (Handling Multi-index columns from yfinance)
    # yfinance structure varies; robust extraction:
    nq_data = data.xs('NQ=F', level=1, axis=1) if isinstance(data.columns, pd.MultiIndex) else data
    
    current_price = nq_data['Close'].iloc[-1]
    prev_close = nq_data['Close'].iloc[-2]
    change = current_price - prev_close
    pct_change = (change / prev_close) * 100
    
except Exception as e:
    st.error(f"Data Feed Error: {e}")
    st.stop()

# --- DASHBOARD GRID ---
col_chart, col_stats, col_news = st.columns([0.6, 0.2, 0.2])

with col_chart:
    st.subheader("PRICE ACTION [15m]")
    
    # Plotly Candlestick Chart
    fig = go.Figure(data=[go.Candlestick(
        x=nq_data.index,
        open=nq_data['Open'],
        high=nq_data['High'],
        low=nq_data['Low'],
        close=nq_data['Close'],
        increasing_line_color='#00ff41',
        decreasing_line_color='#ff3b30'
    )])
    
    fig.update_layout(
        plot_bgcolor='#121212',
        paper_bgcolor='#121212',
        font=dict(color='#e0e0e0', family="Courier New"),
        xaxis_rangeslider_visible=False,
        height=500,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(showgrid=True, gridcolor='#333'),
        yaxis=dict(showgrid=True, gridcolor='#333', side='right')
    )
    st.plotly_chart(fig, use_container_width=True)

with col_stats:
    st.subheader("MARKET INTERNALS")
    
    st.metric(label="NQ PRICE", value=f"{current_price:.2f}", delta=f"{change:.2f} ({pct_change:.2f}%)")
    
    # Mock sentiment (Real sentiment requires heavier NLP libraries)
    sentiment_score = 65
    sentiment_color = "#00ff41" if sentiment_score > 50 else "#ff3b30"
    
    st.markdown(f"""
    <div style="border: 1px solid #333; padding: 10px; margin-top: 20px;">
        <small style="color: #888;">MARKET SENTIMENT</small>
        <h2 style="color: {sentiment_color}; margin: 0;">BULLISH ({sentiment_score}%)</h2>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("**KEY LEVELS**")
    st.text(f"H: {nq_data['High'].iloc[-1]:.2f}")
    st.text(f"L: {nq_data['Low'].iloc[-1]:.2f}")
    st.text(f"VWAP: {(nq_data['Close'].iloc[-1] + nq_data['High'].iloc[-1] + nq_data['Low'].iloc[-1])/3:.2f}")

with col_news:
    st.subheader("NEWS WIRE")
    # Mock news data for the free version
    news_items = [
        {"time": "14:32", "head": "Fed Powell speaks on inflation data", "tag": "MACRO"},
        {"time": "14:15", "head": "Tech sector sees rotation inflow", "tag": "SECTOR"},
        {"time": "13:45", "head": "NVDA breaks all-time high volume", "tag": "STOCK"},
        {"time": "12:30", "head": "10Y Yield hits key resistance", "tag": "RATES"},
    ]
    
    for news in news_items:
        st.markdown(f"""
        <div style="border-left: 2px solid #ff9500; padding-left: 10px; margin-bottom: 15px;">
            <span style="color: #666; font-size: 0.8em;">{news['time']} // {news['tag']}</span>
            <div style="font-size: 0.9em;">{news['head']}</div>
        </div>
        """, unsafe_allow_html=True)

st.sidebar.info("Data provided by Yahoo Finance (Free Tier). Delayed 15m.")
