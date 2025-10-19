import pandas as pd

def simulate_staffing_cost(staffing_df: pd.DataFrame, hourly_rate: float) -> pd.DataFrame:
    """
    Simulate cost impact based on recommended staffing levels.

    Args:
        staffing_df (pd.DataFrame): Data with recommended_staff per hour.
        hourly_rate (float): Cost per staff per hour.

    Returns:
        pd.DataFrame: Staffing cost per hour.
    """
    staffing_df = staffing_df.copy()
    staffing_df['hourly_cost'] = staffing_df['recommended_staff'] * hourly_rate
    return staffing_df[['timestamp', 'recommended_staff', 'hourly_cost']]

def simulate_optimized_cost(staffing_df: pd.DataFrame, hourly_rate: float, optimized_labor_share: float) -> pd.DataFrame:
    """
    Simulate cost impact using an optimized labor share.

    Args:
        staffing_df (pd.DataFrame): Original staffing recommendations.
        hourly_rate (float): Cost per staff per hour.
        optimized_labor_share (float): Hypothetical labor share to simulate.

    Returns:
        pd.DataFrame: Optimized staffing cost and savings.
    """
    staffing_df = staffing_df.copy()

    # Calculate scaling factor based on labor share
    scaling_factor = optimized_labor_share / staffing_df['recommended_staff'].mean()

    # Apply scaling and calculate cost
    staffing_df['optimized_staff'] = (staffing_df['recommended_staff'] * scaling_factor).round().astype(int)
    staffing_df['optimized_cost'] = staffing_df['optimized_staff'] * hourly_rate
    staffing_df['baseline_cost'] = staffing_df['recommended_staff'] * hourly_rate
    staffing_df['savings'] = staffing_df['baseline_cost'] - staffing_df['optimized_cost']

    return staffing_df[['timestamp', 'recommended_staff', 'optimized_staff', 'optimized_cost', 'savings']]
