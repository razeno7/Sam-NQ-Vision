import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import feedparser
from datetime import datetime, timedelta

# --- 1. SETUP PAGE (WIDE MODE) ---
st.set_page_config(
    layout="wide",
    page_title="BLOOMBERG NQ",
    page_icon="terminal",
    initial_sidebar_state="collapsed"
)

# --- 2. CSS "INSTITUTIONAL" (STYLE STRICT) ---
st.markdown("""
    <style>
    /* RESET TOTAL */
    .stApp {background-color: #000000;}
    .block-container {padding: 0px 5px !important; margin: 0px !important; max-width: 100% !important;}
    header, footer {display: none !important;}
    
    /* TYPOGRAPHIE TERMINAL */
    * {font-family: 'Consolas', 'Menlo', 'Deja Vu Sans Mono', monospace !important; font-size: 11px; letter-spacing: -0.5px;}
    
    /* COULEURS */
    .amber {color: #FF9800;}
    .green {color: #00FF00;}
    .red {color: #FF0000;}
    .white {color: #E0E0E0;}
    .dim {color: #666;}
    
    /* PANELS (BENTO BOX) */
    .panel {
        border: 1px solid #333;
        background: #0a0a0a;
        margin-bottom: 2px;
        height: 100%;
        overflow: hidden;
    }
    .panel-header {
        background: #1a1a1a;
        color: #FF9800;
        padding: 2px 5px;
        font-weight: bold;
        border-bottom: 1px solid #333;
        text-transform: uppercase;
        font-size: 10px;
    }
    
    /* TABLEAUX COMPACTS */
    table {width: 100%; border-collapse: collapse;}
    th {text-align: left; color: #888; border-bottom: 1px solid #333; padding: 2px;}
    td {padding: 1px 2px; border-bottom: 1px solid #111; color: #ddd;}
    tr:hover {background-color: #111;}
    </style>
""", unsafe_allow_html=True)

# --- 3. DATA ENGINE ---

@st.cache_data(ttl=60)
def get_data_feed():
    # Tickers: NQ, VIX, TNX, BTC, DXY, AAPL, NVDA
    tickers = ["NQ=F", "QQQ", "^VIX", "^TNX", "BTC-USD", "DX-Y.NYB", "NVDA", "AAPL", "MSFT"]
    try:
        data = yf.download(tickers, period="5d", interval="15m", group_by='ticker', progress=False)
        return data
    except:
        return pd.DataFrame()

def get_news_feed():
    try:
        feed = feedparser.parse("https://finance.yahoo.com/news/rssindex")
        return feed.entries[:10]
    except:
        return []

# --- 4. DATA PROCESSING ---

raw = get_data_feed()
news = get_news_feed()

# Fallback NQ
if not raw.empty and 'NQ=F' in raw and not raw['NQ=F']['Close'].dropna().empty:
    df_nq = raw['NQ=F'].dropna()
    sym_name = "NQ=F (CME)"
elif not raw.empty and 'QQQ' in raw:
    df_nq = raw['QQQ'].dropna()
    sym_name = "QQQ (PROXY)"
else:
    st.error("NO DATA CONNECTION")
    st.stop()

# Calculs Tech
df_nq['SMA20'] = df_nq['Close'].rolling(20).mean()
df_nq['VWAP'] = (df_nq['Volume'] * (df_nq['High']+df_nq['Low']+df_nq['Close'])/3).cumsum() / df_nq['Volume'].cumsum()
current = df_nq.iloc[-1]
prev = df_nq.iloc[-2]
chg = current['Close'] - prev['Close']
pct = (chg / prev['Close']) * 100

# --- 5. UI LAYOUT (GRID SYSTEM) ---

# A. TOP BAR (TICKER)
col_t1, col_t2, col_t3 = st.columns([1, 4, 1])
with col_t1:
    st.markdown(f"<div style='color:#FF9800; font-size:16px; font-weight:bold; padding:5px;'>BLOOMBERG <span style='color:#fff'>TERMINAL</span></div>", unsafe_allow_html=True)
with col_t2:
    # Marquee simulé
    try:
        vix = raw['^VIX']['Close'].iloc[-1]
        tnx = raw['^TNX']['Close'].iloc[-1]
        btc = raw['BTC-USD']['Close'].iloc[-1]
        dxy = raw['DX-Y.NYB']['Close'].iloc[-1]
        st.markdown(f"""
        <div style='display:flex; gap:20px; padding:8px; font-family:monospace;'>
            <span>VIX: <span class='{'red' if vix>20 else 'green'}'>{vix:.2f}</span></span>
            <span>US10Y: <span class='white'>{tnx:.3f}%</span></span>
            <span>DXY: <span class='white'>{dxy:.2f}</span></span>
            <span>BTC: <span class='amber'>${btc:,.0f}</span></span>
        </div>
        """, unsafe_allow_html=True)
    except: st.write("LOADING MACRO...")
with col_t3:
    st.markdown(f"<div style='text-align:right; padding:5px; color:#444'>GATEWAY: <span style='color:#0f0'>CONNECTED</span></div>", unsafe_allow_html=True)

# B. MAIN WORKSPACE (3 COLUMNS)
c1, c2, c3 = st.columns([1, 3, 1], gap="small")

# --- LEFT PANEL: MONITOR & MACRO ---
with c1:
    # 1. SECURITY INFO
    st.markdown(f"""
    <div class="panel">
        <div class="panel-header">1) SECURITY MONITOR</div>
        <div style="padding:5px;">
            <div style="font-size:24px; color:{'#0f0' if chg>0 else '#f00'}; font-weight:bold;">{current['Close']:,.2f}</div>
            <div style="font-size:14px; color:#ddd;">{chg:+.2f} ({pct:+.2f}%)</div>
            <br>
            <table>
                <tr><td class="dim">OPEN</td><td style="text-align:right">{current['Open']:,.2f}</td></tr>
                <tr><td class="dim">HIGH</td><td style="text-align:right">{current['High']:,.2f}</td></tr>
                <tr><td class="dim">LOW</td><td style="text-align:right">{current['Low']:,.2f}</td></tr>
                <tr><td class="dim">VOL</td><td style="text-align:right">{current['Volume']/1000:.0f}K</td></tr>
                <tr><td class="dim">VWAP</td><td style="text-align:right; color:#FF9800">{current['VWAP']:,.2f}</td></tr>
            </table>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 2. WATCHLIST
    st.markdown('<div class="panel"><div class="panel-header">2) SECTOR WATCH (TECH)</div>', unsafe_allow_html=True)
    html_wl = "<table><tr><th>TICKER</th><th>LAST</th><th>CHG%</th></tr>"
    for t in ["NVDA", "AAPL", "MSFT"]:
        try:
            r = raw[t].dropna().iloc[-1]
            p = raw[t].dropna().iloc[-2]
            c = ((r['Close']-p['Close'])/p['Close'])*100
            col = "#0f0" if c >= 0 else "#f00"
            html_wl += f"<tr><td>{t}</td><td>{r['Close']:.2f}</td><td style='color:{col}'>{c:+.2f}%</td></tr>"
        except: pass
    html_wl += "</table></div>"
    st.markdown(html_wl, unsafe_allow_html=True)

# --- CENTER PANEL: CHART ---
with c2:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.8, 0.2], vertical_spacing=0.0)
    
    # Candles
    fig.add_trace(go.Candlestick(
        x=df_nq.index, open=df_nq['Open'], high=df_nq['High'], low=df_nq['Low'], close=df_nq['Close'],
        name="NQ", increasing_line_color='#00FF00', decreasing_line_color='#FF0000'
    ), row=1, col=1)
    
    # VWAP
    fig.add_trace(go.Scatter(x=df_nq.index, y=df_nq['VWAP'], line=dict(color='#FF9800', width=1), name="VWAP"), row=1, col=1)
    
    # Vol
    colors = ['#00FF00' if c >= o else '#FF0000' for c, o in zip(df_nq['Close'], df_nq['Open'])]
    fig.add_trace(go.Bar(x=df_nq.index, y=df_nq['Volume'], marker_color=colors), row=2, col=1)
    
    fig.update_layout(
        height=600,
        margin=dict(l=0, r=40, t=20, b=0),
        template="plotly_dark",
        paper_bgcolor="#0a0a0a",
        plot_bgcolor="#0a0a0a",
        showlegend=False,
        xaxis_rangeslider_visible=False
    )
    fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])], gridcolor="#222")
    fig.update_yaxes(side="right", gridcolor="#222")
    
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- RIGHT PANEL: DATA & NEWS ---
with c3:
    # 3. NEWS WIRE
    st.markdown('<div class="panel"><div class="panel-header">3) NEWS WIRE (REALTIME)</div>', unsafe_allow_html=True)
    
    # CORRECTION SYNTAXE: Construction HTML propre
    news_html = "<div style='height:200px; overflow-y:auto; padding:5px;'>"
    for n in news[:6]:
        t_time = n.published[17:22] if 'published' in n else "LIVE"
        t_title = n.title[:50] + "..." if len(n.title) > 50 else n.title
        news_html += f"<div style='border-bottom:1px solid #333; margin-bottom:4px;'>"
        news_html += f"<span style='color:#FF9800'>[{t_time}]</span> <a href='{n.link}' target='_blank' style='color:#ddd; text-decoration:none'>{t_title}</a></div>"
    news_html += "</div></div>"
    st.markdown(news_html, unsafe_allow_html=True)
    
    # 4. DEPTH OF MARKET (SIMULÉ POUR LE LOOK)
    st.markdown('<div class="panel"><div class="panel-header">4) MARKET DEPTH (L2)</div>', unsafe_allow_html=True)
    
    l2_html = "<table><tr><th>BID SZ</th><th>BID</th><th>ASK</th><th>ASK SZ</th></tr>"
    px = current['Close']
    # Simulation L2
    import random
    for i in range(1, 6):
        bid_px = px - (i*0.25)
        ask_px = px + (i*0.25)
        bid_sz = random.randint(1, 50)
        ask_sz = random.randint(1, 50)
        l2_html += f"<tr><td class='green'>{bid_sz}</td><td class='green'>{bid_px:,.2f}</td><td class='red'>{ask_px:,.2f}</td><td class='red'>{ask_sz}</td></tr>"
    l2_html += "</table></div>"
    st.markdown(l2_html, unsafe_allow_html=True)
    
    # 5. TIME & SALES (SIMULÉ)
    st.markdown('<div class="panel"><div class="panel-header">5) TIME & SALES</div>', unsafe_allow_html=True)
    ts_html = "<table><tr><th>TIME</th><th>PRICE</th><th>SIZE</th></tr>"
    for i in range(5):
        t_str = (datetime.now() - timedelta(seconds=i*2)).strftime("%H:%M:%S")
        p_str = f"{px + random.uniform(-1, 1):.2f}"
        s_str = random.randint(1, 10)
        c_str = "green" if random.choice([True, False]) else "red"
        ts_html += f"<tr><td class='dim'>{t_str}</td><td class='{c_str}'>{p_str}</td><td>{s_str}</td></tr>"
    ts_html += "</table></div>"
    st.markdown(ts_html, unsafe_allow_html=True)

# Footer CMD
st.text_input("CMD >", placeholder="Enter command...", label_visibility="collapsed")
