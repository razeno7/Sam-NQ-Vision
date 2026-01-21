import streamlit as st
import streamlit.components.v1 as components

# --- 1. CONFIGURATION DU TERMINAL ---
st.set_page_config(
    layout="wide",
    page_title="NQ SAM VISION",
    page_icon="🦅",
    initial_sidebar_state="collapsed"
)

# --- 2. CSS "BLOOMBERG BLACK" ---
st.markdown("""
    <style>
    /* RESET TOTAL */
    .stApp {background-color: #000000;}
    .block-container {padding: 0px 10px !important; margin: 0px !important; max-width: 100% !important;}
    
    /* SUPPRESSION DE L'INTERFACE STREAMLIT */
    header, footer, #MainMenu {display: none !important;}
    div[data-testid="stVerticalBlock"] {gap: 5px;}
    
    /* HEADER CUSTOM */
    .bb-header {
        background-color: #111;
        border-bottom: 2px solid #FF9800;
        color: #FF9800;
        padding: 8px 15px;
        font-family: 'Courier New', monospace;
        font-weight: bold;
        font-size: 18px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 5px;
    }
    .bb-status { font-size: 10px; color: #00FF00; letter-spacing: 1px; }
    
    /* CONTAINERS WIDGETS */
    .widget-box { border: 1px solid #333; background: #000; height: 100%; }
    </style>
""", unsafe_allow_html=True)

# --- 3. WIDGETS INSTITUTIONNELS (HTML/JS) ---

def w_ticker_tape():
    # Bandeau défilant (Indices + Commodities)
    code = """
    <div class="tradingview-widget-container">
      <div class="tradingview-widget-container__widget"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js" async>
      {
      "symbols": [
        {"proName": "CME_MINI:NQ1!", "title": "NQ FUTURES"},
        {"proName": "CME_MINI:ES1!", "title": "ES FUTURES"},
        {"proName": "TVC:VIX", "title": "VIX"},
        {"proName": "TVC:DXY", "title": "DOLLAR"},
        {"proName": "US10Y", "title": "US 10Y"},
        {"proName": "BITSTAMP:BTCUSD", "title": "BITCOIN"}
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
    components.html(code, height=46)

def w_chart():
    # Graphique Avancé (Le coeur du terminal)
    code = """
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
      "hotlist": false,
      "calendar": false,
      "studies": [
        "STD;RSI",
        "STD;VWAP",
        "STD;Bollinger_Bands"
      ],
      "support_host": "https://www.tradingview.com"
    }
      </script>
    </div>
    """
    components.html(code, height=700)

def w_sentiment():
    # Jauge Technique (Sentiment Temps Réel)
    code = """
    <div class="tradingview-widget-container">
      <div class="tradingview-widget-container__widget"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-technical-analysis.js" async>
      {
      "interval": "15m",
      "width": "100%",
      "isTransparent": false,
      "height": "350",
      "symbol": "CME_MINI:NQ1!",
      "showIntervalTabs": true,
      "displayMode": "single",
      "locale": "en",
      "colorTheme": "dark"
    }
      </script>
    </div>
    """
    components.html(code, height=350)

def w_news():
    # Flux d'actualités filtré sur le Nasdaq
    code = """
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
      "height": "350",
      "locale": "en"
    }
      </script>
    </div>
    """
    components.html(code, height=350)

def w_calendar():
    # Calendrier Eco (Vital pour le NQ)
    code = """
    <div class="tradingview-widget-container">
      <div class="tradingview-widget-container__widget"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-events.js" async>
      {
      "colorTheme": "dark",
      "isTransparent": false,
      "width": "100%",
      "height": "300",
      "locale": "en",
      "importanceFilter": "0,1",
      "currencyFilter": "USD"
    }
      </script>
    </div>
    """
    components.html(code, height=300)

def w_watchlist():
    # Liste de surveillance Tech
    code = """
    <div class="tradingview-widget-container">
      <div class="tradingview-widget-container__widget"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-market-overview.js" async>
      {
      "colorTheme": "dark",
      "dateRange": "12M",
      "showChart": false,
      "locale": "en",
      "largeChartUrl": "",
      "isTransparent": false,
      "showSymbolLogo": true,
      "showFloatingTooltip": false,
      "width": "100%",
      "height": "400",
      "tabs": [
        {
          "title": "MAG 7",
          "symbols": [
            { "s": "NASDAQ:NVDA" },
            { "s": "NASDAQ:AAPL" },
            { "s": "NASDAQ:MSFT" },
            { "s": "NASDAQ:AMZN" },
            { "s": "NASDAQ:TSLA" },
            { "s": "NASDAQ:META" },
            { "s": "NASDAQ:GOOGL" }
          ]
        },
        {
          "title": "MACRO",
          "symbols": [
             { "s": "TVC:DXY" },
             { "s": "TVC:US10Y" },
             { "s": "CME_MINI:ES1!" }
          ]
        }
      ]
    }
      </script>
    </div>
    """
    components.html(code, height=400)

# --- 4. MISE EN PAGE DU TERMINAL ---

# A. Header & Tape
st.markdown("""
<div class="bb-header">
    <div>NQ SAM VISION <span style="color:#666; font-size:12px;">// PROFESSIONAL TERMINAL</span></div>
    <div class="bb-status">● SYSTEM ONLINE</div>
</div>
""", unsafe_allow_html=True)

w_ticker_tape()

# B. Main Grid (Layout 3 colonnes type Bloomberg : 20% | 60% | 20%)
c_left, c_center, c_right = st.columns([20, 55, 25], gap="small")

with c_left:
    st.markdown('<div class="widget-box">', unsafe_allow_html=True)
    # 1. Sentiment Gauge
    components.html("<div style='color:#FF9800; font-family:monospace; font-size:12px; font-weight:bold; padding:5px;'>MARKET MOOD (15M)</div>", height=25)
    w_sentiment()
    
    # 2. Watchlist Tech
    components.html("<div style='color:#FF9800; font-family:monospace; font-size:12px; font-weight:bold; padding:5px; border-top:1px solid #333'>SECTOR: TECH</div>", height=30)
    w_watchlist()
    st.markdown('</div>', unsafe_allow_html=True)

with c_center:
    st.markdown('<div class="widget-box">', unsafe_allow_html=True)
    # 3. Main Chart
    w_chart()
    st.markdown('</div>', unsafe_allow_html=True)

with c_right:
    st.markdown('<div class="widget-box">', unsafe_allow_html=True)
    # 4. News Feed
    components.html("<div style='color:#FF9800; font-family:monospace; font-size:12px; font-weight:bold; padding:5px;'>NEWS WIRE</div>", height=25)
    w_news()
    
    # 5. Economic Calendar
    components.html("<div style='color:#FF9800; font-family:monospace; font-size:12px; font-weight:bold; padding:5px; border-top:1px solid #333'>MACRO CALENDAR</div>", height=30)
    w_calendar()
    st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("""
<div style='text-align:center; color:#333; font-family:monospace; font-size:10px; margin-top:10px;'>
    CONNECTED TO CME GLOBEX DATA FEED | LATENCY: <10ms | SESSION ID: 882-Alpha
</div>
""", unsafe_allow_html=True)
