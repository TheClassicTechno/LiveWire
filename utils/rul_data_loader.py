"""
NASA CMaps RUL (Remaining Useful Life) Data Loader
================================================

Loads the NASA turbofan engine dataset and prepares it for RUL prediction.
Each row is one operational cycle of an engine, with 26 sensor measurements.
Training data: engines run to failure (RUL = 0 at end)
Test data: engines end before failure (RUL > 0)
"""

import pandas as pd
import numpy as np
from pathlib import Path


class CMapsDataLoader:
    """Load and preprocess NASA CMaps turbofan engine data"""

    def __init__(self, data_dir: str = "data/CMaps"):
        """
        Args:
            data_dir: Path to CMaps data directory
        """
        self.data_dir = Path(data_dir)
        self.datasets = ["FD001", "FD002", "FD003", "FD004"]

        # Column names for the 26 columns in the data
        self.column_names = [
            'unit_id',           # Engine unit number
            'time_cycles',       # Operational cycles
            'op_setting_1',      # Operational setting 1
            'op_setting_2',      # Operational setting 2
            'op_setting_3',      # Operational setting 3
            # Sensor measurements 1-26
            'sensor_1', 'sensor_2', 'sensor_3', 'sensor_4', 'sensor_5',
            'sensor_6', 'sensor_7', 'sensor_8', 'sensor_9', 'sensor_10',
            'sensor_11', 'sensor_12', 'sensor_13', 'sensor_14', 'sensor_15',
            'sensor_16', 'sensor_17', 'sensor_18', 'sensor_19', 'sensor_20',
            'sensor_21', 'sensor_22', 'sensor_23', 'sensor_24', 'sensor_25', 'sensor_26'
        ]

    def load_training_data(self, dataset: str = "FD001") -> pd.DataFrame:
        """
        Load training data where engines run to failure.
        Adds RUL column (Remaining Useful Life).

        Args:
            dataset: One of "FD001", "FD002", "FD003", "FD004"

        Returns:
            DataFrame with columns: all features + 'RUL'
        """
        if dataset not in self.datasets:
            raise ValueError(f"Dataset must be one of {self.datasets}")

        # Load training data
        train_file = self.data_dir / f"train_{dataset}.txt"
        df = pd.read_csv(train_file, sep=r'\s+', header=None, names=self.column_names)

        # Calculate RUL: for each engine, RUL at cycle t = max_cycle - t
        max_cycles = df.groupby('unit_id')['time_cycles'].max()
        df['RUL'] = df.apply(
            lambda row: max_cycles[row['unit_id']] - row['time_cycles'],
            axis=1
        )

        return df

    def load_test_data(self, dataset: str = "FD001") -> pd.DataFrame:
        """
        Load test data where engines end before failure.
        Merges with RUL labels for evaluation.

        Args:
            dataset: One of "FD001", "FD002", "FD003", "FD004"

        Returns:
            DataFrame with columns: all features + 'RUL' (true RUL at end of sequence)
        """
        if dataset not in self.datasets:
            raise ValueError(f"Dataset must be one of {self.datasets}")

        # Load test data
        test_file = self.data_dir / f"test_{dataset}.txt"
        df = pd.read_csv(test_file, sep=r'\s+', header=None, names=self.column_names)

        # Load RUL labels (one value per engine)
        rul_file = self.data_dir / f"RUL_{dataset}.txt"
        rul_data = pd.read_csv(rul_file, header=None, names=['RUL'])

        # Map RUL to last cycle of each engine
        # RUL value in file = true RUL at the last row of test data
        last_cycles = df.groupby('unit_id')['time_cycles'].max().reset_index()
        last_cycles['RUL'] = rul_data['RUL'].values

        # Merge RUL back to full dataframe
        df = df.merge(last_cycles[['unit_id', 'RUL']], on='unit_id', suffixes=('_cycle', '_true'))
        df = df.rename(columns={'RUL_true': 'RUL'})

        return df

    def load_all_datasets(self) -> dict:
        """
        Load all 4 datasets (train + test) for comprehensive analysis.

        Returns:
            Dictionary with keys: 'FD001_train', 'FD001_test', etc.
        """
        all_data = {}
        for dataset in self.datasets:
            all_data[f"{dataset}_train"] = self.load_training_data(dataset)
            all_data[f"{dataset}_test"] = self.load_test_data(dataset)
        return all_data

    def get_sensor_columns(self) -> list:
        """Get list of sensor column names"""
        return [col for col in self.column_names if col.startswith('sensor_')]

    def get_operational_settings(self) -> list:
        """Get list of operational setting column names"""
        return ['op_setting_1', 'op_setting_2', 'op_setting_3']


def explore_dataset(df: pd.DataFrame, dataset_name: str = ""):
    """Quick exploration of loaded data"""
    print(f"\n{'='*60}")
    print(f"Dataset: {dataset_name}")
    print(f"{'='*60}")
    print(f"Shape: {df.shape}")
    print(f"Engines: {df['unit_id'].nunique()}")
    print(f"Cycles per engine: {df.groupby('unit_id')['time_cycles'].max().describe()}")
    print(f"\nRUL range: {df['RUL'].min():.0f} to {df['RUL'].max():.0f} cycles")
    print(f"RUL statistics:\n{df['RUL'].describe()}")
    print(f"\nMemory usage: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")


if __name__ == "__main__":
    # Example usage
    loader = CMapsDataLoader()

    # Load FD001 dataset
    train_df = loader.load_training_data("FD001")
    test_df = loader.load_test_data("FD001")

    explore_dataset(train_df, "FD001 Training Data")
    explore_dataset(test_df, "FD001 Test Data")

    print(f"\nSensor columns: {loader.get_sensor_columns()[:5]}... (26 total)")
    print(f"Operational settings: {loader.get_operational_settings()}")
