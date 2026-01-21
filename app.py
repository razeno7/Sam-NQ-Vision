import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import feedparser
from datetime import datetime

# --- 1. CONFIGURATION DE LA PAGE (PLEIN ÉCRAN) ---
st.set_page_config(
    layout="wide",
    page_title="NQ TERMINAL // BBG STYLE",
    page_icon="💹",
    initial_sidebar_state="collapsed"
)

# --- 2. CSS "BLOOMBERG BLACK" ---
# Ce bloc CSS force l'interface en mode sombre total, style terminal professionnel
st.markdown("""
    <style>
    /* Reset Global */
    .stApp {background-color: #000000;}
    
    /* Typographie */
    * {font-family: 'Consolas', 'Courier New', monospace !important;}
    
    /* Couleurs du texte */
    .text-up {color: #00FF00 !important;}
    .text-down {color: #FF0000 !important;}
    .text-neutral {color: #FF9800 !important;}
    .text-muted {color: #666666 !important;}
    
    /* Structure des blocs (Cards) */
    div.css-1r6slb0, div.stVerticalBlock {gap: 0rem;}
    
    /* Masquer les éléments Streamlit inutiles */
    header, footer, #MainMenu {visibility: hidden;}
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    
    /* Style des métriques */
    div[data-testid="stMetricValue"] {font-size: 20px !important; color: #e0e0e0;}
    div[data-testid="stMetricLabel"] {font-size: 11px !important; color: #888;}
    
    /* Bordures fines style terminal */
    .terminal-card {
        border: 1px solid #333;
        background-color: #050505;
        padding: 10px;
        margin-bottom: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. FONCTIONS DATA (MOTEUR) ---

@st.cache_data(ttl=60) # Mise en cache 60s pour éviter les blocages API
def get_market_data():
    # On récupère NQ=F (Futures), ^VIX (Volatilité), ^TNX (Taux 10 ans), BTC-USD
    tickers = ["NQ=F", "QQQ", "^VIX", "^TNX", "BTC-USD"]
    data = yf.download(tickers, period="5d", interval="15m", group_by='ticker', progress=False)
    return data

def get_news_feed():
    # Flux RSS Yahoo Finance (Gratuit et Temps réel)
    try:
        feed = feedparser.parse("https://finance.yahoo.com/news/rssindex")
        return feed.entries[:8]
    except:
        return []

def calculate_technicals(df):
    # Calcul simple de SMA (Moyennes Mobiles)
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    return df

# --- 4. LOGIQUE PRINCIPALE ---

# Chargement des données
data = get_market_data()

# Gestion du fallback : Si NQ=F (Futures) est vide (marché fermé/payant), on utilise QQQ (ETF)
if 'NQ=F' in data and not data['NQ=F']['Close'].dropna().empty:
    main_df = data['NQ=F'].dropna()
    ticker_name = "NQ=F (CME FUTURES)"
else:
    main_df = data['QQQ'].dropna()
    ticker_name = "QQQ (PROXY ETF)"

# Calculs techniques sur le NQ
main_df = calculate_technicals(main_df)

# Données Macro pour le bandeau de gauche
try:
    vix = data['^VIX']['Close'].iloc[-1]
    tnx = data['^TNX']['Close'].iloc[-1]
    btc = data['BTC-USD']['Close'].iloc[-1]
except:
    vix, tnx, btc = 0, 0, 0

# --- 5. INTERFACE UTILISATEUR (LAYOUT) ---

# HEADER : Ticker principal
last_price = main_df['Close'].iloc[-1]
prev_price = main_df['Open'].iloc[0] # Open du début de la période
change = last_price - prev_price
pct_change = (change / prev_price) * 100
color_header = "#00FF00" if change >= 0 else "#FF0000"

st.markdown(f"""
    <div style="border-bottom: 1px solid #333; padding-bottom: 10px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center;">
        <div>
            <span style="font-size: 24px; font-weight: bold; color: #FF9800;">{ticker_name}</span>
            <span style="color: #666; font-size: 12px; margin-left: 10px;">REAL-TIME DATA FEED</span>
        </div>
        <div style="text-align: right;">
            <span style="font-size: 30px; font-weight: bold; color: {color_header};">{last_price:,.2f}</span>
            <span style="font-size: 18px; color: {color_header}; margin-left: 15px;">{change:+.2f} ({pct_change:+.2f}%)</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# GRID : 3 Colonnes (Macro | Chart | News)
col1, col2, col3 = st.columns([1, 3, 1])

# COLONNE 1 : MACRO & CONTEXTE
with col1:
    st.markdown("### 📊 MACRO")
    
    # VIX (Fear Index)
    vix_color = "text-down" if vix < 20 else "text-neutral" if vix < 30 else "text-up" # Rouge si peur (VIX haut)
    st.markdown(f"""
    <div class="terminal-card">
        <span class="text-muted">VIX (VOLATILITY)</span><br>
        <span style="font-size: 22px; font-weight: bold;" class="{vix_color}">{vix:.2f}</span>
    </div>
    """, unsafe_allow_html=True)
    
    # US 10Y (Yield)
    st.markdown(f"""
    <div class="terminal-card">
        <span class="text-muted">US 10Y BOND</span><br>
        <span style="font-size: 22px; color: #e0e0e0;">{tnx:.3f}%</span>
    </div>
    """, unsafe_allow_html=True)
    
    # BITCOIN (Risk-On Asset)
    btc_color = "text-up" if data['BTC-USD']['Close'].iloc[-1] > data['BTC-USD']['Open'].iloc[0] else "text-down"
    st.markdown(f"""
    <div class="terminal-card">
        <span class="text-muted">BITCOIN (RISK)</span><br>
        <span style="font-size: 22px;" class="{btc_color}">${btc:,.0f}</span>
    </div>
    """, unsafe_allow_html=True)

# COLONNE 2 : LE GRAPHIQUE CENTRAL
with col2:
    # Création du Chart avec Plotly
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.03, subplot_titles=('Price Action', 'Volume'),
                        row_heights=[0.7, 0.3])

    # Chandeliers
    fig.add_trace(go.Candlestick(
        x=main_df.index,
        open=main_df['Open'], high=main_df['High'], low=main_df['Low'], close=main_df['Close'],
        name='Price',
        increasing_line_color='#00FF00', decreasing_line_color='#FF0000'
    ), row=1, col=1)

    # Moyennes Mobiles
    fig.add_trace(go.Scatter(x=main_df.index, y=main_df['SMA_20'], line=dict(color='orange', width=1), name='SMA 20'), row=1, col=1)
    fig.add_trace(go.Scatter(x=main_df.index, y=main_df['SMA_50'], line=dict(color='cyan', width=1), name='SMA 50'), row=1, col=1)

    # Volume
    colors = ['#00FF00' if row['Open'] - row['Close'] >= 0 else '#FF0000' for index, row in main_df.iterrows()]
    fig.add_trace(go.Bar(x=main_df.index, y=main_df['Volume'], marker_color=colors, name='Volume'), row=2, col=1)

    # Styling "Bloomberg Dark"
    fig.update_layout(
        height=600,
        margin=dict(l=0, r=0, t=20, b=0),
        plot_bgcolor='#000000',
        paper_bgcolor='#000000',
        xaxis_rangeslider_visible=False,
        showlegend=False,
        font=dict(color='#888', family="Courier New")
    )
    
    # Axes
    fig.update_xaxes(showgrid=False, gridcolor='#222')
    fig.update_yaxes(showgrid=True, gridcolor='#222', side='right') # Prix à droite comme les pros

    st.plotly_chart(fig, use_container_width=True)

# COLONNE 3 : NEWS & ORDER BOOK SIMULÉ
with col3:
    st.markdown("### 📰 NEWS WIRE")
    news = get_news_feed()
    
    if news:
        for item in news:
            # Formatage de l'heure
            pub_date = item.get('published', '')[:16] # On coupe pour gagner de la place
            st.markdown(f"""
            <div style="border-bottom: 1px solid #333; padding: 8px 0;">
                <span style="color: #FF9800; font-size: 10px;">[{pub_date}]</span><br>
                <a href="{item.link}" target="_blank" style="color: #ddd; text-decoration: none; font-size: 12px; font-weight: bold;">
                    {item.title}
                </a>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("News feed loading...")

    st.markdown("---")
    st.markdown("### 📉 DEPTH (Sim)")
    # Simulation d'un carnet d'ordre pour l'effet visuel "Pro"
    # Note: L2 Data est payante, on simule ici la structure autour du prix actuel
    price_step = 0.25
    depth_data = {
        "Bid Size": [12, 45, 10, 5],
        "Bid": [last_price - i*price_step for i in range(1, 5)],
        "Ask": [last_price + i*price_step for i in range(1, 5)],
        "Ask Size": [8, 22, 15, 30]
    }
    df_depth = pd.DataFrame(depth_data)
    st.dataframe(df_depth, hide_index=True, use_container_width=True)

# Bouton de rafraîchissement manuel
if st.button('REFRESH TERMINAL ⟳'):
    st.rerun()
