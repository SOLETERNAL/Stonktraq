
import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import matplotlib.pyplot as plt

# -----------------------------
# CONFIG
# -----------------------------
st.set_page_config(page_title="EMA Breakout Scanner", layout="wide")
st.title("📈 EMA Breakthrough + Sentiment Scanner")

# -----------------------------
# INPUT
# -----------------------------
tickers_input = st.text_input(
    "Enter stock tickers (comma-separated):",
    value="AAPL,TSLA,NVDA,AMZN,MSFT"
)
tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]

# -----------------------------
# FUNCTIONS
# -----------------------------
@st.cache_data
def fetch_data(ticker):
    df = yf.download(ticker, period="90d", interval="1d")
    df["EMA40"] = df["Close"].ewm(span=40).mean()
    df["Signal"] = (df["Close"] > df["EMA40"]) & (df["Close"].shift(1) <= df["EMA40"].shift(1))
    return df

def fetch_stocktwits(ticker):
    url = f"https://api.stocktwits.com/api/2/streams/symbol/{ticker}.json"
    try:
        r = requests.get(url)
        if r.status_code != 200:
            return "Error loading feed", 0
        messages = r.json()["messages"]
        count = len(messages)
        feed_preview = "\n\n".join([f"{msg['user']['username']}: {msg['body'][:80]}..." for msg in messages[:5]])
        return feed_preview, count
    except Exception as e:
        return str(e), 0

# -----------------------------
# SCANNER OUTPUT
# -----------------------------
results = []

for ticker in tickers:
    df = fetch_data(ticker)
    latest = df.iloc[-1]
    signal = "✅ BUY" if latest["Signal"] else "❌"
    sentiment, volume = fetch_stocktwits(ticker)
    price = round(latest["Close"], 2)
    ema = round(latest["EMA40"], 2)
    delta = round((price - ema), 2)
    results.append({
        "Ticker": ticker,
        "Price": price,
        "EMA40": ema,
        "Δ (P - EMA)": delta,
        "Signal": signal,
        "Chatter Vol.": volume,
        "Sentiment Preview": sentiment
    })

df_results = pd.DataFrame(results).sort_values(by=["Signal", "Chatter Vol."], ascending=[False, False])

st.subheader("📊 Scan Results")
st.dataframe(df_results[["Ticker", "Price", "EMA40", "Δ (P - EMA)", "Signal", "Chatter Vol."]], use_container_width=True)

# -----------------------------
# DETAILED VIEW
# -----------------------------
selected_ticker = st.selectbox("Choose a stock to view chart & sentiment:", tickers)

chart_df = fetch_data(selected_ticker)

st.subheader(f"📉 {selected_ticker} Price + EMA40")
fig, ax = plt.subplots(figsize=(12, 4))
chart_df["Close"].plot(ax=ax, label="Price")
chart_df["EMA40"].plot(ax=ax, label="EMA40")
buy_signals = chart_df[chart_df["Signal"]]
ax.scatter(buy_signals.index, buy_signals["Close"], label="Buy Signal", color="green", marker="^")
ax.legend()
st.pyplot(fig)

st.subheader(f"💬 Recent Stocktwits for {selected_ticker}")
sentiment_preview, _ = fetch_stocktwits(selected_ticker)
st.text(sentiment_preview)
