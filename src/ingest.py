import pandas as pd

def load_dock_metrics(filepath: str) -> pd.DataFrame:
    """
    Loads and preprocesses dock metrics from a CSV file.

    Args:
        filepath (str): Path to the dock metrics CSV file.

    Returns:
        pd.DataFrame: Cleaned DataFrame with parsed timestamps.
    """
    try:
        df = pd.read_csv(filepath)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.sort_values('timestamp', inplace=True)
        df.reset_index(drop=True, inplace=True)
        return df
    except Exception as e:
        print(f"Error loading dock metrics: {e}")
        return pd.DataFrame()
