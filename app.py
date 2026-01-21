import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import feedparser
import numpy as np
from datetime import datetime

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(
    layout="wide",
    page_title="SAM-NQ-VISION [STABLE]",
    page_icon="🦅",
    initial_sidebar_state="collapsed"
)

# --- 2. STYLE CSS (NOIR TOTAL) ---
st.markdown("""
    <style>
    .stApp {background-color: #000000;}
    .block-container {padding: 10px 15px !important; max-width: 100% !important;}
    * {font-family: 'Consolas', 'Monaco', monospace !important; font-size: 13px;}
    
    /* Couleurs Indicateurs */
    .up {color: #00FF00 !important;}
    .down {color: #FF0000 !important;}
    .neu {color: #FF9800 !important;}
    
    /* Cartes (Containers) */
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
    
    /* Métriques */
    div[data-testid="stMetricValue"] {font-size: 20px !important; color: #E0E0E0 !important;}
    div[data-testid="stMetricLabel"] {font-size: 10px !important; color: #666 !important;}
    
    /* Masquer éléments Streamlit inutiles */
    header, footer, #MainMenu {display: none !important;}
    </style>
""", unsafe_allow_html=True)

# --- 3. MOTEUR DE DONNÉES (ROBUSTE) ---

@st.cache_data(ttl=60)
def get_main_data():
    # Tentative NQ=F (Futures) puis fallback sur QQQ
    tickers = ["NQ=F", "QQQ"]
    try:
        # Téléchargement groupé
        data = yf.download(tickers, period="5d", interval="15m", progress=False, group_by='ticker')
        
        # Vérification si NQ=F contient des données valides
        if 'NQ=F' in data and not data['NQ=F']['Close'].dropna().empty:
            df = data['NQ=F']
            name = "NQ=F (FUTURES)"
        else:
            df = data['QQQ']
            name = "QQQ (PROXY)"
            
        return df, name
    except Exception as e:
        # En cas de panne totale Yahoo, on retourne un DataFrame vide
        return pd.DataFrame(), "OFFLINE"

@st.cache_data(ttl=300)
def get_macro_data():
    # Récupération en Daily (1d) pour éviter les trous (NaN) du VIX en intraday
    macro = {}
    assets = {
        "^VIX": "VIX (VOLATILITY)", 
        "^TNX": "US 10Y YIELD", 
        "BTC-USD": "BITCOIN", 
        "GC=F": "GOLD"
    }
    
    for ticker, label in assets.items():
        try:
            d = yf.Ticker(ticker).history(period="5d", interval="1d")
            if not d.empty and len(d) >= 2:
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
    # Données "Seven Magnificent"
    tickers = "NVDA MSFT AAPL AMZN GOOGL META TSLA"
    try:
        df = yf.download(tickers, period="2d", progress=False)['Close']
        res = {}
        if not df.empty and len(df) >= 2:
            for col in df.columns:
                curr = df[col].iloc[-1]
                prev = df[col].iloc[-2]
                pct = ((curr - prev) / prev) * 100
                res[col] = pct
        return res
    except:
        return {}

def get_yahoo_news():
    try:
        feed = feedparser.parse("https://finance.yahoo.com/news/rssindex")
        return feed.entries[:8]
    except:
        return []

# --- 4. CALCULS TECHNIQUES ---

def calculate_technicals(df):
    if df.empty: return pd.DataFrame()
    
    # On travaille sur une copie
    df = df.copy()
    
    # Bollinger Bands
    df['SMA20'] = df['Close'].rolling(20).mean()
    df['STD20'] = df['Close'].rolling(20).std()
    df['Upper'] = df['SMA20'] + (2 * df['STD20'])
    df['Lower'] = df['SMA20'] - (2 * df['STD20'])
    
    # RSI (14)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # CRITIQUE : On supprime les lignes avec NaN (début de l'historique)
    # C'est ce qui corrige le bug du "Triangle Marron" sur le graph
    return df.dropna()

# --- 5. INTERFACE UTILISATEUR (LAYOUT) ---

# Chargement
df_nq_raw, symbol_name = get_main_data()
df_final = calculate_technicals(df_nq_raw) # DataFrame propre pour le graph
macro_data = get_macro_data()
mag7_data = get_mag7_data()

# Layout : 3 Colonnes (Gauche, Centre, Droite)
c_left, c_center, c_right = st.columns([1.5, 4.5, 2])

# --- GAUCHE : MACRO & WATCHLIST ---
with c_left:
    st.markdown("<div class='bb-card'>", unsafe_allow_html=True)
    st.markdown("<div class='bb-header'>GLOBAL MACRO (DAILY)</div>", unsafe_allow_html=True)
    
    for label, (val, chg) in macro_data.items():
        color = "#0f0" if chg >= 0 else "#f00"
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

# --- CENTRE : GRAPHIQUE PRINCIPAL ---
with c_center:
    if not df_final.empty:
        # Header Graphique
        last_p = df_final['Close'].iloc[-1]
        
        # Calcul variation depuis l'open affiché
        start_p = df_final['Open'].iloc[0]
        diff = last_p - start_p
        diff_pct = (diff / start_p) * 100
        color_main = "#0f0" if diff >= 0 else "#f00"
        
        st.markdown(f"""
        <div style='border:1px solid #333; background:#0b0b0b; padding:10px; display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;'>
            <div>
                <span style='color:#FF9800; font-size:22px; font-weight:bold;'>{symbol_name}</span>
                <span style='color:#666; font-size:12px; margin-left:10px;'>REALTIME FEED</span>
            </div>
            <div style='text-align:right'>
                <span style='color:{color_main}; font-size:26px; font-weight:bold;'>{last_p:,.2f}</span>
                <span style='color:{color_main}; font-size:16px; margin-left:10px;'>{diff:+.2f} ({diff_pct:+.2f}%)</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Construction Graphique Plotly
        # C'est ici que tu avais l'erreur "NameError". La fonction make_subplots est bien importée ligne 4.
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.75, 0.25], vertical_spacing=0.02)
        
        # 1. Chandeliers (Prix)
        fig.add_trace(go.Candlestick(
            x=df_final.index, open=df_final['Open'], high=df_final['High'], low=df_final['Low'], close=df_final['Close'],
            name='Price', increasing_line_color='#00FF00', decreasing_line_color='#FF0000'
        ), row=1, col=1)
        
        # 2. Bandes de Bollinger (Zones Grises)
        if 'Upper' in df_final.columns:
            fig.add_trace(go.Scatter(x=df_final.index, y=df_final['Upper'], line=dict(color='gray', width=1), name='BB Up'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df_final.index, y=df_final['Lower'], line=dict(color='gray', width=1), fill='tonexty', fillcolor='rgba(255,255,255,0.05)', name='BB Low'), row=1, col=1)
        
        # 3. Volume
        colors_vol = ['#00FF00' if c >= o else '#FF0000' for c, o in zip(df_final['Close'], df_final['Open'])]
        fig.add_trace(go.Bar(x=df_final.index, y=df_final['Volume'], marker_color=colors_vol, name='Vol'), row=2, col=1)
        
        # Mise en page style Bloomberg
        fig.update_layout(
            height=600,
            template="plotly_dark",
            paper_bgcolor="#000",
            plot_bgcolor="#080808",
            margin=dict(l=0, r=50, t=0, b=0),
            showlegend=False,
            xaxis_rangeslider_visible=False
        )
        fig.update_yaxes(side="right", gridcolor="#222") # Prix à droite
        fig.update_xaxes(gridcolor="#222")
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("DATA FEED DISCONNECTED. PLEASE CLICK 'UPDATE DATA'.")

# --- DROITE : SENTIMENT & NEWS ---
with c_right:
    if not df_final.empty:
        # RSI Display
        rsi_val = df_final['RSI'].iloc[-1]
        lbl_rsi = "OVERBOUGHT" if rsi_val > 70 else "OVERSOLD" if rsi_val < 30 else "NEUTRAL"
        col_rsi = "#f00" if rsi_val > 70 else "#0f0" if rsi_val < 30 else "#FF9800"
        
        st.markdown("<div class='bb-card'>", unsafe_allow_html=True)
        st.markdown("<div class='bb-header'>TECHNICAL SENTIMENT</div>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style='text-align:center'>
            <div style='font-size:24px; font-weight:bold; color:{col_rsi}'>{lbl_rsi}</div>
            <div style='font-size:12px; color:#888'>RSI (14): {rsi_val:.1f}</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # News Section
    st.markdown("<div class='bb-card'>", unsafe_allow_html=True)
    st.markdown("<div class='bb-header'>LIVE NEWS (YAHOO)</div>", unsafe_allow_html=True)
    
    news = get_yahoo_news()
    if news:
        for n in news[:7]:
            st.markdown(f"""
            <div style='border-bottom:1px solid #222; padding-bottom:6px; margin-bottom:6px;'>
                <a href='{n.link}' target='_blank' style='color:#ccc; text-decoration:none; font-size:11px; display:block; line-height:1.2;'>{n.title}</a>
                <span style='color:#555; font-size:9px'>{n.published[17:22] if 'published' in n else ''}</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.write("News feed unavailable.")
    st.markdown("</div>", unsafe_allow_html=True)

# Footer Refresh Button
if st.button("UPDATE DATA"):
    st.cache_data.clear()
    st.rerun()
