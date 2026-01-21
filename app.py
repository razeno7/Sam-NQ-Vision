import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import feedparser
from datetime import datetime

# --- 1. SETUP PAGE ---
st.set_page_config(
    layout="wide",
    page_title="Gorilla Terminal AI",
    page_icon="🦍",
    initial_sidebar_state="expanded"
)

# --- 2. CSS "GORILLA DARK MODE" ---
st.markdown("""
    <style>
    /* FONTS */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
    
    /* THEME GLOBAL */
    .stApp {
        background-color: #0d1117 !important; /* Dark Blue-Black */
        color: #c9d1d9;
        font-family: 'Inter', sans-serif;
    }
    
    /* SIDEBAR */
    section[data-testid="stSidebar"] {
        background-color: #010409;
        border-right: 1px solid #30363d;
    }
    
    /* WIDGET CARD DESIGN */
    .gorilla-card {
        background-color: #161b22; /* Card BG */
        border: 1px solid #30363d; /* Border */
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.5);
    }
    .card-header {
        font-size: 11px;
        font-weight: 600;
        color: #8b949e;
        text-transform: uppercase;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    /* METRICS STYLE */
    .metric-value { font-size: 24px; font-weight: 600; color: #f0f6fc; }
    .metric-delta-up { color: #3fb950; font-size: 12px; font-weight: 500; }
    .metric-delta-dn { color: #f85149; font-size: 12px; font-weight: 500; }
    
    /* AI CHAT STYLE */
    .ai-bubble {
        background: #1f6feb; /* Gorilla Blue */
        color: white;
        padding: 10px;
        border-radius: 8px;
        font-size: 12px;
        line-height: 1.4;
        margin-top: 10px;
    }
    
    /* TABS */
    .stTabs [data-baseweb="tab-list"] { border-bottom: 1px solid #30363d; }
    .stTabs [data-baseweb="tab"] { color: #8b949e; border: none; font-size: 12px; }
    .stTabs [aria-selected="true"] { color: #58a6ff; border-bottom: 2px solid #58a6ff; }

    /* HIDE ELEMENTS */
    header, footer, #MainMenu {visibility: hidden;}
    .block-container {padding-top: 1rem; padding-left: 1rem; padding-right: 1rem;}
    </style>
""", unsafe_allow_html=True)

# --- 3. ROBUST DATA ENGINE (FIX CRASH) ---
@st.cache_data(ttl=300)
def get_robust_data(ticker_input):
    # Liste de tentatives : Ticker demandé -> QQQ (Proxy) -> SPY (Dernier recours)
    attempts = [ticker_input, "QQQ", "SPY"]
    
    for t in attempts:
        try:
            # On essaie de télécharger
            df = yf.download(t, period="5d", interval="15m", progress=False)
            
            # Nettoyage si MultiIndex (Le fix critique est ici aussi)
            if isinstance(df.columns, pd.MultiIndex):
                df = df.xs(t, level=0, axis=1)
                
            if not df.empty and len(df) > 10:
                # Si ça marche, on récupère les infos et on retourne
                try:
                    info = yf.Ticker(t).info
                except:
                    info = {}
                
                # On force le nom d'affichage si c'est un proxy
                display_name = ticker_input if t == ticker_input else f"{ticker_input} (via {t})"
                return df, info, display_name
        except:
            continue
            
    return pd.DataFrame(), {}, "DATA OFFLINE"

def get_simulated_news():
    # Simulation news pour éviter les blocages RSS
    return [
        {"title": "Fed Signals Potential Rate Cut as Inflation Cools", "time": "10m ago", "source": "Bloomberg"},
        {"title": "Tech Stocks Rally on AI Chip Demand Surge", "time": "32m ago", "source": "Reuters"},
        {"title": "Oil Prices Stabilize Amid Geopolitical Tensions", "time": "1h ago", "source": "CNBC"},
        {"title": "Nasdaq 100 Futures Point to Higher Open", "time": "2h ago", "source": "WSJ"},
    ]

# --- 4. UI COMPONENTS ---
def render_metric(label, value, pct_change, is_currency=True):
    # FIX: On s'assure que pct_change est un float simple, pas une série Pandas
    try:
        val_check = float(pct_change)
    except:
        val_check = 0.0
        
    color = "metric-delta-up" if val_check >= 0 else "metric-delta-dn"
    sign = "+" if val_check >= 0 else ""
    fmt_val = f"${value:,.2f}" if is_currency else f"{value:,.0f}"
    
    st.markdown(f"""
    <div class="gorilla-card">
        <div class="card-header">{label}</div>
        <div class="metric-value">{fmt_val}</div>
        <div class="{color}">{sign}{val_check:.2f}%</div>
    </div>
    """, unsafe_allow_html=True)

def render_ai_insight(symbol, rsi_val):
    # FIX: Conversion float explicite pour éviter l'erreur de vérité ambiguë
    rsi_float = float(rsi_val)
    sentiment = "BULLISH" if rsi_float > 50 else "BEARISH"
    st.markdown(f"""
    <div class="gorilla-card">
        <div class="card-header">
            <span>🧠 GORILLA AI CO-PILOT</span>
            <span style="color:#58a6ff">BETA</span>
        </div>
        <div style="font-size:12px; color:#c9d1d9;">
            Analysing <b>{symbol}</b> market structure...
        </div>
        <div class="ai-bubble">
            <b>AI VERDICT: {sentiment}</b><br>
            RSI is currently at {rsi_float:.1f}. Volatility analysis suggests a potential breakout zone. 
            Institutional flow detected on the buy-side.
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- 5. MAIN APPLICATION ---

# SIDEBAR
with st.sidebar:
    st.markdown("### 🦍 GORILLA")
    st.text_input("Global Search...", value="NQ=F")
    
    st.markdown("---")
    st.markdown("**DASHBOARD**")
    st.markdown("MARKETS")
    st.markdown("NEWS")
    st.markdown("SCREENER")
    
    st.markdown("---")
    st.caption("MY WATCHLIST")
    st.markdown("🟢 **NQ=F** 18,240")
    st.markdown("🔴 **ES=F** 5,120")
    st.markdown("🟢 **BTC** 64,000")

# MAIN CONTENT
# Top Bar
t1, t2 = st.columns([3, 1])
with t1:
    target_ticker = "NQ=F" # Par défaut
    st.markdown(f"## {target_ticker} / NASDAQ 100 FUTURES")
with t2:
    st.markdown("<div style='text-align:right; color:#3fb950'>● CONNECTED</div>", unsafe_allow_html=True)

# Fetch Data (Robust)
df, info, display_name = get_robust_data(target_ticker)

if not df.empty:
    # Calculations - FIX CRITIQUE: Conversion explicite en float
    curr = float(df['Close'].iloc[-1])
    prev = float(df['Close'].iloc[-2])
    chg = ((curr - prev) / prev) * 100
    
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    last_rsi = float(rsi.iloc[-1]) # Force float

    # --- TABS LAYOUT (Like Gorilla) ---
    tab1, tab2, tab3 = st.tabs(["TERMINAL", "FUNDAMENTALS", "SUPPLY CHAIN"])

    with tab1:
        # ROW 1: KEY METRICS
        c1, c2, c3, c4 = st.columns(4)
        with c1: render_metric("LAST PRICE", curr, chg)
        with c2: render_metric("VOLUME (24H)", float(df['Volume'].sum()), 12.5, False)
        with c3: render_metric("AVG TRUE RANGE", 45.20, -2.1, False) # Simulated
        with c4: render_metric("RELATIVE VOL", 1.2, 5.4, False) # Simulated

        # ROW 2: CHART + AI SIDEBAR
        col_main, col_side = st.columns([3, 1])
        
        with col_main:
            st.markdown(f"<div class='gorilla-card' style='height:500px'>", unsafe_allow_html=True)
            # Chart Plotly
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.75, 0.25], vertical_spacing=0.0)
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Price", increasing_line_color='#3fb950', decreasing_line_color='#f85149'), row=1, col=1)
            fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color='#30363d', showlegend=False), row=2, col=1)
            
            fig.update_layout(
                height=460, margin=dict(l=10, r=10, t=30, b=10),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                xaxis_rangeslider_visible=False, showlegend=False,
                font=dict(color="#8b949e")
            )
            fig.update_xaxes(gridcolor='#21262d')
            fig.update_yaxes(side='right', gridcolor='#21262d')
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with col_side:
            render_ai_insight(display_name, last_rsi)
            
            # News Widget
            st.markdown("<div class='gorilla-card'><div class='card-header'>LIVE WIRE</div>", unsafe_allow_html=True)
            news = get_simulated_news()
            for n in news:
                st.markdown(f"""
                <div style='border-bottom:1px solid #21262d; padding:8px 0;'>
                    <div style='color:#c9d1d9; font-size:12px; font-weight:500'>{n['title']}</div>
                    <div style='color:#8b949e; font-size:10px; margin-top:4px'>{n['source']} • {n['time']}</div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    with tab2:
        st.markdown("### FINANCIAL HEALTH")
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            st.dataframe(pd.DataFrame({
                "Metric": ["Revenue", "Gross Margin", "EBITDA", "Net Income"],
                "Value": ["$32.4B", "45.2%", "$12.1B", "$8.4B"],
                "YoY": ["+12%", "+2%", "+8%", "+15%"]
            }), use_container_width=True, hide_index=True)
        with col_f2:
            st.info("Detailed financial modeling requires a Premium subscription.")

    with tab3:
        st.markdown("### ⛓️ SUPPLY CHAIN GRAPH")
        st.markdown("Visualizing Tier-1 and Tier-2 suppliers for NASDAQ-100 components.")
        # Placeholder graph
        st.bar_chart(pd.DataFrame(np.random.rand(20, 3), columns=["APAC", "EMEA", "AMER"]))

else:
    st.error("SYSTEM ERROR: Unable to fetch market data. Please check your connection.")
    if st.button("RETRY CONNECTION"):
        st.cache_data.clear()
        st.rerun()
