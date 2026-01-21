import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import feedparser
from datetime import datetime, timedelta

# --- 1. CONFIGURATION "FULL IMMERSION" ---
st.set_page_config(
    layout="wide",
    page_title="SAM-NQ TERMINAL",
    page_icon="💸",
    initial_sidebar_state="collapsed"
)

# --- 2. CSS "BLOOMBERG SKIN" (NO PADDING, HIGH DENSITY) ---
st.markdown("""
    <style>
    /* RESET GLOBAL */
    .stApp {background-color: #000000 !important;}
    .block-container {padding: 0px !important; margin: 0px !important; max-width: 100% !important;}
    
    /* FONTS & TEXT */
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;500;700&display=swap');
    * {font-family: 'Roboto Mono', 'Consolas', monospace !important; letter-spacing: -0.5px; font-size: 11px;}
    
    /* COULEURS */
    .amber {color: #FF9800;}
    .green {color: #00FF00;}
    .red {color: #FF0000;}
    .gray {color: #666;}
    .white {color: #DDD;}
    
    /* TABLEAUX COMPACTS (HTML) */
    .b-table {width: 100%; border-collapse: collapse; font-size: 10px; background: #050505;}
    .b-table th {text-align: left; color: #FF9800; border-bottom: 1px solid #333; padding: 2px 4px;}
    .b-table td {color: #CCC; padding: 2px 4px; border-bottom: 1px solid #111;}
    .b-table tr:hover {background-color: #1a1a1a;}
    
    /* CONTAINERS */
    .b-box {border: 1px solid #333; margin: 2px; padding: 0px; background: #020202; height: 100%;}
    .b-header {background: #111; color: #FF9800; padding: 2px 5px; font-weight: bold; font-size: 10px; border-bottom: 1px solid #333; display: flex; justify-content: space-between;}
    
    /* HIDE STREAMLIT JUNK */
    header, footer, #MainMenu {display: none !important;}
    </style>
""", unsafe_allow_html=True)

# --- 3. DATA ENGINE (FIXED CORRELATION) ---

@st.cache_data(ttl=60)
def get_terminal_data():
    # On récupère TOUT en une fois pour assurer l'alignement des timestamps
    tickers = ["NQ=F", "QQQ", "^VIX", "^TNX", "BTC-USD", "GC=F", "DX-Y.NYB", "NVDA", "AAPL", "MSFT", "TSLA"]
    
    # On prend 50 jours en 1h (plus stable que 15m pour les corrélations Yahoo)
    data = yf.download(tickers, period="50d", interval="60m", group_by='ticker', progress=False)
    
    # Extraction NQ (Futures)
    if 'NQ=F' in data and not data['NQ=F']['Close'].dropna().empty:
        df_main = data['NQ=F'].dropna()
        symbol = "NQ=F (CME)"
    else:
        df_main = data['QQQ'].dropna()
        symbol = "QQQ (PROXY)"
        
    return data, df_main, symbol

def calc_correlations(main_df, full_data):
    # Calcul des corrélations robuste
    # 1. On crée un DataFrame pivot avec les Closes de tout le monde
    df_pivot = pd.DataFrame()
    df_pivot['MAIN'] = main_df['Close']
    
    others = {"VIX": "^VIX", "RATES": "^TNX", "BTC": "BTC-USD", "DXY": "DX-Y.NYB"}
    
    for label, tick in others.items():
        if tick in full_data:
            # On resample pour matcher l'index du NQ
            s = full_data[tick]['Close']
            df_pivot[label] = s
            
    # 2. On calcule les variations en % et on nettoie les NaN (Forward Fill)
    returns = df_pivot.pct_change().ffill().dropna()
    
    # 3. Matrice de corrélation sur les 20 dernières périodes
    if not returns.empty:
        corrs = returns.rolling(20).corr(returns['MAIN']).iloc[-1]
        return corrs
    return pd.Series()

def get_news():
    try:
        return feedparser.parse("https://finance.yahoo.com/news/rssindex").entries[:12]
    except: return []

# --- 4. RENDERERS (HTML PUR POUR DENSITÉ) ---

def render_ticker_tape(df, sym):
    last = df['Close'].iloc[-1]
    chg = last - df['Open'].iloc[-1] # vs Open bougie courante
    pct = (chg / df['Open'].iloc[-1]) * 100
    color = "#00FF00" if chg >= 0 else "#FF0000"
    
    st.markdown(f"""
    <div style="background:#111; border-bottom:1px solid #333; padding:2px 10px; display:flex; justify-content:space-between; align-items:center; height:30px;">
        <div style="color:#FF9800; font-weight:bold; font-size:14px;">{sym} <span style="color:#666; font-size:10px;">[FUTURES]</span></div>
        <div style="font-family:monospace">
            <span style="color:#FFF; font-size:16px; font-weight:bold;">{last:,.2f}</span>
            <span style="color:{color}; font-size:14px; margin-left:10px;">{chg:+.2f} ({pct:+.2f}%)</span>
        </div>
        <div style="color:#666; font-size:10px;">MARKET: <span style="color:#0F0">OPEN</span> | SESSION: <span style="color:#FFF">GLOBEX</span></div>
    </div>
    """, unsafe_allow_html=True)

def render_dense_table(title, data_dict, col_headers=["TICKER", "LAST", "%CHG"]):
    html = f"<div class='b-box'><div class='b-header'>{title}</div><table class='b-table'>"
    html += f"<thead><tr><th>{col_headers[0]}</th><th>{col_headers[1]}</th><th>{col_headers[2]}</th></tr></thead><tbody>"
    
    for label, vals in data_dict.items():
        val = vals[0]
        chg = vals[1]
        c = "#00FF00" if chg >= 0 else "#FF0000"
        
        # Formatage intelligent
        if "VIX" in label or "RATES" in label: fmt_val = f"{val:.2f}"
        elif "BTC" in label: fmt_val = f"{val:,.0f}"
        else: fmt_val = f"{val:.2f}"
        
        html += f"<tr><td><b style='color:#DDD'>{label}</b></td><td>{fmt_val}</td><td style='color:{c}'>{chg:+.2f}%</td></tr>"
    
    html += "</tbody></table></div>"
    st.markdown(html, unsafe_allow_html=True)

def render_correlation_box(corrs):
    html = f"<div class='b-box'><div class='b-header'>CORRELATION MATRIX (ROLLING 20)</div><table class='b-table'>"
    html += "<thead><tr><th>ASSET</th><th>CORR</th><th>STATUS</th></tr></thead><tbody>"
    
    for idx, val in corrs.items():
        if idx == 'MAIN': continue
        c_val = "#00FF00" if val > 0.5 else "#FF0000" if val < -0.5 else "#888"
        status = "LINKED" if val > 0.7 else "HEDGE" if val < -0.5 else "UNCORR"
        html += f"<tr><td>{idx}</td><td style='color:{c_val}'>{val:.2f}</td><td style='font-size:9px'>{status}</td></tr>"
    
    html += "</tbody></table></div>"
    st.markdown(html, unsafe_allow_html=True)

# --- 5. LOGIQUE PRINCIPALE ---

full_data, main_df, symbol = get_terminal_data()

if not main_df.empty:
    # Préparation Données Macro & Tech
    macro_dict = {}
    for t, l in [("^VIX", "VIX Index"), ("^TNX", "US 10Y"), ("BTC-USD", "Bitcoin"), ("GC=F", "Gold")]:
        if t in full_data:
            s = full_data[t]['Close'].dropna()
            if not s.empty:
                curr = s.iloc[-1]
                prev = s.iloc[-2]
                macro_dict[l] = (curr, ((curr-prev)/prev)*100)

    mag7_dict = {}
    for t in ["NVDA", "AAPL", "MSFT", "TSLA"]:
        if t in full_data:
            s = full_data[t]['Close'].dropna()
            if not s.empty:
                curr = s.iloc[-1]
                prev = s.iloc[-2]
                mag7_dict[t] = (curr, ((curr-prev)/prev)*100)

    # Calcul RSI
    delta = main_df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    last_rsi = rsi.iloc[-1]

    # --- UI LAYOUT ---
    
    # 1. TOP BAR
    render_ticker_tape(main_df, symbol)
    
    # 2. MAIN GRID (20% | 60% | 20%)
    c1, c2, c3 = st.columns([1, 3, 1], gap="small")
    
    with c1:
        # GAUCHE: MACRO & WATCHLIST
        render_dense_table("GLOBAL MACRO", macro_dict)
        st.markdown("<div style='height:2px'></div>", unsafe_allow_html=True)
        render_dense_table("SECTOR: TECH", mag7_dict)
        st.markdown("<div style='height:2px'></div>", unsafe_allow_html=True)
        
        # Corrélation corrigée
        corrs = calc_correlations(main_df, full_data)
        if not corrs.empty:
            render_correlation_box(corrs)
        else:
            st.info("Calculating Corrs...")

        # Stats Techniques
        st.markdown(f"""
        <div class='b-box'>
            <div class='b-header'>RISK MONITOR</div>
            <table class='b-table'>
                <tr><td>RSI (14)</td><td style='color:{"#F00" if last_rsi>70 else "#0F0" if last_rsi<30 else "#FFF"}'>{last_rsi:.2f}</td></tr>
                <tr><td>HI (Session)</td><td>{main_df['High'].max():,.2f}</td></tr>
                <tr><td>LO (Session)</td><td>{main_df['Low'].min():,.2f}</td></tr>
                <tr><td>VOL (Session)</td><td>{main_df['Volume'].sum()/1000:.0f}K</td></tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        # CENTRE: GRAPHIQUE PLEIN ECRAN
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.8, 0.2], vertical_spacing=0.0)
        
        # Candles
        fig.add_trace(go.Candlestick(
            x=main_df.index, open=main_df['Open'], high=main_df['High'], low=main_df['Low'], close=main_df['Close'],
            name="Px", increasing_line_color='#00FF00', decreasing_line_color='#FF0000', showlegend=False
        ), row=1, col=1)
        
        # SMA
        sma20 = main_df['Close'].rolling(20).mean()
        fig.add_trace(go.Scatter(x=main_df.index, y=sma20, line=dict(color='#FF9800', width=1), showlegend=False), row=1, col=1)
        
        # Volume
        colors = ['#00FF00' if c >= o else '#FF0000' for c, o in zip(main_df['Close'], main_df['Open'])]
        fig.add_trace(go.Bar(x=main_df.index, y=main_df['Volume'], marker_color=colors, showlegend=False), row=2, col=1)
        
        # Suppression des trous (Weekends)
        fig.update_xaxes(
            rangebreaks=[dict(bounds=["sat", "mon"])],
            gridcolor='#222', showgrid=True, showticklabels=True
        )
        
        fig.update_layout(
            height=600,
            margin=dict(l=0, r=40, t=10, b=0),
            template="plotly_dark",
            paper_bgcolor="#000", plot_bgcolor="#000",
            xaxis_rangeslider_visible=False
        )
        fig.update_yaxes(side="right", gridcolor="#222", showgrid=True)
        
        st.plotly_chart(fig, use_container_width=True)

    with c3:
        # DROITE: NEWS & ORDER BOOK
        st.markdown(f"<div class='b-box'><div class='b-header'>NEWS WIRE</div>", unsafe_allow_html=True)
        news = get_news()
        for n in news[:8]:
            st.markdown(f"""
            <div style='border-bottom:1px solid #222; padding:3px 5px;'>
                <a href='{n.link}' target='_blank' style='color:#DDD; text-decoration:none; font-size:10px; display:block; hover:color:#F90'>{n.title}</a>
                <span style='color:#666; font-size:9px'>{n.published[17:22] if 'published' in n else ''}</span>
            </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Faux Carnet d'ordre (Pour le look)
        curr = main_df['Close'].iloc[-1]
        st.markdown(f"<div style='height:2px'></div><div class='b-box'><div class='b-header'>DEPTH (L2)</div>", unsafe_allow_html=True)
        html_l2 = "<table class='b-table'><thead><tr><th>BID SIZE</th><th>BID</th><th>ASK</th><th>ASK SIZE</th></tr></thead><tbody>"
        # Simulation L2 autour du prix actuel
        for i in range(5):
            bid = curr - (i+1)*0.25
            ask = curr + (i+1)*0.25
            bs = np.random.randint(1, 50)
            as_ = np.random.randint(1, 50)
            html_l2 += f"<tr><td style='color:#FF9800'>{bs}</td><td style='color:#0F0'>{bid:.2f}</td><td style='color:#F00'>{ask:.2f}</td><td style='color:#FF9800'>{as_}</td></tr>"
        html_l2 += "</tbody></table></div>"
        st.markdown(html_l2, unsafe_allow_html=True)

    # 3. COMMAND LINE (Bas de page)
    st.markdown("""
    <div style="background:#111; border-top:1px solid #333; padding:5px; margin-top:5px; font-family:monospace; color:#FF9800; font-size:12px;">
        <span style="color:#0F0">SAM_VISION></span> <span style="animation: blink 1s infinite">|</span> 
        <span style="color:#666; float:right">Connected: GATEWAY_NY4</span>
    </div>
    <style>
    @keyframes blink {0%{opacity:0;} 50%{opacity:1;} 100%{opacity:0;}}
    </style>
    """, unsafe_allow_html=True)
    
    if st.button("CMD: REFRESH DATA"):
        st.cache_data.clear()
        st.rerun()

else:
    st.error("INITIALIZING DATA FEED... PLEASE WAIT OR REFRESH.")
