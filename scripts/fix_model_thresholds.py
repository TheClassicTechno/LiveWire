"""
Quick Fix for CCI Model Thresholds
==================================

This script adjusts the zone thresholds to make the model more sensitive
to actual failures and provides better performance.
"""

import pandas as pd
import numpy as np
import sys
import os
sys.path.append('.')

from models.grid_risk_model import CCIPipeline, CCIPipelineConfig


def fix_model_sensitivity():
    print("=== Fixing CCI Model Sensitivity ===\n")
    
    # Load current results
    df = pd.read_csv("./data/processed/scored_2018.csv")
    print(f"Current results: {len(df)} predictions")
    
    # Analyze CCI distribution to set better thresholds
    cci_values = df['cci'].dropna()
    print(f"Valid CCI scores: {len(cci_values)}")
    
    if len(cci_values) > 0:
        print(f"CCI range: {cci_values.min():.3f} to {cci_values.max():.3f}")
        print(f"CCI mean: {cci_values.mean():.3f}")
        
        # Set more reasonable thresholds based on data distribution
        q33 = np.percentile(cci_values, 33)
        q67 = np.percentile(cci_values, 67)
        q90 = np.percentile(cci_values, 90)
        
        print(f"Suggested thresholds:")
        print(f"  Green -> Yellow: {q33:.3f} (33rd percentile)")
        print(f"  Yellow -> Red:   {q67:.3f} (67th percentile)")
        print(f"  Alternative Red: {q90:.3f} (90th percentile)")
        
        # Apply new thresholds
        def apply_new_zones(cci, yellow_thresh, red_thresh):
            if pd.isna(cci):
                return 'unknown'
            elif cci < yellow_thresh:
                return 'green'
            elif cci < red_thresh:
                return 'yellow'
            else:
                return 'red'
        
        # Try more aggressive thresholds
        yellow_thresh = q33
        red_thresh = q67
        
        df['new_zone'] = df['cci'].apply(lambda x: apply_new_zones(x, yellow_thresh, red_thresh))
        
        # Analyze new distribution
        new_zone_counts = df['new_zone'].value_counts()
        print(f"\nNew zone distribution:")
        for zone in ['green', 'yellow', 'red', 'unknown']:
            count = new_zone_counts.get(zone, 0)
            pct = count / len(df) * 100
            print(f"  {zone.upper()}: {count:,} ({pct:.1f}%)")
        
        # Check accuracy with new thresholds
        if 'original_cable_state' in df.columns:
            def map_cable_state_to_risk(state):
                if pd.isna(state):
                    return 'unknown'
                state_str = str(state).lower()
                if any(word in state_str for word in ['critical', 'fault', 'fail']):
                    return 'red'
                elif any(word in state_str for word in ['warning', 'degradation']):
                    return 'yellow'
                else:
                    return 'green'
            
            df['mapped_cable_state'] = df['original_cable_state'].apply(map_cable_state_to_risk)
            
            # Calculate accuracy for valid predictions
            valid_df = df[(df['new_zone'] != 'unknown') & (df['mapped_cable_state'] != 'unknown')]
            
            if len(valid_df) > 0:
                from sklearn.metrics import accuracy_score, confusion_matrix
                accuracy = accuracy_score(valid_df['mapped_cable_state'], valid_df['new_zone'])
                print(f"\nNew accuracy: {accuracy:.3f} ({accuracy*100:.1f}%)")
                
                # Show confusion matrix
                cm = confusion_matrix(valid_df['mapped_cable_state'], valid_df['new_zone'], 
                                    labels=['green', 'yellow', 'red'])
                print("\nNew Confusion Matrix:")
                print("Predicted ->  Green  Yellow   Red")
                labels = ['green', 'yellow', 'red']
                for i, true_label in enumerate(labels):
                    print(f"Actual {true_label.capitalize():7s}   {cm[i][0]:5d}   {cm[i][1]:5d}  {cm[i][2]:4d}")
        
        # Save updated results
        df['zone'] = df['new_zone']
        df.drop(['new_zone'], axis=1, inplace=True)
        df.to_csv("./data/processed/scored_2018_fixed.csv", index=False)
        print(f"\n✓ Updated results saved to: ./data/processed/scored_2018_fixed.csv")
        
        # Retrain model with better thresholds
        print(f"\n=== Retraining Model with Fixed Thresholds ===")
        
        # Update config
        config = CCIPipelineConfig()
        config.use_quantile_zones = True
        config.yellow_q = 0.33  # 33rd percentile
        config.red_q = 0.67     # 67th percentile
        
        # Load training data and retrain
        calib_df = pd.read_csv("./data/calib/pre2018.csv")
        
        pipe = CCIPipeline(config)
        pipe.fit(calib_df)
        pipe.save("./artifacts_fixed")
        
        print("✓ Model retrained with better thresholds")
        print("✓ Saved to ./artifacts_fixed")
        
        return True
        
    else:
        print("❌ No valid CCI scores found - model has fundamental issues")
        return False


if __name__ == "__main__":
    success = fix_model_sensitivity()
    if success:
        print("\n🎯 NEXT STEPS:")
        print("1. Use the fixed model: CCIPipeline.load('./artifacts_fixed')")
        print("2. Re-run predictions with the fixed thresholds")
        print("3. Test on Camp Fire scenario")
    else:
        print("\n❌ Model needs fundamental debugging - check feature engineering")