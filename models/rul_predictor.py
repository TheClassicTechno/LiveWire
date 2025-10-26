"""
RUL (Remaining Useful Life) Predictor for Turbofan Engines
===========================================================

Predicts how many operational cycles an engine has remaining before failure.
Trained on NASA CMaps data, transferable to power grid components.

Key approach:
- Uses both tabular features AND time-series degradation patterns
- Gradient Boosting for fast, interpretable predictions
- Simple feature engineering focused on sensor degradation trends
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import warnings
warnings.filterwarnings('ignore')


class RULPredictor:
    """Gradient Boosting model for RUL prediction"""

    def __init__(self, max_depth: int = 6, n_estimators: int = 100, learning_rate: float = 0.1,
                 stratified_sampling: bool = True, samples_per_lifecycle: int = 20):
        """
        Initialize RUL predictor.

        Args:
            max_depth: Tree depth (lower = less overfitting)
            n_estimators: Number of boosting stages
            learning_rate: Shrinkage (lower = slower but more robust)
            stratified_sampling: If True, sample uniformly across engine lifecycle
            samples_per_lifecycle: How many snapshots to sample per engine trajectory
        """
        self.model = GradientBoostingRegressor(
            n_estimators=n_estimators,
            learning_rate=learning_rate,
            max_depth=max_depth,
            min_samples_split=10,
            min_samples_leaf=5,
            subsample=0.8,
            random_state=42,
            validation_fraction=0.1,
            n_iter_no_change=10,
            tol=1e-4
        )
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_names = []
        self.stratified_sampling = stratified_sampling
        self.samples_per_lifecycle = samples_per_lifecycle

    def engineer_features(self, df: pd.DataFrame, fit: bool = False):
        """
        Engineer features for RUL prediction (handles time-series data).

        Strategy: For TRAINING data (run-to-failure):
        - If stratified_sampling: sample uniformly across lifecycle (early/mid/late)
        - Else: use ALL rows in each engine's trajectory
        - Features: current sensors, degradation trend, volatility, op settings
        - Target: RUL = max_cycle - current_cycle

        For TEST data:
        - Use LAST ROW (end of test sequence) for each engine
        - Same features, but RUL is the provided ground truth

        Args:
            df: DataFrame with columns [unit_id, time_cycles, sensor_*, op_setting_*]
            fit: If True, learn feature names and return y as well

        Returns:
            X: Feature matrix (n_rows_or_engines, n_features)
            y: RUL values if fit=True, else just X
        """
        sensor_cols = [col for col in df.columns if col.startswith('sensor_')]
        # Filter out sensors with all NaN values
        sensor_cols = [col for col in sensor_cols if not df[col].isna().all()]
        op_cols = ['op_setting_1', 'op_setting_2', 'op_setting_3']

        features_list = []
        rul_list = []

        for unit_id in sorted(df['unit_id'].unique()):
            engine_data = df[df['unit_id'] == unit_id].sort_values('time_cycles').reset_index(drop=True)
            max_cycle = engine_data['time_cycles'].max()

            if fit and self.stratified_sampling:
                # TRAINING with stratified sampling: uniformly sample across lifecycle
                # This balances early/mid/late-life examples
                n_rows = len(engine_data)
                if n_rows <= self.samples_per_lifecycle:
                    # Engine has fewer cycles than sample target, use all
                    indices = list(range(n_rows))
                else:
                    # Uniformly sample across lifecycle
                    indices = np.linspace(0, n_rows - 1, self.samples_per_lifecycle, dtype=int).tolist()
                rows_to_use = engine_data.iloc[indices].reset_index(drop=True)
            elif fit:
                # TRAINING without stratification: use all rows
                rows_to_use = engine_data
            else:
                # TEST: use only last row (predict RUL at end of test)
                rows_to_use = engine_data.iloc[-1:].reset_index(drop=True)

            for idx, row in rows_to_use.iterrows():
                # History up to this point
                history = engine_data.iloc[:engine_data.index.get_loc(row.name) + 1]

                # Current sensor values
                current_sensors = row[sensor_cols].values

                # Sensor degradation trends (slope from first to current)
                trends = []
                for col in sensor_cols:
                    if len(history) > 1:
                        x = history['time_cycles'].values
                        y = history[col].values
                        slope = (y[-1] - y[0]) / (x[-1] - x[0]) if (x[-1] - x[0]) > 0 else 0
                        trends.append(slope)
                    else:
                        trends.append(0)

                # Sensor volatility (std in history)
                volatility = history[sensor_cols].std().fillna(0).values

                # Operational settings
                op_settings = row[op_cols].values

                # Time metrics
                time_in_op = row['time_cycles']
                time_normalized = time_in_op / max_cycle if max_cycle > 0 else 0

                # Combine all features
                all_features = np.concatenate([
                    current_sensors,           # Current sensor values
                    trends,                    # Degradation trends
                    volatility,                # Sensor volatility
                    op_settings,               # Operational settings
                    [time_in_op, time_normalized]
                ])

                features_list.append(all_features)

                # Target: RUL = cycles remaining until failure (max_cycle - current_cycle)
                rul = max_cycle - time_in_op
                rul_list.append(rul)

        X = np.array(features_list)

        # Create feature names for interpretability
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
        Train RUL predictor on training data.

        Args:
            df: DataFrame with columns [unit_id, time_cycles, sensor_*, op_setting_*]
               (RUL will be calculated from time-to-failure)
        """
        print("🔧 Engineering features for training...")
        X, y = self.engineer_features(df, fit=True)

        print(f"📊 Training samples: {len(y)} data points (across {df['unit_id'].nunique()} engines)")
        print(f"📊 Features: {X.shape[1]}")
        print(f"📊 RUL range: {y.min():.0f} to {y.max():.0f} cycles")

        print("🔄 Scaling features...")
        X_scaled = self.scaler.fit_transform(X)

        print("🚀 Training Gradient Boosting model...")
        self.model.fit(X_scaled, y)
        self.is_trained = True

        print(f"✅ Model trained successfully!")
        print(f"   Training R² score: {self.model.score(X_scaled, y):.4f}")

    def predict(self, df: pd.DataFrame) -> dict:
        """
        Predict RUL for engines in test data.

        Args:
            df: DataFrame with engine sensor data (must have same columns as training)

        Returns:
            Dictionary with:
            - 'predictions': RUL predictions (cycles remaining)
            - 'unit_ids': Engine IDs (sorted)
            - 'confidence': Model uncertainty estimate
        """
        if not self.is_trained:
            raise RuntimeError("Model not trained. Call train() first.")

        print("🔧 Engineering features for prediction...")
        X = self.engineer_features(df, fit=False)

        print("🔄 Scaling features...")
        X_scaled = self.scaler.transform(X)

        print("🎯 Making predictions...")
        predictions = self.model.predict(X_scaled)

        # Get prediction variance from ensemble
        predictions_all = np.array([tree.predict(X_scaled) for tree in self.model.estimators_[:, 0]])
        confidence = np.std(predictions_all, axis=0)  # Higher = more uncertain

        unit_ids = sorted(df['unit_id'].unique())

        return {
            'predictions': predictions,
            'unit_ids': unit_ids,
            'confidence': confidence
        }

    def evaluate(self, y_true: np.ndarray, y_pred: np.ndarray) -> dict:
        """
        Evaluate predictions against true RUL values.

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

        # Scoring function: penalize late predictions more (safety critical)
        # If predict RUL=50 but actual=10, you miss the failure -> bad
        # If predict RUL=10 but actual=50, you get warning early -> ok
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
        Get most important features for RUL prediction.

        Args:
            top_n: Number of top features to return

        Returns:
            Dictionary of feature_name: importance_score
        """
        if not self.is_trained:
            return {}

        importances = self.model.feature_importances_
        indices = np.argsort(importances)[::-1][:top_n]

        result = {}
        for idx in indices:
            result[self.feature_names[idx]] = float(importances[idx])

        return result

    def get_info(self) -> dict:
        """Get model information"""
        return {
            'name': 'RUL Predictor (Gradient Boosting)',
            'algorithm': 'GradientBoostingRegressor',
            'trained': self.is_trained,
            'n_features': len(self.feature_names),
            'feature_names': self.feature_names
        }


if __name__ == "__main__":
    # Example usage
    from utils.rul_data_loader import CMapsDataLoader

    loader = CMapsDataLoader()

    # Load training data
    print("Loading training data...")
    train_df = loader.load_training_data("FD001")

    # Train model
    model = RULPredictor(max_depth=6, n_estimators=100)
    model.train(train_df)

    # Load test data
    print("\nLoading test data...")
    test_df = loader.load_test_data("FD001")

    # Make predictions
    results = model.predict(test_df)
    print(f"\nPredictions for {len(results['unit_ids'])} engines")

    # Evaluate
    y_true = test_df.groupby('unit_id')['RUL'].first().values
    metrics = model.evaluate(y_true, results['predictions'])

    print(f"\n{'='*50}")
    print("EVALUATION METRICS")
    print(f"{'='*50}")
    for metric, value in metrics.items():
        print(f"{metric:20s}: {value:10.2f}")

    print(f"\n{'='*50}")
    print("TOP IMPORTANT FEATURES")
    print(f"{'='*50}")
    for feat, importance in model.get_feature_importance(top_n=10).items():
        print(f"{feat:30s}: {importance:10.4f}")
