import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

# --- BLOOMBERG TERMINAL V5 "ALPHA" ---
st.set_page_config(page_title="BLOOMBERG ALPHA", layout="wide", initial_sidebar_state="collapsed")

# AUTHENTIC BLOOMBERG CSS INJECTION
st.markdown("""
<style>
    .stApp { background-color: #000000; color: #d1d1d1; font-family: 'Courier New', monospace; }
    [data-testid="stHeader"] { display: none; }
    .main .block-container { padding: 0.2rem !important; max-width: 100% !important; }
    
    /* Density Overrides */
    div.stButton > button { 
        background-color: #111; border: 1px solid #333; color: #00f0ff; 
        font-size: 10px; padding: 2px 10px; border-radius: 0;
    }
    div.stTabs [data-baseweb="tab-list"] { gap: 1px; background-color: #222; }
    div.stTabs [data-baseweb="tab"] { 
        background-color: #111; color: #00f0ff; font-size: 10px; padding: 5px 15px; border-radius: 0;
    }
    div.stTabs [aria-selected="true"] { background-color: #00f0ff !important; color: #000 !important; }
</style>
""", unsafe_allow_html=True)

# ENGINE: SECURITY DATA
@st.cache_data(ttl=60)
def get_security_data(ticker):
    t = yf.Ticker(ticker)
    info = t.info
    hist = t.history(period="1mo")
    return info, hist

# UI: TOP COMMAND BAR
col_cmd, col_time = st.columns([6, 1])
with col_cmd:
    cmd = st.text_input("COMMAND", value="TSLA US").upper()
with col_time:
    st.markdown(f"**V5-ALPHA**\n{datetime.now().strftime('%H:%M:%S')}")

# UI: BLOOMBERG MENU TABS
tab_gp, tab_des, tab_rv, tab_ee, tab_anr = st.tabs(["GP (Graph)", "DES (Desc)", "RV (Value)", "EE (Earn)", "ANR (Recs)"])

try:
    info, hist = get_security_data(cmd.split(' ')[0])
    
    with tab_gp:
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.8, 0.2])
        fig.add_trace(go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close']), row=1, col=1)
        fig.add_trace(go.Bar(x=hist.index, y=hist['Volume'], marker_color='gray'), row=2, col=1)
        fig.update_layout(template='plotly_dark', height=600, margin=dict(l=0,r=0,t=0,b=0), xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

    with tab_des:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"### {info.get('longName', 'N/A')}")
            st.write(info.get('longBusinessSummary', 'No description available.'))
        with c2:
            st.table(pd.DataFrame({
                "Metric": ["Industry", "Sector", "CEO", "Mkt Cap"],
                "Value": [info.get('industry'), info.get('sector'), info.get('fullTimeEmployees'), f"{info.get('marketCap', 0)/1e12:.2f}T"]
            }))

    with tab_rv:
        st.caption("RELATIVE VALUATION vs INDUSTRY PEERS")
        st.dataframe(pd.DataFrame({
            "Ticker": [cmd, "AAPL", "MSFT", "GOOGL"],
            "P/E": [info.get('trailingPE'), 28.4, 34.2, 22.1],
            "Yield": [info.get('dividendYield'), 0.005, 0.007, 0]
        }), use_container_width=True)

except Exception as e:
    st.error(f"SECURITY_ERROR: {str(e)}")
