"""
Neural Network-Based RUL Predictor
===================================

Uses a multi-layer perceptron (fully connected neural network) for RUL prediction.
Provides a middle ground between simple Gradient Boosting and complex LSTM.

Advantages:
- Always available (scikit-learn)
- Learns nonlinear patterns
- Fast training and inference
- No dependency on TensorFlow/PyTorch
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import warnings
warnings.filterwarnings('ignore')


class RULPredictorNN:
    """Neural Network-based RUL predictor"""

    def __init__(self, hidden_layers: tuple = (128, 64, 32), learning_rate: float = 0.001,
                 max_iter: int = 500, alpha: float = 0.0001, early_stopping: bool = True):
        """
        Initialize Neural Network RUL predictor.

        Args:
            hidden_layers: Tuple of hidden layer sizes
            learning_rate: Learning rate (adam optimizer)
            max_iter: Maximum iterations
            alpha: L2 regularization strength
            early_stopping: Whether to use early stopping
        """
        self.model = MLPRegressor(
            hidden_layer_sizes=hidden_layers,
            activation='relu',
            learning_rate_init=learning_rate,
            max_iter=max_iter,
            alpha=alpha,
            early_stopping=early_stopping,
            validation_fraction=0.1,
            n_iter_no_change=20,
            random_state=42,
            verbose=False
        )
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_names = []

    def engineer_features(self, df: pd.DataFrame, fit: bool = False):
        """
        Engineer features for RUL prediction.

        Strategy: For EACH ENGINE, use THE LAST ROW (end of sequence):
        1. Latest sensor values
        2. Sensor degradation trends (slope over full history)
        3. Operational settings
        4. Time metrics

        Args:
            df: DataFrame with columns [unit_id, time_cycles, sensor_*, op_setting_*]
            fit: If True, learn feature names and return y as well

        Returns:
            X: Feature matrix (n_engines, n_features)
            y: RUL values if fit=True, else just X
        """
        sensor_cols = [col for col in df.columns if col.startswith('sensor_')]
        sensor_cols = [col for col in sensor_cols if not df[col].isna().all()]
        op_cols = ['op_setting_1', 'op_setting_2', 'op_setting_3']

        features_list = []
        rul_list = []

        for unit_id in sorted(df['unit_id'].unique()):
            engine_data = df[df['unit_id'] == unit_id].sort_values('time_cycles').reset_index(drop=True)
            last_row = engine_data.iloc[-1]
            max_cycle = engine_data['time_cycles'].max()

            # Current sensor values
            current_sensors = last_row[sensor_cols].values

            # Sensor degradation trends
            trends = []
            for col in sensor_cols:
                if len(engine_data) > 1:
                    x = engine_data['time_cycles'].values
                    y = engine_data[col].values
                    slope = (y[-1] - y[0]) / (x[-1] - x[0]) if (x[-1] - x[0]) > 0 else 0
                    trends.append(slope)
                else:
                    trends.append(0)

            # Sensor volatility
            volatility = engine_data[sensor_cols].std().fillna(0).values

            # Operational settings
            op_settings = last_row[op_cols].values

            # Time metrics
            time_in_op = last_row['time_cycles']
            time_normalized = time_in_op / max_cycle if max_cycle > 0 else 0

            # Combine all features
            all_features = np.concatenate([
                current_sensors,
                trends,
                volatility,
                op_settings,
                [time_in_op, time_normalized]
            ])

            features_list.append(all_features)

            if fit:
                rul = max_cycle - time_in_op
                rul_list.append(rul)

        X = np.array(features_list)

        if fit:
            self.feature_names = (
                [f"{col}_value" for col in sensor_cols] +
                [f"{col}_trend" for col in sensor_cols] +
                [f"{col}_volatility" for col in sensor_cols] +
                op_cols +
                ["time_in_operation", "time_normalized"]
            )
            return X, np.array(rul_list)
        else:
            return X

    def train(self, df: pd.DataFrame):
        """
        Train Neural Network model on engine data.

        Args:
            df: DataFrame with engine sensor trajectories
        """
        print("🔧 Engineering features for training...")
        X, y = self.engineer_features(df, fit=True)

        print(f"📊 Training samples: {len(y)} engines")
        print(f"📊 Features: {X.shape[1]}")
        print(f"📊 RUL range: {y.min():.0f} to {y.max():.0f} cycles")

        print("🔄 Scaling features...")
        X_scaled = self.scaler.fit_transform(X)

        print("🚀 Training Neural Network model...")
        self.model.fit(X_scaled, y)
        self.is_trained = True

        print(f"✅ Model trained successfully!")
        print(f"   Training R² score: {self.model.score(X_scaled, y):.4f}")
        print(f"   Iterations: {self.model.n_iter_}")

    def predict(self, df: pd.DataFrame) -> dict:
        """
        Predict RUL for test engines.

        Args:
            df: DataFrame with test engine data

        Returns:
            Dictionary with predictions and unit_ids
        """
        if not self.is_trained:
            raise RuntimeError("Model not trained. Call train() first.")

        print("🔧 Engineering features for prediction...")
        X = self.engineer_features(df, fit=False)

        print("🔄 Scaling features...")
        X_scaled = self.scaler.transform(X)

        print("🎯 Making predictions...")
        predictions = self.model.predict(X_scaled)

        unit_ids = sorted(df['unit_id'].unique())

        return {
            'predictions': predictions,
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

    def get_feature_importance(self, top_n: int = 15) -> dict:
        """
        Get feature importance using first layer weights.

        Args:
            top_n: Number of top features to return

        Returns:
            Dictionary of feature_name: importance_score
        """
        if not self.is_trained or not hasattr(self.model, 'coefs_'):
            return {}

        # Use first layer weights as proxy for feature importance
        weights = np.abs(self.model.coefs_[0]).sum(axis=1)
        indices = np.argsort(weights)[::-1][:top_n]

        result = {}
        for idx in indices:
            result[self.feature_names[idx]] = float(weights[idx])

        return result

    def get_info(self) -> dict:
        """Get model information"""
        return {
            'name': 'RUL Predictor (Neural Network)',
            'algorithm': 'Multi-Layer Perceptron (scikit-learn)',
            'trained': self.is_trained,
            'hidden_layers': self.model.hidden_layer_sizes,
            'n_features': len(self.feature_names)
        }


if __name__ == "__main__":
    # Example usage
    from utils.rul_data_loader import CMapsDataLoader

    loader = CMapsDataLoader()

    print("Loading training data...")
    train_df = loader.load_training_data("FD001")

    print("\nTraining Neural Network model...")
    model = RULPredictorNN(hidden_layers=(128, 64, 32), max_iter=500)
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

    print(f"\n{'='*50}")
    print("TOP FEATURES")
    print(f"{'='*50}")
    for feat, imp in model.get_feature_importance(top_n=10).items():
        print(f"{feat:40s}: {imp:10.4f}")
