import streamlit as st
import pandas as pd
import numpy as np
from src.ingest import load_dock_metrics
from src.forecast import forecast_truck_arrivals
from src.optimize import recommend_staffing
from src.cost import simulate_staffing_cost, simulate_optimized_cost

# Sidebar Controls
st.sidebar.header("🔧 Dashboard Controls")
afe_productivity = st.sidebar.slider("AFE Units per Staffer", min_value=50, max_value=400, value=100)
starting_headcount = st.sidebar.number_input("Total Available Staff", min_value=1, value=100)
target_ppr = st.sidebar.number_input("Target Ship Dock PPR (Packages per Staffer)", min_value=50, max_value=500, value=150)

# Simulate hourly AFE volume
hours = [f"{h}:00" for h in range(8, 20)]
afe_volume = np.random.randint(500, 1500, size=len(hours))

afe_df = pd.DataFrame({
    "Hour": hours,
    "AFE Volume": afe_volume
})

# Calculate AFE Staffing
afe_df["Recommended Staffers"] = afe_df["AFE Volume"].apply(lambda v: int(np.ceil(v / afe_productivity)))

# Calculate total AFE volume
total_afe_volume = afe_df["AFE Volume"].sum()

# Recommend ship dock headcount based on target PPR
recommended_dock_headcount = int(np.ceil(total_afe_volume / target_ppr))

# Load data
df = load_dock_metrics("data/raw/dock_metrics.csv")

# Calculate Headcount Range
min_headcount = int(starting_headcount * min_labor)
max_headcount = int(starting_headcount * max_labor)

st.caption(f"Headcount Range: {min_headcount} to {max_headcount} staffers based on selected labor share.")

# Date Filter
start_date = st.sidebar.date_input("Start Date", value=df['timestamp'].min().date())

# Align AFE timestamps with dock staffing
afe_df["timestamp"] = pd.date_range(start=start_date, periods=len(afe_df), freq="H")

# Forecast and Shift Length
future_hours = st.sidebar.slider("Forecast Hours Ahead", min_value=1, max_value=12, value=3)
shift_length = st.sidebar.slider("Shift Length (hours)", min_value=4, max_value=12, value=8)

# Hourly Rate
hourly_rate = st.sidebar.slider("Hourly Rate per Staff ($)", min_value=15.0, max_value=50.0, value=25.0)

# Apply filters
filtered_df = df[
    (df['timestamp'].dt.date >= start_date) &
    (df['labor_share'] >= min_labor) &
    (df['labor_share'] <= max_labor)
]

# Forecast
if filtered_df.empty:
    st.warning("No data available for the selected filters. Please adjust the date or labor share range.")
    st.stop()
forecast_df = forecast_truck_arrivals(filtered_df, future_hours=future_hours)

# Add Staffing Logic 
avg_labor_share = filtered_df['labor_share'].mean()
staffing_df = recommend_staffing(forecast_df, avg_labor_share, shift_length=shift_length)

# Compare actual dock staffing to recommended
actual_dock_headcount = staffing_df["recommended_staff"].sum()
service_level = actual_dock_headcount / recommended_dock_headcount
service_level = min(service_level, 1.0)  # Cap at 100%

# 🚢 Ship Dock Staffing Recommendation
st.subheader("🚢 Ship Dock Staffing Recommendation")
st.metric("Recommended Dock Headcount (based on Target PPR)", f"{recommended_dock_headcount} staffers")
st.metric("Actual Dock Headcount", f"{actual_dock_headcount} staffers")
st.metric("Estimated Service Level", f"{service_level:.2%}")

# Identify understaffed hours
staffing_df['understaffed'] = staffing_df['recommended_staff'] < staffing_df['predicted_truck_arrivals']
understaffed_hours = staffing_df[staffing_df['understaffed']]

# 🎛️ Scenario Presets for Labor Share Optimization
preset = st.selectbox("Choose a Staffing Strategy", ["Custom", "Aggressive Savings", "Balanced Ops", "High Coverage"])

if preset == "Aggressive Savings":
    optimized_labor_share = 0.6
elif preset == "Balanced Ops":
    optimized_labor_share = 0.8
elif preset == "High Coverage":
    optimized_labor_share = 1.0
else:
    optimized_labor_share = st.slider("Optimized Labor Share", min_value=0.1, max_value=1.0, value=0.8)

optimized_cost_df = simulate_optimized_cost(staffing_df, hourly_rate, optimized_labor_share)

with st.expander("📉 Optimized Staffing Cost Simulation", expanded=False):
    st.dataframe(optimized_cost_df[['timestamp', 'recommended_staff', 'optimized_staff', 'optimized_cost', 'savings']])
    st.metric(label="Total Cost Savings", value=f"${optimized_cost_df['total_savings'].iloc[0]:,.2f}")

# Title
st.title("Smart Dock Scheduler Dashboard")

# Historical Metrics
with st.expander("📊 Historical Dock Metrics", expanded=False):
    st.dataframe(filtered_df)

# 📦 AFE Staffing Section Header
st.markdown("### 📦 AFE Staffing Module")
st.caption("Simulated AFE volume and productivity-based staffing recommendations. Adjust productivity to see staffing impact.")
st.info("AFE (Amazon Fulfillment Environment) volume is simulated to demonstrate staffing needs based on productivity. Adjust the slider to explore impact.")

# Display AFE Staffing Section
with st.expander("📦 AFE Volume and Staffing Recommendations", expanded=False):
    st.dataframe(afe_df)

    col1, col2 = st.columns([2, 1])
    with col1:
        afe_chart_type = st.radio("Chart Type", ["Line Chart", "Bar Chart"])
    with col2:
        afe_csv = afe_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Export AFE Data",
            data=afe_csv,
            file_name="afe_staffing.csv",
            mime="text/csv"
        )

    afe_chart_data = afe_df.set_index("Hour")[["Recommended Staffers"]]
    if afe_chart_type == "Line Chart":
        st.line_chart(afe_chart_data)
    else:
        st.bar_chart(afe_chart_data)

# Align timestamps if needed
afe_df["timestamp"] = pd.date_range(start=start_date, periods=len(afe_df), freq="H")

# Merge Dock + AFE Staffing
combined_staffing = pd.merge(
    staffing_df,
    afe_df[["timestamp", "Recommended Staffers"]],
    on="timestamp",
    how="left"
)
combined_staffing["Total Staffers"] = (
    combined_staffing["recommended_staff"] + combined_staffing["Recommended Staffers"]
)

# Display Combined Staffing Chart
with st.expander("📊 Total Staffing: Dock + AFE", expanded=False):
    st.line_chart(combined_staffing.set_index("timestamp")[["Total Staffers"]])

# Convert filtered historical metrics to CSV
historical_csv = filtered_df.to_csv(index=False).encode('utf-8')

# Add download button
st.download_button(
    label="📥 Download Filtered Historical Metrics as CSV",
    data=historical_csv,
    file_name="filtered_historical_metrics.csv",
    mime="text/csv"
)

# Forecasted Arrivals
with st.expander("🔮 Forecasted Truck Arrivals", expanded=False):
    st.dataframe(forecast_df)

# Convert forecast data to CSV
forecast_csv = forecast_df.to_csv(index=False).encode('utf-8')

# Add Download button
st.download_button(
    label="📥 Download Forecasted Arrivals as CSV",
    data=forecast_csv,
    file_name="forecasted_arrivals.csv",
    mime="text/csv"
)

# Display Staffing Recommendations
with st.expander("👷 Recommended Staffing Levels", expanded=False):
    st.dataframe(staffing_df)

# Add Export Button
csv = staffing_df.to_csv(index=False).encode('utf-8')

# Add download button
st.download_button(
    label="📥 Download Staffing Recommendations as CSV",
    data=csv,
    file_name="staffing_recommendations.csv",
    mime="text/csv"
)

# 💰 Simulate Staffing Cost Based on Hourly Rate
cost_df = simulate_staffing_cost(staffing_df, hourly_rate)

# Add Export for Cost Data
with st.expander("💰 Staffing Cost Simulation", expanded=False):
    st.dataframe(cost_df[['timestamp', 'recommended_staff', 'hourly_cost']])
    st.metric(label="Total Staffing Cost", value=f"${cost_df['total_cost'].iloc[0]:,.2f}")

# 📊 Cost vs. Staffing Chart
with st.expander("📊 Cost vs. Staffing Over Time", expanded=False):
    cost_chart_type = st.radio("Chart Type for Cost vs. Staffing", ["Line Chart", "Bar Chart"])
    chart_data = cost_df.set_index('timestamp')[['recommended_staff', 'hourly_cost']]
    if cost_chart_type == "Line Chart":
        st.line_chart(chart_data)
    else:
        st.bar_chart(chart_data)

# Export Optimized Cost Simulation
optimized_csv = optimized_cost_df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Download Optimized Cost Simulation as CSV",
    data=optimized_csv,
    file_name="optimized_staffing_cost.csv",
    mime="text/csv"
)

# Convert cost simulation to CSV
cost_csv = cost_df.to_csv(index=False).encode('utf-8')

# Add download button
st.download_button(
    label="📥 Download Staffing Cost Simulation as CSV",
    data=cost_csv,
    file_name="staffing_cost_simulation.csv",
    mime="text/csv"
)

# 📊 Savings Over Time Chart
with st.expander("📊 Hourly Cost Savings from Optimization", expanded=False):
    savings_chart_type = st.radio("Chart Type for Savings Over Time", ["Line Chart", "Bar Chart"])

    savings_data = optimized_cost_df.set_index('timestamp')[['savings']]

    if savings_chart_type == "Line Chart":
        st.line_chart(savings_data)
    else:
        st.bar_chart(savings_data)

# 🔄 Compare Original vs. Optimized Staffing
with st.expander("🔄 Staffing Comparison: Original vs. Optimized", expanded=False):
    compare_chart_type = st.radio("Chart Type for Staffing Comparison", ["Line Chart", "Bar Chart"])

    comparison_data = optimized_cost_df.set_index('timestamp')[['recommended_staff', 'optimized_staff']]

    if compare_chart_type == "Line Chart":
        st.line_chart(comparison_data)
    else:
        st.bar_chart(comparison_data)

# 📈 Estimated Service Level Impact
optimized_cost_df['service_level'] = (
    optimized_cost_df['optimized_staff'] / optimized_cost_df['recommended_staff']
).clip(upper=1.0)

with st.expander("📈 Estimated Service Level Impact", expanded=False):
    st.dataframe(optimized_cost_df[['timestamp', 'optimized_staff', 'recommended_staff', 'service_level']])
    st.metric(label="Average Service Level", value=f"{optimized_cost_df['service_level'].mean():.2%}")

# Chart type toggle for staffing vs. forecast
staffing_chart_type = st.radio("Chart Type for Staffing vs. Forecast", ["Line Chart", "Bar Chart"])

# Add Staffing vs. Forecast Chart
with st.expander("📊 Staffing vs. Forecast Comparison", expanded=False):
    if staffing_chart_type == "Line Chart":
        st.line_chart(staffing_df.set_index('timestamp')[['predicted_truck_arrivals', 'recommended_staff']])
    else:
        st.bar_chart(staffing_df.set_index('timestamp')[['predicted_truck_arrivals', 'recommended_staff']])

# Combine historical and forecasted data
combined_df = pd.concat([
    filtered_df[['timestamp', 'truck_arrivals']].rename(columns={'truck_arrivals': 'arrivals'}),
    forecast_df.rename(columns={'predicted_truck_arrivals': 'arrivals'})
])

# Display Alerts
with st.expander("⚠️ Understaffed Hours Alert", expanded=False):
    if understaffed_hours.empty:
        st.success("All forecasted hours are adequately staffed.")
    else:
        st.warning(f"{len(understaffed_hours)} hour(s) may be understaffed based on current labor share and shift length.")
        st.dataframe(understaffed_hours[['timestamp', 'predicted_truck_arrivals', 'recommended_staff']])

# Convert understaffed alerts to CSV
alerts_csv = understaffed_hours[['timestamp', 'predicted_truck_arrivals', 'recommended_staff']].to_csv(index=False).encode('utf-8')

# Add download button
st.download_button(
    label="📥 Download Understaffed Alerts as CSV",
    data=alerts_csv,
    file_name="understaffed_alerts.csv",
    mime="text/csv"
)

# Line Chart
with st.expander("📈 Truck Arrivals Over Time", expanded=False):
    chart_type = st.radio("Select Chart Type", ["Line Chart", "Bar Chart"])
    combined_df = pd.concat([
        df[['timestamp', 'truck_arrivals']].rename(columns={'truck_arrivals': 'arrivals'}),
        forecast_df.rename(columns={'predicted_truck_arrivals': 'arrivals'})
    ])
    if chart_type == "Line Chart":
        st.line_chart(combined_df.set_index('timestamp'))
    else:
        st.bar_chart(combined_df.set_index('timestamp'))


