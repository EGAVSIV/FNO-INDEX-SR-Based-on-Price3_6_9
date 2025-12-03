import streamlit as st
from tvDatafeed import TvDatafeed, Interval
import pandas as pd
import numpy as np
from datetime import datetime, time

# --- PAGE BACKGROUND IMAGE ---
def set_page_bg(image_file):
    import base64
    with open(image_file, "rb") as f:
        img_data = f.read()
    b64 = base64.b64encode(img_data).decode()
    page_bg_css = f"""
    <style>
    [data-testid="stAppViewContainer"] > .main {{
        background-image: url("data:image/png;base64,{b64}");
        background-size: cover;
        background-attachment: fixed;
    }}
    </style>
    """
    st.markdown(page_bg_css, unsafe_allow_html=True)

# call this at top — make sure you have 'background.jpg' in same folder
set_page_bg("Image.jpg")

# --- PAGE HEADER ---
st.set_page_config(layout="wide")
st.title("📈 Weekly Price Cycle + ATRP + Styled Output")

tv = TvDatafeed()

SYMBOLS = ['NIFTY','BANKNIFTY','CNXFINANCE','CNXMIDCAP','NIFTYJR','360ONE','ABB','ABCAPITAL','ADANIENSOL','ADANIENT','ADANIGREEN','ADANIPORTS','ALKEM','AMBER','AMBUJACEM','ANGELONE','APLAPOLLO','APOLLOHOSP',
           'ASHOKLEY','ASIANPAINT','ASTRAL','AUBANK','AUROPHARMA','AXISBANK','BAJAJ_AUTO','BAJAJFINSV','BRITANNIA','INDIANB','INDHOTEL','HFCL','HAVELLS','BAJFINANCE','BANDHANBNK','BANKBARODA','BANKINDIA','BDL','BEL','BHARATFORG','BHARTIARTL','BHEL',
           'BIOCON','BLUESTARCO','BOSCHLTD','BPCL''BSE','CAMS','CANBK','CDSL','CGPOWER','CHOLAFIN','CIPLA','COALINDIA','COFORGE','COLPAL','CONCOR','CROMPTON','CUMMINSIND','CYIENT','DABUR',
           'DALBHARAT','DELHIVERY','DIVISLAB','DIXON','DLF','DMART','DRREDDY','EICHERMOT','ETERNAL','EXIDEIND','FEDERALBNK','FORTIS','GAIL','GLENMARK','GMRAIRPORT','GODREJCP','GODREJPROP','GRASIM','HAL',
           'HDFCAMC','HDFCBANK','HDFCLIFE','HEROMOTOCO','HINDALCO','HINDPETRO','HINDUNILVR','HINDZINC','HUDCO','ICICIBANK','ICICIGI','ICICIPRULI','IDEA','IDFCFIRSTB','IEX','IGL',
           'IIFL','INDIGO','INDUSINDBK','INDUSTOWER','INFY','INOXWIND','IOC','IRCTC','IREDA','IRFC','ITC','JINDALSTEL','JIOFIN','JSWENERGY','JSWSTEEL','JUBLFOOD','KALYANKJIL','KAYNES',
           'KEI','KFINTECH','KOTAKBANK','KPITTECH','LAURUSLABS','LICHSGFIN','LICI','LODHA','LT','LTF','LTIM','LUPIN','M&M','MANAPPURAM','MANKIND','MARICO','MARUTI','MAXHEALTH','MAZDOCK','MCX','MFSL',
           'MOTHERSON','MPHASIS','MUTHOOTFIN','NATIONALUM','NAUKRI','NBCC','NCC','NESTLEIND','NMDC','NTPC','NUVAMA','NYKAA','OBEROIRLTY','OFSS','OIL','ONGC','PAGEIND','PATANJALI','PAYTM',
           'PFC','PGEL','PHOENIXLTD','PIIND','PNB','PNBHOUSING','POLICYBZR','POLYCAB','PIDILITIND','PERSISTENT','PETRONET','NHPC', 'HCLTECH','POWERGRID','PPLPHARMA','PRESTIGE','RBLBANK','RECLTD','RELIANCE',
           'RVNL','SAIL','SAMMAANCAP','SBICARD','SBILIFE','SBIN','SHREECEM','SHRIRAMFIN','SIEMENS','SOLARINDS','SONACOMS','SRF','SUNPHARMA','SUPREMEIND','SUZLON','SYNGENE','TATACONSUM',
           'TATAELXSI','TATAMOTORS','TATAPOWER','TATASTEEL','TATATECH','TCS','TECHM','TIINDIA','TITAGARH','TITAN','TORNTPHARM','TORNTPOWER','TRENT','TVSMOTOR','ULTRACEMCO','UNIONBANK','UNITDSPR',
           'UNOMINDA','UPL','VBL','VEDL','VOLTAS','WIPRO','YESBANK','ZYDUSLIFE']

symbol = st.selectbox("Select Symbol / Index", SYMBOLS)

def get_weekly_close(symbol, exchange="NSE"):
    try:
        df = tv.get_hist(symbol=symbol, exchange=exchange,
                         interval=Interval.in_weekly, n_bars=2)
    except Exception:
        return None, None
    if df is None or df.empty or "close" not in df.columns:
        return None, None
    df = df.dropna(subset=["close"])
    if len(df) < 2:
        return None, None
    last = float(df["close"].iloc[-1])
    prev = float(df["close"].iloc[-2])
    now = datetime.now()
    if (now.weekday()==4 and now.time() >= time(15,30)) or now.weekday() in (5,6):
        return last, df.index[-1]
    else:
        return prev, df.index[-2]

def fetch_daily(symbol, bars=50, exchange="NSE"):
    try:
        df = tv.get_hist(symbol=symbol, exchange=exchange,
                         interval=Interval.in_daily, n_bars=bars)
    except Exception:
        return None
    if df is None or df.empty:
        return None
    if not {"open","high","low","close"}.issubset(df.columns):
        return None
    df = df.dropna(subset=["open","high","low","close"])
    return df

def compute_atr(df, period=10):
    df2 = df.copy()
    df2["prev_close"] = df2["close"].shift(1)
    df2 = df2.dropna()
    tr1 = df2["high"] - df2["low"]
    tr2 = (df2["high"] - df2["prev_close"]).abs()
    tr3 = (df2["low"] - df2["prev_close"]).abs()
    df2["TR"] = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = df2["TR"].rolling(window=period).mean().iloc[-1]
    return float(atr)

def price_cycles(close_price, steps):
    resist, support = [], []
    up = close_price
    down = close_price
    for s in steps:
        up += s; resist.append(up)
        down -= s; support.append(down)
    return resist, support

weekly_close, wbar = get_weekly_close(symbol)
if weekly_close is None:
    st.error("Cannot fetch weekly close for symbol")
    st.stop()

daily_df = fetch_daily(symbol)
if daily_df is None:
    last_close = None
    atr = None
else:
    last_close = float(daily_df["close"].iloc[-1])
    atr = compute_atr(daily_df)

# --- Header Info with formatting ---
st.markdown(f"### **<span style='color:blue;'>{symbol}</span>**", unsafe_allow_html=True)
st.markdown(f"**Weekly Close (used):** {weekly_close:.2f}  •  *(bar date: {wbar.date()})*")
if last_close:
    st.markdown(f"**Last Close (Daily):** {last_close:.2f}")
if atr:
    atrp = (atr / last_close) * 100
    st.markdown(f"**ATR(10):** {atr:.2f}    &nbsp;&nbsp;  **ATR%:** {atrp:.2f}%")

st.markdown("---")

# --- Step selection ---
preset = {
    "3-6-9-12-15": [3,6,9,12,15],
    "30-60-90-120-150": [30,60,90,120,150],
    "300-600-900-1200-1500": [300,600,900,1200,1500],
    "Custom": None
}
choice = st.selectbox("Cycle Step Preset", list(preset.keys()))
if choice == "Custom":
    inp = st.text_input("Enter comma-separated steps", "30,60,90")
    try:
        steps = [int(x.strip()) for x in inp.split(",") if x.strip()]
    except:
        st.error("Invalid custom steps")
        st.stop()
else:
    steps = preset[choice]

res, sup = price_cycles(weekly_close, steps)
df = pd.DataFrame({"Resistance": res, "Support": sup})

# --- Style the table ---
def style_cycles(val, is_resist=True):
    color = 'lightgreen' if is_resist else 'salmon'
    return f'background-color: {color}; font-weight: bold;'

styled = df.style.apply(lambda x: ['background-color: lightgreen' for _ in x] , subset=['Resistance']) \
                 .apply(lambda x: ['background-color: salmon' for _ in x], subset=['Support']) \
                 .format("{:.2f}")

st.subheader("🔹 Price Cycle Levels")
st.dataframe(styled, use_container_width=True)
