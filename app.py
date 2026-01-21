import streamlit as st
import streamlit.components.v1 as components

# --- 1. CONFIGURATION DU SITE ---
st.set_page_config(
    layout="wide",
    page_title="SAM-VISION [WEB]",
    page_icon="🦅",
    initial_sidebar_state="collapsed"
)

# --- 2. CSS HACK (POUR UN LOOK APP NATIVE) ---
st.markdown("""
    <style>
    /* Supprimer les marges blanches de Streamlit */
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
        max-width: 100% !important;
    }
    
    /* Fond noir total */
    .stApp {
        background-color: #000000;
    }
    
    /* Cacher le menu Streamlit en haut à droite */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Style pour les titres de section */
    .section-header {
        color: #FF9800;
        font-family: 'Arial', sans-serif;
        font-size: 12px;
        font-weight: bold;
        margin-top: 5px;
        margin-bottom: 5px;
        border-bottom: 1px solid #333;
        padding-bottom: 2px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. WIDGETS TRADINGVIEW (DATA DIRECTE) ---

def widget_ticker_tape():
    # Bandeau défilant en haut
    html = """
    <div class="tradingview-widget-container">
      <div class="tradingview-widget-container__widget"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js" async>
      {
      "symbols": [
        {"proName": "CME_MINI:NQ1!", "title": "Nasdaq 100 Futures"},
        {"proName": "CME_MINI:ES1!", "title": "S&P 500 Futures"},
        {"proName": "BITSTAMP:BTCUSD", "title": "Bitcoin"},
        {"proName": "BLACKBULL:US100", "title": "Nasdaq 100 CFD"},
        {"proName": "OANDA:XAUUSD", "title": "Gold"}
      ],
      "showSymbolLogo": true,
      "colorTheme": "dark",
      "isTransparent": false,
      "displayMode": "adaptive",
      "locale": "en"
    }
      </script>
    </div>
    """
    components.html(html, height=46)

def widget_main_chart():
    # Le vrai graphique pro (NQ Futures)
    html = """
    <div class="tradingview-widget-container" style="height:100%;width:100%">
      <div class="tradingview-widget-container__widget" style="height:calc(100% - 32px);width:100%"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js" async>
      {
      "autosize": true,
      "symbol": "CME_MINI:NQ1!",
      "interval": "5",
      "timezone": "Etc/UTC",
      "theme": "dark",
      "style": "1",
      "locale": "en",
      "enable_publishing": false,
      "hide_side_toolbar": false,
      "allow_symbol_change": true,
      "details": true,
      "hotlist": true,
      "calendar": false,
      "studies": [
        "STD;RSI",
        "STD;MACD",
        "STD;Bollinger_Bands"
      ],
      "support_host": "https://www.tradingview.com"
    }
      </script>
    </div>
    """
    components.html(html, height=650)

def widget_technical_guage():
    # Jauge Achat/Vente
    html = """
    <div class="tradingview-widget-container">
      <div class="tradingview-widget-container__widget"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-technical-analysis.js" async>
      {
      "interval": "15m",
      "width": "100%",
      "isTransparent": false,
      "height": "100%",
      "symbol": "CME_MINI:NQ1!",
      "showIntervalTabs": true,
      "displayMode": "single",
      "locale": "en",
      "colorTheme": "dark"
    }
      </script>
    </div>
    """
    components.html(html, height=350)

def widget_news():
    # Flux news en temps réel
    html = """
    <div class="tradingview-widget-container">
      <div class="tradingview-widget-container__widget"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-timeline.js" async>
      {
      "feedMode": "symbol",
      "symbol": "CME_MINI:NQ1!",
      "colorTheme": "dark",
      "isTransparent": false,
      "displayMode": "compact",
      "width": "100%",
      "height": "100%",
      "locale": "en"
    }
      </script>
    </div>
    """
    components.html(html, height=350)

def widget_economic_calendar():
    # Calendrier Macro
    html = """
    <div class="tradingview-widget-container">
      <div class="tradingview-widget-container__widget"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-events.js" async>
      {
      "colorTheme": "dark",
      "isTransparent": false,
      "width": "100%",
      "height": "100%",
      "locale": "en",
      "importanceFilter": "-1,0,1",
      "currencyFilter": "USD"
    }
      </script>
    </div>
    """
    components.html(html, height=300)

# --- 4. MISE EN PAGE DU DASHBOARD ---

# Bandeau Haut
widget_ticker_tape()

# Layout Principal : Chart (75%) | Sidebar (25%)
col_main, col_side = st.columns([3, 1])

with col_main:
    # Le Chart prend toute la place
    widget_main_chart()

with col_side:
    # Sidebar droite avec les widgets empilés
    st.markdown('<div class="section-header">MARKET SENTIMENT (15M)</div>', unsafe_allow_html=True)
    widget_technical_guage()
    
    st.markdown('<div class="section-header">LIVE NEWSFLOW</div>', unsafe_allow_html=True)
    widget_news()
    
    st.markdown('<div class="section-header">MACRO CALENDAR (USD)</div>', unsafe_allow_html=True)
    widget_economic_calendar()

# Footer discret
st.markdown("""
<div style="text-align:center; font-size:10px; color:#444; margin-top:10px;">
    SAM-VISION WEB TERMINAL | LIVE DATA VIA TRADINGVIEW SOCKETS | NO LATENCY
</div>
""", unsafe_allow_html=True)
