import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import pytz
import time
import yfinance as yf
from fetch import get_stock_data
from charts import plot_chart, compute_rsi
from model import predict_next_days
import numpy as np
from sklearn.ensemble import RandomForestRegressor

st.set_page_config(page_title="Alphalytics", layout="wide", page_icon="🔬")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Space Grotesk', sans-serif; }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    .main { background-color: #080f10; }
    .block-container { padding-top: 2rem !important; }

    .brand {
        font-size: 2.6rem; font-weight: 700; letter-spacing: -1.5px;
        font-family: 'Space Grotesk', sans-serif;
        background: linear-gradient(135deg, #00d4aa 0%, #0891b2 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .brand-sub { font-size: 0.8rem; color: #2a6a6a; margin-top: 6px; letter-spacing: 0.3px; }
    .market-open  { color: #00d4aa; font-size: 0.72rem; font-weight: 600; letter-spacing: 1.5px; }
    .market-closed { color: #f87171; font-size: 0.72rem; font-weight: 600; letter-spacing: 1.5px; }

    .teal-divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, #00d4aa22, transparent);
        margin: 24px 0; border: none;
    }

    .metric-card {
        background: linear-gradient(135deg, rgba(0,212,170,0.07) 0%, rgba(8,145,178,0.04) 100%);
        backdrop-filter: blur(12px);
        border-radius: 14px; padding: 18px 20px;
        border: 1px solid rgba(0,212,170,0.15);
        border-top: 1px solid rgba(0,212,170,0.25);
        box-shadow: 0 4px 24px rgba(0,0,0,0.3), 0 0 0 1px rgba(0,212,170,0.05) inset;
        transition: all 0.25s ease; position: relative; overflow: hidden;
    }
    .metric-card::before {
        content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
        background: linear-gradient(90deg, transparent, rgba(0,212,170,0.4), transparent);
    }
    .metric-card:hover {
        border-color: rgba(0,212,170,0.3);
        box-shadow: 0 8px 32px rgba(0,212,170,0.1);
        transform: translateY(-1px);
    }
    .metric-label { font-size: 0.65rem; color: #2a8a8a; margin-bottom: 10px; letter-spacing: 2px; text-transform: uppercase; }
    .metric-value { font-size: 1.4rem; font-weight: 600; color: #d4f5f0; white-space: nowrap; letter-spacing: -0.5px; }
    .metric-pos { color: #00d4aa; font-size: 0.75rem; margin-top: 6px; font-weight: 500; }
    .metric-neg { color: #f87171; font-size: 0.75rem; margin-top: 6px; font-weight: 500; }
    .metric-sub { color: #1e5a5a; font-size: 0.72rem; margin-top: 6px; }

    .section-header {
        font-size: 0.68rem; font-weight: 600; color: #00b894;
        margin: 28px 0 14px 0; text-transform: uppercase; letter-spacing: 2.5px;
        display: flex; align-items: center; gap: 10px;
    }
    .section-header::before {
        content: ''; display: inline-block; width: 5px; height: 5px;
        border-radius: 50%; background: #00d4aa; box-shadow: 0 0 8px #00d4aa99;
    }

    .profile-card {
        background: linear-gradient(135deg, rgba(0,212,170,0.05), rgba(8,145,178,0.03));
        border: 1px solid rgba(0,212,170,0.12); border-radius: 14px;
        padding: 20px 24px; display: grid;
        grid-template-columns: repeat(4, 1fr); gap: 16px;
    }
    .profile-label { font-size: 0.62rem; color: #2a7a7a; letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 4px; }
    .profile-value { font-size: 0.88rem; color: #c0e8e8; font-weight: 500; }

    .signal-buy  { background: rgba(0,212,170,0.1); border: 1px solid rgba(0,212,170,0.3); color: #00d4aa; border-radius: 8px; padding: 14px 20px; }
    .signal-sell { background: rgba(248,113,113,0.1); border: 1px solid rgba(248,113,113,0.3); color: #f87171; border-radius: 8px; padding: 14px 20px; }
    .signal-hold { background: rgba(251,191,36,0.1); border: 1px solid rgba(251,191,36,0.3); color: #fbbf24; border-radius: 8px; padding: 14px 20px; }
    .signal-label { font-size: 0.65rem; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 6px; opacity: 0.7; }
    .signal-value { font-size: 1.4rem; font-weight: 700; letter-spacing: 1px; }
    .signal-reason { font-size: 0.78rem; margin-top: 6px; opacity: 0.7; }

    .rsi-badge {
        background: rgba(0,212,170,0.04); border: 1px solid rgba(0,212,170,0.12);
        border-radius: 8px; padding: 11px 16px; font-size: 0.82rem; color: #7acfcf;
    }

    div[data-testid="stSidebar"] {
        background: #060d0e; border-right: 1px solid #0e2a2e;
    }
    .sidebar-brand {
        font-size: 1.1rem; font-weight: 700; font-family: 'Space Grotesk', sans-serif;
        background: linear-gradient(135deg, #00d4aa, #0891b2);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    div[data-testid="stSidebar"] input {
        background: #0a1a1c !important; border: 1px solid #0e2a2e !important;
        color: #d4f5f0 !important; border-radius: 8px !important;
    }

    .stButton > button {
        background: rgba(0,212,170,0.05) !important;
        color: #2a8a8a !important;
        border: 1px solid rgba(0,212,170,0.15) !important;
        border-radius: 20px !important;
        font-size: 0.72rem !important;
        font-weight: 600 !important;
        letter-spacing: 1px !important;
        padding: 6px 4px !important;
        width: 100%;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        background: rgba(0,212,170,0.12) !important;
        border-color: rgba(0,212,170,0.4) !important;
        color: #00d4aa !important;
    }

    div[data-testid="stDataFrame"] { border: 1px solid #0e2a2e !important; border-radius: 10px !important; }

    .footer {
        text-align: center; color: #0e2a2e; font-size: 0.7rem;
        margin-top: 48px; padding-top: 20px; border-top: 1px solid #0a1a1c;
    }
    .footer a { color: #1e5a5a; text-decoration: none; }
    .footer a:hover { color: #00d4aa; }
</style>
""", unsafe_allow_html=True)

# --- Cached, retry-safe yfinance info fetch ---
@st.cache_data(ttl=3600, show_spinner=False)
def get_ticker_info(ticker):
    """Fetch ticker info with caching + retries to avoid Yahoo rate limits."""
    base_info = {}
    try:
        fast = yf.Ticker(ticker).fast_info
        base_info.update({
            "currentPrice": fast.get("lastPrice"),
            "marketCap": fast.get("marketCap"),
            "currency": fast.get("currency"),
        })
    except Exception:
        pass

    for attempt in range(3):
        try:
            full_info = yf.Ticker(ticker).info
            base_info.update(full_info)
            return base_info
        except Exception:
            if attempt < 2:
                time.sleep(2 ** attempt)
    return base_info

# --- Helpers ---
def is_market_open():
    now = datetime.now(pytz.timezone('US/Eastern'))
    if now.weekday() >= 5: return False
    return now.replace(hour=9,minute=30,second=0) <= now <= now.replace(hour=16,minute=0,second=0)

def market_status_html():
    now = datetime.now(pytz.timezone('US/Eastern'))
    weekday = now.weekday()
    open_time  = now.replace(hour=9,  minute=30, second=0, microsecond=0)
    close_time = now.replace(hour=16, minute=0,  second=0, microsecond=0)
    if weekday < 5 and open_time <= now <= close_time:
        return '<span class="market-open">● MARKET OPEN</span>'
    if weekday < 5 and now < open_time:
        diff = open_time - now
    else:
        days_ahead = (7 - weekday) % 7
        if days_ahead == 0: days_ahead = 7
        next_open = (now + timedelta(days=days_ahead)).replace(hour=9, minute=30, second=0, microsecond=0)
        if weekday < 5:
            next_open = (now + timedelta(days=1)).replace(hour=9, minute=30, second=0, microsecond=0)
        diff = next_open - now
    hrs, mins = divmod(int(diff.total_seconds() // 60), 60)
    return f'<span class="market-closed">● MARKET CLOSED &nbsp;·&nbsp; Opens in {hrs}h {mins}m</span>'

def fmt_large(n):
    if n >= 1e12: return f"${n/1e12:.2f}T"
    if n >= 1e9:  return f"${n/1e9:.2f}B"
    if n >= 1e6:  return f"${n/1e6:.2f}M"
    return f"${n:,.0f}"

def get_signal(rsi, change_pct, sma20, sma50, current):
    score = 0; reasons = []
    if rsi < 35: score += 2; reasons.append("oversold RSI")
    elif rsi > 65: score -= 2; reasons.append("overbought RSI")
    if change_pct > 0: score += 1
    else: score -= 1
    if sma20 > sma50: score += 1; reasons.append("bullish SMA cross")
    else: score -= 1; reasons.append("bearish SMA cross")
    if score >= 2: return "BUY",  f"Strong signal: {', '.join(reasons)}", min(50+score*10, 90)
    elif score <= -2: return "SELL", f"Weak signal: {', '.join(reasons)}", min(50+abs(score)*10, 90)
    else: return "HOLD", "Mixed signals — no clear direction", 50+abs(score)*5

def card(col, label, value, delta="", mode="neutral"):
    cls = {"pos":"metric-pos","neg":"metric-neg","neutral":"metric-sub"}[mode]
    col.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        <div class="{cls}">{delta}</div>
    </div>""", unsafe_allow_html=True)

# --- Sidebar ---
st.sidebar.markdown('<div class="sidebar-brand">🔬 Alphalytics</div>', unsafe_allow_html=True)
st.sidebar.markdown('<hr style="border-color:#0e2a2e; margin:12px 0">', unsafe_allow_html=True)
ticker  = st.sidebar.text_input("Ticker Symbol", value="AAPL").upper()
ticker2 = st.sidebar.text_input("Compare With", value="", placeholder="e.g. TSLA").upper()
st.sidebar.markdown('<hr style="border-color:#0e2a2e; margin:12px 0">', unsafe_allow_html=True)
st.sidebar.markdown("<div style='font-size:0.63rem; color:#1a4a4a; margin-bottom:8px; letter-spacing:2px'>STOCKS</div>", unsafe_allow_html=True)
sb_cols = st.sidebar.columns(3)
for i, t in enumerate(["AAPL","TSLA","GOOGL","MSFT","AMZN","NVDA","META","NFLX","AMD"]):
    if sb_cols[i%3].button(t, key=f"sb_{t}"): ticker = t
st.sidebar.markdown('<hr style="border-color:#0e2a2e; margin:12px 0">', unsafe_allow_html=True)
st.sidebar.markdown("""
<div style='font-size:0.68rem; color:#1a4a4a; line-height:2'>
    Built by <span style='color:#2a7a7a; font-weight:600'>Anmol Rastogi</span>
</div>""", unsafe_allow_html=True)

# --- Header ---
st.markdown(f"""
<div style="text-align:center; padding: 10px 0 4px 0">
    <div class="brand">Alphalytics</div>
    <div style="font-size:0.82rem; color:#2a6a6a; margin-top:6px;">
        Real-time stock analysis · ML-powered forecasting · Built by <span style="color:#00d4aa">Anmol Rastogi</span>
    </div>
    <div style="margin-top:10px">{market_status_html()}</div>
</div>
""", unsafe_allow_html=True)
st.markdown('<hr class="teal-divider">', unsafe_allow_html=True)

# --- Quick Switch ---
qcols = st.columns(9)
for i, t in enumerate(["AAPL","TSLA","GOOGL","MSFT","AMZN","NVDA","META","NFLX","AMD"]):
    if qcols[i].button(t, key=f"main_{t}"): ticker = t
st.markdown("<br>", unsafe_allow_html=True)

# --- Timeframe ---
st.markdown('<div class="section-header">Timeframe</div>', unsafe_allow_html=True)
tf_map = {"1D":"1d","5D":"5d","1M":"1mo","3M":"3mo","6M":"6mo","1Y":"1y","5Y":"5y"}
selected_tf = st.radio("", list(tf_map.keys()), index=2, horizontal=True, label_visibility="collapsed")
period = tf_map[selected_tf]

# --- Fetch ---
with st.spinner(f"Fetching {ticker}..."):
    df   = get_stock_data(ticker, period)
    info = get_ticker_info(ticker)

if df.empty:
    st.error(f"Could not find data for '{ticker}'. Please check the ticker symbol.")
    st.stop()

current = df['Close'].iloc[-1]
prev    = df['Close'].iloc[-2]
change  = current - prev
pct     = (change / prev) * 100
volume  = df['Volume'].iloc[-1]

# --- Metrics ---
c1,c2,c3,c4,c5 = st.columns(5)
card(c1,"Last Price",  f"${current:.2f}", f"{'▲' if change>=0 else '▼'} {abs(pct):.2f}% today", "pos" if change>=0 else "neg")
card(c2,"Day Change",  f"${change:+.2f}", "vs previous close", "pos" if change>=0 else "neg")
card(c3,"Period High", f"${df['Close'].max():.2f}", "highest close")
card(c4,"Period Low",  f"${df['Close'].min():.2f}", "lowest close")
card(c5,"Volume",      f"{volume/1e6:.1f}M", "shares traded")
st.markdown("<br>", unsafe_allow_html=True)

# --- Company Profile ---
st.markdown('<div class="section-header">Company Profile</div>', unsafe_allow_html=True)
mc   = fmt_large(info.get('marketCap', 0))
pe   = f"{info.get('trailingPE', 0):.1f}x" if info.get('trailingPE') else "N/A"
w52h = f"${info.get('fiftyTwoWeekHigh', 0):.2f}"
w52l = f"${info.get('fiftyTwoWeekLow',  0):.2f}"
sec  = info.get('sector', 'N/A')
ceo  = info.get('companyOfficers',[{}])[0].get('name','N/A') if info.get('companyOfficers') else 'N/A'
emp  = f"{info.get('fullTimeEmployees',0):,}" if info.get('fullTimeEmployees') else 'N/A'
name = info.get('longName', ticker)

st.markdown(f"""
<div style="font-size:1rem; font-weight:600; color:#d4f5f0; margin-bottom:12px; font-family:'Space Grotesk',sans-serif">{name}</div>
<div class="profile-card">
    <div><div class="profile-label">Market Cap</div><div class="profile-value">{mc}</div></div>
    <div><div class="profile-label">P/E Ratio</div><div class="profile-value">{pe}</div></div>
    <div><div class="profile-label">52W High</div><div class="profile-value">{w52h}</div></div>
    <div><div class="profile-label">52W Low</div><div class="profile-value">{w52l}</div></div>
    <div><div class="profile-label">Sector</div><div class="profile-value">{sec}</div></div>
    <div><div class="profile-label">CEO</div><div class="profile-value">{ceo}</div></div>
    <div><div class="profile-label">Employees</div><div class="profile-value">{emp}</div></div>
    <div><div class="profile-label">Exchange</div><div class="profile-value">{info.get('exchange','N/A')}</div></div>
</div>
""", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# --- AI Signal ---
st.markdown('<div class="section-header">AI Signal</div>', unsafe_allow_html=True)
df['SMA20'] = df['Close'].rolling(20).mean()
df['SMA50'] = df['Close'].rolling(50).mean()
df['RSI']   = compute_rsi(df['Close'])
rsi_val     = df['RSI'].iloc[-1]
sma20_val   = df['SMA20'].iloc[-1]
sma50_val   = df['SMA50'].iloc[-1]
signal, reason, confidence = get_signal(rsi_val, pct, sma20_val, sma50_val, current)
signal_class = {"BUY":"signal-buy","SELL":"signal-sell","HOLD":"signal-hold"}[signal]

sig_col, rsi_col = st.columns([1,2])
with sig_col:
    st.markdown(f"""
    <div class="{signal_class}">
        <div class="signal-label">AI Recommendation</div>
        <div class="signal-value">{signal}</div>
        <div class="signal-reason">{reason}</div>
        <div style="margin-top:10px; font-size:0.72rem; opacity:0.6">Confidence: {confidence}%</div>
    </div>""", unsafe_allow_html=True)
with rsi_col:
    if rsi_val > 70: rsi_signal, dot = f"Overbought · RSI {rsi_val:.1f} — momentum may reverse downward", "🔴"
    elif rsi_val < 30: rsi_signal, dot = f"Oversold · RSI {rsi_val:.1f} — potential buying opportunity", "🟢"
    else: rsi_signal, dot = f"Neutral · RSI {rsi_val:.1f} — no strong directional signal", "🟡"
    st.markdown(f'<div class="rsi-badge" style="height:100%; box-sizing:border-box">{dot} &nbsp;&nbsp;{rsi_signal}</div>', unsafe_allow_html=True)

st.markdown('<hr class="teal-divider">', unsafe_allow_html=True)

# --- Price Chart ---
st.markdown('<div class="section-header">Price Chart</div>', unsafe_allow_html=True)
arrow = "▲" if change>=0 else "▼"
fig = plot_chart(ticker, period)
fig.update_layout(
    title=dict(text=f"{ticker} &nbsp;·&nbsp; ${current:.2f} &nbsp;·&nbsp; {arrow} {abs(pct):.2f}%", font=dict(size=13, color="#00d4aa" if change>=0 else "#f87171")),
    plot_bgcolor='#0a1a1c', paper_bgcolor='#080f10',
    xaxis=dict(gridcolor='#0e2a2e'), yaxis=dict(gridcolor='#0e2a2e')
)
st.plotly_chart(fig, use_container_width=True)

# --- Comparison ---
if ticker2 and ticker2 != ticker:
    st.markdown('<div class="section-header">Relative Performance</div>', unsafe_allow_html=True)
    with st.spinner(f"Fetching {ticker2}..."):
        df2 = get_stock_data(ticker2, period)
    fig_comp = go.Figure()
    fig_comp.add_trace(go.Scatter(x=df['Date'], y=(df['Close']/df['Close'].iloc[0]-1)*100,
        name=ticker, line=dict(color='#00d4aa', width=2), fill='tozeroy', fillcolor='rgba(0,212,170,0.03)'))
    fig_comp.add_trace(go.Scatter(x=df2['Date'], y=(df2['Close']/df2['Close'].iloc[0]-1)*100,
        name=ticker2, line=dict(color='#0891b2', width=2)))
    fig_comp.add_hline(y=0, line_dash="dot", line_color="#0e2a2e", line_width=1)
    fig_comp.update_layout(template="plotly_dark", height=320,
        title=dict(text=f"{ticker} vs {ticker2} — Return %", font=dict(size=12, color='#2a7a7a')),
        yaxis_title="Return (%)", plot_bgcolor='#0a1a1c', paper_bgcolor='#080f10',
        xaxis=dict(gridcolor='#0e2a2e'), yaxis=dict(gridcolor='#0e2a2e'))
    st.plotly_chart(fig_comp, use_container_width=True)
    st.markdown('<hr class="teal-divider">', unsafe_allow_html=True)

# --- ML Forecast ---
st.markdown('<div class="section-header">ML Forecast · Next 7 Trading Days</div>', unsafe_allow_html=True)
with st.spinner("Running Random Forest model..."):
    df_1y = get_stock_data(ticker, "1y")
    predictions, score = predict_next_days(df_1y)

df_m = df_1y.copy()
df_m['SMA20'] = df_m['Close'].rolling(20).mean()
df_m['SMA50'] = df_m['Close'].rolling(50).mean()
df_m['Lag1']  = df_m['Close'].shift(1)
df_m['Lag2']  = df_m['Close'].shift(2)
df_m['Lag3']  = df_m['Close'].shift(3)
df_m['Lag5']  = df_m['Close'].shift(5)
df_m.dropna(inplace=True)
X = df_m[['SMA20','SMA50','Lag1','Lag2','Lag3','Lag5']].values
y = df_m['Close'].values
model_tmp = RandomForestRegressor(n_estimators=200, random_state=42)
model_tmp.fit(X, y)
y_pred = model_tmp.predict(X)
rmse = np.sqrt(np.mean((y - y_pred)**2))
mae  = np.mean(np.abs(y - y_pred))

mc1, mc2, mc3 = st.columns(3)
card(mc1, "R² Score", f"{score:.4f}", "variance explained")
card(mc2, "RMSE",     f"${rmse:.2f}", "root mean sq error")
card(mc3, "MAE",      f"${mae:.2f}",  "mean absolute error")
st.markdown("<br>", unsafe_allow_html=True)

last_date    = df['Date'].iloc[-1]
future_dates = pd.bdate_range(start=last_date, periods=8)[1:]

fig_pred = go.Figure()
fig_pred.add_trace(go.Scatter(
    x=df['Date'].tail(30), y=df['Close'].tail(30),
    name="Actual", line=dict(color='#00d4aa', width=2),
    fill='tozeroy', fillcolor='rgba(0,212,170,0.04)'
))
fig_pred.add_trace(go.Scatter(
    x=[df['Date'].iloc[-1]] + list(future_dates),
    y=[df['Close'].iloc[-1]] + predictions,
    name="Forecast", line=dict(color='#0891b2', dash='dash', width=1.5),
    mode='lines+markers', marker=dict(size=6, color='#00d4aa')
))
fig_pred.update_layout(
    template="plotly_dark", height=320,
    title=dict(text=f"{ticker} — 7 Day Price Forecast", font=dict(size=12, color='#2a7a7a')),
    plot_bgcolor='#0a1a1c', paper_bgcolor='#080f10',
    xaxis=dict(gridcolor='#0e2a2e'),
    yaxis=dict(gridcolor='#0e2a2e',
               range=[min(df['Close'].tail(30).min(), min(predictions))*0.98,
                      max(df['Close'].tail(30).max(), max(predictions))*1.02])
)
st.plotly_chart(fig_pred, use_container_width=True)

pred_df = pd.DataFrame({
    "Date": future_dates.strftime("%a, %b %d"),
    "Predicted Price": [f"${p:.2f}" for p in predictions],
    "Expected Move":   [f"{((p-current)/current)*100:+.2f}%" for p in predictions]
})
st.dataframe(pred_df, hide_index=True, use_container_width=True)
st.markdown(f"<div style='font-size:0.68rem; color:#1a4a4a; margin-top:8px'>Random Forest · 200 estimators · Trained on 1Y daily data</div>", unsafe_allow_html=True)

st.markdown('<hr class="teal-divider">', unsafe_allow_html=True)
if st.checkbox("Show Raw Data"):
    st.dataframe(df.tail(20), use_container_width=True)

st.markdown("""
<div class="footer">
    Alphalytics &nbsp;·&nbsp; Built by Anmol Rastogi &nbsp;·&nbsp;
    <a href="https://github.com/anmolrastogi21" target="_blank">GitHub</a> &nbsp;·&nbsp;
    <a href="https://www.linkedin.com/in/anmol-rastogi-916015371/" target="_blank">LinkedIn</a> &nbsp;·&nbsp;
    Not financial advice
</div>""", unsafe_allow_html=True)