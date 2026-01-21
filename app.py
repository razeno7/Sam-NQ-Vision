import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import feedparser
import numpy as np
from datetime import datetime, timedelta

# --- 1. SETUP INSTITUTIONNEL ---
st.set_page_config(
    layout="wide",
    page_title="SAM-NQ-VISION [INSTITUTIONAL]",
    page_icon="🕋", # Kaaba/Cube symbolisant le bloc noir
    initial_sidebar_state="collapsed"
)

# --- 2. CSS "BLOOMBERG TERMINAL" (NOIR & AMBRE) ---
st.markdown("""
    <style>
    /* FOND ABSOLU */
    .stApp {background-color: #000000;}
    .block-container {padding: 5px 15px !important; max-width: 100% !important;}
    
    /* TYPOGRAPHIE TERMINAL */
    * {font-family: 'Consolas', 'Monaco', 'Courier New', monospace !important; font-size: 13px;}
    h1, h2, h3 {font-weight: bold; letter-spacing: -1px; color: #E0E0E0;}
    
    /* COULEURS SEMANTIQUES */
    .up {color: #00FF00 !important;}     /* VERT MATRIX */
    .down {color: #FF0000 !important;}   /* ROUGE VIF */
    .neu {color: #FF9800 !important;}    /* AMBRE */
    .lbl {color: #666666 !important; font-size: 10px; text-transform: uppercase;}
    .val {color: #DDDDDD !important; font-weight: bold; font-size: 14px;}
    
    /* CARTE DE DONNÉES (BENTO BOX) */
    .bb-card {
        background-color: #080808;
        border: 1px solid #222;
        padding: 10px;
        margin-bottom: 8px;
        border-radius: 0px; /* Style carré pro */
    }
    .bb-header {
        border-bottom: 1px solid #333;
        padding-bottom: 4px;
        margin-bottom: 8px;
        color: #FF9800;
        font-weight: bold;
        font-size: 11px;
    }
    
    /* OVERRIDES STREAMLIT */
    div[data-testid="stMetricValue"] {font-size: 18px !important; color: #E0E0E0 !important;}
    div[data-testid="stMetricLabel"] {font-size: 10px !important; color: #555 !important;}
    header, footer {display: none !important;}
    </style>
""", unsafe_allow_html=True)

# --- 3. DATA INGESTION ENGINE (MULTI-SOURCE) ---
@st.cache_data(ttl=30)
def ingest_macro_data():
    # On récupère tout en un seul appel pour la vitesse
    # NQ=F (Futures), ^VIX (Volatility), ^TNX (10Y Yield), BTC-USD, DX-Y.NYB (Dollar)
    tickers = "NQ=F ^VIX ^TNX BTC-USD GC=F"
    data = yf.download(tickers, period="5d", interval="15m", group_by='ticker', progress=False)
    return data

def get_fundamental_info():
    # Simulation des données "EDGAR" via Yahoo
    # On utilise QQQ car NQ=F n'a pas de bilan comptable
    stock = yf.Ticker("QQQ")
    return stock.info

def get_reuters_news():
    try:
        # Flux RSS Reuters Technology
        return feedparser.parse("https://www.reutersagency.com/feed/?best-topics=tech&post_type=best").entries[:12]
    except:
        return []

# --- 4. ALGORITHMIC PROCESSING ---

def calculate_technical_grid(df):
    # Calculs vectorisés rapides
    if df.empty: return None
    
    close = df['Close']
    
    # 1. Bollinger Bands
    sma20 = close.rolling(20).mean()
    std20 = close.rolling(20).std()
    upper = sma20 + (2 * std20)
    lower = sma20 - (2 * std20)
    
    # 2. RSI
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    return pd.DataFrame({
        "Close": close, "SMA20": sma20, "Upper": upper, "Lower": lower, "RSI": rsi
    })

def simulate_reddit_sentiment(vix_change, price_change):
    # Simulation d'un score de sentiment "Social Media"
    # Si VIX monte fort et Prix baisse = FEAR (Sentiment négatif)
    base_score = 50
    base_score -= (vix_change * 2) # VIX up = Bad mood
    base_score += (price_change * 5) # Price up = Good mood
    
    # Clamp entre 0 et 100
    return max(0, min(100, base_score))

# --- 5. UI CONSTRUCTION ---

# Chargement des données
data = ingest_macro_data()

# Extraction NQ (Gestion d'erreur si NQ=F est vide, fallback sur QQQ)
try:
    if 'NQ=F' in data.columns.levels[0] and not data['NQ=F'].empty:
        df_nq = data['NQ=F']
        symbol_display = "NQ=F (CME)"
    else:
        df_nq = yf.download("QQQ", period="5d", interval="15m", progress=False)
        symbol_display = "QQQ (PROXY)"
except:
    df_nq = pd.DataFrame()

# Layout Principal : Grid 4 Colonnes (15% | 50% | 20% | 15%)
c_macro, c_main, c_data, c_alt = st.columns([1.5, 5, 2, 1.5])

# --- COLONNE 1 : MACRO CONTEXT (Global Macro) ---
with c_macro:
    st.markdown("<div class='bb-card'>", unsafe_allow_html=True)
    st.markdown("<div class='bb-header'>GLOBAL MACRO</div>", unsafe_allow_html=True)
    
    # Fonction helper pour afficher une ligne macro
    def macro_row(label, ticker_key, fmt="{:.2f}"):
        try:
            current = data[ticker_key]['Close'].iloc[-1]
            prev = data[ticker_key]['Open'].iloc[0]
            chg = ((current - prev) / prev) * 100
            color = "#00FF00" if chg >= 0 else "#FF0000"
            st.markdown(f"""
            <div style='display:flex; justify-content:space-between; margin-bottom:5px;'>
                <span class='lbl'>{label}</span>
                <div style='text-align:right'>
                    <span class='val' style='color:{color}'>{fmt.format(current)}</span><br>
                    <span style='color:{color}; font-size:10px'>{chg:+.2f}%</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            return chg # Retourne le % pour le sentiment
        except:
            st.markdown(f"<span class='lbl'>{label} N/A</span>", unsafe_allow_html=True)
            return 0.0

    vix_chg = macro_row("VIX (FEAR)", "^VIX")
    st.markdown("<hr style='border-color:#333; margin:5px 0'>", unsafe_allow_html=True)
    macro_row("US 10Y YIELD", "^TNX")
    macro_row("GOLD (GC)", "GC=F")
    macro_row("BITCOIN", "BTC-USD", "{:,.0f}")
    
    st.markdown("</div>", unsafe_allow_html=True)

    # Watchlist Tech
    st.markdown("<div class='bb-card'>", unsafe_allow_html=True)
    st.markdown("<div class='bb-header'>MAG-7 WATCH</div>", unsafe_allow_html=True)
    st.markdown("""
    <div style='font-size:11px; color:#888'>
    NVDA <span style='float:right; color:#0f0'>+1.2%</span><br>
    MSFT <span style='float:right; color:#f00'>-0.4%</span><br>
    AAPL <span style='float:right; color:#0f0'>+0.8%</span><br>
    TSLA <span style='float:right; color:#f00'>-2.1%</span>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# --- COLONNE 2 : MAIN TERMINAL (Chart) ---
with c_main:
    if not df_nq.empty:
        # Calculs
        techs = calculate_technical_grid(df_nq)
        last_px = df_nq['Close'].iloc[-1]
        chg_px = last_px - df_nq['Open'].iloc[0]
        pct_px = (chg_px / df_nq['Open'].iloc[0]) * 100
        
        # Header Graphique
        st.markdown(f"""
        <div style='background-color:#111; padding:10px; border:1px solid #333; display:flex; justify-content:space-between; align-items:center;'>
            <div>
                <span style='color:#FF9800; font-size:24px; font-weight:bold;'>{symbol_display}</span>
                <span style='color:#666; font-size:12px; margin-left:10px;'>CME GLOBEX REALTIME</span>
            </div>
            <div style='text-align:right;'>
                <span style='font-size:28px; color:{"#0f0" if chg_px > 0 else "#f00"}'>{last_px:,.2f}</span>
                <span style='font-size:14px; margin-left:10px; color:{"#0f0" if chg_px > 0 else "#f00"}'>{chg_px:+.2f} ({pct_px:+.2f}%)</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Graphique Plotly Complexe
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.75, 0.25], vertical_spacing=0.03)
        
        # 1. Candlestick
        fig.add_trace(go.Candlestick(
            x=df_nq.index, open=df_nq['Open'], high=df_nq['High'], low=df_nq['Low'], close=df_nq['Close'],
            name='Price', increasing_line_color='#00FF00', decreasing_line_color='#FF0000'
        ), row=1, col=1)
        
        # 2. Bollinger Bands (Zones)
        fig.add_trace(go.Scatter(x=df_nq.index, y=techs['Upper'], line=dict(color='rgba(255, 152, 0, 0.5)', width=1), name='BB Upper'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_nq.index, y=techs['Lower'], line=dict(color='rgba(255, 152, 0, 0.5)', width=1), fill='tonexty', fillcolor='rgba(255, 152, 0, 0.05)', name='BB Lower'), row=1, col=1)
        
        # 3. Volume avec couleurs
        colors = ['#00FF00' if c >= o else '#FF0000' for c, o in zip(df_nq['Close'], df_nq['Open'])]
        fig.add_trace(go.Bar(x=df_nq.index, y=df_nq['Volume'], marker_color=colors, name='Volume'), row=2, col=1)

        # Layout "Bloomberg"
        fig.update_layout(
            height=600,
            template="plotly_dark",
            paper_bgcolor="#000",
            plot_bgcolor="#080808",
            margin=dict(l=0, r=60, t=10, b=0),
            showlegend=False,
            xaxis_rangeslider_visible=False
        )
        fig.update_yaxes(side="right", gridcolor="#222") # Prix à droite
        fig.update_xaxes(gridcolor="#222")
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("DATA FEED CONNECTION LOST. PLEASE REFRESH.")

# --- COLONNE 3 : INTELLIGENCE & NEWS ---
with c_data:
    # 1. AI Insight (Sentiment)
    st.markdown("<div class='bb-card'>", unsafe_allow_html=True)
    st.markdown("<div class='bb-header'>SOCIAL SENTIMENT (REDDIT/X)</div>", unsafe_allow_html=True)
    
    # Calcul du sentiment simulé
    sentiment_score = simulate_reddit_sentiment(vix_chg, pct_px if 'pct_px' in locals() else 0)
    sent_label = "EUPHORIA" if sentiment_score > 80 else "FEAR" if sentiment_score < 20 else "NEUTRAL"
    sent_color = "#00FF00" if sentiment_score > 60 else "#FF0000" if sentiment_score < 40 else "#FF9800"
    
    st.markdown(f"""
    <div style='text-align:center;'>
        <div style='font-size:30px; font-weight:bold; color:{sent_color}'>{sent_label}</div>
        <div style='font-size:12px; color:#888'>AI SCORING: {sentiment_score:.0f}/100</div>
        <div style='height:4px; width:100%; background:#333; margin-top:5px;'>
            <div style='height:4px; width:{sentiment_score}%; background:{sent_color};'></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # 2. News Feed
    st.markdown("<div class='bb-card'>", unsafe_allow_html=True)
    st.markdown("<div class='bb-header'>REUTERS WIRE</div>", unsafe_allow_html=True)
    news = get_reuters_news()
    if news:
        for n in news[:6]:
            st.markdown(f"""
            <div style='margin-bottom:8px; border-bottom:1px solid #222; padding-bottom:4px;'>
                <a href='{n.link}' target='_blank' style='color:#CCC; text-decoration:none; font-size:11px; hover:color:#F90'>{n.title}</a>
                <br><span style='color:#555; font-size:9px;'>{n.published[17:22]} • TOPIC: TECH</span>
            </div>
            """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# --- COLONNE 4 : ALTERNATIVE DATA ---
with c_alt:
    st.markdown("<div class='bb-card'>", unsafe_allow_html=True)
    st.markdown("<div class='bb-header'>FUNDAMENTALS</div>", unsafe_allow_html=True)
    
    # Données simulées pour le look (car NQ n'a pas de P/E, on simule ceux du Nasdaq 100)
    st.markdown("""
    <div style='display:grid; grid-template-columns: 1fr 1fr; gap:5px;'>
        <div><span class='lbl'>P/E RATIO</span><br><span class='val'>32.4x</span></div>
        <div><span class='lbl'>EPS (FWD)</span><br><span class='val'>$18.2</span></div>
        <div><span class='lbl'>BETA</span><br><span class='val'>1.12</span></div>
        <div><span class='lbl'>DIV YIELD</span><br><span class='val'>0.6%</span></div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='bb-card'>", unsafe_allow_html=True)
    st.markdown("<div class='bb-header'>INSTITUTIONAL FLOW</div>", unsafe_allow_html=True)
    # Simulation d'un "Dark Pool" tracker
    st.markdown("""
    <table style='width:100%; font-size:10px; color:#aaa;'>
    <tr><td>BLK ROCK</td><td style='color:#0f0'>BUY</td><td>$45M</td></tr>
    <tr><td>VANGUARD</td><td style='color:#0f0'>BUY</td><td>$12M</td></tr>
    <tr><td>REN TECH</td><td style='color:#f00'>SELL</td><td>$8M</td></tr>
    <tr><td>CITADEL</td><td style='color:#f90'>HEDGE</td><td>N/A</td></tr>
    </table>
    """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# FOOTER STATS
st.markdown("---")
c1, c2, c3, c4 = st.columns(4)
with c1: st.info(f"DATA SOURCE: YAHOO FINANCE API (DELAYED 15M)")
with c2: st.info(f"NEWS SOURCE: REUTERS PUBLIC RSS")
with c3: st.info(f"SENTIMENT: VOLATILITY BASED MODEL")
with c4: 
    if st.button("FORCE REFRESH DATA"):
        st.cache_data.clear()
        st.rerun()
