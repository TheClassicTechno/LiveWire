"""
Compare CCI Model vs Grid Risk Model on Camp Fire Data
=====================================================

This script trains and evaluates both models on realistic Camp Fire data
to determine which is most accurate for predicting the 2018 Camp Fire.
"""

import sys
import os
sys.path.append('.')

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time

# Import both models
from models.grid_risk_model import CCIPipeline, CCIPipelineConfig, validate_predictions_vs_cable_state, backtest_warning_lead_time
from model import CCIModel, timeseries_to_feature_matrix, generate_synthetic_dataset

from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import warnings
warnings.filterwarnings('ignore')


def prepare_data_for_cci_model(df):
    """Convert tabular data to time-series format for CCIModel."""
    
    print("Converting data for CCIModel...")
    
    # Group by component and create time-series windows
    components = df['component_id'].unique()
    X_list = []
    ages_list = []
    y_list = []
    
    window_size = 24  # 24 time steps per sample (6 days at 4-hour intervals)
    
    for comp in components:
        comp_data = df[df['component_id'] == comp].sort_values('timestamp')
        
        if len(comp_data) < window_size:
            continue
            
        # Create sliding windows
        for i in range(len(comp_data) - window_size + 1):
            window = comp_data.iloc[i:i+window_size]
            
            # Extract signals (vibration, temperature, strain)
            signals = window[['vibration', 'temperature', 'strain']].values
            X_list.append(signals)
            
            # Age (constant for all windows of same component)
            ages_list.append(window['age_years'].iloc[0])
            
            # Target (use the final state in the window)
            final_state = window['cable_state'].iloc[-1]
            if final_state == "Critical":
                y_list.append(0.9)
            elif final_state == "Degradation":
                y_list.append(0.7)
            elif final_state == "Warning": 
                y_list.append(0.4)
            else:  # Normal
                y_list.append(0.1)
    
    X = np.array(X_list)
    ages = np.array(ages_list)
    y = np.array(y_list)
    
    print(f"Created {len(X)} time-series samples for CCIModel")
    print(f"Shape: {X.shape}")
    
    return X, ages, y


def train_and_evaluate_grid_risk_model(train_df, test_df):
    """Train and evaluate the Grid Risk Model."""
    
    print("\n=== GRID RISK MODEL ===")
    
    # Configure for better sensitivity
    config = CCIPipelineConfig()
    config.use_quantile_zones = True
    config.yellow_q = 0.6
    config.red_q = 0.8
    
    # Train
    print("Training Grid Risk Model...")
    start_time = time.time()
    
    pipeline = CCIPipeline(config)
    pipeline.fit(train_df)
    
    train_time = time.time() - start_time
    print(f"✓ Training completed in {train_time:.1f} seconds")
    
    # Predict
    print("Making predictions...")
    start_time = time.time()
    
    predictions = pipeline.score(test_df)
    
    predict_time = time.time() - start_time
    print(f"✓ Predictions completed in {predict_time:.1f} seconds")
    
    # Evaluate
    evaluation = evaluate_predictions(predictions, "Grid Risk Model")
    
    # Test Camp Fire warning
    camp_fire_result = test_camp_fire_warning(pipeline, predictions)
    
    return {
        'model_name': 'Grid Risk Model',
        'train_time': train_time,
        'predict_time': predict_time,
        'predictions': predictions,
        'evaluation': evaluation,
        'camp_fire_warning': camp_fire_result
    }


def train_and_evaluate_cci_model(train_df, test_df):
    """Train and evaluate the CCI Model."""
    
    print("\n=== CCI MODEL ===")
    
    # Prepare training data
    print("Preparing training data...")
    X_train, ages_train, y_train = prepare_data_for_cci_model(train_df)
    
    if len(X_train) == 0:
        print("❌ No training data available for CCIModel")
        return None
    
    # Train
    print("Training CCI Model...")
    start_time = time.time()
    
    # Convert to features and train
    train_features = timeseries_to_feature_matrix(X_train, ages_train)
    
    model = CCIModel()
    model.fit(train_features, y_train)
    
    train_time = time.time() - start_time
    print(f"✓ Training completed in {train_time:.1f} seconds")
    
    # Prepare test data
    print("Preparing test data...")
    X_test, ages_test, y_test = prepare_data_for_cci_model(test_df)
    
    if len(X_test) == 0:
        print("❌ No test data available for CCIModel")
        return None
    
    # Predict
    print("Making predictions...")
    start_time = time.time()
    
    test_features = timeseries_to_feature_matrix(X_test, ages_test)
    cci_scores = model.predict_score(test_features)
    
    predict_time = time.time() - start_time
    print(f"✓ Predictions completed in {predict_time:.1f} seconds")
    
    # Convert CCI scores to zones for comparison
    predictions_df = test_df.copy()
    
    # Map CCI scores to components (take average if multiple windows per component)
    component_scores = {}
    component_zones = {}
    
    test_components = [test_df[test_df['component_id'] == comp].iloc[0]['component_id'] 
                      for comp in test_df['component_id'].unique()]
    
    for i, score in enumerate(cci_scores):
        comp_idx = i % len(test_components)
        comp = test_components[comp_idx]
        
        if comp not in component_scores:
            component_scores[comp] = []
        component_scores[comp].append(score)
    
    # Average scores per component and assign zones
    for comp, scores in component_scores.items():
        avg_score = np.mean(scores)
        
        if avg_score > 0.7:
            zone = 'red'
        elif avg_score > 0.4:
            zone = 'yellow'
        else:
            zone = 'green'
            
        component_zones[comp] = zone
    
    # Add predictions to dataframe
    predictions_df['cci'] = predictions_df['component_id'].map(
        lambda x: np.mean(component_scores.get(x, [0.0]))
    )
    predictions_df['zone'] = predictions_df['component_id'].map(
        lambda x: component_zones.get(x, 'green')
    )
    
    # Evaluate
    evaluation = evaluate_predictions(predictions_df, "CCI Model")
    
    # Test Camp Fire warning
    camp_fire_result = test_camp_fire_warning_simple(predictions_df)
    
    return {
        'model_name': 'CCI Model', 
        'train_time': train_time,
        'predict_time': predict_time,
        'predictions': predictions_df,
        'evaluation': evaluation,
        'camp_fire_warning': camp_fire_result
    }


def evaluate_predictions(predictions_df, model_name):
    """Evaluate model predictions against ground truth."""
    
    print(f"\nEvaluating {model_name}...")
    
    # Map cable states to zones for comparison
    def map_cable_state_to_risk(state):
        state_str = str(state).lower()
        if 'critical' in state_str:
            return 'red'
        elif any(word in state_str for word in ['degradation', 'warning']):
            return 'yellow'
        else:
            return 'green'
    
    predictions_df['true_zone'] = predictions_df['cable_state'].apply(map_cable_state_to_risk)
    
    # Calculate accuracy
    accuracy = accuracy_score(predictions_df['true_zone'], predictions_df['zone'])
    
    # Zone distribution
    zone_dist = predictions_df['zone'].value_counts()
    
    # Confusion matrix
    cm = confusion_matrix(predictions_df['true_zone'], predictions_df['zone'], 
                         labels=['green', 'yellow', 'red'])
    
    print(f"  Accuracy: {accuracy:.3f} ({accuracy*100:.1f}%)")
    print(f"  Zone distribution: {dict(zone_dist)}")
    
    return {
        'accuracy': accuracy,
        'zone_distribution': dict(zone_dist),
        'confusion_matrix': cm.tolist()
    }


def test_camp_fire_warning(pipeline, predictions_df):
    """Test Camp Fire early warning capability."""
    
    print("\nTesting Camp Fire early warning...")
    
    try:
        # Test on the 97-year-old hook
        fire_time = "2018-11-08T06:33:00"
        hook_component = "HOOK_97YO"
        
        lead_time = backtest_warning_lead_time(pipeline, predictions_df, fire_time, hook_component)
        
        if lead_time['lead_time_hours'] > 0:
            print(f"  🎯 SUCCESS: {lead_time['lead_time_hours']:.1f} hours lead time")
            return lead_time
        else:
            print(f"  ❌ FAILED: No advance warning")
            return {'lead_time_hours': 0, 'first_red_ts': None}
            
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        return {'lead_time_hours': 0, 'first_red_ts': None}


def test_camp_fire_warning_simple(predictions_df):
    """Simple Camp Fire warning test for CCI model."""
    
    print("\nTesting Camp Fire early warning...")
    
    # Check if HOOK_97YO ever goes red
    hook_data = predictions_df[predictions_df['component_id'] == 'HOOK_97YO']
    red_alerts = hook_data[hook_data['zone'] == 'red']
    
    if len(red_alerts) > 0:
        first_red = red_alerts['timestamp'].min()
        fire_time = pd.Timestamp("2018-11-08T06:33:00")
        
        if first_red < fire_time:
            lead_hours = (fire_time - first_red).total_seconds() / 3600
            print(f"  🎯 SUCCESS: {lead_hours:.1f} hours lead time")
            return {'lead_time_hours': lead_hours, 'first_red_ts': str(first_red)}
        else:
            print(f"  ❌ FAILED: Alert after fire start")
            return {'lead_time_hours': 0, 'first_red_ts': str(first_red)}
    else:
        print(f"  ❌ FAILED: No red alerts for critical component")
        return {'lead_time_hours': 0, 'first_red_ts': None}


def compare_models():
    """Main comparison function."""
    
    print("=== CAMP FIRE MODEL COMPARISON ===\n")
    
    # Generate realistic Camp Fire data
    print("Generating Camp Fire data...")
    from generate_camp_fire_data import generate_camp_fire_data, save_camp_fire_datasets
    
    df = generate_camp_fire_data(
        start_date="2016-01-01",
        end_date="2018-11-08 06:33:00",
        freq_hours=4
    )
    
    # Save data
    calib_path, test_path = save_camp_fire_datasets(df)
    
    # Load train/test splits
    train_df = pd.read_csv(calib_path)
    test_df = pd.read_csv(test_path)
    
    print(f"\nTrain data: {len(train_df):,} records")
    print(f"Test data: {len(test_df):,} records")
    
    # Train and evaluate both models
    results = {}
    
    # Grid Risk Model
    try:
        results['grid_risk'] = train_and_evaluate_grid_risk_model(train_df, test_df)
    except Exception as e:
        print(f"❌ Grid Risk Model failed: {e}")
        results['grid_risk'] = None
    
    # CCI Model  
    try:
        results['cci'] = train_and_evaluate_cci_model(train_df, test_df)
    except Exception as e:
        print(f"❌ CCI Model failed: {e}")
        results['cci'] = None
    
    # Compare results
    print("\n" + "="*60)
    print("FINAL COMPARISON")
    print("="*60)
    
    for model_key, result in results.items():
        if result is None:
            continue
            
        model_name = result['model_name']
        accuracy = result['evaluation']['accuracy']
        lead_time = result['camp_fire_warning']['lead_time_hours']
        
        print(f"\n{model_name}:")
        print(f"  Accuracy: {accuracy:.1%}")
        print(f"  Training time: {result['train_time']:.1f}s")
        print(f"  Prediction time: {result['predict_time']:.1f}s")
        print(f"  Camp Fire lead time: {lead_time:.1f} hours ({lead_time/24:.1f} days)")
        
        # Performance verdict
        if lead_time > 24 and accuracy > 0.6:
            verdict = "🟢 EXCELLENT"
        elif lead_time > 6 and accuracy > 0.4:
            verdict = "🟡 GOOD"
        elif lead_time > 0 or accuracy > 0.3:
            verdict = "🟠 MODERATE" 
        else:
            verdict = "🔴 POOR"
            
        print(f"  Overall: {verdict}")
    
    # Declare winner
    if results['grid_risk'] and results['cci']:
        grid_score = (results['grid_risk']['evaluation']['accuracy'] + 
                     min(results['grid_risk']['camp_fire_warning']['lead_time_hours']/48, 1.0)) / 2
        cci_score = (results['cci']['evaluation']['accuracy'] + 
                    min(results['cci']['camp_fire_warning']['lead_time_hours']/48, 1.0)) / 2
        
        if grid_score > cci_score:
            winner = "Grid Risk Model"
        elif cci_score > grid_score:
            winner = "CCI Model"
        else:
            winner = "TIE"
            
        print(f"\n🏆 WINNER: {winner}")
    
    return results


if __name__ == "__main__":
    results = compare_models()