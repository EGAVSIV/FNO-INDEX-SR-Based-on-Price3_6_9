import streamlit as st
from tvDatafeed import TvDatafeed, Interval
import pandas as pd
import talib as ta
import numpy as np
from datetime import datetime, time
import base64

# ----------------------  CONFIG  ---------------------- #
st.set_page_config(page_title="NSE Price Cycle + ATRP Scanner", layout="wide")

# Function to set background image
def set_bg_image(image_file):
    with open(image_file, "rb") as img_f:
        img_data = img_f.read()
    b64 = base64.b64encode(img_data).decode()
    css = f"""
    <style>
    [data-testid="stAppViewContainer"] > .main {{
        background-image: url("data:SMB2/png;base64,{b64}");
        background-size: cover;
        background-attachment: fixed;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# Call this — ensure Image.jpg (or png) is present in same folder
#set_bg_image("LG1.jpg")

st.title("📈 Price Cycle + ATRP Scanner with Styled Output")

tv = TvDatafeed()

# ------------------- SYMBOL UNIVERSE ------------------- #
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

# ------------------- HELPER FUNCTIONS ------------------- #
def get_weekly_close(symbol: str, exchange: str = "NSE"):
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
    # Friday after 15:30 IST or weekend → use last weekly bar
    if (now.weekday()==4 and now.time() >= time(15,30)) or now.weekday() in (5,6):
        return last, df.index[-1]
    else:
        return prev, df.index[-2]

def fetch_daily(symbol: str, exchange: str = "NSE", bars: int = 50):
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

import talib as ta

def get_atr_with_talib(daily_df, period=10):
    highs  = daily_df["high"].values
    lows   = daily_df["low"].values
    closes = daily_df["close"].values

    atr_array = ta.ATR(highs, lows, closes, timeperiod=period)
    # the array may contain NaNs at start — take last valid
    atr = atr_array[-1]
    if np.isnan(atr):
        # fallback or warning
        return None
    return float(atr)


def price_cycles(close_price: float, steps):
    res = []
    sup = []
    up = close_price
    down = close_price
    for s in steps:
        up += s
        res.append(up)
        down -= s
        sup.append(down)
    return res, sup



def set_background(image_path: str):
    try:
        with open(image_path, "rb") as f:
            img_data = f.read()
        b64 = base64.b64encode(img_data).decode()
    except Exception as e:
        st.error(f"Background image load error: {e}")
        return

    css = f"""
    <style>
    /* Main page background */
    [data-testid="stAppViewContainer"] > .main {{
        background-image: url("data:image/png;base64,{b64}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    /* Transparent header so background shows through */
    .css-18e3th9.ehxs19n2 {{
        background-color: rgba(0,0,0,0) !important;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# Call once at start
set_background("SMB2.jpg")


# ------------------- APP LOGIC ------------------- #
mode = st.radio("Mode:", ["Single Symbol", "Scan Universe (by ATR%)"])

if mode == "Single Symbol":
    symbol = st.selectbox("Select Symbol", SYMBOLS)
    weekly_close, wdate = get_weekly_close(symbol)
    if weekly_close is None:
        st.error("⛔ Could not fetch weekly data for symbol: " + symbol)
        st.stop()

    daily_df = fetch_daily(symbol)
    if daily_df is not None:
        last_close = float(daily_df["close"].iloc[-1])
        atr = compute_atr(daily_df, period=10)
    else:
        last_close = None
        atr = None

    # --- Header Info with styling ---
    st.markdown(f"### **<span style='color:blue;'>{symbol}</span>**", unsafe_allow_html=True)
    st.markdown(f"**Weekly Close (used):** {weekly_close:.2f}  (bar date: {wdate.date()})")
    if last_close:
        st.markdown(f"**Last Close (Daily):** {last_close:.2f}")
    if atr:
        atrp = (atr / last_close) * 100
        st.markdown(f"**ATR(10):** {atr:.2f}    &nbsp;&nbsp;  **ATR%:** {atrp:.2f}%")

    st.markdown("---")

    # Cycle-step selection
    presets = {
        "Default 30-60-90-120-150": [30,60,90,120,150],
        "Short 3-6-9-12-15": [3,6,9,12,15],
        "Long 300-600-900-1200-1500": [300,600,900,1200,1500],
        "Custom": None
    }
    choice = st.selectbox("Cycle Step Preset", list(presets.keys()))
    if choice == "Custom":
        raw = st.text_input("Enter comma-separated steps (e.g. 25,50,75)", "30,60,90")
        try:
            steps = [int(x.strip()) for x in raw.split(",") if x.strip()]
        except:
            st.error("⚠ Invalid custom steps.")
            st.stop()
    else:
        steps = presets[choice]

    res_levels, sup_levels = price_cycles(weekly_close, steps)
    df_cycles = pd.DataFrame({"Resistance": res_levels, "Support": sup_levels})

    # --- Style the table with colors ---
    def style_df(df):
        sty = df.style
        sty = sty.applymap(lambda _: "background-color: lightgreen; color: black;", subset=["Resistance"])
        sty = sty.applymap(lambda _: "background-color: lightcoral; color: black;", subset=["Support"])
        sty = sty.format("{:.2f}")
        return sty

    st.subheader("🔹 Price Cycle Levels")
    st.table(style_df(df_cycles))

else:
    st.write("## 🔍 ATR% Scan — High Volatility Stocks")

    period = st.number_input("ATR lookback (days):", min_value=5, max_value=60, value=10, step=1)
    top_n = st.number_input("Show Top N by ATR%:", min_value=5, max_value=len(SYMBOLS), value=20, step=5)

    results = []
    for s in SYMBOLS:
        daily = fetch_daily(s)
        if daily is None:
            continue
        try:
            last = float(daily["close"].iloc[-1])
            atr = get_atr_with_talib(daily_df, period=10)
            atrp = (atr / last) * 100
            results.append((s, last, atr, atrp))
        except Exception:
            continue

    df_scan = pd.DataFrame(results, columns=["Symbol","Last Close","ATR","ATR%"])
    df_scan = df_scan.sort_values("ATR%", ascending=False).head(top_n).reset_index(drop=True)
    st.subheader(f"Top {top_n} Symbols by ATR%")
    st.dataframe(df_scan)
    csv = df_scan.to_csv(index=False)
    st.download_button("Download ATR% Scan CSV", data=csv,
                       file_name="atr_percent_scan.csv", mime="text/csv")
