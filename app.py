import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from statsmodels.tsa.arima.model import ARIMA

st.set_page_config(page_title="Care Load Analytics", page_icon="📊", layout="wide")
st.title("System Capacity & Care Load Analytics")
st.caption("Monitoring care load across CBP custody and HHS care, with pressure indicators and a 30-day forecast")

COLS = [
    "Children apprehended and placed in CBP custody",
    "Children in CBP custody",
    "Children transferred out of CBP custody",
    "Children in HHS Care",
    "Children discharged from HHS Care",
]


@st.cache_data
def load_data():
    d = pd.read_csv("data/HHS_Unaccompanied_Alien_Children_Program.csv")
    d.columns = (
        d.columns.str.replace("﻿", "", regex=False)
        .str.replace("*", "", regex=False)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )
    if d.shape[1] == 6:
        d.columns = ["Date"] + COLS
    d["Date"] = pd.to_datetime(d["Date"], errors="coerce")
    for c in COLS:
        d[c] = pd.to_numeric(d[c].astype(str).str.replace(",", "", regex=False), errors="coerce")
    d = d.dropna(subset=["Date"]).sort_values("Date").reset_index(drop=True)

    d["Total System Load"] = d["Children in CBP custody"] + d["Children in HHS Care"]
    d["Net HHS Intake"] = (
        d["Children transferred out of CBP custody"] - d["Children discharged from HHS Care"]
    )
    d["7-Day Average"] = d["Total System Load"].rolling(7, min_periods=7).mean()
    d["14-Day Average"] = d["Total System Load"].rolling(14, min_periods=14).mean()
    d["Care Load Volatility Index"] = (
        d["Total System Load"].rolling(7, min_periods=7).std() / d["7-Day Average"]
    )
    d["Backlog Accumulation Rate"] = d["Net HHS Intake"].rolling(7, min_periods=7).mean()
    d["Net Intake Pressure (%)"] = d["Net HHS Intake"] / d["Children in HHS Care"] * 100
    d["Cumulative Net HHS Intake"] = d["Net HHS Intake"].fillna(0).cumsum()

    high = d["7-Day Average"].quantile(0.75)
    low = d["7-Day Average"].quantile(0.25)
    d["Load Status"] = np.where(
        d["7-Day Average"] >= high, "Strain", np.where(d["7-Day Average"] <= low, "Relief", "Normal")
    )
    return d


@st.cache_data
def make_forecast(series: pd.Series, steps: int = 30):
    fc = ARIMA(series, order=(1, 1, 1)).fit().forecast(steps)
    return pd.DataFrame({"Date": fc.index, "Forecast": fc.values})


df = load_data()

# ---------------- Sidebar controls ----------------
st.sidebar.header("Filters")
picked = st.sidebar.date_input(
    "Date range", [df["Date"].min().date(), df["Date"].max().date()],
    min_value=df["Date"].min().date(), max_value=df["Date"].max().date(),
)
if isinstance(picked, (list, tuple)) and len(picked) == 2:
    start, end = picked
else:
    st.sidebar.info("Select both a start and an end date.")
    st.stop()

gran = st.sidebar.radio("Time granularity", ["Daily", "Weekly", "Monthly"])
rule = {"Daily": None, "Weekly": "W", "Monthly": "MS"}[gran]

METRICS = [
    "Children in CBP custody", "Children in HHS Care", "Total System Load",
    "Net HHS Intake", "Backlog Accumulation Rate", "Care Load Volatility Index",
]
metrics = st.sidebar.multiselect("Metrics to show", METRICS,
                                 default=["Children in CBP custody", "Children in HHS Care"])

f = df[(df["Date"] >= pd.to_datetime(start)) & (df["Date"] <= pd.to_datetime(end))]
if f.empty:
    st.warning("No data in the selected range.")
    st.stop()

g = f.set_index("Date").select_dtypes("number")
g = (g.resample(rule).mean() if rule else g).reset_index()

# ---------------- KPI cards ----------------
def last_valid(s):
    s = s.dropna()
    return s.iloc[-1] if len(s) else np.nan

transfers = f["Children transferred out of CBP custody"].sum()
offset = f["Children discharged from HHS Care"].sum() / transfers if transfers else np.nan

k = st.columns(5)
k[0].metric("Total children under care", f"{last_valid(f['Total System Load']):,.0f}")
k[1].metric("Net intake pressure (avg/day)", f"{f['Net HHS Intake'].mean():,.1f}")
k[2].metric("Care load volatility index", f"{f['Care Load Volatility Index'].mean():.3f}")
k[3].metric("Backlog accumulation rate", f"{last_valid(f['Backlog Accumulation Rate']):,.1f}")
k[4].metric("Discharge offset ratio", "n/a" if np.isnan(offset) else f"{offset:.2f}")

c1, c2 = st.columns(2)
c1.metric("Average total load", f"{f['Total System Load'].mean():,.0f}")
c2.metric("Peak total load", f"{f['Total System Load'].max():,.0f}")

# ---------------- Modules ----------------
st.subheader("System load overview")
st.plotly_chart(
    px.line(g, x="Date", y=["Total System Load", "7-Day Average", "14-Day Average"],
            title=f"{gran} total system load",
            labels={"value": "Number of children", "variable": "Measure"}),
    use_container_width=True,
)

st.subheader("CBP vs HHS load comparison")
cmp_cols = [m for m in metrics if m in ("Children in CBP custody", "Children in HHS Care", "Total System Load")]
if cmp_cols:
    st.plotly_chart(
        px.line(g, x="Date", y=cmp_cols, labels={"value": "Number of children", "variable": "Measure"}),
        use_container_width=True,
    )
else:
    st.info("Pick a load metric in the sidebar to see this chart.")

st.subheader("Net intake and backlog trends")
nb_cols = [m for m in metrics if m in ("Net HHS Intake", "Backlog Accumulation Rate", "Care Load Volatility Index")]
nb_cols = nb_cols or ["Net HHS Intake", "Backlog Accumulation Rate"]
st.plotly_chart(
    px.line(g, x="Date", y=nb_cols, labels={"value": "Value", "variable": "Measure"}),
    use_container_width=True,
)

st.subheader("Intake vs discharges")
st.plotly_chart(
    px.line(g, x="Date",
            y=["Children apprehended and placed in CBP custody", "Children discharged from HHS Care"],
            labels={"value": "Number of children", "variable": "Measure"}),
    use_container_width=True,
)

st.subheader("Strain and relief periods")
run_id = (f["Load Status"] != f["Load Status"].shift()).cumsum()
runs = f.groupby(run_id).agg(Status=("Load Status", "first"), Start=("Date", "min"),
                             End=("Date", "max"), Days=("Date", "count"))
long_runs = runs[(runs["Status"] == "Strain") & (runs["Days"] >= 14)].copy()
st.caption("Strain = 7-day average load in the top 25% of the full period. Relief = bottom 25%.")
if long_runs.empty:
    st.write("No prolonged strain windows (14+ days) in this range.")
else:
    long_runs["Start"] = long_runs["Start"].dt.date
    long_runs["End"] = long_runs["End"].dt.date
    st.dataframe(long_runs.reset_index(drop=True), use_container_width=True)

st.subheader("30-day forecast")
series = df.set_index("Date")["Total System Load"].dropna().asfreq("D").interpolate()
fdf = make_forecast(series)
st.plotly_chart(
    px.line(fdf, x="Date", y="Forecast", labels={"Forecast": "Forecast number of children"}),
    use_container_width=True,
)
st.download_button("Download forecast CSV", fdf.to_csv(index=False), "forecast_30_days.csv", "text/csv")
st.caption("Forecasts are statistical estimates, not official capacity limits. The data has no bed capacity.")