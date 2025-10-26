"""
Model Performance Analysis for LiveWire CCI Model
=================================================

This script analyzes the performance of your CCI model by:
1. Checking prediction distribution
2. Validating against original cable states
3. Analyzing component-level patterns
4. Computing key metrics
5. Providing recommendations
"""

import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, classification_report
from collections import Counter


def analyze_model_performance():
    print("=== LiveWire CCI Model Performance Analysis ===\n")
    
    # Load results
    try:
        df = pd.read_csv("./data/processed/scored_2018.csv")
        print(f"✓ Loaded results: {len(df)} predictions")
        print(f"✓ Components analyzed: {df['component_id'].nunique()}")
        print(f"✓ Time range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    except Exception as e:
        print(f"✗ Error loading results: {e}")
        return
    
    # 1. PREDICTION DISTRIBUTION ANALYSIS
    print("\n1. PREDICTION DISTRIBUTION")
    print("=" * 40)
    
    zone_counts = df['zone'].value_counts()
    zone_pct = df['zone'].value_counts(normalize=True) * 100
    
    print("Zone Distribution:")
    for zone in ['green', 'yellow', 'red']:
        count = zone_counts.get(zone, 0)
        pct = zone_pct.get(zone, 0)
        print(f"  {zone.upper()}: {count:,} ({pct:.1f}%)")
    
    # CCI score distribution
    cci_stats = df['cci'].describe()
    print(f"\nCCI Score Statistics:")
    print(f"  Mean: {cci_stats['mean']:.3f}")
    print(f"  Std:  {cci_stats['std']:.3f}")
    print(f"  Min:  {cci_stats['min']:.3f}")
    print(f"  Max:  {cci_stats['max']:.3f}")
    
    # 2. VALIDATION AGAINST ORIGINAL CABLE STATES
    print("\n2. VALIDATION AGAINST ORIGINAL CABLE STATES")
    print("=" * 50)
    
    if 'original_cable_state' in df.columns and df['original_cable_state'].notna().any():
        # Map cable states to risk levels
        def map_cable_state_to_risk(state):
            if pd.isna(state):
                return 'unknown'
            state_str = str(state).lower()
            if any(word in state_str for word in ['critical', 'fault', 'fail', 'danger']):
                return 'red'
            elif any(word in state_str for word in ['warning', 'caution', 'alert', 'moderate', 'degradation']):
                return 'yellow'
            else:
                return 'green'
        
        df['mapped_cable_state'] = df['original_cable_state'].apply(map_cable_state_to_risk)
        
        # Remove unknown states for analysis
        valid_df = df[df['mapped_cable_state'] != 'unknown'].copy()
        
        if len(valid_df) > 0:
            accuracy = accuracy_score(valid_df['mapped_cable_state'], valid_df['zone'])
            
            print(f"Overall Accuracy: {accuracy:.3f} ({accuracy*100:.1f}%)")
            
            # Confusion matrix
            cm = confusion_matrix(valid_df['mapped_cable_state'], valid_df['zone'], 
                                labels=['green', 'yellow', 'red'])
            
            print("\nConfusion Matrix:")
            print("Predicted ->  Green  Yellow   Red")
            labels = ['green', 'yellow', 'red']
            for i, true_label in enumerate(labels):
                print(f"Actual {true_label.capitalize():7s}   {cm[i][0]:5d}   {cm[i][1]:5d}  {cm[i][2]:4d}")
            
            # Per-class metrics
            report = classification_report(valid_df['mapped_cable_state'], valid_df['zone'], 
                                         labels=['green', 'yellow', 'red'], output_dict=True)
            
            print(f"\nPer-class Performance:")
            for zone in ['green', 'yellow', 'red']:
                if zone in report:
                    precision = report[zone]['precision']
                    recall = report[zone]['recall']
                    f1 = report[zone]['f1-score']
                    print(f"  {zone.upper()}: Precision={precision:.3f}, Recall={recall:.3f}, F1={f1:.3f}")
        else:
            print("No valid cable state mappings found for validation")
    else:
        print("No original cable states available for validation")
    
    # 3. COMPONENT-LEVEL ANALYSIS
    print("\n3. COMPONENT-LEVEL ANALYSIS")
    print("=" * 35)
    
    component_stats = df.groupby('component_id').agg({
        'zone': lambda x: (x == 'red').sum(),
        'cci': ['mean', 'max', 'std']
    }).round(3)
    
    component_stats.columns = ['red_alerts', 'avg_cci', 'max_cci', 'cci_std']
    component_stats = component_stats.sort_values('red_alerts', ascending=False)
    
    print("Top 10 High-Risk Components:")
    print("Component    Red Alerts  Avg CCI  Max CCI  CCI Std")
    for comp, row in component_stats.head(10).iterrows():
        print(f"{comp:10s}   {row['red_alerts']:8.0f}  {row['avg_cci']:7.3f}  {row['max_cci']:7.3f}  {row['cci_std']:7.3f}")
    
    # 4. TIME-BASED PATTERNS
    print("\n4. TIME-BASED PATTERNS")
    print("=" * 25)
    
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['month'] = df['timestamp'].dt.month
    
    monthly_red = df[df['zone'] == 'red']['month'].value_counts().sort_index()
    monthly_total = df['month'].value_counts().sort_index()
    monthly_red_pct = (monthly_red / monthly_total * 100).fillna(0)
    
    print("Red Alerts by Month:")
    for month in range(1, 13):
        count = monthly_red.get(month, 0)
        pct = monthly_red_pct.get(month, 0)
        print(f"  Month {month:2d}: {count:4.0f} alerts ({pct:.1f}% of month)")
    
    # 5. LEAD TIME ANALYSIS
    print("\n5. LEAD TIME ANALYSIS")
    print("=" * 25)
    
    # Look at time_left_hours for red zone components
    red_components = df[df['zone'] == 'red']
    if len(red_components) > 0:
        finite_lead_times = red_components[red_components['time_left_hours'] != np.inf]['time_left_hours']
        
        if len(finite_lead_times) > 0:
            print(f"Components with finite lead times: {len(finite_lead_times)}")
            print(f"Average lead time: {finite_lead_times.mean():.1f} hours ({finite_lead_times.mean()/24:.1f} days)")
            print(f"Median lead time: {finite_lead_times.median():.1f} hours ({finite_lead_times.median()/24:.1f} days)")
            print(f"Min lead time: {finite_lead_times.min():.1f} hours")
            print(f"Max lead time: {finite_lead_times.max():.1f} hours")
        else:
            print("No finite lead times found (all components have infinite time left)")
    else:
        print("No red zone components found")
    
    # 6. PERFORMANCE ASSESSMENT
    print("\n6. OVERALL PERFORMANCE ASSESSMENT")
    print("=" * 40)
    
    # Calculate key indicators
    red_rate = (df['zone'] == 'red').mean() * 100
    cci_meaningful = (df['cci'] > 0.1).mean() * 100  # Non-trivial CCI scores
    high_risk_components = len(component_stats[component_stats['red_alerts'] > 0])
    
    print("Key Performance Indicators:")
    print(f"  Red alert rate: {red_rate:.1f}%")
    print(f"  Components with high CCI: {cci_meaningful:.1f}%")
    print(f"  High-risk components detected: {high_risk_components}")
    
    # Performance verdict
    print("\nPERFORMANCE VERDICT:")
    
    if 'original_cable_state' in df.columns and 'accuracy' in locals():
        if accuracy > 0.8:
            verdict = "🟢 EXCELLENT"
        elif accuracy > 0.6:
            verdict = "🟡 GOOD"
        elif accuracy > 0.4:
            verdict = "🟠 MODERATE"
        else:
            verdict = "🔴 NEEDS IMPROVEMENT"
        print(f"  Accuracy-based: {verdict} (Accuracy: {accuracy:.1f}%)")
    
    if red_rate > 0.1:
        risk_detection = "🟢 GOOD" if red_rate < 10 else "🟡 HIGH SENSITIVITY"
    else:
        risk_detection = "🔴 LOW SENSITIVITY"
    print(f"  Risk detection: {risk_detection} ({red_rate:.1f}% red alerts)")
    
    # 7. RECOMMENDATIONS
    print("\n7. RECOMMENDATIONS")
    print("=" * 20)
    
    recommendations = []
    
    if red_rate < 1:
        recommendations.append("• Model may be too conservative - consider lowering red threshold")
    elif red_rate > 15:
        recommendations.append("• Model may be too sensitive - consider raising red threshold")
    
    if 'accuracy' in locals() and accuracy < 0.5:
        recommendations.append("• Low accuracy suggests need for better feature engineering or more training data")
    
    if high_risk_components == 0:
        recommendations.append("• No high-risk components detected - verify model is learning meaningful patterns")
    
    recommendations.extend([
        "• Test on known failure cases to validate early warning capability",
        "• Monitor model performance over time with real operational data",
        "• Consider ensemble methods or deep learning for complex temporal patterns"
    ])
    
    for rec in recommendations:
        print(rec)
    
    print(f"\n=== Analysis Complete ===")
    return df


if __name__ == "__main__":
    results_df = analyze_model_performance()