import streamlit as st
from tvDatafeed import TvDatafeed, Interval
import pandas as pd
from datetime import datetime, time
import numpy as np

# ------------------ STREAMLIT CONFIG ------------------ #
st.set_page_config(page_title="NSE / Stock Price Cycle + ATR", layout="wide")
st.title("📈 Weekly Price Cycle + Daily ATR Calculator")

# ------------------ SYMBOL LIST ------------------ #
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

tv = TvDatafeed()  # optionally pass credentials for private data (if needed)

# ------------------ FUNCTIONS ------------------ #

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

    # If Friday after 15:30 IST, or weekend → weekly candle complete → use last_close
    if (now.weekday() == 4 and now.time() >= time(15, 30)) or now.weekday() in [5, 6]:
        return last_close, last_date
    # Otherwise (Mon–Thu, or Fri before 15:30) → use previous close
    return prev_close, prev_date

def get_daily_data(symbol: str, exchange: str = "NSE", n_bars: int = 50):
    """
    Fetch daily bars for symbol to compute ATR. Returns pandas DataFrame or None.
    """
    try:
        df = tv.get_hist(symbol=symbol, exchange=exchange,
                         interval=Interval.in_daily, n_bars=n_bars)
    except Exception as e:
        return None
    if df is None or df.empty:
        return None
    if not all(col in df.columns for col in ["open", "high", "low", "close"]):
        return None
    df = df.dropna(subset=["open", "high", "low", "close"])
    if df.shape[0] < n_bars // 2:
        # not enough data
        return None
    return df

def compute_atr(df: pd.DataFrame, period: int = 10) -> float | None:
    """
    Compute ATR (Average True Range) over last 'period' days.
    Returns ATR value (float) or None if not enough data.
    """
    df2 = df.copy()
    df2["prev_close"] = df2["close"].shift(1)
    df2 = df2.dropna()
    tr1 = df2["high"] - df2["low"]
    tr2 = (df2["high"] - df2["prev_close"]).abs()
    tr3 = (df2["low"] - df2["prev_close"]).abs()
    df2["TR"] = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    if len(df2) < period:
        return None
    atr = df2["TR"].rolling(period).mean().iloc[-1]
    return float(atr)

def price_cycles(close_price: float, steps):
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

# ------------------ FETCH DATA ------------------ #
weekly_close, used_date = get_weekly_close(symbol)
if weekly_close is None:
    st.error("❌ Could not fetch weekly close for the selected symbol. Data may be unavailable or symbol incorrect.")
    st.stop()

daily_df = get_daily_data(symbol)
if daily_df is None:
    st.warning("⚠ Could not fetch sufficient daily data for ATR calculation.")
    atr_value = None
else:
    atr_value = compute_atr(daily_df, period=10)

last_close_price = float(daily_df["close"].iloc[-1]) if daily_df is not None else None

# ------------------ DISPLAY TOP INFO ------------------ #
info_col1, info_col2 = st.columns(2)
with info_col1:
    st.markdown(f"**Symbol:** {symbol}")
    st.markdown(f"**Weekly Close used:** {weekly_close:.2f}  (bar date: {used_date.date()})")
    if last_close_price is not None:
        st.markdown(f"**Last Close (Daily):** {last_close_price:.2f}")
with info_col2:
    if atr_value is not None:
        st.markdown(f"**ATR (10-day):** {atr_value:.2f}")
    else:
        st.markdown("**ATR (10-day):** —")

st.markdown("---")

# ------------------ STEP SELECTION FOR PRICE CYCLES ------------------ #
preset_dict = {
    "Default (30-60-90-120-150)": [30, 60, 90, 120, 150],
    "Short (3-6-9-12-15)": [3, 6, 9, 12, 15],
    "Long (300-600-900-1200-1500)": [300, 600, 900, 1200, 1500],
    "Custom": None
}

step_choice = st.selectbox("Choose Step Set for Price Cycles", list(preset_dict.keys()))

if step_choice == "Custom":
    custom_input = st.text_input("Enter comma-separated cycle steps (e.g. 25,50,75,100)", "30,60,90,120,150")
    try:
        steps = [int(x.strip()) for x in custom_input.split(",") if x.strip()]
    except:
        st.error("Invalid custom steps. Please enter comma-separated integers.")
        st.stop()
    if not steps:
        st.error("Please enter at least one integer step.")
        st.stop()
else:
    steps = preset_dict[step_choice]

# ------------------ CALCULATE & SHOW PRICE CYCLES ------------------ #
res_levels, sup_levels = price_cycles(weekly_close, steps)

df_cycles = pd.DataFrame({
    "Resistance": res_levels,
    "Support": sup_levels
})

st.subheader("🔹 Price Cycle Levels")
st.dataframe(df_cycles)

csv = df_cycles.to_csv(index=False)
st.download_button("Download Levels as CSV", data=csv,
                   file_name=f"{symbol}_price_cycles.csv", mime="text/csv")
