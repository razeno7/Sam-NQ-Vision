import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta

# Configuration de la page
st.set_page_config(
    page_title="Sam NQ Vision",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Style Bloomberg/Professional (Mode Sombre Profond)
st.markdown("""
<style>
    .reportview-container { background: #000000; }
    .main { background: #000000; color: #ffffff; }
    div[data-testid="stMetricValue"] { color: #ffffff; font-family: 'Courier New', Courier, monospace; }
    .stMetric { background-color: #111111; padding: 10px; border-radius: 5px; border: 1px solid #333; }
</style>
""", unsafe_allow_html=True)

# --- CACHING DATA ---
@st.cache_data(ttl=300)
def load_data(ticker, period="1mo", interval="1h"):
    try:
        data = yf.download(ticker, period=period, interval=interval)
        return data
    except Exception as e:
        st.error(f"Erreur de chargement pour {ticker}: {e}")
        return pd.DataFrame()

# --- SIDEBAR ---
st.sidebar.title("🛠️ Paramètres")
tickers_list = {
    "Nasdaq 100": "NQ=F",
    "Apple": "AAPL",
    "Microsoft": "MSFT",
    "Nvidia": "NVDA",
    "Amazon": "AMZN",
    "Alphabet": "GOOGL",
    "Meta": "META",
    "Tesla": "TSLA",
    "10Y Yield": "^TNX",
    "Dollar Index": "DX-Y.NYB"
}

selection = st.sidebar.selectbox("Sélectionner un actif", list(tickers_list.keys()))
selected_ticker = tickers_list[selection]

period = st.sidebar.select_slider("Période", options=["1d", "5d", "1mo", "6mo", "1y", "max"], value="1mo")
interval = st.sidebar.selectbox("Intervalle", ["15m", "30m", "1h", "1d", "1wk"], index=2)

if st.sidebar.button("🔄 Rafraîchir les données"):
    st.cache_data.clear()
    st.rerun()

# --- MAIN DASHBOARD ---
st.title(f"📊 Sam NQ Vision - {selection}")

# Chargement des données
df = load_data(selected_ticker, period, interval)

if not df.empty:
    # Métriques en temps réel (simulées par la dernière clôture)
    last_close = df['Close'].iloc[-1]
    prev_close = df['Close'].iloc[-2]
    change = last_close - prev_close
    pct_change = (change / prev_close) * 100
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Prix Actuel", f"{last_close:.2f}", f"{change:.2f}")
    col2.metric("Variation %", f"{pct_change:.2f}%")
    col3.metric("Volume", f"{df['Volume'].iloc[-1]:,.0f}")
    col4.metric("Plus Haut (Période)", f"{df['High'].max():.2f}")

    # Graphique en chandeliers
    fig = go.Figure(data=[go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='Prix'
    )])

    # Moyennes Mobiles
    df['SMA20'] = df['Close'].rolling(window=20).mean()
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA20'], line=dict(color='orange', width=1), name='SMA 20'))

    fig.update_layout(
        template='plotly_dark',
        xaxis_rangeslider_visible=False,
        height=600,
        margin=dict(l=20, r=20, t=20, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
    )
    
    st.plotly_chart(fig, use_container_width=True)

    # Analyse Technique Simple
    st.subheader("📋 Données Historiques")
    st.dataframe(df.tail(10).style.highlight_max(axis=0), use_container_width=True)
else:
    st.warning("Aucune donnée trouvée. Vérifiez le ticker ou la connexion.")
