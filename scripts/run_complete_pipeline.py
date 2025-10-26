"""
Complete LiveWire Pipeline Test with Real Dataset
================================================

This script runs the entire pipeline with the real Kaggle dataset:
1. Loads the dataset from ./data/raw/cable_monitoring_dataset.csv
2. Trains the CCI model
3. Makes predictions  
4. Validates against cable_state
5. Tests Camp Fire scenario
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from models.grid_risk_model import CCIPipeline, CCIPipelineConfig, validate_predictions_vs_cable_state, backtest_warning_lead_time
import pandas as pd
from datetime import datetime, timedelta
import numpy as np


def run_complete_pipeline():
    print("=== LiveWire Complete Pipeline with Real Dataset ===\n")
    
    # Step 1: Load the real dataset
    print("1. Loading real Kaggle dataset...")
    try:
        # Check if we have the splits already
        calib_path = "./data/calib/pre2018.csv"
        test_path = "./data/pre_fire/2018_runup.csv"
        
        if not os.path.exists(calib_path) or not os.path.exists(test_path):
            print("Dataset splits not found. Run: python data_loader.py first")
            return
            
        calib_df = pd.read_csv(calib_path)
        test_df = pd.read_csv(test_path)
        
        print(f"✓ Calibration data: {len(calib_df)} rows, {len(calib_df['component_id'].unique())} components")
        print(f"✓ Test data: {len(test_df)} rows, {len(test_df['component_id'].unique())} components")
        
        # Show cable states distribution
        print(f"✓ Cable states in calibration: {calib_df['cable_state'].value_counts().to_dict()}")
        
    except Exception as e:
        print(f"✗ Error loading data: {e}")
        return
    
    # Step 2: Train the model
    print("\n2. Training CCI Pipeline on real data...")
    try:
        pipe = CCIPipeline(CCIPipelineConfig())
        
        # Train on a subset first (for speed)
        sample_size = min(50000, len(calib_df))
        calib_sample = calib_df.sample(n=sample_size, random_state=42)
        print(f"Training on {sample_size} samples for speed...")
        
        pipe.fit(calib_sample)
        print("✓ Model trained successfully")
        
        # Save the model
        os.makedirs("./artifacts", exist_ok=True)
        pipe.save("./artifacts")
        print("✓ Model saved to ./artifacts")
        
    except Exception as e:
        print(f"✗ Error training model: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 3: Make predictions on test data
    print("\n3. Making predictions on test data...")
    try:
        # Use a smaller test sample for speed
        test_sample_size = min(10000, len(test_df))
        test_sample = test_df.sample(n=test_sample_size, random_state=42)
        print(f"Predicting on {test_sample_size} test samples...")
        
        scored = pipe.score(test_sample)
        print(f"✓ Predictions made for {len(scored)} rows")
        
        # Save results
        os.makedirs("./data/processed", exist_ok=True)
        scored.to_csv("./data/processed/scored_2018.csv", index=False)
        print("✓ Results saved to ./data/processed/scored_2018.csv")
        
        # Show zone distribution
        zone_counts = scored['zone'].value_counts()
        print(f"✓ Zone predictions: {zone_counts.to_dict()}")
        
    except Exception as e:
        print(f"✗ Error making predictions: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 4: Validate against cable states
    print("\n4. Validating predictions vs original cable states...")
    try:
        validation = validate_predictions_vs_cable_state(scored)
        
        if "error" in validation:
            print(f"✗ Validation error: {validation['error']}")
        else:
            print(f"✓ Model accuracy: {validation['accuracy']:.3f}")
            
            # Show some examples
            print("\nSample predictions vs actual:")
            for sample in validation['sample_comparison'][:5]:
                print(f"  {sample['component_id']}: predicted={sample['zone']}, actual={sample['original_cable_state']}, cci={sample['cci']:.3f}")
        
    except Exception as e:
        print(f"✗ Error in validation: {e}")
        import traceback
        traceback.print_exc()
    
    # Step 5: Camp Fire backtest
    print("\n5. Testing Camp Fire scenario...")
    try:
        # Find components that go into red zone
        red_components = scored[scored['zone'] == 'red']['component_id'].unique()
        
        if len(red_components) > 0:
            test_component = red_components[0]
            
            # Set fire time as end of our data period + some buffer
            last_ts = pd.to_datetime(scored['timestamp']).max()
            fire_time = (last_ts + timedelta(hours=24)).isoformat()
            
            print(f"Testing component: {test_component}")
            print(f"Simulated fire time: {fire_time}")
            
            lead_time = backtest_warning_lead_time(pipe, scored, fire_time, test_component)
            
            print(f"✓ Camp Fire simulation results:")
            print(f"  - Lead time: {lead_time['lead_time_hours']:.1f} hours")
            print(f"  - First red alert: {lead_time['first_red_ts']}")
            
            if lead_time['lead_time_hours'] > 0:
                days = lead_time['lead_time_hours'] / 24
                print(f"  🎯 SUCCESS: Model would have warned {lead_time['lead_time_hours']:.1f} hours ({days:.1f} days) before the fire!")
            else:
                print("  ⚠️  No early warning detected for this component")
                
        else:
            print("  ℹ️  No components in red zone found in test sample")
            print(f"  Available components: {scored['component_id'].unique()[:10]}...")
            
    except Exception as e:
        print(f"✗ Error in Camp Fire test: {e}")
        import traceback
        traceback.print_exc()
    
    # Step 6: Summary
    print("\n=== Pipeline Complete ===")
    print("Key Results:")
    print(f"- Processed {len(calib_df):,} calibration samples")
    print(f"- Made predictions on {len(scored):,} test samples")
    print(f"- Found {len(scored[scored['zone']=='red']):,} red alerts")
    print(f"- Found {len(scored[scored['zone']=='yellow']):,} yellow warnings")
    
    print("\nFiles created:")
    print("- ./data/processed/scored_2018.csv - Model predictions with cable_state")
    print("- ./artifacts/ - Trained CCI model")
    
    print("\nReal Cable State Distribution:")
    if 'original_cable_state' in scored.columns:
        print(scored['original_cable_state'].value_counts())


if __name__ == "__main__":
    run_complete_pipeline()