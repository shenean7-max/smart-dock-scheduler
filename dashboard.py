import streamlit as st
import pandas as pd
import numpy as np
from src.ingest import load_dock_metrics
from src.forecast import forecast_truck_arrivals
from src.optimize import recommend_staffing
from src.cost import simulate_staffing_cost

# ---------------- Sidebar Controls ----------------
st.sidebar.header("🔧 Dashboard Controls")

# AFE productivity slider: affects staffing calculation
afe_productivity = st.sidebar.slider("AFE Units per Staffer", min_value=50, max_value=400, value=100)

# Target packages per staffer for dock staffing
target_ppr = st.sidebar.number_input("Target Ship Dock PPR (Packages per Staffer)", min_value=50, max_value=500, value=150)

# ---------------- Simulate AFE Volume ----------------
# Generate hourly labels and random AFE volume
hours = [f"{h}:00" for h in range(8, 20)]
afe_volume = np.random.randint(500, 1500, size=len(hours))

# Create AFE DataFrame
afe_df = pd.DataFrame({
    "Hour": hours,
    "AFE Volume": afe_volume
})

# Calculate recommended staffers based on productivity
afe_df["Recommended Staffers"] = afe_df["AFE Volume"].apply(lambda v: int(np.ceil(v / afe_productivity)))

# Total AFE volume and dock staffing recommendation
total_afe_volume = afe_df["AFE Volume"].sum()
recommended_dock_headcount = int(np.ceil(total_afe_volume / target_ppr))

# ---------------- Load Historical Dock Data ----------------
df = load_dock_metrics("data/raw/dock_metrics.csv")

# Date filter for dashboard
start_date = st.sidebar.date_input("Start Date", value=df['timestamp'].min().date())

# Align AFE timestamps with dock data
afe_df["timestamp"] = pd.date_range(start=start_date, periods=len(afe_df), freq="H")

# ---------------- Forecast Settings ----------------
future_hours = st.sidebar.slider("Forecast Hours Ahead", min_value=1, max_value=12, value=3)
shift_length = st.sidebar.slider("Shift Length (hours)", min_value=4, max_value=12, value=8)
hourly_rate = st.sidebar.slider("Hourly Rate per Staff ($)", min_value=15.0, max_value=50.0, value=25.0)

# Filter historical data by selected date
filtered_df = df[df['timestamp'].dt.date >= start_date]
if filtered_df.empty:
    st.warning("No data available for the selected date range. Please adjust the start date.")
    st.stop()

# ---------------- Forecast and Staffing ----------------
forecast_df = forecast_truck_arrivals(filtered_df, future_hours=future_hours)
staffing_df = recommend_staffing(forecast_df, shift_length=shift_length)

# Calculate actual headcount and service level
actual_dock_headcount = staffing_df["recommended_staff"].sum()
service_level = min(actual_dock_headcount / recommended_dock_headcount, 1.0)

# ---------------- Dashboard Header ----------------
st.subheader("🚢 Ship Dock Staffing Recommendation")
st.metric("Recommended Dock Headcount (based on Target PPR)", f"{recommended_dock_headcount} staffers")
st.metric("Actual Dock Headcount", f"{actual_dock_headcount} staffers")
st.metric("Estimated Service Level", f"{service_level:.2%}")

# Color-coded service level metric for visual performance feedback
service_color = "green" if service_level >= 0.9 else "orange" if service_level >= 0.75 else "red"
st.metric("Estimated Service Level", f"{service_level:.2%}", delta=None, delta_color=service_color)

# Flag understaffed hours
staffing_df['understaffed'] = staffing_df['recommended_staff'] < staffing_df['predicted_truck_arrivals']
understaffed_hours = staffing_df[staffing_df['understaffed']]

st.title("Smart Dock Scheduler Dashboard")
st.caption(f"Dashboard generated on {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")

# ---------------- Historical Metrics ----------------
with st.expander("📊 Historical Dock Metrics", expanded=False):
    st.dataframe(filtered_df)

# ---------------- AFE Staffing Module ----------------
st.markdown("### 📦 AFE Staffing Module")
st.caption("Simulated AFE volume and productivity-based staffing recommendations. Adjust productivity to see staffing impact.")
st.info("AFE (Amazon Fulfillment Environment) volume is simulated to demonstrate staffing needs based on productivity. Adjust the slider to explore impact.")

with st.expander("📦 AFE Volume and Staffing Recommendations", expanded=False):
    st.dataframe(afe_df)
    col1, col2 = st.columns([2, 1])
    with col1:
        afe_chart_type = st.radio("Chart Type", ["Line Chart", "Bar Chart"])
    with col2:
        afe_csv = afe_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Export AFE Data", data=afe_csv, file_name="afe_staffing.csv", mime="text/csv")
    chart_data = afe_df.set_index("Hour")[["Recommended Staffers"]]
    st.line_chart(chart_data) if afe_chart_type == "Line Chart" else st.bar_chart(chart_data)

# ---------------- Combined Staffing ----------------
combined_staffing = pd.merge(
    staffing_df,
    afe_df[["timestamp", "Recommended Staffers"]],
    on="timestamp",
    how="left"
)
combined_staffing["Total Staffers"] = combined_staffing["recommended_staff"] + combined_staffing["Recommended Staffers"]

with st.expander("📊 Total Staffing: Dock + AFE", expanded=False):
    st.line_chart(combined_staffing.set_index("timestamp")[["Total Staffers"]])

# ---------------- CSV Export Buttons ----------------
historical_csv = filtered_df.to_csv(index=False).encode('utf-8')
st.download_button("📥 Download Filtered Historical Metrics as CSV", data=historical_csv, file_name="filtered_historical_metrics.csv", mime="text/csv")

forecast_csv = forecast_df.to_csv(index=False).encode('utf-8')
st.download_button("📥 Download Forecasted Arrivals as CSV", data=forecast_csv, file_name="forecasted_arrivals.csv", mime="text/csv")

staffing_csv = staffing_df.to_csv(index=False).encode('utf-8')
st.download_button("📥 Download Staffing Recommendations as CSV", data=staffing_csv, file_name="staffing_recommendations.csv", mime="text/csv")

# ---------------- Cost Simulation ----------------
cost_df = simulate_staffing_cost(staffing_df, hourly_rate)

with st.expander("💰 Staffing Cost Simulation", expanded=False):
    st.dataframe(cost_df[['timestamp', 'recommended_staff', 'hourly_cost']])
    st.metric("Total Staffing Cost", f"${cost_df['total_cost'].iloc[0]:,.2f}")

with st.expander("📊 Cost vs. Staffing Over Time", expanded=False):
    cost_chart_type = st.radio("Chart Type for Cost vs. Staffing", ["Line Chart", "Bar Chart"])
    cost_chart_data = cost_df.set_index('timestamp')[['recommended_staff', 'hourly_cost']]
    st.line_chart(cost_chart_data) if cost_chart_type == "Line Chart" else st.bar_chart(cost_chart_data)

cost_csv = cost_df.to_csv(index=False).encode('utf-8')
st.download_button("📥 Download Staffing Cost Simulation as CSV", data=cost_csv, file_name="staffing_cost_simulation.csv", mime="text/csv")

# ---------------- Staffing vs. Forecast ----------------
staffing_chart_type = st.radio("Chart Type for Staffing vs. Forecast", ["Line Chart", "Bar Chart"])
with st.expander("📊 Staffing vs. Forecast Comparison", expanded=False):
    forecast_chart_data = staffing_df.set_index('timestamp')[['predicted_truck_arrivals', 'recommended_staff']]
    st.line_chart(forecast_chart_data) if staffing_chart_type == "Line Chart" else st.bar_chart(forecast_chart_data)

# ---------------- Understaffed Alerts ----------------
combined_df = pd.concat([
    filtered_df[['timestamp', 'truck_arrivals']].rename(columns={'truck_arrivals': 'arrivals'}),
    forecast_df.rename(columns={'predicted_truck_arrivals': 'arrivals'})
])

with st.expander("⚠️ Understaffed Hours Alert", expanded=False):
    if understaffed_hours.empty:
        st.success("All forecasted hours are adequately staffed.")
    else:
        st.warning(f"{len(understaffed_hours)} hour(s) may be understaffed based on forecasted truck volume and shift length.")
        st.dataframe(understaffed_hours[['timestamp', 'predicted_truck_arrivals', 'recommended_staff']])

alerts_csv = understaffed_hours[['timestamp', 'predicted_truck_arrivals', 'recommended_staff']].to_csv(index=False).encode('utf-8')
st.download_button("📥 Download Understaffed Alerts as CSV", data=alerts_csv, file_name="understaffed_alerts.csv", mime="text/csv")

# ---------------- Truck Arrivals Over Time ----------------
with st.expander("📈 Truck Arrivals Over Time", expanded=False):
    arrivals_chart_type = st.radio("Select Chart Type", ["Line Chart", "Bar Chart"])
    arrivals_df = pd.concat([
        df[['timestamp', 'truck_arrivals']].rename(columns={'truck_arrivals': 'arrivals'}),
        forecast_df.rename(columns={'predicted_truck_arrivals': 'arrivals'})
    ])
    st.line_chart(arrivals_df.set_index('timestamp')) if arrivals_chart_type == "Line Chart" else st.bar_chart(arrivals_df.set_index('timestamp'))
