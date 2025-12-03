import streamlit as st
from tvDatafeed import TvDatafeed, Interval
import pandas as pd
import talib as ta
import numpy as np
from datetime import datetime, time
import base64
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from io import BytesIO
from fpdf import FPDF

# ----------------------  CONFIG  ---------------------- #
st.set_page_config(page_title="NSE Price Cycle & ATRP Scanner_By Rao_Gs", layout="wide")

# Optional background image function (your original)
def set_bg_image(image_file):
    try:
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
    except:
        pass

# New background (you used this one)
def set_background(image_path: str):
    try:
        with open(image_path, "rb") as f:
            img_data = f.read()
        b64 = base64.b64encode(img_data).decode()
    except Exception:
        return

    css = f"""
    <style>
    [data-testid="stAppViewContainer"] > .main {{
        background-image: url("data:image/png;base64,{b64}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    .css-18e3th9.ehxs19n2 {{
        background-color: rgba(0,0,0,0) !important;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# Call once at start
set_background("SMB2.jpg")

st.title("📈 Price Cycle + ATRP Scanner with Styled Output")

tv = TvDatafeed()

# ------------------- SYMBOL UNIVERSE ------------------- #
SYMBOLS = [
    'NIFTY','BANKNIFTY','CNXFINANCE','CNXMIDCAP','NIFTYJR','360ONE','ABB','ABCAPITAL',
    'ADANIENSOL','ADANIENT','ADANIGREEN','ADANIPORTS','ALKEM','AMBER','AMBUJACEM',
    'ANGELONE','APLAPOLLO','APOLLOHOSP','ASHOKLEY','ASIANPAINT','ASTRAL','AUBANK',
    'AUROPHARMA','AXISBANK','BAJAJ_AUTO','BAJAJFINSV','BRITANNIA','INDIANB','INDHOTEL',
    'HFCL','HAVELLS','BAJFINANCE','BANDHANBNK','BANKBARODA','BANKINDIA','BDL','BEL',
    'BHARATFORG','BHARTIARTL','BHEL','BIOCON','BLUESTARCO','BOSCHLTD','BPCL','BSE',
    'CAMS','CANBK','CDSL','CGPOWER','CHOLAFIN','CIPLA','COALINDIA','COFORGE','COLPAL',
    'CONCOR','CROMPTON','CUMMINSIND','CYIENT','DABUR','DALBHARAT','DELHIVERY',
    'DIVISLAB','DIXON','DLF','DMART','DRREDDY','EICHERMOT','ETERNAL','EXIDEIND',
    'FEDERALBNK','FORTIS','GAIL','GLENMARK','GMRAIRPORT','GODREJCP','GODREJPROP',
    'GRASIM','HAL','HDFCAMC','HDFCBANK','HDFCLIFE','HEROMOTOCO','HINDALCO','HINDPETRO',
    'HINDUNILVR','HINDZINC','HUDCO','ICICIBANK','ICICIGI','ICICIPRULI','IDEA',
    'IDFCFIRSTB','IEX','IGL','IIFL','INDIGO','INDUSINDBK','INDUSTOWER','INFY',
    'INOXWIND','IOC','IRCTC','IREDA','IRFC','ITC','JINDALSTEL','JIOFIN','JSWENERGY',
    'JSWSTEEL','JUBLFOOD','KALYANKJIL','KAYNES','KEI','KFINTECH','KOTAKBANK',
    'KPITTECH','LAURUSLABS','LICHSGFIN','LICI','LODHA','LT','LTF','LTIM','LUPIN','M&M',
    'MANAPPURAM','MANKIND','MARICO','MARUTI','MAXHEALTH','MAZDOCK','MCX','MFSL',
    'MOTHERSON','MPHASIS','MUTHOOTFIN','NATIONALUM','NAUKRI','NBCC','NCC','NESTLEIND',
    'NMDC','NTPC','NUVAMA','NYKAA','OBEROIRLTY','OFSS','OIL','ONGC','PAGEIND',
    'PATANJALI','PAYTM','PFC','PGEL','PHOENIXLTD','PIIND','PNB','PNBHOUSING',
    'POLICYBZR','POLYCAB','PIDILITIND','PERSISTENT','PETRONET','NHPC','HCLTECH',
    'POWERGRID','PPLPHARMA','PRESTIGE','RBLBANK','RECLTD','RELIANCE','RVNL','SAIL',
    'SAMMAANCAP','SBICARD','SBILIFE','SBIN','SHREECEM','SHRIRAMFIN','SIEMENS',
    'SOLARINDS','SONACOMS','SRF','SUNPHARMA','SUPREMEIND','SUZLON','SYNGENE',
    'TATACONSUM','TATAELXSI','TATAMOTORS','TATAPOWER','TATASTEEL','TATATECH','TCS',
    'TECHM','TIINDIA','TITAGARH','TITAN','TORNTPHARM','TORNTPOWER','TRENT','TVSMOTOR',
    'ULTRACEMCO','UNIONBANK','UNITDSPR','UNOMINDA','UPL','VBL','VEDL','VOLTAS',
    'WIPRO','YESBANK','ZYDUSLIFE'
]

# ==================== PRICE FUNCTIONS ==================== #
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
    if (now.weekday() == 4 and now.time() >= time(15, 30)) or now.weekday() in (5, 6):
        return last, df.index[-1]
    else:
        return prev, df.index[-2]

def fetch_daily(symbol: str, exchange: str = "NSE", bars: int = 60):
    try:
        df = tv.get_hist(symbol=symbol, exchange=exchange,
                         interval=Interval.in_daily, n_bars=bars)
    except Exception:
        return None
    if df is None or df.empty:
        return None
    if not {"open","high","low","close"}.issubset(df.columns):
        return None
    return df.dropna(subset=["open","high","low","close"])

def get_atr_with_talib(daily_df, period=10):
    atr_arr = ta.ATR(
        daily_df["high"], daily_df["low"], daily_df["close"],
        timeperiod=period
    )
    val = atr_arr.iloc[-1]
    return None if np.isnan(val) else float(val)

def price_cycles(close_price: float, steps):
    res, sup = [], []
    up = down = close_price
    for s in steps:
        up += s
        down -= s
        res.append(up)
        sup.append(down)
    return res, sup

# ------------------- APP LOGIC ------------------- #
mode = st.radio("Mode:", ["Single Symbol", "Scan Universe (by ATR%)"])

# ==================================================
#              SINGLE SYMBOL MODE
# ==================================================
if mode == "Single Symbol":

    symbol = st.selectbox("Select Symbol", SYMBOLS)

    weekly_close, wdate = get_weekly_close(symbol)
    if weekly_close is None:
        st.error("⛔ Could not fetch weekly data.")
        st.stop()

    df_daily = fetch_daily(symbol)
    if df_daily is None or df_daily.empty:
        st.error("⛔ Could not fetch daily data.")
        st.stop()

    last_close = float(df_daily["close"].iloc[-1])
    last_ts = df_daily.index[-1]
    atr = get_atr_with_talib(df_daily)

    # --- Header Info ---
    st.markdown(f"### <span style='color:blue; font-size:26px; font-weight:bold;'>{symbol}</span>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:18px;'>Weekly Close: <b>{weekly_close:.2f}</b> &nbsp;&nbsp; (Bar Date: {wdate.date()})</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:18px;'>Last Daily Candle: <b>{last_ts}</b> &nbsp;&nbsp; Last Close: <b>{last_close:.2f}</b></div>", unsafe_allow_html=True)
    if atr:
        atrp = (atr / last_close) * 100
        st.markdown(f"<div style='font-size:18px;'>ATR(10): <b>{atr:.2f}</b> &nbsp;&nbsp; ATR%: <b>{atrp:.2f}%</b></div>", unsafe_allow_html=True)

    st.markdown("---")

    # -------- Cycle Step Presets -------- #
    presets = {
        "Default 30-60-90-120-150": [30, 60, 90, 120, 150],
        "Short 3-6-9-12-15": [3, 6, 9, 12, 15],
        "Micro .3-.6-.9-1.2-1.5": [0.3, 0.6, 0.9, 1.2, 1.5],
        "Long 300-600-900-1200-1500": [300, 600, 900, 1200, 1500],
        "Custom": None
    }

    choice = st.selectbox("Cycle Step Preset", list(presets.keys()))

    if choice == "Custom":
        raw = st.text_input("Enter comma-separated steps", "30,60,90")
        try:
            steps = [float(x.strip()) for x in raw.split(",") if x.strip()]
        except:
            st.error("Invalid custom range")
            st.stop()
    else:
        steps = presets[choice]

    # -------------- Compute cycles -------------- #
    R_raw, S_raw = price_cycles(weekly_close, steps)

    # Always keep 5 R and 5 S → OPTION A
    R = R_raw[:5]
    S = S_raw[:5]

    # -------------- DYNAMIC RECLASSIFICATION -------------- #
    new_R = []
    new_S = []

    # Resistances above last close stay R
    # Those below last close convert to Support
    for val in R:
        if val > last_close:
            new_R.append(val)
        else:
            new_S.append(val)

    # Keep original S levels
    for val in S:
        new_S.append(val)

    # Ensure exactly 5 R and 5 S (Option A)
    while len(new_R) < 5:
        new_R.append(None)
    new_R = new_R[:5]

    while len(new_S) < 5:
        new_S.append(None)
    new_S = new_S[:5]

    # -------------- DISPLAY STYLED TEXT (no table) -------------- #
    st.markdown("## 🎯 Support & Resistance Levels")

    # ---------------- RESISTANCE BLOCK ---------------- #
    st.markdown("<div style='font-size:22px; color:#ff9933; font-weight:bold;'>🔶 Resistance Levels</div>", unsafe_allow_html=True)

    for i, val in enumerate(new_R, 1):
        txt = f"R{i}: {val:.2f}" if val else f"R{i}: ---"
        st.markdown(f"<div style='font-size:20px; color:#ffb366;'>{txt}</div>", unsafe_allow_html=True)

    # ---------------- TODAY PRICE ---------------- #
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:22px; background:#fff799; padding:6px; width:220px; border-radius:6px;'><b>Today Price: {last_close:.2f}</b></div>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # ---------------- SUPPORT BLOCK ---------------- #
    st.markdown("<div style='font-size:22px; color:#33cc33; font-weight:bold;'>🟢 Support Levels</div>", unsafe_allow_html=True)

    for i, val in enumerate(new_S, 1):
        txt = f"S{i}: {val:.2f}" if val else f"S{i}: ---"
        st.markdown(f"<div style='font-size:20px; color:#99ff99;'>{txt}</div>", unsafe_allow_html=True)

    # ------- CSV Export ------- #
    df_export = pd.DataFrame({
        "Level": [f"R{i}" for i in range(1,6)] + ["Today Price"] + [f"S{i}" for i in range(1,6)],
        "Price": new_R + [last_close] + new_S
    })
    csv_data = df_export.to_csv(index=False)
    st.download_button("📥 Download SR Levels CSV",
                       data=csv_data,
                       file_name=f"{symbol}_SR_levels.csv",
                       mime="text/csv")

    # ------- PDF Export ------- #
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, f"{symbol} - Support & Resistance Levels", ln=True, align="C")

    for lvl, val in zip(df_export["Level"], df_export["Price"]):
        pdf.cell(50, 10, lvl, 1, 0)
        pdf.cell(40, 10, f"{val:.2f}", 1, 1)

    pdf_bytes = pdf.output(dest="S").encode("latin-1")
    st.download_button("📥 Download SR Levels PDF",
                       data=pdf_bytes,
                       file_name=f"{symbol}_SR_levels.pdf",
                       mime="application/pdf")

# ==================================================
#            ATR% SCAN MODE (UNIVERSE)
# ==================================================
else:
    st.write("## 🔍 ATR% Scan — High Volatility Stocks")

    period = st.number_input("ATR lookback (days)", min_value=5, max_value=60, value=10, step=1)
    top_n = st.number_input("Top N volatile stocks", min_value=5, max_value=len(SYMBOLS), value=20, step=5)

    results = []
    for s in SYMBOLS:
        df = fetch_daily(s)
        if df is None: continue
        try:
            lc = float(df["close"].iloc[-1])
            atr = get_atr_with_talib(df, period)
            if atr:
                results.append((s, lc, atr, (atr/lc)*100))
        except:
            pass

    if results:
        df_scan = pd.DataFrame(results, columns=["Symbol","Last Close","ATR","ATR%"])
        df_scan = df_scan.sort_values("ATR%", ascending=False).head(top_n)
        st.dataframe(df_scan, use_container_width=True)

        st.download_button("Download ATR Scan CSV",
                           df_scan.to_csv(index=False),
                           "ATR_scan.csv",
                           "text/csv")
    else:
        st.write("No data available.")
