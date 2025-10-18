# 🚢 Smart Dock Scheduler

A data-driven dashboard for optimizing ship dock staffing at Amazon Fulfillment Centers. It leverages operational metrics—like truck schedules, labor share history, and workload forecasts—to recommend efficient staffing levels, reduce delays, and improve labor utilization.

---

## 📊 Features

- **Forecasting**: Predict truck arrivals using linear regression
- **Staffing Recommendations**: Suggest optimal labor levels based on forecasted workload
- **Cost Simulation**: Compare actual vs. optimized staffing costs
- **Scenario Modeling**: Toggle between presets to explore operational trade-offs
- **Service Level Impact**: Visualize how staffing affects throughput and delay risk
- **Export Options**: Download charts and metrics for reporting

---

## 🚀 Setup Instructions

1. Clone the repository:
   ```bash
   git clone https://github.com/shenean7-max/smart-dock-scheduler.git
   cd smart-dock-scheduler
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # On Windows
3. Install Dependencies
  pip install -r requirements.txt
4. Launch the dashboard:
   streamlit run dashboard.py

