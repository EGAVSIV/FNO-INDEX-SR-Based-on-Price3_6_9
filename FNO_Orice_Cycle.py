import streamlit as st
import datetime as dt
from datetime import datetime, time
import yfinance as yf
import pandas as pd

# ------------------ CONFIGURE SYMBOL LIST ------------------ #
# Put all your FNO symbols + indices here.
# For NSE equities, add ".NS"
symbols = ['PIDILITIND','PERSISTENT','PETRONET','LTIM','INDIANB','INDHOTEL','HFCL','HAVELLS','BRITANNIA','BSE','CAMS','CANBK','CDSL','CGPOWER','CHOLAFIN','CIPLA','COALINDIA','COFORGE','COLPAL','CONCOR','CROMPTON','CUMMINSIND','CYIENT','DABUR',
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

# Map your display names to Yahoo tickers
def yahoo_ticker(symbol: str):
    # For known index
    if symbol.upper() == "NIFTY 50":
        return "^NSEI"
    # For other indices like BANKNIFTY/FINNIFTY — you'll need proper Yahoo ticker or external data source.
    # As fallback treat them as stocks
    return symbol.upper() + ".NS"


# ------------------ WEEKLY CLOSE HANDLING ------------------ #
def get_weekly_close_safe(ticker: str) -> float | None:
    try:
        df = yf.download(ticker, period="2y", interval="1wk", progress=False)
    except Exception as e:
        return None
    if df is None or df.empty or "Close" not in df.columns:
        return None
    df = df.rename(columns={"Close": "close"})
    df = df.dropna(subset=["close"])

    # If less than 2 weeks data — abort
    if len(df) < 2:
        return None

    last_close = df["close"].iloc[-1]
    prev_close = df["close"].iloc[-2]

    now = datetime.now()

    # Determine which close to use
    if (now.weekday() == 4 and now.time() >= time(15, 30)) or now.weekday() in [5, 6]:
        return float(last_close)
    # Monday before 9:00 AM, or Tue–Thu or Fri before 15:30
    return float(prev_close)


# ------------------ PRICE CYCLE CALC ------------------ #
def price_cycles(close_price: float, steps=[30, 60, 90, 120, 150]):
    res = []
    sup = []
    base = close_price
    for s in steps:
        base_up = (res[-1] if res else close_price) + s
        res.append(base_up)

    base = close_price
    for s in steps:
        base_down = (sup[-1] if sup else close_price) - s
        sup.append(base_down)

    return res, sup

# ------------------ STREAMLIT UI ------------------ #
st.title("📈 NSE Price Cycle Checker (Weekly-based)")

symbol = st.selectbox("Select Symbol:", symbols)

yf_tkr = yahoo_ticker(symbol)
st.write("→ Yahoo Ticker:", yf_tkr)

weekly_close = get_weekly_close_safe(yf_tkr)
if weekly_close is None:
    st.error("❌ Could not fetch weekly close for symbol — data unavailable or ticker invalid.")
    st.stop()

st.write("Weekly Close Used:", weekly_close)

res_levels, sup_levels = price_cycles(weekly_close)

df_levels = pd.DataFrame({
    "Resistance": res_levels,
    "Support": sup_levels
})

st.subheader("Calculated Price Cycles (Levels)")
st.dataframe(df_levels)
