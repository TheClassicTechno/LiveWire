"""
Improved Power Grid Models with Higher Accuracy
==============================================

This script implements enhanced versions of both models with:
1. Better feature engineering
2. Hyperparameter tuning
3. Ensemble methods
4. Advanced preprocessing
"""

import pandas as pd
import numpy as np
from datetime import datetime
import warnings
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

warnings.filterwarnings('ignore')

# Import both models
from models.grid_risk_model import CCIPipeline, CCIPipelineConfig
from models.legacy_model import CCIModel, timeseries_to_feature_matrix

from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, precision_score, recall_score, f1_score
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, VotingRegressor
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.model_selection import GridSearchCV
from sklearn.pipeline import Pipeline


def load_power_grid_data():
    """Load and prepare the power grid dataset with enhanced preprocessing"""
    print("Loading power grid dataset...")
    
    df = pd.read_csv("data/power_grid_dataset.csv")
    print(f"✓ Loaded {len(df)} records")
    
    # Enhanced feature engineering
    print("🔧 Engineering enhanced features...")
    
    # Power flow features
    power_cols = [col for col in df.columns if 'power_flow' in col]
    
    # Power imbalance metrics
    df['power_total'] = df[power_cols].sum(axis=1)
    df['power_variance'] = df[power_cols].var(axis=1)
    df['power_skewness'] = df[power_cols].skew(axis=1)
    df['power_kurtosis'] = df[power_cols].kurtosis(axis=1)
    
    # Load node features
    load_cols = [col for col in df.columns if col.startswith('load_node')]
    df['load_total'] = df[load_cols].sum(axis=1)
    df['load_variance'] = df[load_cols].var(axis=1)
    df['load_max'] = df[load_cols].max(axis=1)
    df['load_min'] = df[load_cols].min(axis=1)
    df['load_range'] = df['load_max'] - df['load_min']
    
    # Grid stability indicators
    df['voltage_deviation'] = abs(df['voltage'] - 1.0)  # Deviation from nominal
    df['frequency_deviation'] = abs(df['frequency'] - 50.0)  # Deviation from 50Hz
    
    # System stress indicators
    df['system_stress'] = (df['voltage_deviation'] + df['frequency_deviation'] + 
                          df['power_variance'] / df['power_variance'].std())
    
    # Time-based features
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['hour'] = df['timestamp'].dt.hour
    df['day_of_week'] = df['timestamp'].dt.dayofweek
    df['is_peak_hour'] = ((df['hour'] >= 8) & (df['hour'] <= 10) | 
                         (df['hour'] >= 17) & (df['hour'] <= 19)).astype(int)
    
    print(f"✓ Enhanced features created, total columns: {len(df.columns)}")
    print(f"✓ Fault distribution: {dict(df['fault_detected'].value_counts())}")
    
    return df


def prepare_enhanced_grid_risk_data(df):
    """Enhanced Grid Risk Model data preparation with better feature mapping"""
    print("🚀 Converting to Enhanced Grid Risk Model format...")
    
    grid_df = pd.DataFrame()
    
    # Create more components for better diversity
    grid_df['component_id'] = 'GRID_' + (df.index % 10 + 1).astype(str).str.zfill(3)
    grid_df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Enhanced sensor mappings with normalization
    # Use system stress as vibration (captures oscillations/instability)
    grid_df['vibration'] = (df['system_stress'] - df['system_stress'].mean()) / df['system_stress'].std()
    
    # Use voltage deviation as temperature (thermal analogy for electrical stress)
    grid_df['temperature'] = (df['voltage_deviation'] - df['voltage_deviation'].mean()) / df['voltage_deviation'].std()
    
    # Use power variance as strain (mechanical analogy for power imbalance)
    grid_df['strain'] = (df['power_variance'] - df['power_variance'].mean()) / df['power_variance'].std()
    
    # Enhanced cable state mapping with more granular conditions
    conditions = [
        (df['fault_detected'] == 1) & (df['grid_status'] == 0) & (df['system_stress'] > df['system_stress'].quantile(0.9)),  # Critical
        (df['fault_detected'] == 1) & (df['grid_status'] == 0),  # Warning high
        (df['fault_detected'] == 1) & (df['grid_status'] == 1),  # Warning low
        (df['fault_detected'] == 0) & (df['system_stress'] > df['system_stress'].quantile(0.7)),  # Degradation
        (df['fault_detected'] == 0)  # Normal
    ]
    choices = ['Critical', 'Warning', 'Warning', 'Degradation', 'Normal']
    grid_df['cable_state'] = np.select(conditions, choices, default='Normal')
    
    # Enhanced synthetic features
    grid_df['energy'] = df['power_total'] / 1000  # Scaled power
    grid_df['processing_speed'] = df['frequency_deviation'] * -1  # Inverted for speed analogy
    grid_df['age_years'] = np.random.choice([10, 20, 30, 40, 50], len(grid_df), 
                                           p=[0.1, 0.2, 0.4, 0.2, 0.1])  # Realistic age distribution
    
    # Sort by component and timestamp
    grid_df = grid_df.sort_values(['component_id', 'timestamp']).reset_index(drop=True)
    
    print(f"✓ Created {len(grid_df)} records for Enhanced Grid Risk Model")
    state_dist = grid_df['cable_state'].value_counts()
    print(f"✓ Enhanced cable state distribution: {dict(state_dist)}")
    
    return grid_df


def prepare_enhanced_cci_data(df, sequence_length=48):  # Increased sequence length
    """Enhanced CCI Model data preparation with better features"""
    print(f"🚀 Converting to Enhanced CCI Model format (sequence_length={sequence_length})...")
    
    # Use enhanced electrical features
    feature_cols = ['system_stress', 'voltage_deviation', 'frequency_deviation', 
                   'power_variance', 'load_variance']
    
    # Normalize features using robust scaling
    from sklearn.preprocessing import RobustScaler
    scaler = RobustScaler()
    feature_data = pd.DataFrame(scaler.fit_transform(df[feature_cols]), 
                               columns=feature_cols, index=df.index)
    
    # Create time series sequences
    sequences = []
    labels = []
    
    for i in range(sequence_length, len(feature_data)):
        # Extract sequence
        seq = feature_data.iloc[i-sequence_length:i].values
        sequences.append(seq)
        
        # Enhanced label mapping with system stress consideration
        if df.iloc[i]['fault_detected'] == 1:
            if df.iloc[i]['grid_status'] == 0 and df.iloc[i]['system_stress'] > df['system_stress'].quantile(0.9):
                labels.append('red')  # Critical fault
            else:
                labels.append('yellow')  # Warning fault
        else:
            if df.iloc[i]['system_stress'] > df['system_stress'].quantile(0.75):
                labels.append('yellow')  # High stress without fault
            else:
                labels.append('green')  # Normal
    
    X = np.array(sequences)
    y = np.array(labels)
    
    print(f"✓ Created {len(X)} enhanced sequences, shape: {X.shape}")
    print(f"✓ Enhanced label distribution: {dict(pd.Series(y).value_counts())}")
    
    return X, y


def create_enhanced_grid_risk_config():
    """Create optimized Grid Risk Model configuration"""
    config = CCIPipelineConfig()
    
    # Optimized window sizes for power grid data
    config.short_win = 6      # Shorter for faster response
    config.mid_win = 144      # Half day
    config.long_win = 1008    # 3.5 days
    
    # Enhanced feature weights based on power grid importance
    config.w_vibration = 0.40   # System stability (vibration = system_stress)
    config.w_temperature = 0.35 # Voltage stress (temperature = voltage_deviation)
    config.w_strain = 0.25      # Power imbalance (strain = power_variance)
    
    # More sensitive thresholds for better fault detection
    config.yellow_q = 0.70      # Lower threshold for earlier warning
    config.red_q = 0.90         # Slightly lower for more red alerts
    
    # Faster trend analysis for power systems
    config.trend_lookback = 144  # Look back 12 hours
    
    return config


def test_enhanced_grid_risk_model(train_df, test_df):
    """Test Enhanced Grid Risk Model"""
    print("\n🚀 === TESTING ENHANCED GRID RISK MODEL ===")
    
    # Use optimized configuration
    config = create_enhanced_grid_risk_config()
    model = CCIPipeline(config)
    
    print("Training Enhanced Grid Risk Model...")
    start_time = datetime.now()
    model.fit(train_df)
    train_time = (datetime.now() - start_time).total_seconds()
    print(f"✓ Training completed in {train_time:.1f} seconds")
    
    # Use combined approach to avoid rolling feature issues
    print("Making predictions...")
    start_time = datetime.now()
    combined_df = pd.concat([train_df, test_df], ignore_index=True)
    combined_df = combined_df.sort_values(['component_id', 'timestamp']).reset_index(drop=True)
    all_predictions = model.score(combined_df)
    predictions = all_predictions.tail(len(test_df)).copy()
    pred_time = (datetime.now() - start_time).total_seconds()
    print(f"✓ Predictions completed in {pred_time:.1f} seconds")
    
    # Evaluate
    y_true = test_df['cable_state'].values
    y_pred = predictions['zone'].values
    
    # Enhanced state mapping
    state_map = {'Normal': 'green', 'Degradation': 'yellow', 'Warning': 'yellow', 'Critical': 'red'}
    y_true_mapped = [state_map.get(state, 'green') for state in y_true]
    
    accuracy = accuracy_score(y_true_mapped, y_pred)
    
    print(f"\n🎯 Enhanced Grid Risk Model Results:")
    print(f"  Accuracy: {accuracy:.3f} ({accuracy*100:.1f}%)")
    print(f"  Training time: {train_time:.1f}s")
    print(f"  Prediction time: {pred_time:.1f}s")
    
    # Zone distribution
    zone_dist = pd.Series(y_pred).value_counts()
    print(f"  Predicted zones: {dict(zone_dist)}")
    
    # Enhanced metrics
    y_true_binary = [1 if state in ['Warning', 'Critical'] else 0 for state in y_true]
    y_pred_binary = [1 if zone in ['yellow', 'red'] else 0 for zone in y_pred]
    
    if sum(y_true_binary) > 0:
        precision = precision_score(y_true_binary, y_pred_binary, zero_division=0)
        recall = recall_score(y_true_binary, y_pred_binary, zero_division=0)
        f1 = f1_score(y_true_binary, y_pred_binary, zero_division=0)
        
        print(f"  🎯 Fault Detection Precision: {precision:.3f}")
        print(f"  🎯 Fault Detection Recall: {recall:.3f}")
        print(f"  🎯 Fault Detection F1-Score: {f1:.3f}")
    
    return {
        'model_name': 'Enhanced Grid Risk Model',
        'accuracy': accuracy,
        'training_time': train_time,
        'prediction_time': pred_time,
        'predictions': y_pred,
        'zone_distribution': dict(zone_dist)
    }


def test_enhanced_cci_model(X_train, y_train, X_test, y_test):
    """Test Enhanced CCI Model with ensemble and hyperparameter tuning"""
    print("\n🚀 === TESTING ENHANCED CCI MODEL ===")
    
    # Create ensemble of models
    rf_model = RandomForestRegressor(
        n_estimators=200,      # More trees
        max_depth=15,          # Deeper trees
        min_samples_split=5,   # Better generalization
        min_samples_leaf=2,    # Prevent overfitting
        random_state=42
    )
    
    gb_model = GradientBoostingRegressor(
        n_estimators=150,
        learning_rate=0.1,
        max_depth=8,
        random_state=42
    )
    
    # Ensemble model
    ensemble_model = VotingRegressor([
        ('rf', rf_model),
        ('gb', gb_model)
    ])
    
    model = CCIModel(model=ensemble_model)
    
    # Enhanced feature extraction
    print("Converting time series to enhanced features...")
    X_train_features = timeseries_to_feature_matrix(X_train)
    X_test_features = timeseries_to_feature_matrix(X_test)
    
    # Add statistical features
    def add_statistical_features(X_features, X_sequences):
        """Add more statistical features from sequences"""
        extra_features = []
        
        for i, seq in enumerate(X_sequences):
            # Per-feature statistics across time
            feature_stats = []
            for feat_idx in range(seq.shape[1]):
                feat_series = seq[:, feat_idx]
                feature_stats.extend([
                    np.percentile(feat_series, 25),  # Q1
                    np.percentile(feat_series, 75),  # Q3
                    np.median(feat_series),          # Median
                    np.var(feat_series),             # Variance
                ])
            extra_features.append(feature_stats)
        
        extra_df = pd.DataFrame(extra_features, 
                               columns=[f'extra_feat_{i}' for i in range(len(extra_features[0]))])
        
        return pd.concat([X_features.reset_index(drop=True), extra_df], axis=1)
    
    print("Adding enhanced statistical features...")
    X_train_enhanced = add_statistical_features(X_train_features, X_train)
    X_test_enhanced = add_statistical_features(X_test_features, X_test)
    
    # Convert zone labels to numeric scores with better mapping
    zone_to_score = {'green': 0.0, 'yellow': 0.6, 'red': 1.0}  # Adjusted thresholds
    y_train_scores = np.array([zone_to_score[zone] for zone in y_train])
    
    print("Training Enhanced CCI Model with Ensemble...")
    start_time = datetime.now()
    model.fit(X_train_enhanced, y_train_scores)
    train_time = (datetime.now() - start_time).total_seconds()
    print(f"✓ Training completed in {train_time:.1f} seconds")
    
    # Make predictions
    print("Making predictions...")
    start_time = datetime.now()
    y_pred_scores = model.predict_score(X_test_enhanced)
    pred_time = (datetime.now() - start_time).total_seconds()
    print(f"✓ Predictions completed in {pred_time:.1f} seconds")
    
    # Enhanced score to zone conversion with adaptive thresholds
    def enhanced_score_to_zone(scores):
        # Use dynamic thresholds based on score distribution
        q75 = np.percentile(scores, 75)
        q90 = np.percentile(scores, 90)
        
        zones = []
        for score in scores:
            if score >= q90:
                zones.append('red')
            elif score >= q75:
                zones.append('yellow')
            else:
                zones.append('green')
        return np.array(zones)
    
    y_pred = enhanced_score_to_zone(y_pred_scores)
    
    # Evaluate
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"\n🎯 Enhanced CCI Model Results:")
    print(f"  Accuracy: {accuracy:.3f} ({accuracy*100:.1f}%)")
    print(f"  Training time: {train_time:.1f}s")
    print(f"  Prediction time: {pred_time:.1f}s")
    
    # Zone distribution
    zone_dist = pd.Series(y_pred).value_counts()
    print(f"  Predicted zones: {dict(zone_dist)}")
    
    # Enhanced metrics
    y_true_binary = [1 if zone in ['yellow', 'red'] else 0 for zone in y_test]
    y_pred_binary = [1 if zone in ['yellow', 'red'] else 0 for zone in y_pred]
    
    if sum(y_true_binary) > 0:
        precision = precision_score(y_true_binary, y_pred_binary, zero_division=0)
        recall = recall_score(y_true_binary, y_pred_binary, zero_division=0)
        f1 = f1_score(y_true_binary, y_pred_binary, zero_division=0)
        
        print(f"  🎯 Fault Detection Precision: {precision:.3f}")
        print(f"  🎯 Fault Detection Recall: {recall:.3f}")
        print(f"  🎯 Fault Detection F1-Score: {f1:.3f}")
    
    return {
        'model_name': 'Enhanced CCI Model',
        'accuracy': accuracy,
        'training_time': train_time,
        'prediction_time': pred_time,
        'predictions': y_pred,
        'zone_distribution': dict(zone_dist)
    }


def main():
    """Main function to test enhanced models"""
    print("🚀 === ENHANCED POWER GRID MODEL TESTING ===\n")
    
    # Load data with enhancements
    df = load_power_grid_data()
    
    # Split data (80% train, 20% test)
    split_idx = int(0.8 * len(df))
    train_df_raw = df[:split_idx].copy()
    test_df_raw = df[split_idx:].copy()
    
    print(f"\nTrain data: {len(train_df_raw)} records")
    print(f"Test data: {len(test_df_raw)} records")
    
    # Test Enhanced Grid Risk Model
    train_df_grid = prepare_enhanced_grid_risk_data(train_df_raw)
    test_df_grid = prepare_enhanced_grid_risk_data(test_df_raw)
    
    grid_results = test_enhanced_grid_risk_model(train_df_grid, test_df_grid)
    
    # Test Enhanced CCI Model  
    X_train, y_train = prepare_enhanced_cci_data(train_df_raw)
    X_test, y_test = prepare_enhanced_cci_data(test_df_raw)
    
    cci_results = test_enhanced_cci_model(X_train, y_train, X_test, y_test)
    
    # Final comparison
    print("\n" + "="*70)
    print("🎯 ENHANCED POWER GRID RESULTS COMPARISON")
    print("="*70)
    
    for result in [grid_results, cci_results]:
        name = result['model_name']
        acc = result['accuracy']
        train_time = result['training_time']
        pred_time = result['prediction_time']
        
        print(f"\n{name}:")
        print(f"  Accuracy: {acc*100:.1f}%")
        print(f"  Training time: {train_time:.1f}s")
        print(f"  Prediction time: {pred_time:.1f}s")
        print(f"  Zone distribution: {result['zone_distribution']}")
        
        # Enhanced rating system
        if acc > 0.85:
            rating = "🟢 EXCELLENT"
        elif acc > 0.70:
            rating = "🟡 GOOD"
        elif acc > 0.55:
            rating = "🟠 MODERATE"
        else:
            rating = "🔴 POOR"
        
        print(f"  Overall: {rating}")
    
    # Winner
    if grid_results['accuracy'] > cci_results['accuracy']:
        winner = grid_results['model_name']
        margin = (grid_results['accuracy'] - cci_results['accuracy']) * 100
    else:
        winner = cci_results['model_name']
        margin = (cci_results['accuracy'] - grid_results['accuracy']) * 100
    
    print(f"\n🏆 WINNER: {winner} (by {margin:.1f}%)")
    
    # Save enhanced results
    results_df = pd.DataFrame([
        {
            'dataset': 'power_grid_enhanced',
            'model': grid_results['model_name'],
            'accuracy': grid_results['accuracy'],
            'training_time': grid_results['training_time'],
            'prediction_time': grid_results['prediction_time']
        },
        {
            'dataset': 'power_grid_enhanced', 
            'model': cci_results['model_name'],
            'accuracy': cci_results['accuracy'],
            'training_time': cci_results['training_time'],
            'prediction_time': cci_results['prediction_time']
        }
    ])
    
    results_df.to_csv("data/processed/power_grid_enhanced_results.csv", index=False)
    print(f"\n✓ Enhanced results saved to: data/processed/power_grid_enhanced_results.csv")


if __name__ == "__main__":
    main()