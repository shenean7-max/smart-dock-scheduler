import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np

def forecast_truck_arrivals(df: pd.DataFrame, future_hours: int = 3) -> pd.DataFrame:
    """
    Forecast future truck arrivals using linear regression.

    Args:
        df (pd.DataFrame): Historical dock metrics.
        future_hours (int): Number of future time slots to predict.

    Returns:
        pd.DataFrame: DataFrame with predicted truck arrivals.
    """
    if df.empty or len(df) < 2:
        raise ValueError("Insufficient data to generate forecast.")

    df = df.copy()

    # Convert timestamps to numeric values (hours since start)
    df['time_numeric'] = (df['timestamp'] - df['timestamp'].min()).dt.total_seconds() / 3600

    # Prepare training data
    X = df[['time_numeric']]
    y = df['truck_arrivals']

    # Train model
    model = LinearRegression()
    model.fit(X, y)

    # Generate future time points
    last_time = df['time_numeric'].max()
    future_times = np.array([[last_time + i] for i in range(1, future_hours + 1)])
    predictions = model.predict(future_times)

    # Create future timestamps
    future_timestamps = [df['timestamp'].max() + pd.Timedelta(hours=i) for i in range(1, future_hours + 1)]

    # Return forecasted DataFrame
    return pd.DataFrame({
        'timestamp': future_timestamps,
        'predicted_truck_arrivals': predictions.round(1)
    })
