"""
Test the complete pipeline with cable_state validation
====================================================

This script:
1. Loads the Kaggle dataset (or creates synthetic data)
2. Trains the grid_risk_model 
3. Makes predictions
4. Compares predictions vs original cable_state for validation
5. Tests the Camp Fire backtest scenario
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from models.grid_risk_model import CCIPipeline, CCIPipelineConfig, validate_predictions_vs_cable_state, backtest_warning_lead_time
from experiments.data_loader import load_kaggle_cable_dataset, create_sample_datasets
import pandas as pd
from datetime import datetime, timedelta
import json


def run_complete_test():
    print("=== LiveWire Complete Pipeline Test ===\n")
    
    # Step 1: Load data
    print("1. Loading dataset...")
    try:
        # Try to load the real Kaggle dataset first
        csv_path = "./data/raw/cable_monitoring_dataset.csv"
        if not os.path.exists(csv_path):
            print("Kaggle dataset not found, creating synthetic data...")
            from experiments.data_loader import create_synthetic_test_data
            csv_path = create_synthetic_test_data()
        
        mapped_df = load_kaggle_cable_dataset(csv_path)
        print(f"✓ Dataset loaded: {len(mapped_df)} rows, {len(mapped_df['component_id'].unique())} components")
        
    except Exception as e:
        print(f"✗ Error loading data: {e}")
        return
    
    # Step 2: Create train/test splits
    print("\n2. Creating train/test splits...")
    calib_path, test_path = create_sample_datasets(mapped_df, train_split=0.7)
    
    calib_df = pd.read_csv(calib_path)
    test_df = pd.read_csv(test_path)
    print(f"✓ Calibration data: {len(calib_df)} rows")
    print(f"✓ Test data: {len(test_df)} rows")
    
    # Step 3: Train the model
    print("\n3. Training CCI Pipeline...")
    try:
        pipe = CCIPipeline(CCIPipelineConfig())
        pipe.fit(calib_df)
        print("✓ Model trained successfully")
        
        # Save the model
        os.makedirs("./artifacts", exist_ok=True)
        pipe.save("./artifacts")
        print("✓ Model saved to ./artifacts")
        
    except Exception as e:
        print(f"✗ Error training model: {e}")
        return
    
    # Step 4: Make predictions
    print("\n4. Making predictions on test data...")
    try:
        scored = pipe.score(test_df)
        print(f"✓ Predictions made for {len(scored)} rows")
        
        # Save results
        os.makedirs("./data/processed", exist_ok=True)
        scored.to_csv("./data/processed/scored_results.csv", index=False)
        print("✓ Results saved to ./data/processed/scored_results.csv")
        
    except Exception as e:
        print(f"✗ Error making predictions: {e}")
        return
    
    # Step 5: Validate predictions vs original cable states
    print("\n5. Validating predictions vs original cable states...")
    try:
        validation = validate_predictions_vs_cable_state(scored)
        
        if "error" in validation:
            print(f"✗ Validation error: {validation['error']}")
        else:
            print(f"✓ Model accuracy: {validation['accuracy']:.3f}")
            print("\nConfusion Matrix (Predicted vs Actual):")
            conf_df = pd.DataFrame(validation['confusion_matrix'])
            print(conf_df)
            
            print("\nSample predictions:")
            for sample in validation['sample_comparison'][:5]:
                print(f"  {sample['component_id']}: predicted={sample['zone']}, actual={sample['original_cable_state']}, cci={sample['cci']:.3f}")
        
    except Exception as e:
        print(f"✗ Error in validation: {e}")
    
    # Step 6: Test Camp Fire scenario
    print("\n6. Testing Camp Fire backtest scenario...")
    try:
        # Find a component that goes critical in the test data
        critical_components = scored[scored['zone'] == 'red']['component_id'].unique()
        
        if len(critical_components) > 0:
            test_component = critical_components[0]
            # Simulate fire start time as the last timestamp + 1 hour
            last_ts = pd.to_datetime(scored['timestamp']).max()
            fire_time = (last_ts + timedelta(hours=1)).isoformat()
            
            lead_time = backtest_warning_lead_time(pipe, scored, fire_time, test_component)
            
            print(f"✓ Camp Fire simulation for component '{test_component}':")
            print(f"  - Lead time: {lead_time['lead_time_hours']:.1f} hours")
            print(f"  - First red alert: {lead_time['first_red_ts']}")
            
            if lead_time['lead_time_hours'] > 0:
                print(f"  🎯 SUCCESS: Model would have warned {lead_time['lead_time_hours']:.1f} hours before the event!")
            else:
                print("  ⚠️  No early warning detected")
                
        else:
            print("  ℹ️  No critical components found in test data")
            
    except Exception as e:
        print(f"✗ Error in Camp Fire test: {e}")
    
    # Step 7: Summary
    print("\n=== Test Complete ===")
    print("Files created:")
    print("- ./data/calib/pre2018.csv - Training data")
    print("- ./data/pre_fire/2018_runup.csv - Test data")  
    print("- ./data/processed/scored_results.csv - Model predictions")
    print("- ./artifacts/ - Trained model")
    print("\nNext steps:")
    print("- Review predictions in scored_results.csv")
    print("- Adjust model parameters if needed")
    print("- Integrate with frontend/hardware for live monitoring")


if __name__ == "__main__":
    run_complete_test()