"""
Test Advanced Hybrid Cascade Model
==================================

Test the hybrid model that combines:
- Deep Neural Networks with attention
- Grid Risk Model features
- Advanced ensemble methods
- Enhanced feature engineering

Target: >75% accuracy on cascade failure prediction
"""

import pandas as pd
import numpy as np
from datetime import datetime
import warnings
import sys
import os
import ast

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

warnings.filterwarnings('ignore')

from models.hybrid_cascade_model import HybridCascadeModel, create_advanced_hybrid_model
from scripts.test_enhanced_neural_network_cascade_models import load_and_analyze_cascade_data, engineer_advanced_cascade_features

from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder
import networkx as nx


def prepare_hybrid_data():
    """Prepare data for hybrid model testing"""
    print("🔧 Preparing data for hybrid model...")
    
    # Load and engineer features
    df = load_and_analyze_cascade_data()
    df = engineer_advanced_cascade_features(df)
    
    # Encode labels
    le = LabelEncoder()
    y = le.fit_transform(df['status'])  # 0=active, 1=damaged
    
    print(f"✓ Prepared {len(df)} samples")
    print(f"✓ Label distribution: {dict(zip(le.classes_, np.bincount(y)))}")
    
    return df, y, le


def test_hybrid_vs_baselines(df, y):
    """Test hybrid model against baseline approaches"""
    print("\n🔥 === HYBRID MODEL VS BASELINES ===")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        df, y, test_size=0.3, random_state=42, stratify=y
    )
    
    print(f"Train: {len(X_train)} samples, Test: {len(X_test)} samples")
    
    models_to_test = {}
    
    # 1. Previous best single model (Enhanced Neural Network equivalent)
    from sklearn.neural_network import MLPClassifier
    from scripts.test_enhanced_neural_network_cascade_models import select_cascade_features
    
    feature_cols = select_cascade_features(df)
    X_train_features = X_train[feature_cols].fillna(0)
    X_test_features = X_test[feature_cols].fillna(0)
    
    print("\n🔧 Testing Enhanced Neural Network (baseline)...")
    baseline_nn = MLPClassifier(
        hidden_layer_sizes=(64, 32, 16),
        activation='relu',
        solver='adam',
        alpha=0.001,
        learning_rate='adaptive',
        max_iter=500,
        random_state=42
    )
    
    from sklearn.preprocessing import StandardScaler
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train_features)
    X_test_scaled = scaler.transform(X_test_features)
    
    start_time = datetime.now()
    baseline_nn.fit(X_train_scaled, y_train)
    baseline_train_time = (datetime.now() - start_time).total_seconds()
    
    start_time = datetime.now()
    baseline_pred = baseline_nn.predict(X_test_scaled)
    baseline_pred_time = (datetime.now() - start_time).total_seconds()
    
    baseline_accuracy = accuracy_score(y_test, baseline_pred)
    baseline_report = classification_report(y_test, baseline_pred, output_dict=True, zero_division=0)
    
    models_to_test['Enhanced Neural Network (Baseline)'] = {
        'accuracy': baseline_accuracy,
        'train_time': baseline_train_time,
        'pred_time': baseline_pred_time,
        'report': baseline_report,
        'predictions': baseline_pred
    }
    
    print(f"   ✅ Baseline NN Accuracy: {baseline_accuracy:.3f} ({baseline_accuracy*100:.1f}%)")
    
    # 2. Hybrid Model - Voting Ensemble
    print("\n🔧 Testing Hybrid Model (Voting Ensemble)...")
    
    hybrid_voting = HybridCascadeModel(ensemble_method='voting')
    
    start_time = datetime.now()
    hybrid_voting.fit(X_train, y_train)
    voting_train_time = (datetime.now() - start_time).total_seconds()
    
    start_time = datetime.now()
    voting_pred = hybrid_voting.predict(X_test)
    voting_pred_time = (datetime.now() - start_time).total_seconds()
    
    voting_accuracy = accuracy_score(y_test, voting_pred)
    voting_report = classification_report(y_test, voting_pred, output_dict=True, zero_division=0)
    
    models_to_test['Hybrid Model (Voting)'] = {
        'accuracy': voting_accuracy,
        'train_time': voting_train_time,
        'pred_time': voting_pred_time,
        'report': voting_report,
        'predictions': voting_pred,
        'model': hybrid_voting
    }
    
    print(f"   ✅ Hybrid Voting Accuracy: {voting_accuracy:.3f} ({voting_accuracy*100:.1f}%)")
    
    # 3. Hybrid Model - Weighted Ensemble
    print("\n🔧 Testing Hybrid Model (Weighted Ensemble)...")
    
    hybrid_weighted = HybridCascadeModel(ensemble_method='weighted')
    
    start_time = datetime.now()
    hybrid_weighted.fit(X_train, y_train)
    weighted_train_time = (datetime.now() - start_time).total_seconds()
    
    start_time = datetime.now()
    weighted_pred = hybrid_weighted.predict(X_test)
    weighted_pred_time = (datetime.now() - start_time).total_seconds()
    
    weighted_accuracy = accuracy_score(y_test, weighted_pred)
    weighted_report = classification_report(y_test, weighted_pred, output_dict=True, zero_division=0)
    
    models_to_test['Hybrid Model (Weighted)'] = {
        'accuracy': weighted_accuracy,
        'train_time': weighted_train_time,
        'pred_time': weighted_pred_time,
        'report': weighted_report,
        'predictions': weighted_pred,
        'model': hybrid_weighted
    }
    
    print(f"   ✅ Hybrid Weighted Accuracy: {weighted_accuracy:.3f} ({weighted_accuracy*100:.1f}%)")
    
    # 4. Advanced Hybrid Model
    print("\n🔧 Testing Advanced Hybrid Model...")
    
    advanced_hybrid = create_advanced_hybrid_model()
    
    start_time = datetime.now()
    advanced_hybrid.fit(X_train, y_train)
    advanced_train_time = (datetime.now() - start_time).total_seconds()
    
    start_time = datetime.now()
    advanced_pred = advanced_hybrid.predict(X_test)
    advanced_pred_time = (datetime.now() - start_time).total_seconds()
    
    advanced_accuracy = accuracy_score(y_test, advanced_pred)
    advanced_report = classification_report(y_test, advanced_pred, output_dict=True, zero_division=0)
    
    models_to_test['Advanced Hybrid Model'] = {
        'accuracy': advanced_accuracy,
        'train_time': advanced_train_time,
        'pred_time': advanced_pred_time,
        'report': advanced_report,
        'predictions': advanced_pred,
        'model': advanced_hybrid
    }
    
    print(f"   ✅ Advanced Hybrid Accuracy: {advanced_accuracy:.3f} ({advanced_accuracy*100:.1f}%)")
    
    return models_to_test, X_test, y_test


def analyze_hybrid_results(results, X_test, y_test):
    """Analyze and compare hybrid model results"""
    print("\n📊 === HYBRID MODEL ANALYSIS ===")
    
    # Find best model
    best_model_name = max(results.keys(), key=lambda k: results[k]['accuracy'])
    best_accuracy = results[best_model_name]['accuracy']
    
    print(f"\n🏆 BEST MODEL: {best_model_name}")
    print(f"🎯 Best Accuracy: {best_accuracy:.3f} ({best_accuracy*100:.1f}%)")
    
    # Compare all models
    print(f"\n📈 MODEL COMPARISON:")
    print("=" * 80)
    print(f"{'Model':<35} {'Accuracy':<10} {'F1-Score':<10} {'Train Time':<12}")
    print("=" * 80)
    
    for name, result in results.items():
        f1_score = result['report']['weighted avg']['f1-score']
        print(f"{name:<35} {result['accuracy']:<10.3f} {f1_score:<10.3f} {result['train_time']:<12.1f}s")
    
    # Improvement analysis
    baseline_accuracy = results['Enhanced Neural Network (Baseline)']['accuracy']
    
    print(f"\n📈 IMPROVEMENT ANALYSIS:")
    for name, result in results.items():
        if 'Hybrid' in name:
            improvement = (result['accuracy'] - baseline_accuracy) * 100
            if improvement > 0:
                print(f"   {name}: +{improvement:.1f}% improvement over baseline")
            else:
                print(f"   {name}: {improvement:.1f}% vs baseline")
    
    # Detailed analysis of best model
    if 'model' in results[best_model_name]:
        best_model = results[best_model_name]['model']
        
        if hasattr(best_model, 'get_feature_importance'):
            print(f"\n🔍 FEATURE IMPORTANCE (Best Model):")
            importance_df = best_model.get_feature_importance()
            if importance_df is not None:
                for i, row in importance_df.head(10).iterrows():
                    print(f"   {i+1:2d}. {row['feature']:<30} {row['importance']:.4f}")
        
        if hasattr(best_model, 'model_weights_'):
            print(f"\n⚖️  MODEL WEIGHTS (Ensemble):")
            for model_name, weight in best_model.model_weights_.items():
                print(f"   {model_name:<20} {weight:.3f}")
    
    # Performance ratings
    def get_rating(accuracy):
        if accuracy > 0.80:
            return "🟢 EXCELLENT"
        elif accuracy > 0.75:
            return "🟡 VERY GOOD"
        elif accuracy > 0.70:
            return "🟠 GOOD"
        elif accuracy > 0.60:
            return "🔴 MODERATE"
        else:
            return "🔴 POOR"
    
    print(f"\n🏅 PERFORMANCE RATINGS:")
    for name, result in results.items():
        rating = get_rating(result['accuracy'])
        print(f"   {name:<35} {rating}")
    
    return best_model_name, best_accuracy


def save_hybrid_results(results):
    """Save hybrid model results"""
    
    results_data = []
    for name, result in results.items():
        results_data.append({
            'model': name,
            'dataset': 'cascade_failures_hybrid',
            'accuracy': result['accuracy'],
            'f1_score': result['report']['weighted avg']['f1-score'],
            'damage_precision': result['report'].get('1', {}).get('precision', 0),
            'damage_recall': result['report'].get('1', {}).get('recall', 0),
            'damage_f1': result['report'].get('1', {}).get('f1-score', 0),
            'training_time': result['train_time'],
            'prediction_time': result['pred_time']
        })
    
    results_df = pd.DataFrame(results_data)
    results_df.to_csv("data/processed/hybrid_cascade_results.csv", index=False)
    print(f"\n✅ Hybrid results saved to: data/processed/hybrid_cascade_results.csv")
    
    return results_df


def main():
    """Main function for hybrid model testing"""
    print("🔥 === ADVANCED HYBRID CASCADE MODEL TESTING ===\n")
    
    # Prepare data
    df, y, le = prepare_hybrid_data()
    
    # Test hybrid models vs baselines
    results, X_test, y_test = test_hybrid_vs_baselines(df, y)
    
    # Analyze results
    best_model_name, best_accuracy = analyze_hybrid_results(results, X_test, y_test)
    
    # Save results
    results_df = save_hybrid_results(results)
    
    # Final summary
    print("\n" + "="*80)
    print("🔥 HYBRID CASCADE MODEL FINAL RESULTS")
    print("="*80)
    
    baseline_acc = results['Enhanced Neural Network (Baseline)']['accuracy']
    best_acc = best_accuracy
    improvement = (best_acc - baseline_acc) * 100
    
    print(f"\n🎯 PERFORMANCE SUMMARY:")
    print(f"   Baseline (Enhanced NN): {baseline_acc*100:.1f}%")
    print(f"   Best Hybrid Model: {best_acc*100:.1f}%")
    print(f"   Improvement: +{improvement:.1f}% points")
    
    # Achievement levels
    if best_acc > 0.80:
        print(f"\n🎉 OUTSTANDING: {best_acc*100:.1f}% - Excellent cascade prediction!")
        print("   Ready for production deployment!")
    elif best_acc > 0.75:
        print(f"\n🚀 EXCELLENT: {best_acc*100:.1f}% - Very strong performance!")
        print("   Significant improvement achieved!")
    elif best_acc > 0.70:
        print(f"\n✅ GOOD: {best_acc*100:.1f}% - Meaningful improvement!")
        print("   Hybrid approach shows promise!")
    else:
        print(f"\n⚠️  MODERATE: {best_acc*100:.1f}% - Some improvement shown")
        print("   Further tuning may be needed")
    
    # Historical comparison
    print(f"\n📈 HISTORICAL COMPARISON:")
    print(f"   Advanced Hybrid: {best_acc*100:.1f}%")
    print(f"   Enhanced Neural Network: 70.0%")
    print(f"   Basic Cascade Models: 56.7%")
    print(f"   Power Grid Models: 51.7%")
    
    total_improvement = (best_acc - 0.517) * 100
    print(f"   Total improvement from start: +{total_improvement:.1f}% points")


if __name__ == "__main__":
    main()