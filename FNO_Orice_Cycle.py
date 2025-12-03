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

from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter

# ----------------------  CONFIG  ---------------------- #
st.set_page_config(page_title="NSE Price Cycle & ATRP Scanner_By Rao_Gs", layout="wide")

# ----------------------  BG IMAGE  -------------------- #
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
    [data-testid="stAppViewContainer"] > .main {{
        background-image: url("data:image/png;base64,{b64}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    .block-container {{
        padding-top: 1rem;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# Call once at start (image must exist in same folder)
set_background("SMB2.jpg")

st.title("📈 Price Cycle + ATRP Scanner with Styled Output")

tv = TvDatafeed()

# ------------------- SYMBOL UNIVERSE ------------------- #
SYMBOLS = [
    'NIFTY','BANKNIFTY','CNXFINANCE','CNXMIDCAP','NIFTYJR','360ONE','ABB','ABCAPITAL',
    'ADANIENSOL','ADANIENT','ADANIGREEN','ADANIPORTS','ALKEM','AMBER','AMBUJACEM',
    'ANGELONE','APLAPOLLO','APOLLOHOSP','ASHOKLEY','ASIANPAINT','ASTRAL','AUBANK',
    'AUROPHARMA','AXISBANK','BAJAJ_AUTO','BAJAJFINSV','BRITANNIA','INDIANB',
    'INDHOTEL','HFCL','HAVELLS','BAJFINANCE','BANDHANBNK','BANKBARODA','BANKINDIA',
    'BDL','BEL','BHARATFORG','BHARTIARTL','BHEL','BIOCON','BLUESTARCO','BOSCHLTD',
    'BPCL','BSE','CAMS','CANBK','CDSL','CGPOWER','CHOLAFIN','CIPLA','COALINDIA',
    'COFORGE','COLPAL','CONCOR','CROMPTON','CUMMINSIND','CYIENT','DABUR','DALBHARAT',
    'DELHIVERY','DIVISLAB','DIXON','DLF','DMART','DRREDDY','EICHERMOT','ETERNAL',
    'EXIDEIND','FEDERALBNK','FORTIS','GAIL','GLENMARK','GMRAIRPORT','GODREJCP',
    'GODREJPROP','GRASIM','HAL','HDFCAMC','HDFCBANK','HDFCLIFE','HEROMOTOCO',
    'HINDALCO','HINDPETRO','HINDUNILVR','HINDZINC','HUDCO','ICICIBANK','ICICIGI',
    'ICICIPRULI','IDEA','IDFCFIRSTB','IEX','IGL','IIFL','INDIGO','INDUSINDBK',
    'INDUSTOWER','INFY','INOXWIND','IOC','IRCTC','IREDA','IRFC','ITC','JINDALSTEL',
    'JIOFIN','JSWENERGY','JSWSTEEL','JUBLFOOD','KALYANKJIL','KAYNES','KEI',
    'KFINTECH','KOTAKBANK','KPITTECH','LAURUSLABS','LICHSGFIN','LICI','LODHA','LT',
    'LTF','LTIM','LUPIN','M&M','MANAPPURAM','MANKIND','MARICO','MARUTI','MAXHEALTH',
    'MAZDOCK','MCX','MFSL','MOTHERSON','MPHASIS','MUTHOOTFIN','NATIONALUM','NAUKRI',
    'NBCC','NCC','NESTLEIND','NMDC','NTPC','NUVAMA','NYKAA','OBEROIRLTY','OFSS',
    'OIL','ONGC','PAGEIND','PATANJALI','PAYTM','PFC','PGEL','PHOENIXLTD','PIIND',
    'PNB','PNBHOUSING','POLICYBZR','POLYCAB','PIDILITIND','PERSISTENT','PETRONET',
    'NHPC','HCLTECH','POWERGRID','PPLPHARMA','PRESTIGE','RBLBANK','RECLTD','RELIANCE',
    'RVNL','SAIL','SAMMAANCAP','SBICARD','SBILIFE','SBIN','SHREECEM','SHRIRAMFIN',
    'SIEMENS','SOLARINDS','SONACOMS','SRF','SUNPHARMA','SUPREMEIND','SUZLON',
    'SYNGENE','TATACONSUM','TATAELXSI','TATAMOTORS','TATAPOWER','TATASTEEL',
    'TATATECH','TCS','TECHM','TIINDIA','TITAGARH','TITAN','TORNTPHARM','TORNTPOWER',
    'TRENT','TVSMOTOR','ULTRACEMCO','UNIONBANK','UNITDSPR','UNOMINDA','UPL','VBL',
    'VEDL','VOLTAS','WIPRO','YESBANK','ZYDUSLIFE'
]

# ------------------- HELPER FUNCTIONS ------------------- #
def get_weekly_close(symbol: str, exchange: str = "NSE"):
    """Return (weekly_close_used, bar_datetime) based on Friday 15:30 logic."""
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
    if (now.weekday() == 4 and now.time() >= time(15, 30)) or now.weekday() in (5, 6):
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
    if not {"open", "high", "low", "close"}.issubset(df.columns):
        return None
    df = df.dropna(subset=["open", "high", "low", "close"])
    return df


def get_atr_with_talib(daily_df, period=10):
    highs = daily_df["high"].values
    lows = daily_df["low"].values
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


def create_pdf(levels, symbol: str):
    """
    Create a colored PDF of SR levels and return bytes.
    levels: list of (SR_Level, Price)
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)

    data = [["SR Level", "Price"]] + [[lvl, f"{price:.2f}"] for lvl, price in levels]
    tbl = Table(data, colWidths=[120, 120])

    style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#003366")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 14),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("ALIGN", (0, 1), (-1, -1), "CENTER"),
        ("BOX", (0, 0), (-1, -1), 1, colors.black),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ]

    # Row-wise colors based on SR label
    for idx, (lvl, _) in enumerate(levels, start=1):  # start=1 because header is row 0
        if lvl.startswith("R"):
            style.append(
                ("BACKGROUND", (0, idx), (-1, idx), colors.HexColor("#ffb380"))
            )  # orange
        elif lvl == "Today Price":
            style.append(
                ("BACKGROUND", (0, idx), (-1, idx), colors.HexColor("#fff799"))
            )  # yellow
        elif lvl.startswith("S"):
            style.append(
                ("BACKGROUND", (0, idx), (-1, idx), colors.HexColor("#b3ffb3"))
            )  # green

    tbl.setStyle(TableStyle(style))
    doc.build([tbl])
    buffer.seek(0)
    return buffer.getvalue()


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

    daily_df = fetch_daily(symbol, bars=60)
    if daily_df is None or daily_df.empty:
        st.error("⛔ Could not fetch daily data for symbol: " + symbol)
        st.stop()

    last_close = float(daily_df["close"].iloc[-1])
    atr = get_atr_with_talib(daily_df, period=10)

    # --- Header Info with styling ---
    st.markdown(
        f"### <span style='color:#4dc3ff; font-weight:bold;'>{symbol}</span>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"**Weekly Close (used for cycles):** `{weekly_close:.2f}`  &nbsp; "
        f"**Bar date:** `{wdate.date()}`"
    )
    st.markdown(f"**Today Close (Daily):** `{last_close:.2f}`")

    if atr:
        atrp = (atr / last_close) * 100
        st.markdown(
            f"**ATR(10):** `{atr:.2f}`  &nbsp;&nbsp;  **ATR%:** `{atrp:.2f}%`"
        )

    st.markdown("---")

    # Cycle-step selection
    presets = {
        "Default 30-60-90-120-150": [30, 60, 90, 120, 150],
        "Short 3-6-9-12-15": [3, 6, 9, 12, 15],
        "Long 300-600-900-1200-1500": [300, 600, 900, 1200, 1500],
        "Custom": None,
    }
    choice = st.selectbox("Cycle Step Preset", list(presets.keys()))
    if choice == "Custom":
        raw = st.text_input(
            "Enter comma-separated steps (e.g. 25,50,75)", "30,60,90"
        )
        try:
            steps = [int(x.strip()) for x in raw.split(",") if x.strip()]
        except Exception:
            st.error("⚠ Invalid custom steps.")
            st.stop()
    else:
        steps = presets[choice]

    # ----- Price cycles computed from WEEKLY CLOSE -----
    res_levels, sup_levels = price_cycles(weekly_close, steps)

    # ----- Build SR level list for table + PDF -----
    levels = []

    # Resistance: R4 to R1 (reverse list)
    for i, val in enumerate(reversed(res_levels), start=1):
        levels.append((f"R{i}", val))

    # Today price
    levels.append(("Today Price", last_close))

    # Supports: S1 to S4
    for i, val in enumerate(sup_levels, start=1):
        levels.append((f"S{i}", val))

    df_sr = pd.DataFrame(levels, columns=["SR_Level", "Price"])

    # ----- Beautiful UI styled table -----
    def style_rows(row):
        lvl = row["SR_Level"]
        if lvl.startswith("R"):
            return [
                "background-color: #ffb380; font-weight: bold; color: black"
            ] * 2
        elif lvl == "Today Price":
            return [
                "background-color: #fff799; font-weight: bold; color: black"
            ] * 2
        elif lvl.startswith("S"):
            return [
                "background-color: #b3ffb3; font-weight: bold; color: black"
            ] * 2
        return [""] * 2

    styled_ui = (
        df_sr.style.apply(style_rows, axis=1)
        .set_table_styles(
            [
                {
                    "selector": "th",
                    "props": "background-color: #003366; color: white; padding:8px; font-size:16px;",
                },
                {
                    "selector": "td",
                    "props": "padding: 6px; font-size:15px;",
                },
                {"selector": "table", "props": "border-radius: 8px; overflow:hidden;"},
            ]
        )
        .format({"Price": "{:.2f}"})
    )

    st.subheader("📘 Support & Resistance Dashboard")
    st.table(styled_ui)

    # ==================================================
    #               CHART WITH R/S LINES
    # ==================================================
    st.subheader("📉 Price Chart with S/R Levels")

    chart_df = daily_df.copy()
    if not chart_df.empty:
        fig, ax = plt.subplots(figsize=(12, 6))

        ax.plot(chart_df.index, chart_df["close"], label="Close Price", linewidth=1.6)

        # R levels (orange)
        for i, val in enumerate(reversed(res_levels), start=1):
            ax.axhline(val, color="#ff6600", linestyle="--", linewidth=1)
            ax.text(
                chart_df.index[-1],
                val,
                f" R{i}",
                color="white",
                fontsize=8,
                va="center",
            )

        # Today close (yellow)
        ax.axhline(last_close, color="yellow", linestyle="-", linewidth=2)
        ax.text(
            chart_df.index[-1],
            last_close,
            " Today",
            color="yellow",
            fontsize=8,
            va="bottom",
        )

        # S levels (green)
        for i, val in enumerate(sup_levels, start=1):
            ax.axhline(val, color="#00cc44", linestyle="--", linewidth=1)
            ax.text(
                chart_df.index[-1],
                val,
                f" S{i}",
                color="white",
                fontsize=8,
                va="center",
            )

        ax.set_title(
            f"{symbol} — Price with Support/Resistance Levels",
            fontsize=16,
            color="cyan",
        )
        ax.grid(True, linestyle=":", alpha=0.3)
        ax.set_facecolor("#111")
        fig.patch.set_facecolor("#111")

        st.pyplot(fig)
    else:
        st.info("Not enough candles to draw chart.")

    # ==================================================
    #                 EXPORT PDF & CSV
    # ==================================================
    st.subheader("📦 Export Levels")

    # CSV
    csv_data = df_sr.to_csv(index=False)
    st.download_button(
        "📥 Download SR Levels CSV",
        data=csv_data,
        file_name=f"{symbol}_SR_Levels.csv",
        mime="text/csv",
    )

    # PDF
    pdf_bytes = create_pdf(levels, symbol)
    st.download_button(
        "📥 Download SR Levels PDF",
        data=pdf_bytes,
        file_name=f"{symbol}_SR_Levels.pdf",
        mime="application/pdf",
    )

# ==================================================
#            ATR% SCAN MODE (UNIVERSE)
# ==================================================
else:
    st.write("## 🔍 ATR% Scan — High Volatility Stocks")

    period = st.number_input(
        "ATR lookback (days)", min_value=5, max_value=60, value=10, step=1
    )
    top_n = st.number_input(
        "Top N volatile stocks to show",
        min_value=5,
        max_value=len(SYMBOLS),
        value=20,
        step=5,
    )

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
        df_scan = pd.DataFrame(
            results, columns=["Symbol", "Last Close", "ATR", "ATR%"]
        )
        df_scan = (
            df_scan.sort_values("ATR%", ascending=False)
            .head(top_n)
            .reset_index(drop=True)
        )
        st.subheader(f"Top {top_n} Symbols by ATR%")
        st.dataframe(df_scan)

        csv = df_scan.to_csv(index=False)
        st.download_button(
            "Download ATR% Scan CSV",
            data=csv,
            file_name="atr_percent_scan.csv",
            mime="text/csv",
        )
    else:
        st.write("No symbols met criteria (data unavailable or insufficient history).")
