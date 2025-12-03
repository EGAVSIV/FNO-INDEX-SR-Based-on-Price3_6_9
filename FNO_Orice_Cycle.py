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
from fpdf import FPDF  # CLOUD-SAFE PDF GENERATOR (NO REPORTLAB!)

# ----------------------  CONFIG  ---------------------- #
st.set_page_config(page_title="NSE Price Cycle & ATRP Scanner_By Rao_Gs", layout="wide")

# ----------------------  BG IMAGE  -------------------- #
def set_background(image_path: str):
    try:
        with open(image_path, "rb") as f:
            img_data = f.read()
        b64 = base64.b64encode(img_data).decode()
    except:
        return

    css = f"""
    <style>
    [data-testid="stAppViewContainer"] > .main {{
        background-image: url("data:image/png;base64,{b64}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    .block-container {{ padding-top: 1rem; }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

set_background("SMB2.jpg")

st.title("📈 Price Cycle + ATRP Scanner with Styled Output")

tv = TvDatafeed()

# ------------------- SYMBOL UNIVERSE ------------------- #
SYMBOLS = ["NIFTY","BANKNIFTY","RELIANCE","HDFCBANK","ICICIBANK","INFY","TCS","SBIN",
           "AXISBANK","HCLTECH","ITC","LT","HINDUNILVR","MARUTI","ULTRACEMCO","SUNPHARMA"]


# ------------------- HELPER FUNCTIONS ------------------- #
def get_weekly_close(symbol: str):
    try:
        df = tv.get_hist(symbol=symbol, exchange="NSE",
                         interval=Interval.in_weekly, n_bars=2)
    except:
        return None, None

    if df is None or df.empty:
        return None, None

    last = float(df["close"].iloc[-1])
    prev = float(df["close"].iloc[-2])

    now = datetime.now()
    if (now.weekday()==4 and now.time() >= time(15,30)) or now.weekday() in (5,6):
        return last, df.index[-1]
    else:
        return prev, df.index[-2]


def fetch_daily(symbol: str, bars: int = 60):
    try:
        df = tv.get_hist(symbol=symbol, exchange="NSE",
                         interval=Interval.in_daily, n_bars=bars)
    except:
        return None
    return df


def get_atr_with_talib(df, period=10):
    atr = ta.ATR(df["high"], df["low"], df["close"], timeperiod=period)
    val = atr.iloc[-1]
    return None if np.isnan(val) else float(val)


def price_cycles(close_price: float, steps):
    res, sup = [], []
    up, down = close_price, close_price
    for s in steps:
        up += s; down -= s
        res.append(up); sup.append(down)
    return res, sup


# --------------------------------------------------------
#  PDF GENERATOR (Cloud Compatible)
# --------------------------------------------------------
def create_pdf(levels, symbol):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"{symbol} — Support & Resistance Levels", ln=True, align="C")

    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)

    # Header
    pdf.set_fill_color(0, 51, 102)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(60, 10, "SR Level", border=1, fill=True, align="C")
    pdf.cell(60, 10, "Price", border=1, fill=True, ln=True, align="C")

    pdf.set_font("Arial", "", 12)
    pdf.set_text_color(0, 0, 0)

    # Rows
    for lvl, price in levels:
        if lvl.startswith("R"):
            pdf.set_fill_color(255, 179, 128)
        elif lvl == "Today Price":
            pdf.set_fill_color(255, 247, 153)
        elif lvl.startswith("S"):
            pdf.set_fill_color(179, 255, 179)

        pdf.cell(60, 10, lvl, border=1, fill=True, align="C")
        pdf.cell(60, 10, f"{price:.2f}", border=1, fill=True, ln=True, align="C")

    return pdf.output(dest="S").encode("latin-1")


# --------------------------------------------------------
#                   APP LOGIC
# --------------------------------------------------------
mode = st.radio("Mode:", ["Single Symbol", "Scan Universe (by ATR%)"])


# ===============================
#       SINGLE SYMBOL MODE
# ===============================
if mode == "Single Symbol":

    symbol = st.selectbox("Select Symbol", SYMBOLS)

    weekly_close, wdate = get_weekly_close(symbol)
    if weekly_close is None:
        st.error("Could not fetch weekly data.")
        st.stop()

    df_daily = fetch_daily(symbol)
    if df_daily is None or df_daily.empty:
        st.error("Daily data unavailable.")
        st.stop()

    last_close = float(df_daily["close"].iloc[-1])
    atr = get_atr_with_talib(df_daily)

    st.markdown(f"### **{symbol}**")
    st.write(f"Weekly Close: **{weekly_close:.2f}**")
    st.write(f"Today's Close: **{last_close:.2f}**")

    # Step presets
    steps = [30,60,90,120,150]
    res_levels, sup_levels = price_cycles(weekly_close, steps)

    # Build SR list
    levels = []
    for i,v in enumerate(reversed(res_levels),1):
        levels.append((f"R{i}", v))
    levels.append(("Today Price", last_close))
    for i,v in enumerate(sup_levels,1):
        levels.append((f"S{i}", v))

    df_sr = pd.DataFrame(levels, columns=["Level","Price"])

    # ---- Styled SR Table ----
    def color_rows(row):
        lvl=row["Level"]
        if lvl.startswith("R"): return ["background-color:#ffb380"]*2
        if lvl=="Today Price": return ["background-color:#fff799"]*2
        if lvl.startswith("S"): return ["background-color:#b3ffb3"]*2
        return [""]*2

    styled = (
        df_sr.style.apply(color_rows, axis=1)
        .set_table_styles([
            {'selector':'th','props':'background-color:#003366; color:white; padding:10px; font-size:16px;'}
        ])
        .format({"Price":"{:.2f}"})
    )

    st.subheader("📘 Support & Resistance Table")
    st.table(styled)

    # ---- Chart ----
    st.subheader("📉 Chart with S/R Lines")

    fig, ax = plt.subplots(figsize=(12,5))
    ax.plot(df_daily.index, df_daily["close"], label="Close", linewidth=1.8)

    for i,v in enumerate(reversed(res_levels),1):
        ax.axhline(v, color="orange", linestyle="--")
        ax.text(df_daily.index[-1], v, f" R{i}", color="white")

    ax.axhline(last_close, color="yellow", linewidth=2)
    ax.text(df_daily.index[-1], last_close, " Today", color="yellow")

    for i,v in enumerate(sup_levels,1):
        ax.axhline(v, color="green", linestyle="--")
        ax.text(df_daily.index[-1], v, f" S{i}", color="white")

    ax.set_facecolor("#111")
    fig.patch.set_facecolor("#111")
    ax.grid(True, linestyle=":")

    st.pyplot(fig)

    # ---- Export ----
    st.subheader("📦 Export Tools")

    # CSV
    csv_data = df_sr.to_csv(index=False)
    st.download_button("📥 Download CSV", csv_data, file_name=f"{symbol}_SR.csv")

    # PDF (cloud-safe: FPDF)
    pdf_bytes = create_pdf(levels, symbol)
    st.download_button(
        "📥 Download PDF",
        data=pdf_bytes,
        file_name=f"{symbol}_SR.pdf",
        mime="application/pdf",
    )


# ===============================
#     ATR% SCAN MODE
# ===============================
else:
    st.write("### 🔍 ATR% Scan — High Volatility Stocks")

    results = []
    for s in SYMBOLS:
        df = fetch_daily(s)
        if df is None: continue
        try:
            lc = float(df["close"].iloc[-1])
            atr = get_atr_with_talib(df)
            if atr:
                atrp = (atr/lc)*100
                results.append((s, lc, atr, atrp))
        except:
            continue

    df_scan = pd.DataFrame(results, columns=["Symbol","Close","ATR","ATR%"])
    df_scan = df_scan.sort_values("ATR%", ascending=False).reset_index(drop=True)
    st.dataframe(df_scan)

    st.download_button(
        "📥 Download ATR Scan CSV",
        df_scan.to_csv(index=False),
        file_name="ATR_scan.csv"
    )
