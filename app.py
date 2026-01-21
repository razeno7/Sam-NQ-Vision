import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import feedparser
from datetime import datetime

# --- 1. SETUP PAGE (MODE DASHBOARD) ---
st.set_page_config(
    layout="wide",
    page_title="Gorilla Terminal Clone",
    page_icon="🦍",
    initial_sidebar_state="expanded"
)

# --- 2. CSS "MODERN SAAS" (STYLE GORILLA) ---
st.markdown("""
    <style>
    /* IMPORT FONTS MODERNE */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    
    /* GLOBAL THEME */
    .stApp {
        background-color: #0b0f19 !important; /* Deep Blue/Black Gorilla Style */
        color: #e2e8f0;
        font-family: 'Inter', sans-serif;
    }
    
    /* SIDEBAR */
    section[data-testid="stSidebar"] {
        background-color: #07090f;
        border-right: 1px solid #1e293b;
    }
    
    /* CARDS (WIDGETS) */
    .g-card {
        background-color: #111827;
        border: 1px solid #1f2937;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .g-card-header {
        font-size: 14px;
        font-weight: 600;
        color: #94a3b8;
        margin-bottom: 15px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    /* METRICS */
    .g-metric-val { font-size: 28px; font-weight: 700; color: #fff; }
    .g-metric-lbl { font-size: 12px; color: #64748b; }
    .g-up { color: #10b981; } /* Emerald Green */
    .g-down { color: #ef4444; } /* Rose Red */
    
    /* AI CHAT BOX */
    .ai-box {
        background: #1e1b4b; /* Indigo tint */
        border: 1px solid #4338ca;
        border-radius: 8px;
        padding: 15px;
        font-size: 13px;
        line-height: 1.5;
        color: #c7d2fe;
    }
    
    /* TABS */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 4px;
        color: #94a3b8;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1f2937;
        color: #60a5fa; /* Blue accent */
    }

    /* SEARCH BAR OVERRIDE */
    .stTextInput input {
        background-color: #1f2937 !important;
        color: white !important;
        border: 1px solid #374151 !important;
        border-radius: 8px;
    }
    
    /* HIDE STREAMLIT DECORATION */
    header, footer, #MainMenu {visibility: hidden;}
    .block-container {padding-top: 2rem;}
    </style>
""", unsafe_allow_html=True)

# --- 3. DATA ENGINE ---
@st.cache_data(ttl=60)
def get_data(ticker):
    try:
        df = yf.download(ticker, period="1mo", interval="1h", progress=False)
        info = yf.Ticker(ticker).info
        return df, info
    except: return pd.DataFrame(), {}

def get_news(ticker):
    try:
        # Simulation news feed intelligent
        return feedparser.parse("https://finance.yahoo.com/news/rssindex").entries[:5]
    except: return []

# --- 4. COMPOSANTS UI (WIDGETS) ---

def metric_card(label, value, delta, is_currency=True):
    color = "g-up" if delta >= 0 else "g-down"
    arrow = "↑" if delta >= 0 else "↓"
    fmt_val = f"${value:,.2f}" if is_currency else f"{value:,.0f}"
    st.markdown(f"""
    <div class="g-card" style="padding: 15px;">
        <div class="g-metric-lbl">{label}</div>
        <div class="g-metric-val">{fmt_val}</div>
        <div class="{color}" style="font-size: 12px; font-weight: 600; margin-top: 5px;">
            {arrow} {abs(delta):.2f}%
        </div>
    </div>
    """, unsafe_allow_html=True)

def ai_insight_card(ticker, info, rsi):
    # Simulation d'un insight généré par IA
    sentiment = "BULLISH" if rsi < 30 else "BEARISH" if rsi > 70 else "NEUTRAL"
    summary = info.get('longBusinessSummary', 'No data')[:150] + "..."
    
    st.markdown(f"""
    <div class="g-card">
        <div class="g-card-header">
            <span>🦍 GORILLA AI INSIGHTS</span>
            <span style="background:#4338ca; color:white; padding:2px 8px; border-radius:10px; font-size:10px;">BETA</span>
        </div>
        <div class="ai-box">
            <b>ANALYSIS FOR {ticker}:</b><br><br>
            • <b>Sentiment:</b> <span style="color:{'#10b981' if sentiment=='BULLISH' else '#ef4444'}">{sentiment}</span> based on technicals (RSI: {rsi:.1f}).<br>
            • <b>Fundamental:</b> {summary}<br><br>
            <i>"Based on current volatility, {ticker} shows strong support levels. AI suggests monitoring volume spikes in the next 4H session."</i>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- 5. LAYOUT PRINCIPAL ---

# SIDEBAR NAVIGATION
with st.sidebar:
    st.markdown("### 🦍 GorillaTerm")
    st.markdown("---")
    menu = st.radio("MENU", ["Dashboard", "Supply Chain", "Financials", "Macro Data"], label_visibility="collapsed")
    st.markdown("---")
    st.caption("WATCHLIST")
    st.markdown("**NQ=F** `+1.2%`", unsafe_allow_html=True)
    st.markdown("**AAPL** `-0.5%`", unsafe_allow_html=True)
    st.markdown("**NVDA** `+2.4%`", unsafe_allow_html=True)
    
    st.markdown("<div style='margin-top: auto; padding-top: 50px; color: #64748b; font-size: 11px;'>v2.4.0 PRO</div>", unsafe_allow_html=True)

# TOP BAR (SEARCH)
c1, c2 = st.columns([3, 1])
with c1:
    search_ticker = st.text_input("Search Ticker (e.g., NQ=F, AAPL, BTC-USD)", value="NQ=F", label_visibility="collapsed", placeholder="Search assets, data, or ask AI...")
with c2:
    st.markdown("<div style='text-align:right; padding-top:10px; color:#94a3b8;'><b>CONNECTED</b> ●</div>", unsafe_allow_html=True)

# CHARGEMENT DATA
data, info = get_data(search_ticker)

if not data.empty:
    current_price = data['Close'].iloc[-1]
    prev_close = data['Close'].iloc[-2]
    pct_chg = ((current_price - prev_close) / prev_close) * 100
    
    # Calcul RSI
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    last_rsi = rsi.iloc[-1]

    # --- CONTENU DES ONGLETS ---
    
    if menu == "Dashboard":
        # ROW 1: METRICS
        m1, m2, m3, m4 = st.columns(4)
        with m1: metric_card("CURRENT PRICE", current_price, pct_chg)
        with m2: metric_card("MARKET CAP", info.get('marketCap', 0), 0)
        with m3: metric_card("VOLUME (24H)", data['Volume'].sum(), 5.2, False)
        with m4: metric_card("P/E RATIO", info.get('trailingPE', 0), -1.2, False)
        
        # ROW 2: CHART & AI (The "Gorilla" Layout)
        c_chart, c_ai = st.columns([2, 1])
        
        with c_chart:
            st.markdown(f"<div class='g-card' style='height: 500px;'>", unsafe_allow_html=True)
            # Chart Plotly Pro
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.75, 0.25], vertical_spacing=0.05)
            fig.add_trace(go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'], name="Price", increasing_line_color='#10b981', decreasing_line_color='#ef4444'), row=1, col=1)
            fig.add_trace(go.Bar(x=data.index, y=data['Volume'], marker_color='#374151', name="Vol"), row=2, col=1)
            
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=10, r=10, t=10, b=10),
                height=450,
                showlegend=False,
                xaxis_rangeslider_visible=False
            )
            fig.update_xaxes(showgrid=True, gridcolor='#1f2937')
            fig.update_yaxes(showgrid=True, gridcolor='#1f2937', side='right')
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with c_ai:
            # Module AI Insight (Spécifique Gorilla)
            ai_insight_card(search_ticker, info, last_rsi)
            
            # Module News Compact
            st.markdown("<div class='g-card'><div class='g-card-header'>LATEST NEWS</div>", unsafe_allow_html=True)
            news = get_news(search_ticker)
            for n in news:
                st.markdown(f"""
                <div style="border-bottom:1px solid #1f2937; padding:8px 0;">
                    <a href="{n.link}" style="color:#e2e8f0; text-decoration:none; font-size:12px; font-weight:500;">{n.title}</a>
                    <div style="color:#64748b; font-size:10px; margin-top:4px;">{n.published[:16]}</div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    elif menu == "Supply Chain":
        st.markdown("### ⛓️ SUPPLY CHAIN ANALYSIS")
        s1, s2 = st.columns(2)
        with s1:
            st.markdown("<div class='g-card'><div class='g-card-header'>KEY SUPPLIERS</div>", unsafe_allow_html=True)
            # Fake data pour démo
            st.dataframe(pd.DataFrame({
                "Company": ["TSMC", "Foxconn", "Samsung", "LG Display"],
                "Reliance": ["High", "High", "Medium", "Low"],
                "Risk Score": [12, 45, 23, 10]
            }), use_container_width=True, hide_index=True)
            st.markdown("</div>", unsafe_allow_html=True)
        with s2:
            st.markdown("<div class='g-card'><div class='g-card-header'>REVENUE EXPOSURE BY REGION</div>", unsafe_allow_html=True)
            # Fake chart
            exp_data = pd.DataFrame({"Region": ["Americas", "Europe", "China", "APAC"], "Revenue": [45, 25, 20, 10]})
            st.bar_chart(exp_data.set_index("Region"))
            st.markdown("</div>", unsafe_allow_html=True)

    elif menu == "Financials":
        st.markdown("### 📊 FINANCIAL STATEMENTS")
        # Utilisation de st.dataframe avec column_config pour un look pro
        fin_data = pd.DataFrame({
            "Metric": ["Total Revenue", "Gross Profit", "Operating Income", "Net Income"],
            "2023": [383000, 170000, 114000, 96000],
            "2022": [394000, 170000, 119000, 99000],
            "YoY Growth": [-0.02, 0.00, -0.04, -0.03]
        })
        st.dataframe(
            fin_data,
            column_config={
                "YoY Growth": st.column_config.ProgressColumn(
                    "Growth Trend", format="%.2f%%", min_value=-0.1, max_value=0.1
                ),
                "2023": st.column_config.NumberColumn(format="$%d M"),
                "2022": st.column_config.NumberColumn(format="$%d M"),
            },
            use_container_width=True,
            hide_index=True
        )

    elif menu == "Macro Data":
        st.markdown("### 🌍 GLOBAL MACRO CONTEXT")
        # Grid de données macro
        mac_data = {
            "US 10Y YIELD": "4.25%",
            "VIX (FEAR)": "13.40",
            "FED RATE": "5.50%",
            "INFLATION (CPI)": "3.1%"
        }
        cols = st.columns(4)
        for i, (k, v) in enumerate(mac_data.items()):
            with cols[i]:
                st.markdown(f"""
                <div class="g-card" style="text-align:center;">
                    <div style="color:#94a3b8; font-size:12px;">{k}</div>
                    <div style="color:#fff; font-size:24px; font-weight:bold; margin-top:5px;">{v}</div>
                </div>
                """, unsafe_allow_html=True)

else:
    st.error("Ticker not found. Try NQ=F")
