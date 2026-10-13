import streamlit as st
import pandas as pd
import plotly.express as px
from statsmodels.tsa.arima.model import ARIMA

st.set_page_config(page_title="Care Load Analytics", page_icon="📊", layout="wide")
st.title("System Capacity & Care Load Analytics")

COLS = ["Children apprehended and placed in CBP custody", "Children in CBP custody",
        "Children transferred out of CBP custody", "Children in HHS Care",
        "Children discharged from HHS Care"]

@st.cache_data
def load_data():
    d = pd.read_csv("data/HHS_Unaccompanied_Alien_Children_Program.csv")
    d.columns = (d.columns.str.replace("\ufeff", "", regex=False).str.replace("*", "", regex=False)
                  .str.replace(r"\s+", " ", regex=True).str.strip())
    if d.shape[1] == 6:
        d.columns = ["Date"] + COLS
    d["Date"] = pd.to_datetime(d["Date"], errors="coerce")
    for c in COLS:
        d[c] = pd.to_numeric(d[c].astype(str).str.replace(",", "", regex=False), errors="coerce")
    d = d.dropna(subset=["Date"]).sort_values("Date").reset_index(drop=True)
    d["Total System Load"] = d["Children in CBP custody"] + d["Children in HHS Care"]
    d["Net HHS Intake"] = d["Children transferred out of CBP custody"] - d["Children discharged from HHS Care"]
    return d

df = load_data()

start, end = st.sidebar.date_input("Date range", [df["Date"].min(), df["Date"].max()])
f = df[(df["Date"] >= pd.to_datetime(start)) & (df["Date"] <= pd.to_datetime(end))]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Latest total load", f"{f['Total System Load'].dropna().iloc[-1]:,.0f}")
c2.metric("Average load", f"{f['Total System Load'].mean():,.0f}")
c3.metric("Peak load", f"{f['Total System Load'].max():,.0f}")
c4.metric("Avg net HHS intake", f"{f['Net HHS Intake'].mean():,.1f}")

st.plotly_chart(px.line(f, x="Date", y=["Children in CBP custody", "Children in HHS Care"],
                title="CBP vs HHS care load"), use_container_width=True)
st.plotly_chart(px.line(f, x="Date", y=["Children apprehended and placed in CBP custody",
                "Children discharged from HHS Care"], title="Intake vs discharges"),
                use_container_width=True)

st.subheader("30-day forecast")
series = df.set_index("Date")["Total System Load"].dropna().asfreq("D").interpolate()
fc = ARIMA(series, order=(1, 1, 1)).fit().forecast(30)
fdf = pd.DataFrame({"Date": fc.index, "Forecast": fc.values})
st.plotly_chart(px.line(fdf, x="Date", y="Forecast"), use_container_width=True)
st.caption("Forecasts are statistical estimates, not official capacity limits.")