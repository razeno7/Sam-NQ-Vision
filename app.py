import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import time

# --- 1. CONFIGURATION SYSTEME ---
st.set_page_config(layout="wide", page_title="GORILLA LITE", page_icon="🦍", initial_sidebar_state="collapsed")

# --- 2. CSS & DESIGN (GORILLA STYLE) ---
st.markdown("""
    <style>
    /* RESET TOTAL */
    .stApp {background-color: #0d1117 !important;} /* Couleur VS Code Dark */
    
    /* FONTS */
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    * {font-family: 'JetBrains Mono', monospace !important; font-size: 13px;}
    
    /* INPUT BAR (La barre de commande) */
    .stChatInput {position: fixed; bottom: 0; width: 100%; z-index: 1000; background: #0d1117;}
    textarea {background-color: #161b22 !important; color: #58a6ff !important; border: 1px solid #30363d !important;}
    
    /* CONTAINERS */
    .terminal-box {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 6px;
        padding: 15px;
        margin-bottom: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    
    /* TEXT COLORS */
    .cmd-success {color: #2ea043;} /* Vert GitHub */
    .cmd-error {color: #da3633;} /* Rouge GitHub */
    .cmd-info {color: #58a6ff;} /* Bleu GitHub */
    .cmd-warn {color: #d29922;} /* Orange GitHub */
    .ticker-tag {background: #238636; color: white; padding: 2px 6px; border-radius: 4px; font-size: 10px;}
    
    /* HIDE JUNK */
    header, footer, #MainMenu {display: none !important;}
    .block-container {padding-top: 20px; padding-bottom: 100px;}
    </style>
""", unsafe_allow_html=True)

# --- 3. SESSION STATE (MEMOIRE DU TERMINAL) ---
if "history" not in st.session_state:
    st.session_state.history = [] # Logs des commandes
if "active_view" not in st.session_state:
    st.session_state.active_view = None # Ce qu'on affiche (Chart, Data, etc)
if "current_ticker" not in st.session_state:
    st.session_state.current_ticker = "NQ=F"

# --- 4. ENGINE (FONCTIONS) ---

def fetch_price(ticker):
    try:
        df = yf.download(ticker, period="1d", interval="1m", progress=False)
        if df.empty: return None
        return df
    except: return None

def get_info(ticker):
    try:
        t = yf.Ticker(ticker)
        return t.info
    except: return {}

# --- 5. LOGIQUE DE COMMANDE (PARSER) ---
def execute_command(cmd):
    cmd = cmd.strip().upper()
    parts = cmd.split(" ")
    action = parts[0]
    
    # LOG LE MESSAGE
    st.session_state.history.append(f"<span style='color:#8b949e'>user@gorilla:~$</span> {cmd}")
    
    # COMMANDE: HELP
    if action in ["HELP", "?"]:
        st.session_state.active_view = "HELP"
        return
        
    # COMMANDE: CLEAR
    if action == "CLEAR":
        st.session_state.history = []
        st.session_state.active_view = None
        return

    # GESTION TICKER (ex: /NQ ou NQ)
    target = parts[1] if len(parts) > 1 else st.session_state.current_ticker
    
    # COMMANDE: PRICE / QUOTE
    if action in ["PRICE", "QUOTE", "P"]:
        st.session_state.current_ticker = target
        st.session_state.active_view = "QUOTE"
        
    # COMMANDE: CHART / C
    elif action in ["CHART", "C", "GRAPH"]:
        st.session_state.current_ticker = target
        st.session_state.active_view = "CHART"
        
    # COMMANDE: NEWS / N
    elif action in ["NEWS", "N"]:
        st.session_state.current_ticker = target
        st.session_state.active_view = "NEWS"
        
    # COMMANDE: MACRO / M
    elif action in ["MACRO", "M"]:
        st.session_state.active_view = "MACRO"
    
    # UNKNOWN
    else:
        st.session_state.history.append(f"<span class='cmd-error'>Error: Command '{action}' not recognized. Type HELP.</span>")

# --- 6. RENDU DE L'INTERFACE (UI) ---

# HEADER MINIMALISTE
col1, col2 = st.columns([1, 4])
with col1:
    st.markdown("### 🦍 GORILLA_LITE")
with col2:
    st.markdown(f"<div style='text-align:right; color:#8b949e'>CONNECTED: {st.session_state.current_ticker} | LATENCY: 12ms</div>", unsafe_allow_html=True)

st.markdown("---")

# MAIN VIEWPORT (L'ECRAN DU TERMINAL)
view = st.session_state.active_view
ticker = st.session_state.current_ticker

if view == "HELP":
    st.markdown("""
    <div class='terminal-box'>
        <div class='cmd-info'><b>COMMAND LIST</b></div>
        <br>
        <b>CHART [TICKER]</b> - Afficher le graphique (ex: CHART AAPL)<br>
        <b>PRICE [TICKER]</b> - Afficher le prix en gros (ex: PRICE BTC-USD)<br>
        <b>NEWS [TICKER]</b>  - Lire les news (ex: NEWS TSLA)<br>
        <b>MACRO</b>          - Vue globale du marché<br>
        <b>CLEAR</b>          - Nettoyer le terminal
    </div>
    """, unsafe_allow_html=True)

elif view == "QUOTE":
    df = fetch_price(ticker)
    if df is not None:
        last = df['Close'].iloc[-1]
        prev = df['Open'].iloc[0]
        chg = last - prev
        pct = (chg/prev)*100
        color = "#2ea043" if chg >= 0 else "#da3633"
        
        st.markdown(f"""
        <div class='terminal-box' style='text-align:center'>
            <h1 style='font-size: 60px; color:{color}; margin:0'>{last:,.2f}</h1>
            <h3 style='color:#8b949e'>{ticker}</h3>
            <span style='color:{color}; font-size:18px'>{chg:+.2f} ({pct:+.2f}%)</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Mini Stats
        info = get_info(ticker)
        st.markdown(f"""
        <div class='terminal-box'>
            <div style='display:flex; justify-content:space-between'>
                <span>VOL: <b class='cmd-info'>{info.get('volume', 'N/A')}</b></span>
                <span>MKT CAP: <b class='cmd-info'>{info.get('marketCap', 'N/A')}</b></span>
                <span>PE RATIO: <b class='cmd-info'>{info.get('trailingPE', 'N/A')}</b></span>
            </div>
        </div>
        """, unsafe_allow_html=True)

elif view == "CHART":
    df = fetch_price(ticker)
    if df is not None:
        fig = go.Figure(data=[go.Candlestick(
            x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
            increasing_line_color='#2ea043', decreasing_line_color='#da3633'
        )])
        fig.update_layout(
            height=500, margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor="#161b22", plot_bgcolor="#0d1117",
            font=dict(family="JetBrains Mono", color="#8b949e"),
            xaxis_rangeslider_visible=False
        )
        fig.update_xaxes(gridcolor="#30363d")
        fig.update_yaxes(gridcolor="#30363d", side="right")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error(f"Failed to load data for {ticker}")

elif view == "MACRO":
    # Dashboard rapide
    c1, c2, c3 = st.columns(3)
    def mini_metric(label, sym):
        d = fetch_price(sym)
        if d is not None:
            l = d['Close'].iloc[-1]
            p = ((l - d['Open'].iloc[0])/d['Open'].iloc[0])*100
            col = "cmd-success" if p > 0 else "cmd-error"
            return f"<div class='terminal-box'><div>{label}</div><div class='{col}' style='font-size:20px'>{l:.2f} ({p:+.2f}%)</div></div>"
        return ""
    
    with c1: st.markdown(mini_metric("S&P 500", "^GSPC"), unsafe_allow_html=True)
    with c2: st.markdown(mini_metric("NASDAQ", "NQ=F"), unsafe_allow_html=True)
    with c3: st.markdown(mini_metric("BITCOIN", "BTC-USD"), unsafe_allow_html=True)

# LOGS (HISTORIQUE DE COMMANDES - EN HAUT)
with st.container():
    st.markdown("<div style='font-size:10px; color:#30363d; margin-top:20px'>TERMINAL LOGS:</div>", unsafe_allow_html=True)
    # On affiche les 5 dernières commandes
    for h in st.session_state.history[-5:]:
        st.markdown(f"<div style='font-family:monospace; font-size:11px'>{h}</div>", unsafe_allow_html=True)

# INPUT BAR (LE CŒUR DU SYSTÈME)
# C'est ce qui rend l'appli "Gorilla style"
cmd = st.chat_input("Enter command (e.g. 'CHART NVDA' or 'MACRO')...")
if cmd:
    execute_command(cmd)
    st.rerun()
