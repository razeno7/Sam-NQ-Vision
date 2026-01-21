import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import feedparser
import numpy as np
from datetime import datetime

# --- 1. SETUP INSTITUTIONNEL ---
st.set_page_config(
    layout="wide",
    page_title="SAM-NQ-VISION [V2]",
    page_icon="🦅",
    initial_sidebar_state="collapsed"
)

# --- 2. CSS "BLOOMBERG TERMINAL" (NOIR & AMBRE) ---
st.markdown("""
    <style>
    .stApp {background-color: #000000;}
    .block-container {padding: 10px 15px !important; max-width: 100% !important;}
    * {font-family: 'Consolas', 'Monaco', monospace !important; font-size: 13px;}
    
    /* Couleurs */
    .up {color: #00FF00 !important;}
    .down {color: #FF0000 !important;}
    .neu {color: #FF9800 !important;}
    
    /* Cards */
    .bb-card {
        background-color: #0b0b0b;
        border: 1px solid #333;
        padding: 10px;
        margin-bottom: 10px;
    }
    .bb-header {
        border-bottom: 1px solid #333;
        color: #FF9800;
        font-weight: bold;
        font-size: 11px;
        margin-bottom: 8px;
        text-transform: uppercase;
    }
    
    /* Metrics override */
    div[data-testid="stMetricValue"] {font-size: 20px !important; color: #E0E0E0 !important;}
    div[data-testid="stMetricLabel"] {font-size: 10px !important; color: #666 !important;}
    
    /* Hide Streamlit elements */
    header, footer, #MainMenu {display: none !important;}
    </style>
""", unsafe_allow_html=True)

# --- 3. DATA ENGINE (ROBUSTE) ---

@st.cache_data(ttl=60)
def get_main_data():
    # 1. NQ Futures (Intraday)
    # Si NQ=F échoue (souvent le cas), fallback sur QQQ
    tickers = ["NQ=F", "QQQ"]
    data = yf.download(tickers, period="5d", interval="15m", progress=False, group_by='ticker')
    
    # Vérification : Est-ce que NQ=F a des données ?
    try:
        df = data['NQ=F']
        if df['Close'].dropna().empty:
            raise ValueError("Empty NQ")
        name = "NQ=F (FUTURES)"
    except:
        df = data['QQQ']
        name = "QQQ (PROXY)"
    
    # Nettoyage des NaNs pour éviter le bug graphique "Triangle"
    df = df.dropna()
    return df, name

@st.cache_data(ttl=300)
def get_macro_data():
    # On récupère VIX et TNX en '1d' car '15m' est souvent bloqué par Yahoo
    macro = {}
    
    # Liste : Ticker Yahoo -> Nom Affiché
    assets = {
        "^VIX": "VIX (VOLATILITY)", 
        "^TNX": "US 10Y YIELD", 
        "BTC-USD": "BITCOIN", 
        "GC=F": "GOLD"
    }
    
    for ticker, label in assets.items():
        try:
            # Période plus longue, intervalle daily pour stabilité
            d = yf.Ticker(ticker).history(period="5d", interval="1d")
            if not d.empty:
                last = d['Close'].iloc[-1]
                prev = d['Close'].iloc[-2]
                chg = ((last - prev) / prev) * 100
                macro[label] = (last, chg)
            else:
                macro[label] = (0.0, 0.0)
        except:
            macro[label] = (0.0, 0.0)
            
    return macro

@st.cache_data(ttl=60)
def get_mag7_data():
    # Vraies données pour les 7 magnifiques
    tickers = "NVDA MSFT AAPL AMZN GOOGL META TSLA"
    try:
        df = yf.download(tickers, period="2d", progress=False)['Close']
        # Calcul variation jour
        res = {}
        for col in df.columns:
            curr = df[col].iloc[-1]
            prev = df[col].iloc[-2]
            pct = ((curr - prev) / prev) * 100
            res[col] = pct
        return res
    except:
        return {}

def get_yahoo_news():
    # Flux RSS Yahoo Finance (Plus fiable que Reuters)
    try:
        feed = feedparser.parse("https://finance.yahoo.com/news/rssindex")
        return feed.entries[:8]
    except:
        return []

# --- 4. ALGO & CALCULS ---

def calculate_technicals(df):
    if df.empty: return None
    df = df.copy()
    
    # Bollinger
    df['SMA20'] = df['Close'].rolling(20).mean()
    df['STD20'] = df['Close'].rolling(20).std()
    df['Upper'] = df['SMA20'] + (2 * df['STD20'])
    df['Lower'] = df['SMA20'] - (2 * df['STD20'])
    
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    return df

# --- 5. UI LAYOUT ---

# Chargement données
df_nq, symbol_name = get_main_data()
df_tech = calculate_technicals(df_nq)
macro_data = get_macro_data()
mag7_data = get_mag7_data()

# Layout Grid
c_left, c_center, c_right = st.columns([1.5, 4.5, 2])

# --- GAUCHE : MACRO & MAG 7 ---
with c_left:
    st.markdown("<div class='bb-card'>", unsafe_allow_html=True)
    st.markdown("<div class='bb-header'>GLOBAL MACRO</div>", unsafe_allow_html=True)
    
    for label, (val, chg) in macro_data.items():
        color = "#0f0" if chg >= 0 else "#f00"
        # Gestion affichage format (Bitoin sans décimale, Taux avec 2)
        fmt = "{:,.0f}" if "BITCOIN" in label else "{:.2f}"
        
        st.markdown(f"""
        <div style='display:flex; justify-content:space-between; margin-bottom:6px; font-size:12px;'>
            <span style='color:#888'>{label}</span>
            <div style='text-align:right'>
                <span style='color:#eee; font-weight:bold'>{fmt.format(val)}</span><br>
                <span style='color:{color}; font-size:10px'>{chg:+.2f}%</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='bb-card'>", unsafe_allow_html=True)
    st.markdown("<div class='bb-header'>MAG-7 WATCH</div>", unsafe_allow_html=True)
    
    if mag7_data:
        for ticker, pct in mag7_data.items():
            color = "#0f0" if pct >= 0 else "#f00"
            st.markdown(f"""
            <div style='display:flex; justify-content:space-between; font-size:11px; margin-bottom:4px;'>
                <span style='color:#ccc'>{ticker}</span>
                <span style='color:{color}'>{pct:+.2f}%</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.write("Loading...")
    st.markdown("</div>", unsafe_allow_html=True)

# --- CENTRE : GRAPHIQUE ---
with c_center:
    # Header
    last_p = df_nq['Close'].iloc[-1]
    prev_p = df_nq['Open'].iloc[0] # Open du début de fenêtre
    diff = last_p - prev_p
    diff_pct = (diff / prev_p) * 100
    color_main = "#0f0" if diff >= 0 else "#f00"
    
    st.markdown(f"""
    <div style='border:1px solid #333; background:#0b0b0b; padding:10px; display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;'>
        <div>
            <span style='color:#FF9800; font-size:22px; font-weight:bold;'>{symbol_name}</span>
            <span style='color:#666; font-size:12px; margin-left:10px;'>REALTIME</span>
        </div>
        <div style='text-align:right'>
            <span style='color:{color_main}; font-size:26px; font-weight:bold;'>{last_p:,.2f}</span>
            <span style='color:{color_main}; font-size:16px; margin-left:10px;'>{diff:+.2f} ({diff_pct:+.2f}%)</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Graphique
    fig = make_
