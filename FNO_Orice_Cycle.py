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
    # Friday after 15:30 IST or weekend -> use last weekly bar
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
    df = df.dropna(subset=["open","high","low","close"])
    return df

def get_atr_with_talib(daily_df, period=10):
    highs  = daily_df["high"].values
    lows   = daily_df["low"].values
    closes = daily_df["close"].values
    atr_array = ta.ATR(highs, lows, closes, timeperiod=period)
    atr = atr_array[-1]
    if np.isnan(atr):
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

# ---------- IMAGE TABLE FOR SR LEVELS ---------- #
def create_sr_table_image(df_sr, symbol):
    fig, ax = plt.subplots(figsize=(4, 6))
    ax.axis('tight')
    ax.axis('off')

    table = ax.table(
        cellText=df_sr.values,
        colLabels=df_sr.columns,
        cellLoc='center',
        loc='center'
    )

    # Header style
    for (row, col), cell in table.get_celld().items():
        if row == 0:
            cell.set_facecolor("#003366")
            cell.set_text_props(color="white", weight="bold")
        else:
            lvl = df_sr.iloc[row-1, 0]
            if lvl.startswith("R"):
                cell.set_facecolor("#ffb380")
            elif lvl == "Today Price":
                cell.set_facecolor("#fff799")
            elif lvl.startswith("S"):
                cell.set_facecolor("#b3ffb3")

    fig.tight_layout()
    buf = BytesIO()
    plt.savefig(buf, format="png", dpi=200, bbox_inches="tight")
    buf.seek(0)
    plt.close(fig)
    return buf.getvalue()

# ---------- PDF EXPORT FOR SR LEVELS ---------- #
def create_pdf(levels, symbol):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, f"{symbol} - Support and Resistance Levels", ln=True, align="C")
    pdf.ln(5)

    pdf.set_font("Arial", "B", 12)
    pdf.set_fill_color(0, 51, 102)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(50, 10, "Level", 1, 0, "C", True)
    pdf.cell(60, 10, "Price", 1, 1, "C", True)

    pdf.set_font("Arial", "", 12)
    pdf.set_text_color(0, 0, 0)

    for lvl, price in levels:
        if lvl.startswith("R"):
            pdf.set_fill_color(255, 179, 128)
        elif lvl == "Today Price":
            pdf.set_fill_color(255, 247, 153)
        else:
            pdf.set_fill_color(179, 255, 179)

        pdf.cell(50, 10, lvl, 1, 0, "C", True)
        pdf.cell(60, 10, f"{price:.2f}", 1, 1, "C", True)

    return pdf.output(dest="S").encode("latin-1")

# ------------------- APP LOGIC ------------------- #
mode = st.radio("Mode:", ["Single Symbol", "Scan Universe (by ATR%)"])

# ==================================================
#              SINGLE SYMBOL MODE
# ==================================================
if mode == "Single Symbol":
    symbol = st.selectbox("Select Symbol", SYMBOLS)
    weekly_close, wdate = get_weekly_close(symbol)
    if weekly_close is None:
        st.error("⛔ Could not fetch weekly data for symbol: " + symbol)
        st.stop()

    daily_df = fetch_daily(symbol)
    if daily_df is not None and not daily_df.empty:
        last_close = float(daily_df["close"].iloc[-1])
        last_ts = daily_df.index[-1]
        atr = get_atr_with_talib(daily_df, period=10)
    else:
        st.error("⛔ Could not fetch daily data for symbol: " + symbol)
        st.stop()

    # --- Header Info with styling ---
    st.markdown(f"### **<span style='color:blue;'>{symbol}</span>**",
                unsafe_allow_html=True)
    st.markdown(f"**Weekly Close (used):** {weekly_close:.2f}  (bar date: {wdate.date()})")
    st.markdown(f"**Last Daily Candle:** {last_ts}  **Last Close:** {last_close:.2f}")
    if atr:
        atrp = (atr / last_close) * 100
        st.markdown(f"**ATR(10):** {atr:.2f}    &nbsp;&nbsp;  **ATR%:** {atrp:.2f}%")

    st.markdown("---")

    # Cycle-step selection (range presets)
    presets = {
        "Default 30-60-90-120-150": [30, 60, 90, 120, 150],
        "Short 3-6-9-12-15": [3, 6, 9, 12, 15],
        "Long 300-600-900-1200-1500": [300, 600, 900, 1200, 1500],
        "Micro .3-.6-.9-1.2-1.5": [0.3, 0.6, 0.9, 1.2, 1.5],
        "Custom": None
    }
    choice = st.selectbox("Cycle Step Preset", list(presets.keys()))
    if choice == "Custom":
        raw = st.text_input("Enter comma-separated steps (e.g. 25,50,75)", "30,60,90")
        try:
            steps = [int(x.strip()) for x in raw.split(",") if x.strip()]
        except Exception:
            st.error("⚠ Invalid custom steps.")
            st.stop()
    else:
        steps = presets[choice]

    # Compute price cycles based on WEEKLY CLOSE
    res_levels, sup_levels = price_cycles(weekly_close, steps)

    # Build vertical SR list: R4..R1, Today Price, S1..S4
    levels = []
    for i, val in enumerate(reversed(res_levels), 1):
        levels.append((f"R{i}", val))
    levels.append(("Today Price", last_close))
    for i, val in enumerate(sup_levels, 1):
        levels.append((f"S{i}", val))

    df_sr = pd.DataFrame(levels, columns=["Level", "Price"])

    # Create image of SR table
    img_bytes = create_sr_table_image(df_sr, symbol)

    st.subheader("📌 Support & Resistance Levels (Image)")
    st.image(img_bytes, use_column_width=False)

    # CSV Download
    csv_data = df_sr.to_csv(index=False)
    st.download_button("📥 Download SR Levels CSV",
                       data=csv_data,
                       file_name=f"{symbol}_SR_levels.csv",
                       mime="text/csv")

    # PDF Download
    pdf_bytes = create_pdf(levels, symbol)
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
    top_n = st.number_input("Top N volatile stocks to show",
                            min_value=5, max_value=len(SYMBOLS), value=20, step=5)

    results = []
    for s in SYMBOLS:
        df = fetch_daily(s)
        if df is None or df.shape[0] < period + 5:
            continue
        try:
            last_close = float(df["close"].iloc[-1])
            atr = get_atr_with_talib(df, period=period)
            if atr is None or np.isnan(atr):
                continue
            atrp = (atr / last_close) * 100
            results.append((s, last_close, atr, atrp))
        except Exception:
            continue

    if results:
        df_scan = pd.DataFrame(results, columns=["Symbol", "Last Close", "ATR", "ATR%"])
        df_scan = df_scan.sort_values("ATR%", ascending=False).head(top_n).reset_index(drop=True)
        st.subheader(f"Top {top_n} Symbols by ATR%")
        st.dataframe(df_scan, use_container_width=True)

        csv = df_scan.to_csv(index=False)
        st.download_button("Download ATR% Scan CSV",
                           data=csv,
                           file_name="atr_percent_scan.csv",
                           mime="text/csv")
    else:
        st.write("No symbols met criteria (data unavailable or insufficient history).")
