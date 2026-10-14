import pandas as pd
import numpy as np


def load_data(file_obj, filename):
    """Loads a CSV or Excel file into a Pandas DataFrame."""
    if filename.endswith(".csv"):
        # Trying a few common separators
        try:
            df = pd.read_csv(file_obj)
            if len(df.columns) == 1:
                file_obj.seek(0)
                df = pd.read_csv(file_obj, sep=";")
        except Exception as e:
            raise ValueError(f"Erreur de lecture CSV : {e}")
    elif filename.endswith(".xlsx"):
        df = pd.read_excel(file_obj)
    else:
        raise ValueError("Format de fichier non supporté. Utilisez CSV ou Excel.")
    return df


def clean_data(df, date_col, sales_col, freq="D", handle_outliers=True):
    """
    Cleans the dataframe: parses dates, sorts, handles missing values and outliers.
    """
    # 1. Select and rename columns for consistency
    df = df[[date_col, sales_col]].copy()
    df.columns = ["Date", "Sales"]

    # 2. Parse dates
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"])  # Drop rows with invalid dates

    # Ensure sales are numeric
    df["Sales"] = pd.to_numeric(df["Sales"], errors="coerce").fillna(0)

    # 3. Sort by date
    df = df.sort_values("Date")

    # 4. Aggregate duplicates (sum sales if multiple transactions on the same date)
    df = df.groupby("Date", as_index=False)["Sales"].sum()

    # 5. Set Date as index for resampling
    df.set_index("Date", inplace=True)

    # 6. Resample to fill missing dates and interpolate
    # 'D' = Daily, 'W' = Weekly, 'ME' = Month End (updated for newer pandas versions)
    pandas_freq = "ME" if freq == "M" else freq
    df = df.resample(pandas_freq).sum()

    # Replace 0s with NaN for interpolation (assuming 0 means missing data in continuous periods)
    df["Sales"] = df["Sales"].replace(0, np.nan)
    df["Sales"] = df["Sales"].interpolate(method="time")
    df["Sales"] = df["Sales"].fillna(
        0
    )  # Fill remaining NaNs (e.g., at the start) with 0

    # 7. Outlier Detection (Z-Score capping)
    if handle_outliers:
        mean = df["Sales"].mean()
        std = df["Sales"].std()

        # Cap at 3 standard deviations
        upper_bound = mean + 3 * std
        lower_bound = max(0, mean - 3 * std)  # Sales cannot be negative

        df["Sales"] = np.clip(df["Sales"], lower_bound, upper_bound)

    return df.reset_index()
