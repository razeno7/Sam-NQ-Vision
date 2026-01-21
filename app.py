import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import feedparser
import time
from datetime import datetime

# --- 1. SETUP DE LA PAGE (MODE WIDE TOTAL) ---
st.set_page_config(
    layout="wide",
    page_title="BLOOMBERG NQ=F",
    page_icon="🦅",
    initial_sidebar_state="collapsed"
)

# --- 2. CSS "HEDGE FUND STYLE" ---
st.markdown("""
    <style>
    /* Fond noir absolu */
    .stApp {background-color: #000000;}
    .block-container {padding: 0px 10px 0px 10px !important; max-width: 100% !important;}
    
    /* Typographie */
    * {font-family: 'Roboto Mono', 'Consolas', monospace !important;}
    
    /* Couleurs Terminal */
    .up {color: #00FF00 !important;}
    .down {color: #FF0000 !important;}
    .text-gray {color: #888888 !important;}
    .text-orange {color: #FF9800 !important;}
    
    /* Metrics Custom */
    div[data-testid="stMetricValue"] {font-size: 24px !important; color: #E0E0E0 !important;}
    div[data-testid="stMetricLabel"] {font-size: 11px !important; color: #666 !important; font-weight: bold;}
    
    /* Bordures de section */
    .css-card {
        border: 1px solid #222;
        background-color: #0A0A0A;
        padding: 10px;
        border-radius: 0px;
        margin-bottom: 5px;
    }
    
    /* Cacher Header Streamlit */
    header, footer, #MainMenu {display: none !important;}
    </style>
""", unsafe_allow_html=True)

# --- 3. DATA ENGINE ---
@st.cache_data(ttl=15) # Refresh rapide
def get_market_data():
    # ESSAI 1: Le Future NQ
    ticker_symbol = "NQ=F" 
    ticker = yf.Ticker(ticker_symbol)
    df = ticker.history(period="5d", interval="5m")
    
    # FALLBACK: Si NQ=F plante (souvent le cas le week-end ou maintenance), on prend l'indice NDX
    if df.empty:
        ticker_symbol = "^NDX"
        ticker = yf.Ticker(ticker_symbol)
        df = ticker.history(period="5d", interval="5m")
        
    return df, ticker_symbol

def get_live_news():
    try:
        # Flux Reuters Tech
        feed = feedparser.parse("https://www.reutersagency.com/feed/?best-topics=tech&post_type=best")
        return feed.entries[:10]
    except:
        return []

def calculate_smart_sentiment(df):
    if df.empty: return "WAITING...", "gray"
    
    # Derniers prix
    close = df['Close'].iloc[-1]
    sma20 = df['Close'].rolling(20).mean().iloc[-1]
    sma50 = df['Close'].rolling(50).mean().iloc[-1]
    
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    current_rsi = rsi.iloc[-1]
    
    # LOGIQUE BULLISH (Trend Following)
    score = 0
    if close > sma20: score += 2 # Prix au dessus de la moyenne courte
    if sma20 > sma50: score += 2 # Tendance haussière confirmée
    if current_rsi > 50 and current_rsi < 80: score += 1 # Momentum sain
    if current_rsi > 80: score += 2 # Super momentum (Extreme Bull)
    
    if score >= 4: return "STRONG BULLISH", "#00FF00" # Vert Vif
    elif score >= 2: return "BULLISH", "#90EE90" # Vert clair
    elif score <= -2: return "BEARISH", "#FF0000" # Rouge
    else: return "NEUTRAL / CHOPPY", "#FF9800" # Orange

# --- 4. UI ARCHITECTURE ---

df, symbol = get_market_data()
news = get_live_news()

# HEADER DU TERMINAL
if not df.empty:
    current = df['Close'].iloc[-1]
    prev = df['Open'].iloc[0] # Open du début de l'historique chargé (approx)
    chg = current - prev
    pct = (chg / prev) * 100
    color_class = "up" if chg >= 0 else "down"
    
    # BARRE SUPERIEURE
    st.markdown(f"""
    <div style='display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #333; padding-bottom: 5px; margin-bottom: 10px;'>
        <div>
            <span style='font-size: 28px; font-weight: bold; color: #fff;'>{symbol}</span>
            <span style='font-size: 14px; color: #666; margin-left: 10px;'>NASDAQ 100 FUTURES</span>
        </div>
        <div style='text-align: right;'>
            <span style='font-size: 32px; font-weight: bold;' class='{color_class}'>{current:,.2f}</span>
            <span style='font-size: 18px; margin-left: 15px;' class='{color_class}'>{chg:+.2f} ({pct:+.2f}%)</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # GRID SYSTÈME (Gauche: Stats, Centre: Graph, Droite: News)
    col_left, col_center, col_right = st.columns([1, 3, 1])

    # --- COLONNE GAUCHE : MARKET DATA ---
    with col_left:
        st.markdown("<div class='css-card'>", unsafe_allow_html=True)
        st.markdown("<h4 class='text-orange'>KEY LEVELS</h4>", unsafe_allow_html=True)
        
        st.metric("HIGH (Session)", f"{df['High'].max():,.2f}")
        st.metric("LOW (Session)", f"{df['Low'].min():,.2f}")
        st.metric("VWAP (Approx)", f"{(df['Close'].mean()):,.2f}")
        
        st.markdown("---")
        sentiment, sent_color = calculate_smart_sentiment(df)
        st.markdown(f"<small class='text-gray'>ALGO SENTIMENT</small><br><b style='color:{sent_color}; font-size:18px'>{sentiment}</b>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Petit tableau technique
        st.markdown("<div class='css-card'>", unsafe_allow_html=True)
        st.markdown("<h4 class='text-orange'>TECHNICALS</h4>", unsafe_allow_html=True)
        st.write(pd.DataFrame({
            "IND": ["RSI(14)", "SMA(20)", "SMA(50)"],
            "VAL": [f"{calculate_smart_sentiment(df)[0] if 'x' in 'x' else 0}", f"{df['Close'].rolling(20).mean().iloc[-1]:,.0f}", f"{df['Close'].rolling(50).mean().iloc[-1]:,.0f}"]
        }).set_index("IND"))
        st.markdown("</div>", unsafe_allow_html=True)

    # --- COLONNE CENTRE : GRAPHIQUE MAITRE ---
    with col_center:
        # Création du graph multi-pane
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.8, 0.2], vertical_spacing=0.03)
        
        # Bougies
        fig.add_trace(go.Candlestick(
            x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
            name="Price",
            increasing_line_color='#00FF00', increasing_fillcolor='rgba(0,255,0,0.1)',
            decreasing_line_color='#FF0000', decreasing_fillcolor='rgba(255,0,0,0.1)'
        ), row=1, col=1)
        
        # SMA 20 (Ligne Orange)
        sma20 = df['Close'].rolling(window=20).mean()
        fig.add_trace(go.Scatter(x=df.index, y=sma20, line=dict(color='#FF9800', width=1), name="SMA 20"), row=1, col=1)

        # Volume
        colors = ['#00FF00' if c >= o else '#FF0000' for c, o in zip(df['Close'], df['Open'])]
        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors, name="Vol"), row=2, col=1)

        # Layout Graphique
        fig.update_layout(
            height=650,
            template="plotly_dark",
            plot_bgcolor="#0A0A0A",
            paper_bgcolor="#000000",
            margin=dict(l=0, r=50, t=10, b=0),
            showlegend=False,
            xaxis_rangeslider_visible=False
        )
        # Axes Pro
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#1A1A1A')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#1A1A1A', side='right') # Prix à droite
        
        st.plotly_chart(fig, use_container_width=True)

    # --- COLONNE DROITE : NEWS TERMINAL ---
    with col_right:
        st.markdown("<div class='css-card'>", unsafe_allow_html=True)
        st.markdown("<h4 class='text-orange'>LIVE WIRE</h4>", unsafe_allow_html=True)
        
        if news:
            for item in news:
                title = item.title
                link = item.link
                # Hack pour raccourcir
                if len(title) > 60: title = title[:60] + "..."
                
                st.markdown(f"""
                <div style='margin-bottom: 12px; border-left: 2px solid #333; padding-left: 8px;'>
                    <a href='{link}' target='_blank' style='text-decoration: none; color: #CCC; font-size: 13px; hover: color: #FF9800;'>
                    {title}
                    </a>
                    <br><span style='color: #555; font-size: 10px;'>REUTERS • JUST NOW</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Connecting to wire...")
            
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Sim Order Book
        st.markdown("<div class='css-card'>", unsafe_allow_html=True)
        st.markdown("<h4 class='text-orange'>DEPTH (L2)</h4>", unsafe_allow_html=True)
        bid = current - 0.25
        ask = current + 0.25
        st.code(f"""
BID      |  ASK
---------+---------
{bid:.2f}  |  {ask:.2f}
{bid-0.5:.2f}  |  {ask+0.5:.2f}
{bid-1.0:.2f}  |  {ask+1.0:.2f}
        """)
        st.markdown("</div>", unsafe_allow_html=True)

else:
    st.error("DATA FEED DISCONNECTED. Market might be closed or API Limit reached.")
    st.button("RETRY CONNECTION")
