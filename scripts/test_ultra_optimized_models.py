"""
Ultra-Optimized Cascade Failure Model
=====================================

Final ultra-optimized approach using the absolute best techniques discovered:
- Best performing configurations from all previous tests
- Advanced preprocessing and feature engineering  
- Hyperparameter optimization
- Ensemble of top-performing models
- Data augmentation for small dataset
- Robust evaluation methodology

Target: Achieve the highest possible accuracy on cascade failure prediction.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import warnings
import sys
import os
import ast
from itertools import combinations

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

warnings.filterwarnings('ignore')

from scripts.test_enhanced_neural_network_cascade_models import load_and_analyze_cascade_data, engineer_advanced_cascade_features

from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler, LabelEncoder, PolynomialFeatures
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier, ExtraTreesClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression
from sklearn.feature_selection import SelectKBest, f_classif, RFE
from sklearn.decomposition import PCA
import networkx as nx


def advanced_feature_engineering(df):
    """Ultra-advanced feature engineering"""
    print("🔧 Ultra-advanced feature engineering...")
    
    # Start with base features
    base_features = [
        'demand_capacity_ratio', 'capacity_utilization', 'load_stress',
        'overload_risk', 'capacity_margin', 'degree_centrality', 
        'betweenness_centrality', 'closeness_centrality', 'eigenvector_centrality',
        'pagerank', 'clustering_coefficient', 'distance_from_center',
        'grid_edge_distance', 'neighbor_damage_ratio', 'neighbor_avg_load',
        'neighbor_max_load', 'cascade_exposure', 'network_isolation',
        'structural_vulnerability', 'load_vulnerability', 'cascade_vulnerability',
        'overall_vulnerability', 'cascade_risk_spread'
    ]
    
    X_base = df[base_features].fillna(0)
    
    # Advanced interaction features
    interactions = pd.DataFrame(index=df.index)
    
    # Top feature interactions (based on previous importance analysis)
    key_features = ['demand_capacity_ratio', 'overall_vulnerability', 'cascade_risk_spread', 
                   'betweenness_centrality', 'neighbor_damage_ratio']
    
    for i, feat1 in enumerate(key_features):
        for feat2 in key_features[i+1:]:
            interactions[f'{feat1}_x_{feat2}'] = df[feat1] * df[feat2]
            interactions[f'{feat1}_div_{feat2}'] = df[feat1] / (df[feat2] + 1e-6)
    
    # Non-linear transformations
    nonlinear = pd.DataFrame(index=df.index)
    for feat in key_features:
        nonlinear[f'{feat}_squared'] = df[feat] ** 2
        nonlinear[f'{feat}_log'] = np.log1p(df[feat])
        nonlinear[f'{feat}_sqrt'] = np.sqrt(np.abs(df[feat]))
    
    # Statistical aggregations
    stats = pd.DataFrame(index=df.index)
    feature_groups = {
        'centrality': ['degree_centrality', 'betweenness_centrality', 'closeness_centrality', 'eigenvector_centrality'],
        'vulnerability': ['structural_vulnerability', 'load_vulnerability', 'cascade_vulnerability'],
        'load': ['demand_capacity_ratio', 'capacity_utilization', 'load_stress'],
        'spatial': ['distance_from_center', 'grid_edge_distance']
    }
    
    for group_name, group_features in feature_groups.items():
        group_data = df[group_features]
        stats[f'{group_name}_mean'] = group_data.mean(axis=1)
        stats[f'{group_name}_std'] = group_data.std(axis=1)
        stats[f'{group_name}_max'] = group_data.max(axis=1)
        stats[f'{group_name}_min'] = group_data.min(axis=1)
    
    # Combine all features
    X_ultra = pd.concat([X_base, interactions, nonlinear, stats], axis=1)
    X_ultra = X_ultra.fillna(0)
    
    print(f"✓ Created {X_ultra.shape[1]} ultra-advanced features")
    
    return X_ultra


def data_augmentation(X, y, augment_factor=0.5):
    """Simple data augmentation for small dataset"""
    print(f"🔄 Data augmentation (factor: {augment_factor})...")
    
    # Add noise to minority class (damaged nodes)
    damaged_mask = y == 1
    X_damaged = X[damaged_mask]
    y_damaged = y[damaged_mask]
    
    n_augment = int(len(X_damaged) * augment_factor)
    
    if n_augment > 0:
        # Add small amount of noise
        noise = np.random.normal(0, 0.05, (n_augment, X.shape[1]))
        X_augmented = X_damaged.iloc[:n_augment].values + noise
        y_augmented = np.ones(n_augment)
        
        # Combine with original data
        X_combined = np.vstack([X.values, X_augmented])
        y_combined = np.hstack([y, y_augmented])
        
        print(f"✓ Augmented {n_augment} samples for minority class")
        
        return pd.DataFrame(X_combined, columns=X.columns), y_combined
    
    return X, y


def create_ultra_optimized_models():
    """Create ultra-optimized model ensemble"""
    
    # Model 1: Best Neural Network
    ultra_nn = MLPClassifier(
        hidden_layer_sizes=(256, 128, 64, 32, 16),
        activation='relu',
        solver='adam',
        alpha=0.001,
        learning_rate='adaptive',
        learning_rate_init=0.0005,
        max_iter=2000,
        early_stopping=True,
        validation_fraction=0.2,
        n_iter_no_change=50,
        random_state=42
    )
    
    # Model 2: Extra Trees (often performs better than Random Forest)
    ultra_et = ExtraTreesClassifier(
        n_estimators=300,
        max_depth=20,
        min_samples_split=2,
        min_samples_leaf=1,
        max_features='sqrt',
        class_weight='balanced',
        random_state=42
    )
    
    # Model 3: Optimized Gradient Boosting
    ultra_gb = GradientBoostingClassifier(
        n_estimators=200,
        learning_rate=0.05,
        max_depth=10,
        min_samples_split=3,
        min_samples_leaf=2,
        subsample=0.8,
        max_features='sqrt',
        random_state=42
    )
    
    # Model 4: SVM with RBF kernel
    ultra_svm = SVC(
        kernel='rbf',
        C=10,
        gamma='scale',
        class_weight='balanced',
        probability=True,
        random_state=42
    )
    
    # Model 5: Logistic Regression with regularization
    ultra_lr = LogisticRegression(
        C=1.0,
        penalty='l2',
        class_weight='balanced',
        max_iter=1000,
        random_state=42
    )
    
    return {
        'Ultra Neural Network': ultra_nn,
        'Ultra Extra Trees': ultra_et,
        'Ultra Gradient Boosting': ultra_gb,
        'Ultra SVM': ultra_svm,
        'Ultra Logistic Regression': ultra_lr
    }


def hyperparameter_optimization(X, y):
    """Perform hyperparameter optimization for best model"""
    print("\n🎯 === HYPERPARAMETER OPTIMIZATION ===")
    
    # Optimize Neural Network (most promising)
    nn_param_grid = {
        'hidden_layer_sizes': [(128, 64, 32), (256, 128, 64), (128, 64, 32, 16)],
        'alpha': [0.0001, 0.001, 0.01],
        'learning_rate_init': [0.0005, 0.001, 0.005]
    }
    
    nn_base = MLPClassifier(
        activation='relu',
        solver='adam',
        learning_rate='adaptive',
        max_iter=1000,
        early_stopping=True,
        random_state=42
    )
    
    print("🔧 Optimizing Neural Network...")
    nn_grid = GridSearchCV(
        nn_base, nn_param_grid, cv=3, scoring='accuracy', n_jobs=-1
    )
    nn_grid.fit(X, y)
    
    print(f"   Best NN params: {nn_grid.best_params_}")
    print(f"   Best NN CV score: {nn_grid.best_score_:.3f}")
    
    # Optimize Extra Trees
    et_param_grid = {
        'n_estimators': [200, 300, 500],
        'max_depth': [15, 20, 25],
        'min_samples_split': [2, 3, 5]
    }
    
    et_base = ExtraTreesClassifier(
        max_features='sqrt',
        class_weight='balanced',
        random_state=42
    )
    
    print("🔧 Optimizing Extra Trees...")
    et_grid = GridSearchCV(
        et_base, et_param_grid, cv=3, scoring='accuracy', n_jobs=-1
    )
    et_grid.fit(X, y)
    
    print(f"   Best ET params: {et_grid.best_params_}")
    print(f"   Best ET CV score: {et_grid.best_score_:.3f}")
    
    return nn_grid.best_estimator_, et_grid.best_estimator_


def ultra_ensemble_training(X, y):
    """Train ultra-optimized ensemble"""
    print("\n🚀 === ULTRA ENSEMBLE TRAINING ===")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Get optimized models
    best_nn, best_et = hyperparameter_optimization(X_train_scaled, y_train)
    
    # Additional optimized models
    ultra_gb = GradientBoostingClassifier(
        n_estimators=200, learning_rate=0.05, max_depth=10,
        min_samples_split=3, random_state=42
    )
    
    # Create ensemble
    ensemble_models = [
        ('best_nn', best_nn),
        ('best_et', best_et),
        ('ultra_gb', ultra_gb)
    ]
    
    # Voting ensemble
    voting_ensemble = VotingClassifier(ensemble_models, voting='soft')
    
    # Train ensemble
    start_time = datetime.now()
    voting_ensemble.fit(X_train_scaled, y_train)
    train_time = (datetime.now() - start_time).total_seconds()
    
    # Predictions
    start_time = datetime.now()
    y_pred = voting_ensemble.predict(X_test_scaled)
    y_proba = voting_ensemble.predict_proba(X_test_scaled)
    pred_time = (datetime.now() - start_time).total_seconds()
    
    # Evaluation
    accuracy = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
    
    print(f"🎯 Ultra Ensemble Performance:")
    print(f"   Accuracy: {accuracy:.3f} ({accuracy*100:.1f}%)")
    print(f"   F1-Score: {report['weighted avg']['f1-score']:.3f}")
    print(f"   Training time: {train_time:.1f}s")
    
    # Individual model performance
    print(f"\n📊 Individual Model Performance:")
    for name, model in ensemble_models:
        model.fit(X_train_scaled, y_train)
        model_pred = model.predict(X_test_scaled)
        model_acc = accuracy_score(y_test, model_pred)
        print(f"   {name}: {model_acc:.3f} ({model_acc*100:.1f}%)")
    
    return {
        'ensemble': voting_ensemble,
        'scaler': scaler,
        'accuracy': accuracy,
        'report': report,
        'train_time': train_time,
        'pred_time': pred_time,
        'y_test': y_test,
        'y_pred': y_pred,
        'y_proba': y_proba
    }


def main():
    """Main function for ultra-optimized testing"""
    print("🔥 === ULTRA-OPTIMIZED CASCADE FAILURE PREDICTION ===\n")
    
    # Load and prepare data
    df = load_and_analyze_cascade_data()
    df = engineer_advanced_cascade_features(df)
    
    # Encode labels
    le = LabelEncoder()
    y = le.fit_transform(df['status'])
    
    print(f"✓ Data prepared: {len(df)} samples")
    
    # Ultra-advanced feature engineering
    X_ultra = advanced_feature_engineering(df)
    
    # Data augmentation
    X_augmented, y_augmented = data_augmentation(X_ultra, y)
    
    print(f"✓ Final dataset: {len(X_augmented)} samples, {X_augmented.shape[1]} features")
    
    # Ultra ensemble training
    results = ultra_ensemble_training(X_augmented, y_augmented)
    
    # Save results
    ultra_results = pd.DataFrame([{
        'model': 'Ultra-Optimized Ensemble',
        'dataset': 'cascade_failures_ultra',
        'accuracy': results['accuracy'],
        'f1_score': results['report']['weighted avg']['f1-score'],
        'damage_precision': results['report'].get('1', {}).get('precision', 0),
        'damage_recall': results['report'].get('1', {}).get('recall', 0),
        'damage_f1': results['report'].get('1', {}).get('f1-score', 0),
        'training_time': results['train_time'],
        'prediction_time': results['pred_time'],
        'num_features': X_augmented.shape[1]
    }])
    ultra_results.to_csv("data/processed/ultra_optimized_results.csv", index=False)
    
    # Final summary
    print("\n" + "="*80)
    print("🔥 ULTRA-OPTIMIZED CASCADE MODEL FINAL RESULTS")
    print("="*80)
    
    final_acc = results['accuracy']
    
    print(f"\n🎯 ULTIMATE PERFORMANCE:")
    print(f"   Ultra-Optimized Ensemble: {final_acc:.3f} ({final_acc*100:.1f}%)")
    print(f"   Features used: {X_augmented.shape[1]}")
    print(f"   Training samples: {len(X_augmented)}")
    
    # Achievement level
    if final_acc > 0.80:
        print(f"\n🏆 OUTSTANDING: {final_acc*100:.1f}% - World-class performance!")
        print("   🚀 Ready for immediate production deployment!")
    elif final_acc > 0.75:
        print(f"\n🎉 EXCELLENT: {final_acc*100:.1f}% - Superior predictive capability!")
        print("   ✅ Highly suitable for operational use!")
    elif final_acc > 0.70:
        print(f"\n🚀 VERY GOOD: {final_acc*100:.1f}% - Strong performance!")
        print("   ✅ Suitable for most practical applications!")
    elif final_acc > 0.65:
        print(f"\n✅ GOOD: {final_acc*100:.1f}% - Solid predictive power!")
        print("   ⚠️  Good for non-critical applications!")
    else:
        print(f"\n⚠️  MODERATE: {final_acc*100:.1f}% - Baseline performance")
        print("   🔧 Consider domain-specific adaptations!")
    
    # Complete historical progression
    print(f"\n📈 COMPLETE PROGRESSION:")
    print(f"   🏆 Ultra-Optimized Ensemble: {final_acc*100:.1f}%")
    print(f"   🔧 Optimized Models: 68.0% (CV)")
    print(f"   🧠 Enhanced Neural Network: 70.0%")
    print(f"   🌊 Basic Cascade Models: 56.7%")
    print(f"   ⚡ Power Grid Models: 51.7%")
    print(f"   🔥 Camp Fire Prediction: ✅ 308 days warning (Grid Risk)")
    
    total_improvement = (final_acc - 0.517) * 100
    print(f"\n🚀 TOTAL IMPROVEMENT: +{total_improvement:.1f}% points from baseline")
    
    # Model recommendations
    print(f"\n🎯 FINAL RECOMMENDATIONS:")
    print(f"   🔥 Critical Infrastructure: Grid Risk Model (proven with Camp Fire)")
    print(f"   🌐 Network Cascade Failures: Ultra-Optimized Ensemble ({final_acc*100:.1f}%)")
    print(f"   ⚡ General Applications: Enhanced Neural Network (70%)")
    
    print(f"\n✅ Ultra-optimized results saved to: data/processed/ultra_optimized_results.csv")


if __name__ == "__main__":
    main()