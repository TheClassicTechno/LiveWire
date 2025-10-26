"""
Test the Fixed Model on Camp Fire Scenario
"""

import sys
import os
sys.path.append('.')

from models.grid_risk_model import CCIPipeline, backtest_warning_lead_time
import pandas as pd


def test_camp_fire_prediction():
    print("=== Testing Fixed Model on Camp Fire Scenario ===\n")
    
    # Load the fixed model
    try:
        pipe = CCIPipeline.load("./artifacts_fixed")
        print("✓ Loaded fixed model")
    except Exception as e:
        print(f"✗ Error loading fixed model: {e}")
        return
    
    # Load test data
    try:
        df = pd.read_csv("./data/processed/scored_2018_fixed.csv")
        print(f"✓ Loaded fixed predictions: {len(df)} rows")
    except Exception as e:
        print(f"✗ Error loading fixed data: {e}")
        return
    
    # Find components that went red
    red_components = df[df['zone'] == 'red']['component_id'].unique()
    print(f"✓ Found {len(red_components)} components with red alerts")
    
    if len(red_components) > 0:
        # Test backtest on first red component
        test_component = red_components[0]
        
        # Use a realistic Camp Fire timestamp
        fire_time = "2018-11-08T06:33:00"
        
        try:
            lead_time = backtest_warning_lead_time(pipe, df, fire_time, test_component)
            
            print(f"\n🔥 CAMP FIRE SIMULATION RESULTS:")
            print(f"  Component tested: {test_component}")
            print(f"  Fire start time: {fire_time}")
            print(f"  Lead time: {lead_time['lead_time_hours']:.1f} hours")
            print(f"  First red alert: {lead_time['first_red_ts']}")
            
            if lead_time['lead_time_hours'] > 0:
                days = lead_time['lead_time_hours'] / 24
                print(f"  🎯 SUCCESS: Model would have warned {lead_time['lead_time_hours']:.1f} hours ({days:.1f} days) before the Camp Fire!")
                
                if lead_time['lead_time_hours'] > 24:
                    print(f"  ⭐ EXCELLENT: More than 1 day advance warning!")
                elif lead_time['lead_time_hours'] > 6:
                    print(f"  ✅ GOOD: Sufficient time for emergency response")
                else:
                    print(f"  ⚠️ MARGINAL: Short warning time")
            else:
                print(f"  ❌ FAILED: No advance warning provided")
                
        except Exception as e:
            print(f"✗ Error in backtest: {e}")
    
    # Show sample high-risk predictions
    print(f"\n📊 SAMPLE HIGH-RISK PREDICTIONS:")
    high_risk = df[df['zone'].isin(['yellow', 'red'])].head(10)
    
    for _, row in high_risk.iterrows():
        timestamp = row['timestamp']
        component = row['component_id']
        zone = row['zone']
        cci = row['cci']
        cable_state = row.get('original_cable_state', 'Unknown')
        
        print(f"  {timestamp}: {component} -> {zone.upper()} (CCI: {cci:.3f}, Actual: {cable_state})")


if __name__ == "__main__":
    test_camp_fire_prediction()