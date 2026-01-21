import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import feedparser
import numpy as np
from datetime import datetime, timedelta

# --- 1. CONFIGURATION STRICTE ---
st.set_page_config(
    layout="wide",
    page_title="BLOOMBERG TERMINAL",
    page_icon="💹",
    initial_sidebar_state="collapsed"
)

# --- 2. CSS "PIXEL PERFECT" BLOOMBERG ---
st.markdown("""
    <style>
    /* RESET TOTAL */
    .stApp {background-color: #000000 !important;}
    .block-container {padding: 0px 10px !important; max-width: 100% !important;}
    
    /* FONTS */
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;700&display=swap');
    * {font-family: 'Roboto Mono', 'Consolas', monospace !important; letter-spacing: -0.5px;}
    
    /* COULEURS TERMINAL */
    .neon-orange {color: #FF9800;}
    .neon-green {color: #00FF00;}
    .neon-red {color: #FF0000;}
    .text-gray {color: #666666;}
    .text-white {color: #E0E0E0;}
    
    /* TABLEAUX STYLE BLOOMBERG (CUSTOM HTML) */
    .bb-table {width: 100%; border-collapse: collapse; font-size: 11px;}
    .bb-table th {text-align: left; color: #FF9800; border-bottom: 1px solid #333; padding: 2px;}
    .bb-table td {color: #DDD; padding: 2px; border-bottom: 1px solid #111;}
    .bb-row:hover {background-color: #111;}
    
    /* CONTAINERS */
    .bb-box {
        border: 1px solid #333;
        background-color: #050505;
        padding: 5px;
        margin-bottom: 5px;
    }
    
    /* HIDE STREAMLIT UI */
    header, footer, #MainMenu {display: none !important;}
    div[data-testid="stDecoration"] {display: none;}
    </style>
""", unsafe_allow_html=True)

# --- 3. DATA ENGINE (ROBUSTE) ---

@st.cache_data(ttl=60)
def get_data_bundle():
    # Récupération groupée pour performance
    tickers = ["NQ=F", "QQQ", "^VIX", "^TNX", "BTC-USD", "GC=F", "NVDA", "AAPL", "MSFT", "TSLA"]
    try:
        data = yf.download(tickers, period="5d", interval="15m", group_by='ticker', progress=False)
        return data
    except:
        return None

def get_news_feed():
    try:
        # Flux Yahoo Finance (Plus stable)
        return feedparser.parse("https://finance.yahoo.com/news/rssindex").entries[:10]
    except:
        return []

# --- 4. LOGIQUE METIER & INDICATEURS ---

def process_nq_data(data):
    # Logique de fallback NQ -> QQQ
    if 'NQ=F' in data and not data['NQ=F']['Close'].dropna().empty:
        df = data['NQ=F'].dropna()
        name = "NQ=F (CME)"
    else:
        df = data['QQQ'].dropna()
        name = "QQQ (PROXY)"
    
    # Indicateurs
    df['SMA20'] = df['Close'].rolling(20).mean()
    df['Upper'] = df['SMA20'] + (2 * df['Close'].rolling(20).std())
    df['Lower'] = df['SMA20'] - (2 * df['Close'].rolling(20).std())
    
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    return df, name

# --- 5. COMPOSANTS UI (RENDERING) ---

def render_header(symbol, price, change, pct):
    color = "#00FF00" if change >= 0 else "#FF0000"
    st.markdown(f"""
    <div style='background-color:#111; border-bottom: 2px solid #FF9800; padding: 5px 10px; display: flex; justify-content: space-between; align-items: center;'>
        <div style='font-size: 14px;'>
            <span class='neon-orange'><b>1) SECURITY</b></span> <span class='text-gray'>|</span> 
            <span class='text-white'><b>{symbol}</b></span> <span class='text-gray'>[US FUTURES]</span>
        </div>
        <div style='text-align: right;'>
            <span style='font-size: 28px; font-weight: bold; color: {color};'>{price:,.2f}</span>
            <span style='font-size: 16px; margin-left: 10px; color: {color};'>{change:+.2f} ({pct:+.2f}%)</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_html_table(title, rows, col_names=["TICKER", "LAST", "CHG%"]):
    # Création d'un tableau HTML pur pour éviter le style Streamlit par défaut
    html = f"<div class='bb-box'><div style='color:#FF9800; font-weight:bold; font-size:10px; margin-bottom:4px; border-bottom:1px solid #333'>{title}</div>"
    html += "<table class='bb-table'>"
    html += "<thead><tr>" + "".join([f"<th>{c}</th>" for c in col_names]) + "</tr></thead><tbody>"
    
    for row in rows:
        c_val = "#00FF00" if row[2] >= 0 else "#FF0000"
        html += f"<tr class='bb-row'><td><b style='color:#DDD'>{row[0]}</b></td><td style='color:#DDD'>{row[1]}</td><td style='color:{c_val}'>{row[2]:+.2f}%</td></tr>"
    
    html += "</tbody></table></div>"
    st.markdown(html, unsafe_allow_html=True)

# --- 6. EXÉCUTION ---

raw_data = get_data_bundle()

if raw_data is not None:
    df_main, sym_name = process_nq_data(raw_data)
    
    # --- HEADER ---
    curr = df_main['Close'].iloc[-1]
    prev = df_main['Open'].iloc[0] # Open de la fenetre chargée
    chg = curr - prev
    pct = (chg / prev) * 100
    render_header(sym_name, curr, chg, pct)
    
    # --- LAYOUT GRID (20% - 60% - 20%) ---
    c1, c2, c3 = st.columns([1.2, 3.6, 1.2], gap="small")
    
    with c1:
        # MACRO DATA
        st.markdown("<div style='height:5px'></div>", unsafe_allow_html=True)
        macro_rows = []
        for t, label in [("^VIX", "VIX"), ("^TNX", "US10Y"), ("BTC-USD", "BTC"), ("GC=F", "GOLD")]:
            try:
                sub = raw_data[t].dropna()
                l = sub['Close'].iloc[-1]
                p = sub['Open'].iloc[-1] # Open du jour (approx 15m)
                c = ((l - p)/p)*100
                fmt = "{:,.0f}" if "BTC" in t else "{:.2f}"
                macro_rows.append([label, fmt.format(l), c])
            except: pass
        render_html_table("GLOBAL MARKETS", macro_rows)
        
        # MAG 7
        tech_rows = []
        for t in ["NVDA", "AAPL", "MSFT", "TSLA"]:
            try:
                sub = raw_data[t].dropna()
                l = sub['Close'].iloc[-1]
                p = sub['Open'].iloc[-1]
                c = ((l - p)/p)*100
                tech_rows.append([t, f"{l:.2f}", c])
            except: pass
        render_html_table("SECTOR: TECH", tech_rows)

        # KEY STATS
        st.markdown(f"""
        <div class='bb-box'>
            <div style='color:#FF9800; font-size:10px; font-weight:bold; border-bottom:1px solid #333'>KEY LEVELS</div>
            <div style='display:flex; justify-content:space-between; font-size:11px; margin-top:2px;'>
                <span class='text-gray'>HIGH</span> <span class='text-white'>{df_main['High'].max():,.2f}</span>
            </div>
            <div style='display:flex; justify-content:space-between; font-size:11px;'>
                <span class='text-gray'>LOW</span> <span class='text-white'>{df_main['Low'].min():,.2f}</span>
            </div>
            <div style='display:flex; justify-content:space-between; font-size:11px;'>
                <span class='text-gray'>VWAP</span> <span class='text-white'>{df_main['Close'].mean():,.2f}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        # --- CHARTING PRO ---
        # Note: rangebreaks hide weekends/hours to fix the "Triangles" issue
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.75, 0.25], vertical_spacing=0.01)
        
        # Candlestick
        fig.add_trace(go.Candlestick(
            x=df_main.index, open=df_main['Open'], high=df_main['High'], low=df_main['Low'], close=df_main['Close'],
            name="Price", increasing_line_color='#00FF00', decreasing_line_color='#FF0000', showlegend=False
        ), row=1, col=1)
        
        # Bollinger
        fig.add_trace(go.Scatter(x=df_main.index, y=df_main['Upper'], line=dict(color='gray', width=1, dash='dot'), showlegend=False), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_main.index, y=df_main['Lower'], line=dict(color='gray', width=1, dash='dot'), fill='tonexty', fillcolor='rgba(255,255,255,0.02)', showlegend=False), row=1, col=1)
        
        # Volume
        colors = ['#00FF00' if c >= o else '#FF0000' for c, o in zip(df_main['Close'], df_main['Open'])]
        fig.add_trace(go.Bar(x=df_main.index, y=df_main['Volume'], marker_color=colors, showlegend=False), row=2, col=1)
        
        # Configuration AXES pour éviter les trous (Rangebreaks)
        fig.update_xaxes(
            rangebreaks=[
                dict(bounds=["sat", "mon"]), # Cacher les week-ends
                dict(bounds=[20, 5], pattern="hour"), # Optionnel: focus session US (cache nuit)
            ],
            gridcolor='#222', showgrid=True
        )
        
        # Style Bloomberg Chart
        fig.update_layout(
            height=600,
            template="plotly_dark",
            paper_bgcolor="#000000",
            plot_bgcolor="#000000",
            margin=dict(l=0, r=50, t=10, b=0),
            xaxis_rangeslider_visible=False,
            hovermode="x unified"
        )
        fig.update_yaxes(side="right", gridcolor="#222", showgrid=True)
        
        st.plotly_chart(fig, use_container_width=True)

    with c3:
        # --- SENTIMENT & NEWS ---
        st.markdown("<div style='height:5px'></div>", unsafe_allow_html=True)
        
        # RSI WIDGET
        last_rsi = df_main['RSI'].iloc[-1]
        rsi_col = "#FF0000" if last_rsi > 70 else "#00FF00" if last_rsi < 30 else "#FF9800"
        st.markdown(f"""
        <div class='bb-box' style='text-align:center'>
            <div style='color:#666; font-size:10px; font-weight:bold'>MOMENTUM (RSI 14)</div>
            <div style='font-size:24px; font-weight:bold; color:{rsi_col}'>{last_rsi:.1f}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # NEWS WIRE
        st.markdown("<div class='bb-box'><div style='color:#FF9800; font-size:10px; font-weight:bold; border-bottom:1px solid #333; margin-bottom:5px'>NEWS WIRE</div>", unsafe_allow_html=True)
        news = get_news_feed()
        if news:
            for n in news[:8]:
                st.markdown(f"""
                <div style='margin-bottom:8px; border-bottom:1px solid #222; padding-bottom:4px;'>
                    <a href='{n.link}' target='_blank' style='color:#E0E0E0; text-decoration:none; font-size:11px; line-height:1.2; display:block; hover:color:#FF9800'>{n.title}</a>
                    <span style='color:#666; font-size:9px'>{n.published[17:22] if 'published' in n else ''}</span>
                </div>
                """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Footer Action
    if st.button(" CMD: REFRESH_TERMINAL ", type="secondary"):
        st.cache_data.clear()
        st.rerun()

else:
    st.error("SYSTEM OFFLINE: UNABLE TO CONNECT TO DATA GATEWAY.")
