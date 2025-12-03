import streamlit as st
from tvDatafeed import TvDatafeed, Interval
import pandas as pd
import numpy as np
from datetime import datetime, time

# --- CONFIG ---
st.set_page_config(page_title="NSE Price Cycle + ATRP Scanner", layout="wide")
st.title("📈 Weekly Price Cycles + ATRP (Volatility) + Scanner")

tv = TvDatafeed()  # supply credentials if required

# --- SYMBOL UNIVERSE ---
# Add all F&O / stocks / indices you need
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

# --- FUNCTIONS ---
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
    if (now.weekday()==4 and now.time() >= time(15,30)) or now.weekday() in (5,6):
        return last, df.index[-1]
    return prev, df.index[-2]

def fetch_daily(symbol: str, exchange: str = "NSE", bars: int = 50):
    try:
        df = tv.get_hist(symbol=symbol, exchange=exchange,
                         interval=Interval.in_daily, n_bars=bars)
    except Exception:
        return None
    if df is None or df.empty:
        return None
    required = {"open","high","low","close"}
    if not required.issubset(df.columns):
        return None
    df = df.dropna(subset=list(required))
    if df.shape[0] < bars//2:
        return None
    return df

def compute_atr(df: pd.DataFrame, period: int = 10) -> float:
    df2 = df.copy()
    df2["prev_close"] = df2["close"].shift(1)
    df2 = df2.dropna()
    tr1 = df2["high"] - df2["low"]
    tr2 = (df2["high"] - df2["prev_close"]).abs()
    tr3 = (df2["low"] - df2["prev_close"]).abs()
    df2["TR"] = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return float(df2["TR"].rolling(window=period).mean().iloc[-1])

def price_cycles(close_price: float, steps):
    resist = []; support = []
    up = close_price; down = close_price
    for s in steps:
        up += s; resist.append(up)
        down -= s; support.append(down)
    return resist, support

# --- APP MODE: single symbol or scan filter ---
mode = st.radio("Mode:", ["Single Symbol", "Scan Universe (by ATR%)"])

if mode == "Single Symbol":
    symbol = st.selectbox("Select Symbol", SYMBOLS)
    weekly_close, wdate = get_weekly_close(symbol)
    if weekly_close is None:
        st.error("Cannot fetch weekly close for " + symbol)
        st.stop()

    daily_df = fetch_daily(symbol)
    if daily_df is None:
        st.warning("Not enough daily data for ATR/ATRP calculation.")
        atr = None
    else:
        atr = compute_atr(daily_df, period=10)

    last_close = float(daily_df["close"].iloc[-1]) if daily_df is not None else None

    st.markdown(f"**Symbol:** {symbol}")
    st.markdown(f"**Weekly Close (used):** {weekly_close:.2f}  (date {wdate.date()})")
    if last_close:
        st.markdown(f"**Last Close (Daily):** {last_close:.2f}")
    if atr:
        st.markdown(f"**ATR(10):** {atr:.2f}")
        atrp = (atr / last_close) * 100 if last_close else None
        st.markdown(f"**ATR% (ATR / Close * 100):** {atrp:.2f}%")

    # Price-cycle steps selection (as before)
    presets = {
        "Default 30-60-90-120-150": [30,60,90,120,150],
        "Short 3-6-9": [3,6,9,12,15],
        "Long 300-600-900": [300,600,900,1200,1500],
        "Custom": None
    }
    choice = st.selectbox("Cycle Step Preset", list(presets.keys()))
    if choice == "Custom":
        user = st.text_input("Enter comma-separated steps", "30,60,90")
        try:
            steps = [int(x.strip()) for x in user.split(",") if x.strip()]
        except:
            st.error("Invalid custom steps.")
            st.stop()
    else:
        steps = presets[choice]

    res, sup = price_cycles(weekly_close, steps)
    df_cycles = pd.DataFrame({"Resistance": res, "Support": sup})
    st.subheader("Price Cycle Levels")
    st.dataframe(df_cycles)

else:  # Scan Universe mode
    st.write("This will scan all symbols and show those with highest ATR% (top 20 by default)")

    period = st.number_input("ATR lookback period (days)", min_value=5, max_value=50, value=10, step=1)
    top_n = st.number_input("Top N volatile stocks to show", min_value=5, max_value=100, value=20, step=1)

    results = []
    for s in SYMBOLS:
        daily = fetch_daily(s)
        if daily is None:
            continue
        try:
            atr = compute_atr(daily, period=period)
            last = float(daily["close"].iloc[-1])
            atrp = (atr / last) * 100
            results.append((s, last, atr, atrp))
        except Exception:
            continue

    df_scan = pd.DataFrame(results, columns=["Symbol","Last Close","ATR","ATR%"])
    df_scan = df_scan.sort_values("ATR%", ascending=False).head(top_n).reset_index(drop=True)
    st.subheader(f"Top {top_n} by ATR%")
    st.dataframe(df_scan)
    csv = df_scan.to_csv(index=False)
    st.download_button("Download scan results CSV", data=csv,
                       file_name="atr_percent_scan.csv", mime="text/csv")
