import pandas as pd

def recommend_staffing(forecast_df: pd.DataFrame, avg_labor_share: float, shift_length: int = 8) -> pd.DataFrame:
    """
    Recommend staffing levels based on forecasted arrivals and labor share.

    Args:
        forecast_df (pd.DataFrame): Forecasted truck arrivals.
        avg_labor_share (float): Average labor share from historical data or user input.
        shift_length (int): Length of a work shift in hours.

    Returns:
        pd.DataFrame: Staffing recommendations per time slot.
    """
    # Make a copy to avoid modifying original DataFrame
    forecast_df = forecast_df.copy()

    # Calculate recommended staff based on labor share
    forecast_df['recommended_staff'] = (forecast_df['predicted_truck_arrivals'] * avg_labor_share).round().astype(int)

    # Add shift length for reference
    forecast_df['shift_length'] = shift_length

    # Return relevant columns
    return forecast_df[['timestamp', 'predicted_truck_arrivals', 'recommended_staff', 'shift_length']]
