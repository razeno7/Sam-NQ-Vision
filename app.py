import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(
    page_title="Sam NQ Vision",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Style Bloomberg Deep Dark
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background-color: #000000; }
    [data-testid="stHeader"] { background: rgba(0,0,0,0); }
    [data-testid="stSidebar"] { background-color: #0a0a0a; border-right: 1px solid #333; }
    .stMetric { background-color: #111; padding: 15px; border-radius: 5px; border: 1px solid #222; }
    div[data-testid="stMetricValue"] { color: #00ff00; font-family: 'Courier New', monospace; }
</style>
""", unsafe_allow_html=True)

# --- ENGINE ---
@st.cache_data(ttl=300)
def fetch_market_data(ticker, period="1mo", interval="1h"):
    try:
        data = yf.download(ticker, period=period, interval=interval, progress=False)
        if data.empty:
            return None
        
        # FIX IMPORTANT: Aplatir l'index des colonnes si yfinance renvoie un MultiIndex (bug fréquent en cloud)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
            
        return data
    except Exception as e:
        st.error(f"Erreur API Yahoo: {e}")
        return None

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://img.icons8.com/color/96/bullish.png", width=50)
    st.title("SAM NQ VISION")
    st.markdown("---")
    
    tickers = {
        "NASDAQ 100": "NQ=F",
        "NVIDIA": "NVDA",
        "APPLE": "AAPL",
        "MICROSOFT": "MSFT",
        "TESLA": "TSLA",
        "BITCOIN": "BTC-USD",
        "10Y YIELD": "^TNX",
        "USD INDEX": "DX-Y.NYB"
    }
    
    selected_label = st.selectbox("Instrument", list(tickers.keys()))
    ticker = tickers[selected_label]
    
    period = st.select_slider("Période", options=["1d", "5d", "1mo", "3mo", "6mo", "1y"], value="1mo")
    interval = st.selectbox("Timeframe", ["15m", "30m", "1h", "1d"], index=2)
    
    if st.button("🚀 FORCE REFRESH"):
        st.cache_data.clear()
        st.rerun()

# --- MAIN DASHBOARD ---
st.header(f"📈 {selected_label} | {ticker}")

with st.status("Récupération des flux de données...", expanded=False) as status:
    df = fetch_market_data(ticker, period, interval)
    if df is not None:
        status.update(label="Données reçues", state="complete", expanded=False)
    else:
        status.update(label="Échec de connexion", state="error")

if df is not None:
    # Métriques
    last_price = df['Close'].iloc[-1]
    prev_price = df['Close'].iloc[-2]
    delta = last_price - prev_price
    delta_pct = (delta / prev_price) * 100
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("PRIX", f"{last_price:,.2f}", f"{delta:,.2f}")
    m2.metric("VAR %", f"{delta_pct:.2f}%", f"{delta_pct:.2f}%")
    m3.metric("VOLUME", f"{df['Volume'].iloc[-1]:,.0f}")
    m4.metric("MAX PERIOD", f"{df['High'].max():,.2f}")

    # Chart
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='Candles'
    ))
    
    # Moyenne Mobile
    df['MA20'] = df['Close'].rolling(20).mean()
    fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], line=dict(color='#ffb000', width=1), name='MA20'))

    fig.update_layout(
        template='plotly_dark',
        xaxis_rangeslider_visible=False,
        height=600,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=0, b=0)
    )
    st.plotly_chart(fig, use_container_width=True)

    # Footer style Terminal
    st.markdown("---")
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("📋 Derniers ticks")
        st.dataframe(df.tail(5), use_container_width=True)
    with col_b:
        st.subheader("⚙️ Stats d'Analyse")
        st.write(f"Volatilité (Std): {df['Close'].std():.2f}")
        st.write(f"RSI (14) - Simulé: {np.random.randint(30, 70)}")
else:
    st.error("Impossible de charger les données. Vérifiez votre connexion ou essayez un autre instrument.")
