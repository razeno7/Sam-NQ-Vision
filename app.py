import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import feedparser
from textblob import TextBlob # Pour l'analyse de sentiment NLP
from datetime import datetime, timedelta

# --- 1. CONFIGURATION DU TERMINAL ---
st.set_page_config(
    layout="wide",
    page_title="NQ SAM VISION [QUANT]",
    page_icon="🦅",
    initial_sidebar_state="collapsed"
)

# --- 2. CSS CUSTOM "BLOOMBERG QUANT" ---
st.markdown("""
    <style>
    /* FOND NOIR ABSOLU */
    .stApp {background-color: #050505;}
    
    /* TYPO TERMINAL */
    * {font-family: 'Consolas', 'Courier New', monospace !important; font-size: 12px;}
    
    /* SUPPRESSION MARGES */
    .block-container {padding-top: 0px !important; padding-left: 10px !important; padding-right: 10px !important;}
    header, footer {display: none !important;}
    
    /* COULEURS SEMANTIQUES */
    .bull {color: #00FF00; font-weight: bold;}
    .bear {color: #FF0000; font-weight: bold;}
    .neutral {color: #FF9800; font-weight: bold;}
    
    /* PANELS */
    .quant-panel {
        background: #0e0e0e;
        border: 1px solid #333;
        padding: 10px;
        margin-bottom: 5px;
    }
    .panel-header {
        border-bottom: 1px solid #333;
        color: #FF9800;
        font-size: 11px;
        text-transform: uppercase;
        margin-bottom: 8px;
        letter-spacing: 1px;
    }
    
    /* TABLES CUSTOM */
    table {width: 100%; border-collapse: collapse;}
    td, th {border-bottom: 1px solid #222; padding: 4px; color: #ddd;}
    th {text-align: left; color: #666;}
    </style>
""", unsafe_allow_html=True)

# --- 3. MOTEUR D'ANALYSE (PYTHON BACKEND) ---

@st.cache_data(ttl=60)
def fetch_market_data():
    # Récupération NQ + Macro
    # Utilisation de QQQ comme proxy fiable si NQ=F (Futures) est bloqué par Yahoo
    tickers = ["NQ=F", "QQQ", "^VIX", "BTC-USD", "^TNX"]
    data = yf.download(tickers, period="5d", interval="15m", group_by='ticker', progress=False)
    return data

def process_sentiment_nlp():
    # C'EST ICI QUE L'IA ANALYSE LE TEXTE
    # On récupère les news RSS
    rss_urls = [
        "https://finance.yahoo.com/news/rssindex",
        "http://feeds.marketwatch.com/marketwatch/topstories/"
    ]
    
    news_items = []
    total_polarity = 0
    count = 0
    
    for url in rss_urls:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:5]:
                # Analyse de sentiment avec TextBlob
                analysis = TextBlob(entry.title)
                polarity = analysis.sentiment.polarity # Score entre -1 (Neg) et +1 (Pos)
                
                # Classification
                if polarity > 0.1: sent = "BULL"
                elif polarity < -0.1: sent = "BEAR"
                else: sent = "NEUT"
                
                news_items.append({
                    "title": entry.title,
                    "link": entry.link,
                    "time": entry.published[17:22] if 'published' in entry else "LIVE",
                    "score": polarity,
                    "label": sent
                })
                total_polarity += polarity
                count += 1
        except: continue
        
    # Score global du marché (-100 à +100)
    avg_score = (total_polarity / count) * 100 if count > 0 else 0
    return news_items, avg_score

def calculate_quant_indicators(df):
    if df.empty: return df
    
    # 1. VWAP (Volume Weighted Average Price)
    df['VWAP'] = (df['Volume'] * (df['High'] + df['Low'] + df['Close']) / 3).cumsum() / df['Volume'].cumsum()
    
    # 2. Bandes de Bollinger (2 Std Dev)
    df['SMA20'] = df['Close'].rolling(window=20).mean()
    df['STD20'] = df['Close'].rolling(window=20).std()
    df['Upper'] = df['SMA20'] + (2 * df['STD20'])
    df['Lower'] = df['SMA20'] - (2 * df['STD20'])
    
    # 3. RSI (Relative Strength Index)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    return df

# --- 4. DATA LOADING & PROCESSING ---

raw_data = fetch_market_data()
news_data, sentiment_score = process_sentiment_nlp()

# Sélection Intelligente NQ vs QQQ
if 'NQ=F' in raw_data and not raw_data['NQ=F']['Close'].dropna().empty:
    main_df = raw_data['NQ=F'].dropna()
    symbol_display = "NQ=F (FUTURES)"
else:
    main_df = raw_data['QQQ'].dropna()
    symbol_display = "QQQ (PROXY)"

# Calcul des indicateurs par notre moteur Python
df_tech = calculate_quant_indicators(main_df)
current = df_tech.iloc[-1]
prev = df_tech.iloc[-2]

# --- 5. INTERFACE DASHBOARD ---

# HEADER
col_h1, col_h2, col_h3 = st.columns([2, 1, 1])
chg = current['Close'] - prev['Close']
pct = (chg / prev['Close']) * 100
color_h = "#00FF00" if chg >= 0 else "#FF0000"

with col_h1:
    st.markdown(f"""
    <div style='font-size: 24px; color: #FF9800; font-weight: bold;'>{symbol_display}</div>
    <div style='font-size: 12px; color: #666;'>NQ SAM VISION // REALTIME QUANT ENGINE</div>
    """, unsafe_allow_html=True)

with col_h2:
    st.markdown(f"""
    <div style='text-align:right'>
        <div style='font-size: 32px; color: {color_h}; font-weight: bold;'>{current['Close']:,.2f}</div>
        <div style='font-size: 14px; color: {color_h};'>{chg:+.2f} ({pct:+.2f}%)</div>
    </div>
    """, unsafe_allow_html=True)

with col_h3:
    # Jauge de sentiment NLP
    sent_col = "#00FF00" if sentiment_score > 5 else "#FF0000" if sentiment_score < -5 else "#FF9800"
    st.markdown(f"""
    <div style='background:#111; border:1px solid #333; padding:5px; text-align:center'>
        <div style='color:#666; font-size:10px'>NEWS SENTIMENT (NLP)</div>
        <div style='font-size:20px; font-weight:bold; color:{sent_col}'>{sentiment_score:.1f}</div>
        <div style='font-size:10px; color:#aaa'>SCORE AI</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# MAIN GRID
c_left, c_main, c_right = st.columns([1, 3, 1])

# --- GAUCHE : DONNÉES MACRO ---
with c_left:
    st.markdown('<div class="quant-panel"><div class="panel-header">MACRO CONTEXT</div>', unsafe_allow_html=True)
    
    # Extraction Macro
    try:
        vix = raw_data['^VIX']['Close'].iloc[-1]
        tnx = raw_data['^TNX']['Close'].iloc[-1]
        btc = raw_data['BTC-USD']['Close'].iloc[-1]
        
        st.markdown(f"""
        <table>
            <tr><td>VIX (FEAR)</td><td style='color:{"#f00" if vix > 20 else "#0f0"}; text-align:right'>{vix:.2f}</td></tr>
            <tr><td>US 10Y</td><td style='color:#ddd; text-align:right'>{tnx:.3f}%</td></tr>
            <tr><td>BITCOIN</td><td style='color:#FF9800; text-align:right'>${btc:,.0f}</td></tr>
        </table>
        """, unsafe_allow_html=True)
    except:
        st.write("Macro Data Loading...")
    st.markdown('</div>', unsafe_allow_html=True)

    # Données Techniques
    st.markdown('<div class="quant-panel"><div class="panel-header">TECHNICALS</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <table>
        <tr><td>RSI (14)</td><td style='text-align:right; color:{"#f00" if current['RSI']>70 else "#0f0" if current['RSI']<30 else "#fff"}'>{current['RSI']:.1f}</td></tr>
        <tr><td>VWAP</td><td style='text-align:right; color:#FF9800'>{current['VWAP']:,.2f}</td></tr>
        <tr><td>VOLATILITY</td><td style='text-align:right'>{(current['Upper']-current['Lower']):.2f}</td></tr>
    </table>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- CENTRE : GRAPHIQUE PYTHON (PLOTLY) ---
with c_main:
    st.markdown('<div class="quant-panel">', unsafe_allow_html=True)
    
    # Construction du graphique complexe
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.75, 0.25], vertical_spacing=0.02)
    
    # 1. Candlestick
    fig.add_trace(go.Candlestick(
        x=df_tech.index, open=df_tech['Open'], high=df_tech['High'], low=df_tech['Low'], close=df_tech['Close'],
        name='Price', increasing_line_color='#00FF00', decreasing_line_color='#FF0000'
    ), row=1, col=1)
    
    # 2. VWAP & Bollinger
    fig.add_trace(go.Scatter(x=df_tech.index, y=df_tech['VWAP'], line=dict(color='#FF9800', width=1, dash='dot'), name='VWAP'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df_tech.index, y=df_tech['Upper'], line=dict(color='#333', width=1), name='BB Up'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df_tech.index, y=df_tech['Lower'], line=dict(color='#333', width=1), fill='tonexty', fillcolor='rgba(255,255,255,0.05)', name='BB Low'), row=1, col=1)
    
    # 3. Volume
    colors_vol = ['#00FF00' if c >= o else '#FF0000' for c, o in zip(df_tech['Close'], df_tech['Open'])]
    fig.add_trace(go.Bar(x=df_tech.index, y=df_tech['Volume'], marker_color=colors_vol, name='Vol'), row=2, col=1)
    
    # Layout Pro
    fig.update_layout(
        height=550,
        margin=dict(l=0, r=50, t=10, b=0),
        template="plotly_dark",
        paper_bgcolor='#0e0e0e',
        plot_bgcolor='#0e0e0e',
        showlegend=False,
        xaxis_rangeslider_visible=False
    )
    # Hiding weekends (Gap removal)
    fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])], gridcolor='#222')
    fig.update_yaxes(side='right', gridcolor='#222')
    
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- DROITE : NEWS NLP & AI ---
with c_right:
    st.markdown('<div class="quant-panel"><div class="panel-header">AI NEWS ANALYSIS</div>', unsafe_allow_html=True)
    
    for item in news_data:
        # Code couleur selon l'analyse de sentiment
        s_color = "#00FF00" if item['label'] == "BULL" else "#FF0000" if item['label'] == "BEAR" else "#888"
        
        st.markdown(f"""
        <div style='border-bottom:1px solid #222; padding:8px 0;'>
            <div style='font-size:10px; color:#FF9800; display:flex; justify-content:space-between;'>
                <span>{item['time']}</span>
                <span style='color:{s_color}; font-weight
