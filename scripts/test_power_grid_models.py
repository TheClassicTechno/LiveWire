"""
Test LiveWire CCI Models on Power Grid Dataset
==============================================

This script tests both the Grid Risk Model and CCI Model on real power grid data
to evaluate their performance on electrical grid fault detection.
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


def load_power_grid_data():
    """Load and prepare the power grid dataset"""
    print("Loading power grid dataset...")
    
    df = pd.read_csv("data/power_grid_dataset.csv")
    print(f"✓ Loaded {len(df)} records")
    print(f"✓ Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    
    # Check fault distribution
    fault_dist = df['fault_detected'].value_counts()
    print(f"✓ Fault distribution: {dict(fault_dist)}")
    
    return df


def prepare_grid_risk_data(df):
    """Convert power grid data to Grid Risk Model format"""
    print("Converting to Grid Risk Model format...")
    
    # Map power grid features to cable monitoring features
    grid_df = pd.DataFrame()
    
    # Create component_id (simulate multiple grid components)
    grid_df['component_id'] = 'GRID_' + (df.index % 5 + 1).astype(str).str.zfill(3)
    
    # Map timestamp
    grid_df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Map electrical features to sensor features (raw features only)
    # Voltage variations as temperature proxy
    grid_df['temperature'] = (df['voltage'] - df['voltage'].mean()) / df['voltage'].std()
    
    # Frequency variations as vibration proxy  
    grid_df['vibration'] = (df['frequency'] - df['frequency'].mean()) / df['frequency'].std()
    
    # Power flow imbalances as strain proxy
    power_cols = [col for col in df.columns if 'power_flow' in col]
    grid_df['strain'] = df[power_cols].std(axis=1)
    grid_df['strain'] = (grid_df['strain'] - grid_df['strain'].mean()) / grid_df['strain'].std()
    
    # Map grid status and faults to cable states
    conditions = [
        (df['fault_detected'] == 1) & (df['grid_status'] == 0),  # Fault + unstable = Critical
        (df['fault_detected'] == 1) & (df['grid_status'] == 1),  # Fault + stable = Warning  
        (df['fault_detected'] == 0) & (df['voltage'] < 0.95),    # Low voltage = Degradation
        (df['fault_detected'] == 0) & (df['voltage'] >= 0.95)    # Normal voltage = Normal
    ]
    choices = ['Critical', 'Warning', 'Degradation', 'Normal']
    grid_df['cable_state'] = np.select(conditions, choices, default='Normal')
    
    # Add synthetic features that the Grid Risk Model expects
    grid_df['energy'] = np.random.normal(0, 1, len(grid_df))
    grid_df['processing_speed'] = np.random.normal(0, 1, len(grid_df))
    grid_df['age_years'] = np.random.choice([15, 25, 35, 45], len(grid_df))
    
    # Sort by component and timestamp for proper rolling feature computation
    grid_df = grid_df.sort_values(['component_id', 'timestamp']).reset_index(drop=True)
    
    print(f"✓ Created {len(grid_df)} records for Grid Risk Model")
    state_dist = grid_df['cable_state'].value_counts()
    print(f"✓ Cable state distribution: {dict(state_dist)}")
    
    return grid_df


def prepare_cci_data(df, sequence_length=24):
    """Convert power grid data to CCI Model format (time series)"""
    print(f"Converting to CCI Model format (sequence_length={sequence_length})...")
    
    # Use key electrical features
    feature_cols = ['voltage', 'frequency']
    
    # Add load summary as third feature
    load_cols = [col for col in df.columns if col.startswith('load_node')]
    df['load_avg'] = df[load_cols].mean(axis=1)
    feature_cols.append('load_avg')
    
    # Normalize features
    feature_data = df[feature_cols].copy()
    for col in feature_cols:
        feature_data[col] = (feature_data[col] - feature_data[col].mean()) / feature_data[col].std()
    
    # Create time series sequences
    sequences = []
    labels = []
    
    for i in range(sequence_length, len(feature_data)):
        # Extract sequence
        seq = feature_data.iloc[i-sequence_length:i].values
        sequences.append(seq)
        
        # Map fault to zone (simplified)
        if df.iloc[i]['fault_detected'] == 1:
            if df.iloc[i]['grid_status'] == 0:
                labels.append('red')  # Critical fault
            else:
                labels.append('yellow')  # Warning fault
        else:
            labels.append('green')  # Normal
    
    X = np.array(sequences)
    y = np.array(labels)
    
    print(f"✓ Created {len(X)} sequences, shape: {X.shape}")
    print(f"✓ Label distribution: {dict(pd.Series(y).value_counts())}")
    
    return X, y


def test_grid_risk_model(train_df, test_df):
    """Test Grid Risk Model on power grid data"""
    print("\n=== TESTING GRID RISK MODEL ===")
    
    # Initialize model
    config = CCIPipelineConfig()
    model = CCIPipeline(config)
    
    print("Training Grid Risk Model...")
    start_time = datetime.now()
    model.fit(train_df)
    train_time = (datetime.now() - start_time).total_seconds()
    print(f"✓ Training completed in {train_time:.1f} seconds")
    
    # Make predictions on the SAME training data first to ensure consistency
    print("Scoring training data...")
    train_scored = model.score(train_df)
    
    # Now try test data
    print("Making predictions on test data...")
    start_time = datetime.now()
    try:
        predictions = model.score(test_df)
        pred_time = (datetime.now() - start_time).total_seconds()
        print(f"✓ Predictions completed in {pred_time:.1f} seconds")
    except Exception as e:
        print(f"❌ Prediction failed: {e}")
        # Use a simpler evaluation on combined dataset
        combined_df = pd.concat([train_df, test_df], ignore_index=True)
        combined_df = combined_df.sort_values(['component_id', 'timestamp']).reset_index(drop=True)
        print("Trying combined dataset approach...")
        all_predictions = model.score(combined_df)
        # Extract test portion
        predictions = all_predictions.tail(len(test_df)).copy()
        pred_time = (datetime.now() - start_time).total_seconds()
        print(f"✓ Predictions completed in {pred_time:.1f} seconds")
    
    # Evaluate
    y_true = test_df['cable_state'].values
    y_pred = predictions['zone'].values
    
    # Map states to common format for evaluation
    state_map = {'Normal': 'green', 'Degradation': 'yellow', 'Warning': 'yellow', 'Critical': 'red'}
    y_true_mapped = [state_map.get(state, 'green') for state in y_true]
    
    accuracy = accuracy_score(y_true_mapped, y_pred)
    
    print(f"\nGrid Risk Model Results:")
    print(f"  Accuracy: {accuracy:.3f} ({accuracy*100:.1f}%)")
    print(f"  Training time: {train_time:.1f}s")
    print(f"  Prediction time: {pred_time:.1f}s")
    
    # Zone distribution
    zone_dist = pd.Series(y_pred).value_counts()
    print(f"  Predicted zones: {dict(zone_dist)}")
    
    # Fault detection metrics
    y_true_binary = [1 if state in ['Warning', 'Critical'] else 0 for state in y_true]
    y_pred_binary = [1 if zone in ['yellow', 'red'] else 0 for zone in y_pred]
    
    if sum(y_true_binary) > 0:
        precision = precision_score(y_true_binary, y_pred_binary, zero_division=0)
        recall = recall_score(y_true_binary, y_pred_binary, zero_division=0)
        f1 = f1_score(y_true_binary, y_pred_binary, zero_division=0)
        
        print(f"  Fault Detection Precision: {precision:.3f}")
        print(f"  Fault Detection Recall: {recall:.3f}")
        print(f"  Fault Detection F1-Score: {f1:.3f}")
    
    return {
        'model_name': 'Grid Risk Model',
        'accuracy': accuracy,
        'training_time': train_time,
        'prediction_time': pred_time,
        'predictions': y_pred,
        'zone_distribution': dict(zone_dist)
    }


def test_cci_model(X_train, y_train, X_test, y_test):
    """Test CCI Model on power grid data"""
    print("\n=== TESTING CCI MODEL ===")
    
    # Initialize model with RandomForestRegressor
    from sklearn.ensemble import RandomForestRegressor
    rf_model = RandomForestRegressor(n_estimators=50, random_state=42)
    model = CCIModel(model=rf_model)
    
    # Convert time series to feature matrix for training
    print("Converting time series to features...")
    X_train_features = timeseries_to_feature_matrix(X_train)
    X_test_features = timeseries_to_feature_matrix(X_test)
    
    # Convert zone labels to numeric scores for regression
    zone_to_score = {'green': 0.0, 'yellow': 0.5, 'red': 1.0}
    y_train_scores = np.array([zone_to_score[zone] for zone in y_train])
    
    print("Training CCI Model...")
    start_time = datetime.now()
    model.fit(X_train_features, y_train_scores)
    train_time = (datetime.now() - start_time).total_seconds()
    print(f"✓ Training completed in {train_time:.1f} seconds")
    
    # Make predictions
    print("Making predictions...")
    start_time = datetime.now()
    y_pred_scores = model.predict_score(X_test_features)
    pred_time = (datetime.now() - start_time).total_seconds()
    print(f"✓ Predictions completed in {pred_time:.1f} seconds")
    
    # Convert scores back to zones
    def score_to_zone(score):
        if score >= 0.75:
            return 'red'
        elif score >= 0.25:
            return 'yellow'
        else:
            return 'green'
    
    y_pred = np.array([score_to_zone(score) for score in y_pred_scores])
    
    # Evaluate
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"\nCCI Model Results:")
    print(f"  Accuracy: {accuracy:.3f} ({accuracy*100:.1f}%)")
    print(f"  Training time: {train_time:.1f}s")
    print(f"  Prediction time: {pred_time:.1f}s")
    
    # Zone distribution
    zone_dist = pd.Series(y_pred).value_counts()
    print(f"  Predicted zones: {dict(zone_dist)}")
    
    # Fault detection metrics
    y_true_binary = [1 if zone in ['yellow', 'red'] else 0 for zone in y_test]
    y_pred_binary = [1 if zone in ['yellow', 'red'] else 0 for zone in y_pred]
    
    if sum(y_true_binary) > 0:
        precision = precision_score(y_true_binary, y_pred_binary, zero_division=0)
        recall = recall_score(y_true_binary, y_pred_binary, zero_division=0)
        f1 = f1_score(y_true_binary, y_pred_binary, zero_division=0)
        
        print(f"  Fault Detection Precision: {precision:.3f}")
        print(f"  Fault Detection Recall: {recall:.3f}")
        print(f"  Fault Detection F1-Score: {f1:.3f}")
    
    return {
        'model_name': 'CCI Model',
        'accuracy': accuracy,
        'training_time': train_time,
        'prediction_time': pred_time,
        'predictions': y_pred,
        'zone_distribution': dict(zone_dist)
    }


def main():
    """Main function to test both models on power grid data"""
    print("=== POWER GRID MODEL TESTING ===\n")
    
    # Load data
    df = load_power_grid_data()
    
    # Split data (80% train, 20% test)
    split_idx = int(0.8 * len(df))
    train_df_raw = df[:split_idx].copy()
    test_df_raw = df[split_idx:].copy()
    
    print(f"\nTrain data: {len(train_df_raw)} records")
    print(f"Test data: {len(test_df_raw)} records")
    
    # Test Grid Risk Model
    train_df_grid = prepare_grid_risk_data(train_df_raw)
    test_df_grid = prepare_grid_risk_data(test_df_raw)
    
    grid_results = test_grid_risk_model(train_df_grid, test_df_grid)
    
    # Test CCI Model  
    X_train, y_train = prepare_cci_data(train_df_raw)
    X_test, y_test = prepare_cci_data(test_df_raw)
    
    cci_results = test_cci_model(X_train, y_train, X_test, y_test)
    
    # Final comparison
    print("\n" + "="*60)
    print("FINAL POWER GRID RESULTS COMPARISON")
    print("="*60)
    
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
        
        # Overall rating
        if acc > 0.8:
            rating = "🟢 EXCELLENT"
        elif acc > 0.6:
            rating = "🟡 GOOD"
        elif acc > 0.4:
            rating = "🟠 MODERATE"
        else:
            rating = "🔴 POOR"
        
        print(f"  Overall: {rating}")
    
    # Winner
    if grid_results['accuracy'] > cci_results['accuracy']:
        winner = "Grid Risk Model"
        margin = (grid_results['accuracy'] - cci_results['accuracy']) * 100
    else:
        winner = "CCI Model"
        margin = (cci_results['accuracy'] - grid_results['accuracy']) * 100
    
    print(f"\n🏆 WINNER: {winner} (by {margin:.1f}%)")
    
    # Save results
    results_df = pd.DataFrame([
        {
            'dataset': 'power_grid',
            'model': 'Grid Risk Model',
            'accuracy': grid_results['accuracy'],
            'training_time': grid_results['training_time'],
            'prediction_time': grid_results['prediction_time']
        },
        {
            'dataset': 'power_grid', 
            'model': 'CCI Model',
            'accuracy': cci_results['accuracy'],
            'training_time': cci_results['training_time'],
            'prediction_time': cci_results['prediction_time']
        }
    ])
    
    results_df.to_csv("data/processed/power_grid_results.csv", index=False)
    print(f"\n✓ Results saved to: data/processed/power_grid_results.csv")


if __name__ == "__main__":
    main()