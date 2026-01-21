import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import feedparser
from datetime import datetime, timedelta

# --- 1. CONFIGURATION "BLACK BOX" ---
st.set_page_config(layout="wide", page_title="NQ QUANT TERMINAL", page_icon="💠", initial_sidebar_state="collapsed")

# --- 2. CSS "INSTITUTIONAL GRADE" ---
st.markdown("""
    <style>
    /* RESET & FONTS */
    .stApp {background-color: #000000 !important;}
    .block-container {padding: 0px 5px !important; max-width: 100% !important;}
    * {font-family: 'Roboto Mono', 'Consolas', monospace !important; letter-spacing: -0.5px; font-size: 12px;}
    
    /* COULEURS SEMANTIQUES */
    .c-up {color: #00FF00;}
    .c-dn {color: #FF0000;}
    .c-nu {color: #FF9800;}
    .c-gy {color: #666;}
    .c-wh {color: #EEE;}
    
    /* TABLEAUX DATA-DENSE */
    table {width: 100%; border-collapse: collapse; font-size: 10px;}
    th {text-align: left; color: #FF9800; border-bottom: 1px solid #333; padding: 3px;}
    td {padding: 2px 3px; border-bottom: 1px solid #111; color: #DDD;}
    
    /* BOITES DE CONTENU */
    .quant-box {
        border: 1px solid #222;
        background: #080808;
        padding: 5px;
        margin-bottom: 5px;
    }
    .box-title {
        color: #FF9800; 
        font-weight: bold; 
        font-size: 11px; 
        text-transform: uppercase; 
        border-bottom: 1px solid #333; 
        margin-bottom: 5px;
        display: flex;
        justify-content: space-between;
    }
    
    /* HIDE STREAMLIT UI */
    header, footer, #MainMenu {display: none !important;}
    </style>
""", unsafe_allow_html=True)

# --- 3. QUANT ENGINE (CALCULS AVANCÉS) ---

@st.cache_data(ttl=60)
def fetch_and_process_data():
    # On charge plus d'historique pour les corrélations (60 jours)
    tickers = ["NQ=F", "QQQ", "^VIX", "^TNX", "BTC-USD", "GC=F", "DX-Y.NYB", "NVDA", "AAPL"]
    try:
        data = yf.download(tickers, period="60d", interval="15m", group_by='ticker', progress=False)
        
        # Selection NQ
        if 'NQ=F' in data and not data['NQ=F']['Close'].dropna().empty:
            main_df = data['NQ=F'].dropna()
            name = "NQ=F (FUTURES)"
        else:
            main_df = data['QQQ'].dropna()
            name = "QQQ (PROXY)"
            
        return data, main_df, name
    except:
        return None, pd.DataFrame(), "OFFLINE"

def calculate_quant_metrics(df, full_data):
    if df.empty: return pd.DataFrame(), {}

    # 1. Signaux Techniques (Dernière bougie)
    # On travaille sur une copie pour éviter les warnings
    close = df['Close'].copy()
    high = df['High'].copy()
    low = df['Low'].copy()
    
    # RSI
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    # MACD
    exp1 = close.ewm(span=12, adjust=False).mean()
    exp2 = close.ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    
    # Bollinger
    sma20 = close.rolling(20).mean()
    std20 = close.rolling(20).std()
    upper = sma20 + (2 * std20)
    lower = sma20 - (2 * std20)
    
    # ATR (Volatilité en points)
    high_low = high - low
    atr = high_low.rolling(14).mean()
    
    # Z-Score (Deviation par rapport à la moyenne)
    z_score = (close - sma20) / std20
    
    # 2. Corrélations (Rolling 30 periodes)
    # On aligne les données
    corrs = {}
    ref_ret = close.pct_change()
    
    for t in ["^VIX", "^TNX", "BTC-USD", "DX-Y.NYB"]:
        try:
            if t in full_data:
                asset_ret = full_data[t]['Close'].pct_change()
                # Correlation glissante
                val = ref_ret.rolling(30).corr(asset_ret).iloc[-1]
                corrs[t] = 0.0 if np.isnan(val) else val
            else:
                corrs[t] = 0.0
        except:
            corrs[t] = 0.0

    # Assemblage DataFrame Technique
    df_tech = pd.DataFrame({
        'Close': close,
        'RSI': rsi,
        'MACD': macd,
        'Signal': signal,
        'Upper': upper,
        'Lower': lower,
        'SMA20': sma20,
        'SMA50': close.rolling(50).mean(),
        'SMA200': close.rolling(200).mean(),
        'ATR': atr,
        'ZScore': z_score
    })
    
    return df_tech, corrs

def generate_signals(last_row):
    signals = []
    
    # RSI Logic
    if last_row['RSI'] > 70: signals.append(("RSI", "OVERBOUGHT", "SELL"))
    elif last_row['RSI'] < 30: signals.append(("RSI", "OVERSOLD", "BUY"))
    else: signals.append(("RSI", "NEUTRAL", "-"))
    
    # MACD Logic
    if last_row['MACD'] > last_row['Signal']: signals.append(("MACD", "CROSS UP", "BULLISH"))
    else: signals.append(("MACD", "CROSS DOWN", "BEARISH"))
    
    # Trend Logic
    if last_row['Close'] > last_row['SMA50']: signals.append(("TREND", "ABOVE SMA50", "BULLISH"))
    else: signals.append(("TREND", "BELOW SMA50", "BEARISH"))
    
    # Bollinger Logic
    if last_row['Close'] > last_row['Upper']: signals.append(("VOLTY", "BREAKOUT UP", "STRONG BUY"))
    elif last_row['Close'] < last_row['Lower']: signals.append(("VOLTY", "BREAKOUT DN", "STRONG SELL"))
    
    return signals

def get_rss():
    try:
        return feedparser.parse("https://finance.yahoo.com/news/rssindex").entries[:8]
    except: return []

# --- 4. RENDER UI ---

data_pack, main_df, sym_name = fetch_and_process_data()

if not main_df.empty:
    tech_df, correlations = calculate_quant_metrics(main_df, data_pack)
    
    # Si calcul échoué (trop peu de data), on évite le crash
    if tech_df.empty or len(tech_df) < 50:
         st.error("NOT ENOUGH DATA FOR QUANT METRICS. WAITING FOR MARKET...")
         st.stop()

    current = tech_df.iloc[-1]
    
    # --- HEADER ---
    last_p = current['Close']
    chg = last_p - main_df['Close'].iloc[-2]
    pct = (chg / main_df['Close'].iloc[-2]) * 100
    col_h = "#0F0" if chg >= 0 else "#F00"
    
    st.markdown(f"""
    <div style='background:#111; padding:5px 10px; display:flex; justify-content:space-between; border-bottom:2px solid #333'>
        <div>
            <span style='color:#FF9800; font-weight:bold; font-size:16px'>SAM-NQ-VISION</span>
            <span style='color:#666; font-size:12px'> | QUANT TERMINAL | {sym_name}</span>
        </div>
        <div style='text-align:right'>
            <span style='color:{col_h}; font-size:20px; font-weight:bold'>{last_p:,.2f}</span>
            <span style='color:{col_h}; font-size:14px; margin-left:10px'>{chg:+.2f} ({pct:+.2f}%)</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # --- LAYOUT GRID ---
    c1, c2, c3 = st.columns([1.5, 4, 1.5], gap="small")
    
    # === COLONNE GAUCHE : QUANT METRICS ===
    with c1:
        st.markdown("<div style='height:5px'></div>", unsafe_allow_html=True)
        
        # 1. CORRELATION MATRIX
        st.markdown(f"""
        <div class='quant-box'>
            <div class='box-title'><span>CROSS-ASSET CORRELATION (30D)</span></div>
            <table>
                <tr><th>ASSET</th><th>CORR. COEFF</th><th>IMPLICATION</th></tr>
                <tr><td>VIX (FEAR)</td><td style='color:{"#F00" if correlations["^VIX"] > 0 else "#0F0"}'>{correlations["^VIX"]:.2f}</td><td>HEDGE</td></tr>
                <tr><td>TNX (RATES)</td><td style='color:{"#F00" if correlations["^TNX"] > 0 else "#0F0"}'>{correlations["^TNX"]:.2f}</td><td>MACRO</td></tr>
                <tr><td>BITCOIN</td><td style='color:#FF9800'>{correlations["BTC-USD"]:.2f}</td><td>RISK-ON</td></tr>
                <tr><td>DOLLAR (DXY)</td><td style='color:{"#F00" if correlations["DX-Y.NYB"] > 0 else "#0F0"}'>{correlations["DX-Y.NYB"]:.2f}</td><td>FX</td></tr>
            </table>
        </div>
        """, unsafe_allow_html=True)
        
        # 2. VOLATILITY & RISK
        st.markdown(f"""
        <div class='quant-box'>
            <div class='box-title'><span>RISK METRICS</span></div>
            <table>
                <tr><td>ATR (14)</td><td style='text-align:right; color:#FFF'>{current['ATR']:.2f} pts</td></tr>
                <tr><td>Z-SCORE (20)</td><td style='text-align:right; color:{"#F00" if abs(current['ZScore']) > 2 else "#FFF"}'>{current['ZScore']:.2f} σ</td></tr>
                <tr><td>RSI (14)</td><td style='text-align:right; color:#FFF'>{current['RSI']:.1f}</td></tr>
                <tr><td>DIST TO SMA200</td><td style='text-align:right; color:{"#0F0" if current['Close'] > current['SMA200'] else "#F00"}'>{(current['Close'] - current['SMA200']):.1f}</td></tr>
            </table>
        </div>
        """, unsafe_allow_html=True)
        
        # 3. GLOBAL MACRO (Mini)
        try:
            vix_p = data_pack['^VIX']['Close'].iloc[-1]
            tnx_p = data_pack['^TNX']['Close'].iloc[-1]
            btc_p = data_pack['BTC-USD']['Close'].iloc[-1]
            st.markdown(f"""
            <div class='quant-box'>
                <div class='box-title'><span>MACRO CONTEXT</span></div>
                <table>
                    <tr><td>VIX</td><td style='text-align:right; color:{"#F00" if vix_p > 20 else "#0F0"}'>{vix_p:.2f}</td></tr>
                    <tr><td>US10Y</td><td style='text-align:right'>{tnx_p:.2f}%</td></tr>
                    <tr><td>BTC</td><td style='text-align:right; color:#FF9800'>${btc_p:,.0f}</td></tr>
                </table>
            </div>
            """, unsafe_allow_html=True)
        except: pass

    # === COLONNE CENTRE : CHART AVANCÉ ===
    with c2:
        # Chart Logic
        fig = make_subplots(rows=3, cols=1, shared_xaxes=True, 
                            row_heights=[0.6, 0.2, 0.2], vertical_spacing=0.01)
        
        # Main Price
        fig.add_trace(go.Candlestick(
            x=main_df.index, open=main_df['Open'], high=main_df['High'], low=main_df['Low'], close=main_df['Close'],
            name="Price", increasing_line_color='#00FF00', decreasing_line_color='#FF0000', showlegend=False
        ), row=1, col=1)
        
        # Bollinger Bands & SMA
        fig.add_trace(go.Scatter(x=main_df.index, y=tech_df['Upper'], line=dict(color='gray', width=1, dash='dot'), showlegend=False), row=1, col=1)
        fig.add_trace(go.Scatter(x=main_df.index, y=tech_df['Lower'], line=dict(color='gray', width=1, dash='dot'), fill='tonexty', fillcolor='rgba(255,255,255,0.02)', showlegend=False), row=1, col=1)
        fig.add_trace(go.Scatter(x=main_df.index, y=tech_df['SMA50'], line=dict(color='#FF9800', width=1), name="SMA50", showlegend=False), row=1, col=1)

        # Subplot 1: MACD
        fig.add_trace(go.Scatter(x=main_df.index, y=tech_df['MACD'], line=dict(color='#00E5FF', width=1), name="MACD", showlegend=False), row=2, col=1)
        fig.add_trace(go.Scatter(x=main_df.index, y=tech_df['Signal'], line=dict(color='#FF5252', width=1), name="Signal", showlegend=False), row=2, col=1)
        fig.add_bar(x=main_df.index, y=(tech_df['MACD']-tech_df['Signal']), marker_color='gray', name="Hist", showlegend=False, row=2, col=1)

        # Subplot 2: Volume
        colors_vol = ['#00FF00' if c >= o else '#FF0000' for c, o in zip(main_df['Close'], main_df['Open'])]
        fig.add_trace(go.Bar(x=main_df.index, y=main_df['Volume'], marker_color=colors_vol, showlegend=False), row=3, col=1)
        
        # Gap Fix (Weekends)
        fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])], gridcolor='#222')
        
        fig.update_layout(
            height=650, margin=dict(l=0, r=50, t=10, b=0),
            template="plotly_dark", paper_bgcolor="#000", plot_bgcolor="#000",
            xaxis_rangeslider_visible=False
        )
        fig.update_yaxes(side="right", gridcolor="#222")
        
        st.plotly_chart(fig, use_container_width=True)

    # === COLONNE DROITE : SIGNAUX & NEWS ===
    with c3:
        st.markdown("<div style='height:5px'></div>", unsafe_allow_html=True)
        
        # 1. TECHNICAL SIGNALS BOARD
        signals = generate_signals(current)
        sig_html = "<div class='quant-box'><div class='box-title'><span>ALGO SIGNALS (15M)</span></div><table>"
        for s in signals:
            col = "#0F0" if s[2] in ["BUY", "BULLISH", "STRONG BUY"] else "#F00" if s[2] in ["SELL", "BEARISH", "STRONG SELL"] else "#AAA"
            sig_html += f"<tr><td>{s[0]}</td><td>{s[1]}</td><td style='color:{col}; font-weight:bold'>{s[2]}</td></tr>"
        sig_html += "</table></div>"
        st.markdown(sig_html, unsafe_allow_html=True)

        # 2. SENTIMENT GAUGE (Simulé via RSI + VIX)
        sent_score = 50 - (correlations["^VIX"] * 20) + (1 if current['RSI'] > 50 else -1) * 10
        sent_score = max(0, min(100, sent_score))
        sent_txt = "GREED" if sent_score > 60 else "FEAR" if sent_score < 40 else "NEUTRAL"
        sent_col = "#0F0" if sent_score > 60 else "#F00" if sent_score < 40 else "#FA0"
        
        st.markdown(f"""
        <div class='quant-box' style='text-align:center'>
            <div class='box-title'><span>MARKET MOOD</span></div>
            <div style='font-size:22px; font-weight:bold; color:{sent_col}'>{sent_txt}</div>
            <div style='font-size:10px; color:#666'>SCORE: {sent_score:.0f}/100</div>
            <div style='width:100%; height:4px; background:#333; margin-top:5px'>
                <div style='width:{sent_score}%; height:100%; background:{sent_col}'></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 3. NEWS WIRE
        st.markdown(f"<div class='quant-box'><div class='box-title'><span>NEWS WIRE</span></div>", unsafe_allow_html=True)
        news = get_rss()
        for n in news[:6]:
             st.markdown(f"""
             <div style='border-bottom:1px solid #222; padding:3px 0; margin-bottom:3px'>
                <a href='{n.link}' target='_blank' style='color:#DDD; text-decoration:none; font-size:10px; line-height:1.1; display:block; hover:color:#F90'>{n.title}</a>
                <span style='color:#555; font-size:9px'>{n.published[17:22] if 'published' in n else ''}</span>
             </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Footer
    if st.button("RUN QUANT DIAGNOSTIC"):
        st.cache_data.clear()
        st.rerun()

else:
    st.error("DATA FEED DISCONNECTED. PLEASE REFRESH.")
