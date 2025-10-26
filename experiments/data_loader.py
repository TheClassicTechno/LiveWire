"""
Data loading utilities for LiveWire project
============================================

This module helps load and preprocess the Kaggle cable monitoring dataset:
https://www.kaggle.com/datasets/ziya07/cable-multi-state-monitoring-system-dataset

The dataset contains columns like:
- Cable ID, Timestamp, Cable State (target)
- Temperature (°C), Humidity (%), Vibration Level (Hz), Current (A), Voltage (V)
- Energy Consumption (W), Processing Speed (ms), Edge Device Used

We map these to the grid_risk_model expected schema:
- timestamp, component_id, vibration, temperature, strain
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta


def load_kaggle_cable_dataset(csv_path: str) -> pd.DataFrame:
    """Load the Kaggle cable monitoring dataset and map to grid_risk_model schema.
    
    Args:
        csv_path: Path to cable_monitoring_dataset.csv
        
    Returns:
        DataFrame with columns: timestamp, component_id, vibration, temperature, strain, cable_state
    """
    # Load the original dataset
    df = pd.read_csv(csv_path)
    
    # Print original columns for reference
    print("Original dataset columns:", df.columns.tolist())
    print("Dataset shape:", df.shape)
    print("Sample of original data:")
    print(df.head())
    
    # Map to expected schema
    mapped_df = pd.DataFrame()
    
    # Map columns to our expected format
    mapped_df['component_id'] = df['Cable ID'].astype(str)
    
    # Convert timestamp (if it's already datetime-like, keep it; otherwise create synthetic)
    if 'Timestamp' in df.columns:
        try:
            mapped_df['timestamp'] = pd.to_datetime(df['Timestamp'])
        except:
            # If timestamp parsing fails, create synthetic timestamps
            print("Warning: Could not parse timestamps, creating synthetic ones")
            base_time = datetime(2017, 1, 1)  # Start before 2018 Camp Fire
            mapped_df['timestamp'] = [base_time + timedelta(minutes=i*5) for i in range(len(df))]
    else:
        # Create synthetic timestamps if none exist
        print("No timestamp column found, creating synthetic timestamps")
        base_time = datetime(2017, 1, 1)
        mapped_df['timestamp'] = [base_time + timedelta(minutes=i*5) for i in range(len(df))]
    
    # Map sensor data
    mapped_df['temperature'] = df['Temperature (°C)']
    mapped_df['vibration'] = df['Vibration Level (Hz)']  # Use vibration as-is
    
    # Create strain proxy from current/voltage (since we don't have direct strain)
    # Strain is often related to electrical load, so we'll use Current as a proxy
    mapped_df['strain'] = df['Current (A)']
    
    # Keep original target variable
    mapped_df['cable_state'] = df['Cable State']
    
    # Add optional columns if available
    if 'Voltage (V)' in df.columns:
        mapped_df['voltage'] = df['Voltage (V)']
    if 'Humidity (%)' in df.columns:
        mapped_df['humidity'] = df['Humidity (%)']
    
    # Add synthetic age (since we don't have component age in the dataset)
    # Create realistic age distribution
    np.random.seed(42)  # For reproducibility
    unique_components = mapped_df['component_id'].unique()
    age_map = {comp_id: np.random.uniform(1, 100) for comp_id in unique_components}
    mapped_df['age_years'] = mapped_df['component_id'].map(age_map)
    
    print(f"\nMapped dataset shape: {mapped_df.shape}")
    print("Mapped columns:", mapped_df.columns.tolist())
    print("Sample of mapped data:")
    print(mapped_df.head())
    
    return mapped_df


def download_kaggle_dataset(dataset_name: str = "ziya07/cable-multi-state-monitoring-system-dataset", 
                          download_dir: str = "./data/raw") -> str:
    """Download Kaggle dataset using kaggle API.
    
    Prerequisites:
    1. Install kaggle package: pip install kaggle
    2. Set up Kaggle API credentials (kaggle.json in ~/.kaggle/)
    
    Args:
        dataset_name: Kaggle dataset identifier
        download_dir: Directory to download files
        
    Returns:
        Path to the downloaded CSV file
    """
    try:
        import kaggle
        
        # Create download directory
        os.makedirs(download_dir, exist_ok=True)
        
        # Download dataset
        print(f"Downloading {dataset_name} to {download_dir}...")
        kaggle.api.dataset_download_files(dataset_name, path=download_dir, unzip=True)
        
        # Find the CSV file
        csv_files = [f for f in os.listdir(download_dir) if f.endswith('.csv')]
        if csv_files:
            csv_path = os.path.join(download_dir, csv_files[0])
            print(f"Dataset downloaded to: {csv_path}")
            return csv_path
        else:
            raise FileNotFoundError("No CSV files found in downloaded dataset")
            
    except ImportError:
        print("Error: kaggle package not installed. Install with: pip install kaggle")
        return ""
    except Exception as e:
        print(f"Error downloading dataset: {e}")
        print("Manual download instructions:")
        print("1. Go to: https://www.kaggle.com/datasets/ziya07/cable-multi-state-monitoring-system-dataset")
        print("2. Click 'Download' button")
        print("3. Extract the CSV to ./data/raw/")
        return ""


def create_sample_datasets(mapped_df: pd.DataFrame, train_split: float = 0.8):
    """Split the mapped dataset into calibration and test sets for the Camp Fire scenario.
    
    Args:
        mapped_df: Output from load_kaggle_cable_dataset()
        train_split: Fraction of data to use for calibration (pre-2018)
    """
    # Sort by timestamp
    df_sorted = mapped_df.sort_values('timestamp').reset_index(drop=True)
    
    # Split chronologically (earlier data for calibration, later for testing)
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


def create_synthetic_test_data() -> str:
    """Create synthetic cable monitoring data for testing when Kaggle dataset is not available."""
    print("Creating synthetic test data...")
    
    # Create synthetic data that matches the Kaggle dataset schema
    np.random.seed(42)
    n_samples = 1000
    n_cables = 5
    
    data = []
    base_time = datetime(2017, 1, 1)
    
    for i in range(n_samples):
        for cable_id in range(1, n_cables + 1):
            timestamp = base_time + timedelta(hours=i)
            
            # Create realistic patterns
            age_factor = cable_id * 20  # Cables 1-5 have ages 20-100 years
            temp = 20 + 10 * np.sin(i * 0.1) + np.random.normal(0, 2)
            vibration = 0.5 + age_factor * 0.01 + np.random.exponential(0.5)
            current = 10 + age_factor * 0.1 + np.random.normal(0, 1)
            voltage = 240 + np.random.normal(0, 5)
            humidity = 50 + np.random.normal(0, 10)
            
            # Create cable state based on conditions
            if age_factor > 80 and vibration > 2.0:
                cable_state = "Critical"
            elif age_factor > 60 or vibration > 1.5:
                cable_state = "Warning"
            else:
                cable_state = "Normal"
            
            data.append({
                'Cable ID': f'Cable_{cable_id:03d}',
                'Timestamp': timestamp.isoformat(),
                'Temperature (°C)': temp,
                'Humidity (%)': max(0, min(100, humidity)),
                'Vibration Level (Hz)': vibration,
                'Current (A)': current,
                'Voltage (V)': voltage,
                'Energy Consumption (W)': current * voltage + np.random.normal(0, 100),
                'Processing Speed (ms)': np.random.uniform(10, 100),
                'Edge Device Used': f'Device_{np.random.randint(1, 4)}',
                'Cable State': cable_state
            })
    
    # Save synthetic data
    os.makedirs("./data/raw", exist_ok=True)
    synthetic_path = "./data/raw/cable_monitoring_dataset.csv"
    pd.DataFrame(data).to_csv(synthetic_path, index=False)
    print(f"Synthetic test data created: {synthetic_path}")
    return synthetic_path


if __name__ == "__main__":
    # Example usage
    print("LiveWire Data Loading Example")
    print("=" * 40)
    
    # Option 1: Download using Kaggle API (requires setup)
    csv_path = download_kaggle_dataset()
    
    # Option 2: Manual path (if you downloaded manually)
    if not csv_path or not os.path.exists(csv_path):
        csv_path = "./data/raw/cable_monitoring_dataset.csv"
        if not os.path.exists(csv_path):
            print("\nDataset not found. Two options:")
            print("Option 1 - Auto download (requires Kaggle API setup):")
            print("  1. pip install kaggle")
            print("  2. Get kaggle.json from your Kaggle account settings")
            print("  3. Place in ~/.kaggle/ folder")
            print("  4. Re-run this script")
            print("\nOption 2 - Manual download:")
            print("  1. Go to: https://www.kaggle.com/datasets/ziya07/cable-multi-state-monitoring-system-dataset")
            print("  2. Download and extract to ./data/raw/cable_monitoring_dataset.csv")
            print("  3. Re-run this script")
            print("\nFor now, I'll create synthetic data to test the pipeline...")
            csv_path = create_synthetic_test_data()
    
    # Load and map the dataset
    mapped_df = load_kaggle_cable_dataset(csv_path)
    
    # Create train/test splits for the Camp Fire scenario
    calib_path, test_path = create_sample_datasets(mapped_df)
    
    print("\nDataset ready for LiveWire pipeline!")
    print("Next steps:")
    print("1. Run: python experiments/calibrate_baseline.py")
    print("2. Run: python experiments/predict_fire.py")