import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import feedparser
from datetime import datetime

# --- CONFIGURATION DU PROJET ---
st.set_page_config(
    layout="wide", 
    page_title="Sam-NQ-Vision",
    initial_sidebar_state="collapsed",
    page_icon="🦅"
)

# --- CSS HACK (DESIGN BLOOMBERG) ---
st.markdown("""
    <style>
    /* Fond noir global */
    .stApp {background-color: #050505;}
    
    /* Typographie Terminal */
    .stMarkdown, .stText, p, div, span {
        color: #e0e0e0; 
        font-family: 'Consolas', 'Courier New', monospace;
    }
    
    /* Métriques (Prix, etc.) */
    div[data-testid="stMetricValue"] {
        color: #FF9800 !important; /* Orange Bloomberg */
        font-size: 26px !important;
    }
    div[data-testid="stMetricLabel"] {
        color: #888; 
        font-size: 11px !important;
    }
    
    /* Masquer le menu hamburger et le footer Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Réduire les marges pour effet "Dense" */
    .block-container {
        padding-top: 1rem; 
        padding-bottom: 0rem; 
        padding-left: 1rem; 
        padding-right: 1rem;
    }
    
    /* Style des Onglets */
    button[data-baseweb="tab"] {
        background-color: #111;
        border: 1px solid #333;
        color: #888;
        border-radius: 0px;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        background-color: #FF9800;
        color: #000;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# --- FONCTIONS BACKEND ---

@st.cache_data(ttl=60)
def get_market_data(ticker="QQQ"):
    try:
        # On force le téléchargement sans progress bar
        df = yf.download(ticker, period="5d", interval="5m", progress=False)
        
        if df.empty:
            return None

        # Indicateurs Techniques
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        return df
    except Exception as e:
        return None

def get_rss_news():
    # Flux RSS Yahoo Finance
    rss_url = "https://finance.yahoo.com/news/rssindex"
    try:
        feed = feedparser.parse(rss_url)
        return feed.entries[:10]
    except:
        return []

# --- INTERFACE UTILISATEUR (UI) ---

# Sidebar cachée (Menu config)
with st.sidebar:
    st.header("SAM-NQ-VISION CONFIG")
    ticker_input = st.text_input("SYMBOL", "QQQ").upper()
    if st.button("CLEAR CACHE"):
        st.cache_data.clear()

# --- INITIALISATION DES VARIABLES (ANTI-CRASH) ---
current_price = 0.0
daily_change = 0.0
pct_change = 0.0
rsi_now = 0.0
data_available = False 

# 1. HEADER (Tentative de chargement)
df = get_market_data(ticker_input)

if df is not None and not df.empty:
    data_available = True
    current_price = float(df['Close'].iloc[-1])
    open_price = float(df['Open'].iloc[0])
    daily_change = current_price - open_price
    pct_change = (daily_change / open_price) * 100
    rsi_now = df['RSI'].iloc[-1]
    
    # Affichage Header
    c1, c2, c3, c4 = st.columns([1, 1, 1, 3])
    with c1: st.metric("LAST PRICE", f"{current_price:.2f}")
    with c2: st.metric("CHANGE", f"{daily_change:+.2f}", f"{pct_change:+.2f}%")
    with c3: st.metric("RSI (14)", f"{rsi_now:.1f}")
    with c4:
        st.markdown(f"""
        <div style='text-align:right; padding-top:10px;'>
        <span style='color:#FF9800; font-weight:bold; font-size:20px;'>SAM-NQ-VISION</span> 
        <span style='color:#666;'> | {ticker_input} PROXY | </span>
        <span style='color:#00FF00;'>● ONLINE</span>
        </div>
        """, unsafe_allow_html=True)
else:
    st.error(f"DATA FEED OFFLINE: Impossible de joindre Yahoo Finance pour {ticker_input}. Réessayez 'CLEAR CACHE' ou attendez.")
    current_price = 0.0 

st.markdown("---")

# 2. ESPACE DE TRAVAIL
tab_chart, tab_news, tab_depth = st.tabs(["CHARTING [F1]", "NEWS WIRE [F2]", "LEVEL II [F3]"])

with tab_chart:
    if data_available and df is not None:
        fig = make_subplots(
            rows=2, cols=1, 
            shared_xaxes=True, 
            vertical_spacing=0.05, 
            row_heights=[0.75, 0.25]
        )

        fig.add_trace(go.Candlestick(
            x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
            name="Price", increasing_line_color='#00FF00', decreasing_line_color='#FF0000'
        ), row=1, col=1)

        fig.add_trace(go.Scatter(x=df.index, y=df['SMA_20'], line=dict(color='orange', width=1), name="SMA 20"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='#00E5FF', width=1), name="RSI"), row=2, col=1)
        
        fig.add_hline(y=70, line_width=1, line_dash="dot", line_color="red", row=2, col=1)
        fig.add_hline(y=30, line_width=1, line_dash="dot", line_color="green", row=2, col=1)

        # --- CORRECTION DE L'ERREUR PLOTLY ICI ---
        # J'ai supprimé "bg_color='black'" qui causait le crash
        fig.update_layout(
            height=600,
            plot_bgcolor='black',   # Couleur de la zone de tracé
            paper_bgcolor='black',  # Couleur du fond global
            font=dict(color='#888', family="Courier New"),
            xaxis_rangeslider_visible=False,
            showlegend=False,
            margin=dict(l=0, r=40, t=10, b=0),
        )
        
        fig.update_xaxes(showgrid=False, gridcolor='#222')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#1a1a1a', side='right') 

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.markdown("<br><br><h3 style='text-align:center; color:#333'>WAITING FOR DATA...</h3>", unsafe_allow_html=True)

with tab_news:
    st.markdown("### 📰 REAL-TIME NEWS WIRE")
    news_items = get_rss_news()
    if news_items:
        for item in news_items:
            pub_date = item.get('published', 'No Date')
            st.markdown(f"""
            <div style='border-bottom: 1px solid #222; padding: 10px; font-size: 14px;'>
                <span style='color:#FF9800;'>[{pub_date}]</span><br>
                <a href='{item.link}' target='_blank' style='color:#ddd; text-decoration:none; font-weight:bold;'>
                    {item.title}
                </a>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("News feed loading...")

with tab_depth:
    st.markdown("### MARKET DEPTH (SIMULATION)")
    
    if current_price > 0:
        c_bid, c_ask = st.columns(2)
        with c_bid:
            st.markdown("**BID**")
            st.dataframe(pd.DataFrame({"SIZE": [5, 12, 4], "PRICE": [current_price-0.05, current_price-0.10, current_price-0.15]}), hide_index=True)
        with c_ask:
            st.markdown("**ASK**")
            st.dataframe(pd.DataFrame({"PRICE": [current_price+0.05, current_price+0.10, current_price+0.15], "SIZE": [8, 20, 2]}), hide_index=True)
    else:
        st.warning("Data offline: Cannot calculate Level II depth.")

if st.button('REFRESH DATA ⟳'):
    st.rerun()
