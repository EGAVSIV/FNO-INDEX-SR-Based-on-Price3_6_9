# app_price_cycle.py

import streamlit as st
from tvDatafeed import TvDatafeed, Interval
import pandas as pd
from datetime import datetime, time

st.set_page_config(page_title="Weekly Price Cycle Calculator (Flexible Steps)", layout="wide")
st.title("📊 Weekly Price Cycle Calculator – Flexible Step Sizes")

# --- SYMBOL LIST (example subset; expand as needed) ---
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

tv = TvDatafeed()  # Optionally with credentials

def get_weekly_close(symbol: str, exchange: str = "NSE"):
    df = tv.get_hist(symbol=symbol, exchange=exchange,
                     interval=Interval.in_weekly, n_bars=2)
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
    # Friday after 15:30 or weekend ⇒ latest candle complete
    if (now.weekday() == 4 and now.time() >= time(15, 30)) or now.weekday() in [5, 6]:
        return last_close, last_date
    # Else take previous
    return prev_close, prev_date

weekly_close, used_date = get_weekly_close(symbol)
if weekly_close is None:
    st.error("❌ Could not fetch weekly close for the selected symbol.")
    st.stop()

st.write("Weekly Close used:", weekly_close, "  (bar date:", used_date.date(), ")")

# --- Step-set dropdown + custom option ---
preset_label = st.selectbox(
    "Choose step-set for price cycles",
    ("3,6,9,12,15","30,60,90,120,150", "300,600,900,1200,1500", "Custom..."),
)

if preset_label == "Custom...":
    user_input = st.text_input(
        "Enter custom steps separated by comma (e.g. 25, 50, 75, 100)",
        value="30,60,90,120,150"
    )
    try:
        steps = [int(x.strip()) for x in user_input.split(",") if x.strip()]
    except ValueError:
        st.error("Invalid input — please enter comma-separated integers.")
        st.stop()
else:
    steps = [int(x) for x in preset_label.split(",")]

st.write("Using step sizes:", steps)

def price_cycles(close_price: float, steps: list[int]):
    resist = []
    support = []
    up = close_price
    down = close_price
    for s in steps:
        up += s
        down -= s
        resist.append(up)
        support.append(down)
    return resist, support

res_levels, sup_levels = price_cycles(weekly_close, steps)

df = pd.DataFrame({
    "Resistance": res_levels,
    "Support": sup_levels
})

st.subheader("🔹 Price Cycle Levels")
st.dataframe(df)

csv = df.to_csv(index=False)
st.download_button("Download Levels as CSV", data=csv,
                   file_name=f"{symbol}_price_cycles.csv", mime="text/csv")
