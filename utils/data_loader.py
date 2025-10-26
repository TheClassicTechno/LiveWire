"""
Data loading utilities for LiveWire project - Load the real Kaggle dataset
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta


def load_kaggle_cable_dataset(csv_path: str) -> pd.DataFrame:
    """Load the Kaggle cable monitoring dataset and map to grid_risk_model schema."""
    # Load the original dataset
    df = pd.read_csv(csv_path)
    
    print("Original dataset columns:", df.columns.tolist())
    print("Dataset shape:", df.shape)
    print("Sample of original data:")
    print(df.head())
    
    # Map to expected schema
    mapped_df = pd.DataFrame()
    
    # Map columns to our expected format
    mapped_df['component_id'] = df['Cable ID'].astype(str)
    
    # Convert timestamp
    if 'Timestamp' in df.columns:
        try:
            mapped_df['timestamp'] = pd.to_datetime(df['Timestamp'])
        except:
            print("Warning: Could not parse timestamps, creating synthetic ones")
            base_time = datetime(2017, 1, 1)
            mapped_df['timestamp'] = [base_time + timedelta(minutes=i*5) for i in range(len(df))]
    else:
        print("No timestamp column found, creating synthetic timestamps")
        base_time = datetime(2017, 1, 1)
        mapped_df['timestamp'] = [base_time + timedelta(minutes=i*5) for i in range(len(df))]
    
    # Map sensor data
    mapped_df['temperature'] = df['Temperature (°C)']
    mapped_df['vibration'] = df['Vibration (m/s²)']  # Real column name
    mapped_df['strain'] = df['Strain (mm/m)']  # Real column name
    
    # Keep original target variable
    mapped_df['cable_state'] = df['Cable State']
    
    # Add optional columns if available
    if 'Energy Consumption (W)' in df.columns:
        mapped_df['energy'] = df['Energy Consumption (W)']
    if 'Processing Speed (ms)' in df.columns:
        mapped_df['processing_speed'] = df['Processing Speed (ms)']
    
    # Add synthetic age
    np.random.seed(42)
    unique_components = mapped_df['component_id'].unique()
    age_map = {comp_id: np.random.uniform(1, 100) for comp_id in unique_components}
    mapped_df['age_years'] = mapped_df['component_id'].map(age_map)
    
    print(f"\nMapped dataset shape: {mapped_df.shape}")
    print("Mapped columns:", mapped_df.columns.tolist())
    print("Sample of mapped data:")
    print(mapped_df.head())
    
    return mapped_df


def create_sample_datasets(mapped_df: pd.DataFrame, train_split: float = 0.8):
    """Split the mapped dataset into calibration and test sets."""
    df_sorted = mapped_df.sort_values('timestamp').reset_index(drop=True)
    
    split_idx = int(len(df_sorted) * train_split)
    
    calib_df = df_sorted.iloc[:split_idx].copy()
    test_df = df_sorted.iloc[split_idx:].copy()
    
    # Create directories
    os.makedirs("./data/calib", exist_ok=True)
    os.makedirs("./data/pre_fire", exist_ok=True)
    
    # Save splits
    calib_path = "./data/calib/pre2018.csv"
    test_path = "./data/pre_fire/2018_runup.csv"
    
    calib_df.to_csv(calib_path, index=False)
    test_df.to_csv(test_path, index=False)
    
    print(f"Calibration data saved to: {calib_path} (shape: {calib_df.shape})")
    print(f"Test data saved to: {test_path} (shape: {test_df.shape})")
    
    return calib_path, test_path


if __name__ == "__main__":
    print("LiveWire Data Loading")
    print("=" * 40)
    
    csv_path = "./data/raw/cable_monitoring_dataset.csv"
    if not os.path.exists(csv_path):
        print(f"Error: Dataset not found at {csv_path}")
        print("Please ensure the cable_monitoring_dataset.csv is in ./data/raw/")
        exit(1)
    
    # Load and map the dataset
    mapped_df = load_kaggle_cable_dataset(csv_path)
    
    # Create train/test splits
    calib_path, test_path = create_sample_datasets(mapped_df)
    
    print("\nDataset ready for LiveWire pipeline!")
    print("Next steps:")
    print("1. Run: python experiments/calibrate_baseline.py")
    print("2. Run: python experiments/predict_fire.py")
    print("3. Run: python experiments/backtest_leadtime.py")