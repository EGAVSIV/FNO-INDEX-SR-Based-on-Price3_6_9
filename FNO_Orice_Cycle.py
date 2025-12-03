# app_price_cycle.py

import streamlit as st
from tvDatafeed import TvDatafeed, Interval
import pandas as pd
from datetime import datetime, time
import numpy as np

# ------------------------ UI Setup ------------------------
st.set_page_config(page_title="NSE / Stock Price Cycle Calculator", layout="wide")
st.title("📊 Weekly Price Cycle Calculator (3-6-9 / Custom Steps)")

# ------------------------ SYMBOL LIST ------------------------
# Add your F&O / common NSE stocks & indices here
SYMBOLS = ['PIDILITIND','PERSISTENT','PETRONET','LTIM','INDIANB','INDHOTEL','HFCL','HAVELLS','BRITANNIA','BSE','CAMS','CANBK','CDSL','CGPOWER','CHOLAFIN','CIPLA','COALINDIA','COFORGE','COLPAL','CONCOR','CROMPTON','CUMMINSIND','CYIENT','DABUR',
           'DALBHARAT','DELHIVERY','DIVISLAB','DIXON','DLF','DMART','DRREDDY','EICHERMOT','ETERNAL','EXIDEIND','FEDERALBNK','FORTIS','GAIL','GLENMARK','GMRAIRPORT','GODREJCP','GODREJPROP','GRASIM','HAL',
           'HDFCAMC','HDFCBANK','HDFCLIFE','HEROMOTOCO','HINDALCO','HINDPETRO','HINDUNILVR','HINDZINC','HUDCO','ICICIBANK','ICICIGI','ICICIPRULI','IDEA','IDFCFIRSTB','IEX','IGL',
           'IIFL','INDIGO','INDUSINDBK','INDUSTOWER','INFY','INOXWIND','IOC','IRCTC','IREDA','IRFC','ITC','JINDALSTEL','JIOFIN','JSWENERGY','JSWSTEEL','JUBLFOOD','KALYANKJIL','KAYNES',
           'KEI','KFINTECH','KOTAKBANK','KPITTECH','LAURUSLABS','LICHSGFIN','LICI','LODHA','LT','LTF','LUPIN','M&M','MANAPPURAM','MANKIND','MARICO','MARUTI','MAXHEALTH','MAZDOCK','MCX','MFSL',
           'MOTHERSON','MPHASIS','MUTHOOTFIN','NATIONALUM','NAUKRI','NBCC','NCC','NESTLEIND','NMDC','NTPC','NUVAMA','NYKAA','OBEROIRLTY','OFSS','OIL','ONGC','PAGEIND','PATANJALI','PAYTM',
           'PFC','PGEL','PHOENIXLTD','PIIND','PNB','PNBHOUSING','POLICYBZR','POLYCAB','NHPC', 'HCLTECH','POWERGRID','PPLPHARMA','PRESTIGE','RBLBANK','RECLTD','RELIANCE',
           'RVNL','SAIL','SAMMAANCAP','SBICARD','SBILIFE','SBIN','SHREECEM','SHRIRAMFIN','SIEMENS','SOLARINDS','SONACOMS','SRF','SUNPHARMA','SUPREMEIND','SUZLON','SYNGENE','TATACONSUM',
           'TATAELXSI','TATAMOTORS','TATAPOWER','TATASTEEL','TATATECH','TCS','TECHM','TIINDIA','TITAGARH','TITAN','TORNTPHARM','TORNTPOWER','TRENT','TVSMOTOR','ULTRACEMCO','UNIONBANK','UNITDSPR',
           'UNOMINDA','UPL','VBL','VEDL','VOLTAS','WIPRO','YESBANK','ZYDUSLIFE','BANKNIFTY','CNXFINANCE','CNXMIDCAP','NIFTY','NIFTYJR','360ONE','ABB','ABCAPITAL','ADANIENSOL','ADANIENT','ADANIGREEN','ADANIPORTS','ALKEM','AMBER','AMBUJACEM','ANGELONE','APLAPOLLO','APOLLOHOSP',
           'ASHOKLEY','ASIANPAINT','ASTRAL','AUBANK','AUROPHARMA','AXISBANK','BAJAJ_AUTO','BAJAJFINSV','BAJFINANCE','BANDHANBNK','BANKBARODA','BANKINDIA','BDL','BEL','BHARATFORG','BHARTIARTL','BHEL',
           'BIOCON','BLUESTARCO','BOSCHLTD','BPCL']

symbol = st.selectbox("Select Symbol / Index", SYMBOLS)

# ------------------------ Fetch Data Function ------------------------
tv = TvDatafeed()  # you may optionally supply username/password if needed

def get_weekly_close(symbol: str, exchange: str = "NSE"):
    """
    Fetch last 2 weekly bars for symbol from TradingView via tvDatafeed.
    Decide whether to use the latest or previous weekly close based on current day/time.
    """
    try:
        df = tv.get_hist(symbol=symbol, exchange=exchange,
                         interval=Interval.in_weekly, n_bars=2)
    except Exception as e:
        return None, None

    if df is None or df.empty or "close" not in df.columns:
        return None, None

    df = df.dropna(subset=["close"])
    if len(df) < 2:
        return None, None

    last_close = float(df["close"].iloc[-1])
    prev_close = float(df["close"].iloc[-2])
    last_date = df.index[-1]
    prev_date = df.index[-2]

    now = datetime.now()

    # If Friday after 15:30, or weekend => use last close
    if (now.weekday() == 4 and now.time() >= time(15, 30)) or now.weekday() in [5, 6]:
        return last_close, last_date
    # If Monday before 9:00, or Tue–Thu, or Fri before 15:30 => use previous close
    return prev_close, prev_date

# ------------------------ Calculate Price Cycles ------------------------
def price_cycles(close_price: float, steps=[30, 60, 90, 120, 150]):
    resist = []
    support = []
    base_up = close_price
    base_down = close_price
    for s in steps:
        base_up += s
        resist.append(base_up)
        base_down -= s
        support.append(base_down)
    return resist, support

# ------------------------ Main Logic ------------------------
weekly_close, used_date = get_weekly_close(symbol)

if weekly_close is None:
    st.error("❌ Could not fetch weekly close for the selected symbol. Data may be unavailable or symbol incorrect.")
    st.stop()

st.write("**Weekly Close used:**", weekly_close, "  (bar date:", used_date.date(), ")")

# Let user optionally choose custom steps
custom = st.checkbox("Use custom steps instead of default [30,60,90,120,150]")
if custom:
    user_steps_input = st.text_input("Enter comma-separated step values (e.g. 25,50,75)", "30,60,90,120,150")
    try:
        steps = [int(x.strip()) for x in user_steps_input.split(",") if x.strip()]
    except:
        st.error("Invalid steps input. Please enter comma-separated integers.")
        st.stop()
else:
    steps = [30, 60, 90, 120, 150]

res_levels, sup_levels = price_cycles(weekly_close, steps)

df_cycles = pd.DataFrame({
    "Resistance": res_levels,
    "Support": sup_levels
})

st.subheader("📈 Price Cycle Levels")
st.dataframe(df_cycles)

# Optionally download data
csv = df_cycles.to_csv(index=False)
st.download_button("Download Levels as CSV", data=csv, file_name=f"{symbol}_price_cycles.csv", mime="text/csv")
