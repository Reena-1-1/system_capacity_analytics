# System Capacity & Care Load Analytics

An end-to-end time-series analytics and forecasting project that monitors
care load across CBP custody and HHS care, calculates system KPIs, forecasts
future load, and presents the results in an interactive Streamlit dashboard.

**Live dashboard:** [paste Streamlit link after Step 6.8]

## Problem Statement
Care-system managers need to understand how many children are in each care
stage, when pressure builds, and what load may look like in the coming weeks.
This project analyses daily records and forecasts total system load.

## Dataset
- Source: HHS Unaccompanied Alien Children Program data
- Period: 12 Jan 2023 to 21 Dec 2025 (daily records)
- Columns:
  - Children apprehended and placed in CBP custody
  - Children in CBP custody
  - Children transferred out of CBP custody
  - Children in HHS Care
  - Children discharged from HHS Care

## Tech Stack
Python, Pandas, NumPy, Matplotlib, Seaborn, Plotly, Statsmodels,
Scikit-learn, Streamlit, Jupyter, Git/GitHub

## Methodology
1. **Data cleaning:** standardised column names, parsed dates, converted
   numeric fields, checked duplicates, missing values and missing dates.
2. **Validation:** flagged negative counts and transfer/discharge
   inconsistencies.
3. **EDA:** trend, monthly pattern, correlation and distribution analysis.
4. **Feature engineering / KPIs:**
   - Total System Load = CBP custody + HHS care
   - Net HHS Intake = transfers out of CBP - discharges from HHS
   - Daily load change, growth rate, 7-day and 14-day rolling averages
   - Sustained HHS pressure indicator
5. **Forecasting:** chronological 80/20 train-test split; naive baseline vs
   ARIMA(1,1,1); evaluated with MAE and RMSE; refit on all data for a
   30-day forecast.

## Key Findings
- Total system load peaked at **11,762** children.
- Average daily system load was **6,233**.
- HHS care load fell sharply in early 2025 and remained low (around 2,500).
- Average net HHS intake was **-44.7**, meaning discharges exceeded transfers.
- [add 1-2 more findings from your charts]

## Model Results
| Model | MAE | RMSE |
|---|---|---|
| Naive baseline | [value] | [value] |
| ARIMA(1,1,1) | [value] | [value] |

[One sentence: which model performed better and by how much.]

## Dashboard Features
- Date-range filter
- KPI cards (latest, average, peak load, net HHS intake)
- CBP vs HHS trend chart
- Intake vs discharges chart
- 30-day forecast

![KPIs](images/dashboard_kpis.png)
![Charts](images/dashboard_charts.png)
![Forecast](images/dashboard_forecast.png)

## How to Run Locally
```bash
git clone https://github.com/<your-username>/System-Capacity-Analytics.git
cd System-Capacity-Analytics
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m streamlit run app.py
```

## Limitations
- The dataset has recorded counts, not bed capacity, so the project
  identifies pressure periods but cannot prove overcrowding.
- ARIMA(1,1,1) is a starting configuration; other models may do better.
- Forecasts are statistical estimates, not official projections.

## Future Improvements
SARIMA/Prophet comparison, lag-feature ML models, alert thresholds, and
automated data refresh.

## Author
[Your Name] - Machine Learning Internship Project, Unified Mentor