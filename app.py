import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import feedparser
import time

# --- 1. CONFIGURATION "FULL SCREEN" ---
st.set_page_config(
    layout="wide",
    page_title="BLOOMBERG NQ VISION",
    page_icon="terminal",
    initial_sidebar_state="collapsed"
)

# --- 2. CSS "PIXEL PERFECT" (STYLE TERMINAL) ---
st.markdown("""
    <style>
    /* Reset total */
    .stApp {background-color: #0e0e0e;}
    .block-container {padding: 0.5rem 1rem !important;}
    
    /* Typographie Bloomberg */
    * {font-family: 'Roboto Mono', 'Consolas', monospace !important; letter-spacing: -0.5px;}
    
    /* Couleurs du Terminal */
    .bullish {color: #00ff00 !important;}
    .bearish {color: #ff0000 !important;}
    .neutral {color: #ff9800 !important;}
    .terminal-text {color: #b0b0b0;}
    
    /* Panels (Bento Box style) */
    div[data-testid="stVerticalBlock"] > div {
        background-color: #161616;
        border: 1px solid #333;
        border-radius: 4px;
        padding: 10px;
        margin-bottom: 5px;
    }
    
    /* Métriques Compactes */
    div[data-testid="stMetricValue"] {font-size: 20px !important; color: #ff9800 !important;}
    div[data-testid="stMetricLabel"] {font-size: 10px !important; color: #666 !important;}
    
    /* Cacher les éléments inutiles */
    header, footer, #MainMenu {display: none !important;}
    </style>
""", unsafe_allow_html=True)

# --- 3. MOTEUR DE DONNÉES ---
@st.cache_data(ttl=30)
def get_data():
    # On récupère le QQQ (Proxy NQ)
    ticker = yf.Ticker("QQQ")
    # Données intraday précises (1m ou 5m selon dispo)
    df = ticker.history(period="1d", interval="5m")
    return df

def get_news():
    try:
        # Flux Reuters Technology ou CNBC
        feed = feedparser.parse("https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664")
        return feed.entries[:8]
    except:
        return []

def calculate_sentiment(df):
    # Algo simple de sentiment technique
    if df.empty: return "NEUTRAL", 50
    
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    current_rsi = rsi.iloc[-1]
    
    # SMA Trend
    sma_short = df['Close'].rolling(5).mean().iloc[-1]
    sma_long = df['Close'].rolling(20).mean().iloc[-1]
    
    score = 50
    if current_rsi > 70: score -= 20 (Overbought)
    elif current_rsi < 30: score += 20 (Oversold)
    
    if sma_short > sma_long: score += 20 # Bullish trend
    else: score -= 20 # Bearish trend
    
    if score > 60: return "BULLISH", score
    elif score < 40: return "BEARISH", score
    else: return "NEUTRAL", score

# --- 4. INTERFACE PRINCIPALE ---

df = get_data()
news = get_news()

# A. HEADER BAR (Bandeau supérieur)
if not df.empty:
    last_price = df['Close'].iloc[-1]
    prev_close = df['Open'].iloc[0]
    chg = last_price - prev_close
    pct = (chg / prev_close) * 100
    
    # Layout en 6 colonnes serrées
    h1, h2, h3, h4, h5, h6 = st.columns([1, 1, 1, 1, 1, 2])
    
    with h1: st.metric("NQ PROXY", f"{last_price:.2f}")
    with h2: st.metric("CHANGE", f"{chg:+.2f}", f"{pct:+.2f}%")
    with h3: st.metric("HIGH", f"{df['High'].max():.2f}")
    with h4: st.metric("LOW", f"{df['Low'].min():.2f}")
    with h5: 
        sentiment, score = calculate_sentiment(df)
        color = "green" if "BULL" in sentiment else "red" if "BEAR" in sentiment else "orange"
        st.markdown(f"<div style='text-align:center'><small>ALGO SENTIMENT</small><br><b style='color:{color}'>{sentiment}</b></div>", unsafe_allow_html=True)
    with h6:
        st.markdown(f"<div style='text-align:right; color:#444; font-size:12px'>SYSTEM: ONLINE<br>LATENCY: 24ms<br>FEED: NASDAQ VIA YAHOO</div>", unsafe_allow_html=True)

# B. MAIN GRID (Chart + Sidebar Data)
c_main, c_side = st.columns([3, 1])

with c_main:
    # GRAPHIQUE PRO (CANDLESTICK + VOLUME)
    if not df.empty:
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.8, 0.2], vertical_spacing=0.02)
        
        # Candles
        fig.add_trace(go.Candlestick(
            x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
            name="NQ",
            increasing_line_color='#00ff00', increasing_fillcolor='rgba(0,255,0,0.1)',
            decreasing_line_color='#ff0000', decreasing_fillcolor='rgba(255,0,0,0.1)'
        ), row=1, col=1)
        
        # VWAP (Approximation simple)
        df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum()
        fig.add_trace(go.Scatter(x=df.index, y=df['VWAP'], mode='lines', line=dict(color='#ff9800', width=1, dash='dot'), name='VWAP'), row=1, col=1)

        # Volume
        colors = ['#00ff00' if c >= o else '#ff0000' for c, o in zip(df['Close'], df['Open'])]
        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors, name="Vol"), row=2, col=1)

        # Style Bloomberg "Blackout"
        fig.update_layout(
            height=600,
            template="plotly_dark",
            paper_bgcolor="#161616",
            plot_bgcolor="#0e0e0e",
            margin=dict(l=0, r=50, t=10, b=0),
            showlegend=False,
            xaxis_rangeslider_visible=False
        )
        # Grilles subtiles
        fig.update_xaxes(gridcolor='#222', showgrid=True)
        fig.update_yaxes(gridcolor='#222', showgrid=True, side='right') # PRIX A DROITE COMME LES PROS
        
        st.plotly_chart(fig, use_container_width=True)

with c_side:
    st.markdown("**📡 NEWS WIRE**")
    if news:
        for n in news:
            t = n.get('published', '')[17:22]
            st.markdown(f"""
            <div style='border-left: 2px solid #ff9800; padding-left: 8px; margin-bottom: 8px; font-size: 12px;'>
                <span style='color:#666'>{t}</span> <a href='{n.link}' style='color:#ddd; text-decoration:none'>{n.title}</a>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No news feed.")

    st.markdown("---")
    st.markdown("**📊 MARKET DEPTH (L2 SIM)**")
    # Carnet d'ordre simulé pour l'effet visuel
    if not df.empty:
        price = last_price
        l2_data = pd.DataFrame({
            "BID SIZE": [120, 450, 100],
            "BID": [price-0.02, price-0.05, price-0.09],
            "ASK": [price+0.02, price+0.05, price+0.09],
            "ASK SIZE": [300, 150, 500]
        })
        st.dataframe(l2_data, hide_index=True, use_container_width=True)

# Bouton discret pour refresh
if st.button("SYNC TERMINAL"):
    st.rerun()
