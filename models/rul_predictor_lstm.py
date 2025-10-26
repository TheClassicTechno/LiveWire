"""
LSTM-Based RUL Predictor for Turbofan Engines
==============================================

Uses sequence-to-sequence learning to predict RUL from time-series sensor data.
Captures nonlinear degradation patterns that Gradient Boosting may miss.

Key advantage: Works with variable-length sequences and learns temporal dependencies.

Implementation: Uses PyTorch for flexibility and performance.
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import warnings
warnings.filterwarnings('ignore')

# Check GPU availability
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')


class LSTMNet(nn.Module):
    """PyTorch LSTM network for RUL prediction"""

    def __init__(self, input_size: int, lstm_units: int = 64, dropout: float = 0.2):
        super(LSTMNet, self).__init__()
        self.lstm_units = lstm_units

        self.lstm1 = nn.LSTM(input_size, lstm_units, batch_first=True, dropout=dropout if lstm_units > 0 else 0)
        self.dropout1 = nn.Dropout(dropout)

        self.lstm2 = nn.LSTM(lstm_units, lstm_units // 2, batch_first=True)
        self.dropout2 = nn.Dropout(dropout)

        # Fully connected layers
        self.fc1 = nn.Linear(lstm_units // 2, 32)
        self.relu = nn.ReLU()
        self.dropout3 = nn.Dropout(dropout)

        self.fc2 = nn.Linear(32, 16)
        self.fc3 = nn.Linear(16, 1)

    def forward(self, x):
        # LSTM layers
        x, _ = self.lstm1(x)
        x = self.dropout1(x)

        x, _ = self.lstm2(x)
        x = self.dropout2(x)

        # Use last output
        x = x[:, -1, :]

        # Fully connected
        x = self.fc1(x)
        x = self.relu(x)
        x = self.dropout3(x)

        x = self.fc2(x)
        x = self.relu(x)

        x = self.fc3(x)

        return x


class RULPredictorLSTM:
    """LSTM-based RUL predictor for time-series degradation modeling"""

    def __init__(self, sequence_length: int = 50, lstm_units: int = 64, dropout: float = 0.2,
                 learning_rate: float = 0.001, epochs: int = 100, batch_size: int = 32):
        """
        Initialize LSTM RUL predictor.

        Args:
            sequence_length: Number of past cycles to use for prediction
            lstm_units: Number of LSTM units
            dropout: Dropout rate for regularization
            learning_rate: Learning rate for Adam optimizer
            epochs: Training epochs
            batch_size: Batch size for training
        """
        self.sequence_length = sequence_length
        self.lstm_units = lstm_units
        self.dropout = dropout
        self.learning_rate = learning_rate
        self.epochs = epochs
        self.batch_size = batch_size

        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self.sensor_cols = []

    def create_sequences(self, data: np.ndarray, sequence_length: int = None) -> tuple:
        """
        Create overlapping sequences for LSTM training.

        Args:
            data: Array of shape (n_samples, n_features)
            sequence_length: Length of sequences

        Returns:
            X: Sequences of shape (n_sequences, sequence_length, n_features)
            y: Corresponding RUL targets
        """
        if sequence_length is None:
            sequence_length = self.sequence_length

        X, y = [], []

        for i in range(len(data) - sequence_length):
            X.append(data[i:i + sequence_length])
            y.append(data[i + sequence_length, -1])  # Last column is RUL

        return np.array(X), np.array(y)

    def prepare_training_data(self, df: pd.DataFrame) -> tuple:
        """
        Prepare training data from engine trajectories.

        Args:
            df: DataFrame with [unit_id, time_cycles, sensor_*, op_setting_*]

        Returns:
            X_train: Training sequences
            y_train: Target RUL values
        """
        sensor_cols = [col for col in df.columns if col.startswith('sensor_')]
        sensor_cols = [col for col in sensor_cols if not df[col].isna().all()]
        self.sensor_cols = sensor_cols

        all_sequences = []
        all_targets = []

        for unit_id in sorted(df['unit_id'].unique()):
            engine_data = df[df['unit_id'] == unit_id].sort_values('time_cycles').reset_index(drop=True)
            max_cycle = engine_data['time_cycles'].max()

            # Extract sensor data
            sensor_data = engine_data[sensor_cols].values

            # Add RUL as last column
            rul_column = (max_cycle - engine_data['time_cycles'].values).reshape(-1, 1)
            sequence_data = np.concatenate([sensor_data, rul_column], axis=1)

            # Create sequences
            if len(sequence_data) > self.sequence_length:
                X_engine, y_engine = self.create_sequences(sequence_data, self.sequence_length)
                all_sequences.append(X_engine)
                all_targets.append(y_engine)

        # Combine all engines
        X_train = np.concatenate(all_sequences, axis=0)
        y_train = np.concatenate(all_targets, axis=0)

        print(f"📊 Training data prepared:")
        print(f"   Sequences: {X_train.shape[0]}")
        print(f"   Sequence length: {X_train.shape[1]}")
        print(f"   Features: {X_train.shape[2]}")
        print(f"   RUL range: {y_train.min():.0f} to {y_train.max():.0f}")

        # Normalize features (but NOT the RUL column)
        X_train_features = X_train[:, :, :-1]
        X_train_features_flat = X_train_features.reshape(-1, X_train_features.shape[-1])
        self.scaler.fit(X_train_features_flat)
        X_train_features_scaled = self.scaler.transform(X_train_features_flat)
        X_train_features_scaled = X_train_features_scaled.reshape(X_train.shape[0], X_train.shape[1], -1)

        # Append RUL back (not scaled)
        X_train_scaled = np.concatenate([X_train_features_scaled, X_train[:, :, -1:]], axis=2)

        return X_train_scaled.astype(np.float32), y_train.astype(np.float32)

    def train(self, df: pd.DataFrame):
        """
        Train LSTM model on engine degradation data.

        Args:
            df: DataFrame with engine sensor trajectories
        """
        print("🔧 Preparing training data...")
        X_train, y_train = self.prepare_training_data(df)

        # Convert to PyTorch tensors
        X_train_tensor = torch.from_numpy(X_train).to(DEVICE)
        y_train_tensor = torch.from_numpy(y_train).to(DEVICE).reshape(-1, 1)

        # Create DataLoader
        dataset = TensorDataset(X_train_tensor, y_train_tensor)
        dataloader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True)

        # Build model
        print(f"\n🔧 Building LSTM model ({X_train.shape[2]} input features)...")
        self.model = LSTMNet(
            input_size=X_train.shape[2],
            lstm_units=self.lstm_units,
            dropout=self.dropout
        ).to(DEVICE)

        # Loss and optimizer
        criterion = nn.MSELoss()
        optimizer = optim.Adam(self.model.parameters(), lr=self.learning_rate)

        print(f"🚀 Training ({self.epochs} epochs)...")

        # Training loop
        best_loss = float('inf')
        patience = 10
        no_improve_count = 0

        for epoch in range(self.epochs):
            total_loss = 0
            for X_batch, y_batch in dataloader:
                # Forward pass
                outputs = self.model(X_batch)
                loss = criterion(outputs, y_batch)

                # Backward pass
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

                total_loss += loss.item()

            avg_loss = total_loss / len(dataloader)

            # Early stopping
            if avg_loss < best_loss:
                best_loss = avg_loss
                no_improve_count = 0
            else:
                no_improve_count += 1

            if (epoch + 1) % 10 == 0 or epoch == 0:
                print(f"  Epoch {epoch+1}/{self.epochs}, Loss: {avg_loss:.4f}")

            if no_improve_count >= patience:
                print(f"  Early stopping at epoch {epoch+1}")
                break

        self.is_trained = True
        print(f"✅ Model trained! Final loss: {best_loss:.4f}")

    def predict(self, df: pd.DataFrame) -> dict:
        """
        Predict RUL for test engines.

        Args:
            df: DataFrame with test engine data

        Returns:
            Dictionary with predictions, unit_ids, and confidence
        """
        if not self.is_trained:
            raise RuntimeError("Model not trained. Call train() first.")

        print("🔧 Preparing test data...")

        predictions = []
        unit_ids = []

        self.model.eval()

        with torch.no_grad():
            for unit_id in sorted(df['unit_id'].unique()):
                engine_data = df[df['unit_id'] == unit_id].sort_values('time_cycles').reset_index(drop=True)
                max_cycle = engine_data['time_cycles'].max()

                # Extract sensor data
                sensor_data = engine_data[self.sensor_cols].values
                rul_column = (max_cycle - engine_data['time_cycles'].values).reshape(-1, 1)
                sequence_data = np.concatenate([sensor_data, rul_column], axis=1)

                if len(sequence_data) >= self.sequence_length:
                    last_sequence = sequence_data[-self.sequence_length:]
                else:
                    # Pad if sequence is shorter
                    padding = np.zeros((self.sequence_length - len(sequence_data), sequence_data.shape[1]))
                    last_sequence = np.concatenate([padding, sequence_data], axis=0)

                # Normalize features
                features = last_sequence[:, :-1]
                features_scaled = self.scaler.transform(features)
                last_sequence_scaled = np.concatenate([features_scaled, last_sequence[:, -1:]], axis=1)

                # Convert to tensor
                X_pred = torch.from_numpy(last_sequence_scaled).float().unsqueeze(0).to(DEVICE)

                # Predict
                pred_rul = self.model(X_pred).cpu().numpy()[0, 0]
                predictions.append(max(0, pred_rul))
                unit_ids.append(unit_id)

        print(f"🎯 Predicted RUL for {len(unit_ids)} engines")

        return {
            'predictions': np.array(predictions),
            'unit_ids': unit_ids,
            'confidence': np.zeros(len(unit_ids))
        }

    def evaluate(self, y_true: np.ndarray, y_pred: np.ndarray) -> dict:
        """
        Evaluate predictions.

        Args:
            y_true: True RUL values
            y_pred: Predicted RUL values

        Returns:
            Dictionary with metrics
        """
        mae = mean_absolute_error(y_true, y_pred)
        mse = mean_squared_error(y_true, y_pred)
        rmse = np.sqrt(mse)
        r2 = r2_score(y_true, y_pred)

        scoring_error = np.mean(np.maximum(y_pred - y_true, 0) * 10 + np.maximum(y_true - y_pred, 0))

        return {
            'MAE': mae,
            'RMSE': rmse,
            'R2': r2,
            'Scoring_Error': scoring_error,
            'mean_pred': y_pred.mean(),
            'mean_true': y_true.mean()
        }

    def get_info(self) -> dict:
        """Get model information"""
        return {
            'name': 'RUL Predictor (LSTM)',
            'algorithm': 'LSTM (PyTorch)',
            'trained': self.is_trained,
            'sequence_length': self.sequence_length,
            'lstm_units': self.lstm_units,
            'device': str(DEVICE)
        }


if __name__ == "__main__":
    # Example usage
    from utils.rul_data_loader import CMapsDataLoader

    loader = CMapsDataLoader()

    print("Loading training data...")
    train_df = loader.load_training_data("FD001")

    print("\nTraining LSTM model...")
    model = RULPredictorLSTM(sequence_length=50, lstm_units=64, epochs=30)
    model.train(train_df)

    print("\nLoading test data...")
    test_df = loader.load_test_data("FD001")

    print("\nMaking predictions...")
    results = model.predict(test_df)

    # Evaluate
    y_true = test_df.groupby('unit_id')['RUL'].first().values
    metrics = model.evaluate(y_true, results['predictions'])

    print(f"\n{'='*50}")
    print("EVALUATION METRICS")
    print(f"{'='*50}")
    for metric, value in metrics.items():
        if metric in ['MAE', 'RMSE', 'Scoring_Error']:
            print(f"{metric:20s}: {value:10.2f}")
        else:
            print(f"{metric:20s}: {value:10.4f}")
