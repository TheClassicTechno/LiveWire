"""
Optimized Cascade Failure Prediction Model
==========================================

Final optimized approach combining the best techniques:
- Cross-validation for robust evaluation
- Best hyperparameters from previous testing
- Advanced feature selection
- Proper ensemble methods
- Multiple random seeds for stability
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

from scripts.test_enhanced_neural_network_cascade_models import load_and_analyze_cascade_data, engineer_advanced_cascade_features, select_cascade_features

from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.feature_selection import SelectKBest, f_classif
import networkx as nx


def create_optimized_models():
    """Create optimized models based on previous best results"""
    
    # Best Neural Network from previous testing
    best_nn = MLPClassifier(
        hidden_layer_sizes=(128, 64, 32, 16),  # Slightly deeper
        activation='relu',
        solver='adam',
        alpha=0.001,
        learning_rate='adaptive',
        learning_rate_init=0.001,
        max_iter=1000,  # More iterations
        early_stopping=True,
        validation_fraction=0.2,
        random_state=42
    )
    
    # Optimized Random Forest
    optimized_rf = RandomForestClassifier(
        n_estimators=200,
        max_depth=15,
        min_samples_split=3,
        min_samples_leaf=2,
        max_features='sqrt',
        class_weight='balanced',
        random_state=42
    )
    
    # Optimized Gradient Boosting
    optimized_gb = GradientBoostingClassifier(
        n_estimators=150,
        learning_rate=0.1,
        max_depth=8,
        min_samples_split=4,
        min_samples_leaf=2,
        subsample=0.8,
        random_state=42
    )
    
    # Ensemble of best models
    ensemble_model = VotingClassifier([
        ('best_nn', best_nn),
        ('opt_rf', optimized_rf),
        ('opt_gb', optimized_gb)
    ], voting='soft')
    
    return {
        'Optimized Neural Network': best_nn,
        'Optimized Random Forest': optimized_rf,
        'Optimized Gradient Boosting': optimized_gb,
        'Optimized Ensemble': ensemble_model
    }


def robust_evaluation(models, X, y, cv_folds=5, n_trials=3):
    """Perform robust evaluation with cross-validation and multiple trials"""
    print(f"\n🔬 === ROBUST EVALUATION ({cv_folds}-fold CV, {n_trials} trials) ===")
    
    results = {}
    
    for model_name, model in models.items():
        print(f"\n🔧 Evaluating {model_name}...")
        
        trial_scores = []
        
        # Multiple trials with different random states
        for trial in range(n_trials):
            # Stratified K-Fold cross-validation
            skf = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=42 + trial)
            
            # Cross-validation scores
            cv_scores = cross_val_score(model, X, y, cv=skf, scoring='accuracy')
            trial_scores.extend(cv_scores)
        
        # Calculate statistics
        mean_score = np.mean(trial_scores)
        std_score = np.std(trial_scores)
        min_score = np.min(trial_scores)
        max_score = np.max(trial_scores)
        
        results[model_name] = {
            'mean_accuracy': mean_score,
            'std_accuracy': std_score,
            'min_accuracy': min_score,
            'max_accuracy': max_score,
            'all_scores': trial_scores
        }
        
        print(f"   Mean Accuracy: {mean_score:.3f} ± {std_score:.3f}")
        print(f"   Range: [{min_score:.3f}, {max_score:.3f}]")
    
    return results


def feature_selection_experiment(df, y):
    """Experiment with different feature selection approaches"""
    print(f"\n🎯 === FEATURE SELECTION EXPERIMENT ===")
    
    # Base features
    base_features = select_cascade_features(df)
    X_base = df[base_features].fillna(0)
    
    print(f"Base features: {len(base_features)}")
    
    # Feature selection approaches
    feature_sets = {
        'All Features': X_base,
    }
    
    # Top K features using statistical tests
    for k in [10, 15, 20]:
        selector = SelectKBest(score_func=f_classif, k=k)
        X_selected = selector.fit_transform(X_base, y)
        selected_features = np.array(base_features)[selector.get_support()]
        
        feature_sets[f'Top {k} Features'] = pd.DataFrame(X_selected, columns=selected_features)
        print(f"Top {k} features: {list(selected_features[:5])}...")
    
    # Test each feature set
    best_nn = MLPClassifier(
        hidden_layer_sizes=(64, 32, 16),
        activation='relu',
        solver='adam',
        alpha=0.001,
        learning_rate='adaptive',
        max_iter=500,
        random_state=42
    )
    
    feature_results = {}
    
    for fs_name, X_fs in feature_sets.items():
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X_fs)
        
        # Cross-validation
        cv_scores = cross_val_score(best_nn, X_scaled, y, cv=5, scoring='accuracy')
        
        feature_results[fs_name] = {
            'mean_accuracy': np.mean(cv_scores),
            'std_accuracy': np.std(cv_scores),
            'num_features': X_fs.shape[1]
        }
        
        print(f"{fs_name:<20} {np.mean(cv_scores):.3f} ± {np.std(cv_scores):.3f} ({X_fs.shape[1]} features)")
    
    # Find best feature set
    best_fs = max(feature_results.keys(), key=lambda k: feature_results[k]['mean_accuracy'])
    print(f"\n🏆 Best feature set: {best_fs}")
    
    return feature_results, feature_sets[best_fs]


def final_model_training(X_best, y):
    """Train final model with best configuration"""
    print(f"\n🚀 === FINAL MODEL TRAINING ===")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X_best, y, test_size=0.3, random_state=42, stratify=y
    )
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Best model configuration
    final_model = MLPClassifier(
        hidden_layer_sizes=(128, 64, 32, 16),
        activation='relu',
        solver='adam',
        alpha=0.001,
        learning_rate='adaptive',
        learning_rate_init=0.001,
        max_iter=1000,
        early_stopping=True,
        validation_fraction=0.2,
        random_state=42
    )
    
    # Train model
    start_time = datetime.now()
    final_model.fit(X_train_scaled, y_train)
    train_time = (datetime.now() - start_time).total_seconds()
    
    # Predictions
    start_time = datetime.now()
    y_pred = final_model.predict(X_test_scaled)
    pred_time = (datetime.now() - start_time).total_seconds()
    
    # Evaluation
    accuracy = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
    
    print(f"🎯 Final Model Performance:")
    print(f"   Accuracy: {accuracy:.3f} ({accuracy*100:.1f}%)")
    print(f"   F1-Score: {report['weighted avg']['f1-score']:.3f}")
    print(f"   Training time: {train_time:.1f}s")
    print(f"   Prediction time: {pred_time:.3f}s")
    
    # Detailed results
    if '1' in report:  # Damaged class
        print(f"   Damage Detection:")
        print(f"     Precision: {report['1']['precision']:.3f}")
        print(f"     Recall: {report['1']['recall']:.3f}")
        print(f"     F1-Score: {report['1']['f1-score']:.3f}")
    
    return {
        'model': final_model,
        'scaler': scaler,
        'accuracy': accuracy,
        'report': report,
        'train_time': train_time,
        'pred_time': pred_time,
        'y_test': y_test,
        'y_pred': y_pred
    }


def save_optimized_results(cv_results, feature_results, final_results):
    """Save all optimization results"""
    
    # Cross-validation results
    cv_df = pd.DataFrame([
        {
            'model': name,
            'mean_accuracy': result['mean_accuracy'],
            'std_accuracy': result['std_accuracy'],
            'min_accuracy': result['min_accuracy'],
            'max_accuracy': result['max_accuracy']
        }
        for name, result in cv_results.items()
    ])
    cv_df.to_csv("data/processed/optimized_cv_results.csv", index=False)
    
    # Feature selection results
    fs_df = pd.DataFrame([
        {
            'feature_set': name,
            'mean_accuracy': result['mean_accuracy'],
            'std_accuracy': result['std_accuracy'],
            'num_features': result['num_features']
        }
        for name, result in feature_results.items()
    ])
    fs_df.to_csv("data/processed/feature_selection_results.csv", index=False)
    
    # Final model results
    final_df = pd.DataFrame([{
        'model': 'Optimized Final Model',
        'dataset': 'cascade_failures_optimized',
        'accuracy': final_results['accuracy'],
        'f1_score': final_results['report']['weighted avg']['f1-score'],
        'damage_precision': final_results['report'].get('1', {}).get('precision', 0),
        'damage_recall': final_results['report'].get('1', {}).get('recall', 0),
        'damage_f1': final_results['report'].get('1', {}).get('f1-score', 0),
        'training_time': final_results['train_time'],
        'prediction_time': final_results['pred_time']
    }])
    final_df.to_csv("data/processed/optimized_final_results.csv", index=False)
    
    print(f"\n✅ Results saved:")
    print(f"   CV results: data/processed/optimized_cv_results.csv")
    print(f"   Feature selection: data/processed/feature_selection_results.csv")
    print(f"   Final model: data/processed/optimized_final_results.csv")


def main():
    """Main function for optimized cascade model testing"""
    print("🔥 === OPTIMIZED CASCADE FAILURE PREDICTION ===\n")
    
    # Load and prepare data
    df = load_and_analyze_cascade_data()
    df = engineer_advanced_cascade_features(df)
    
    # Encode labels
    le = LabelEncoder()
    y = le.fit_transform(df['status'])
    
    print(f"✓ Data prepared: {len(df)} samples")
    print(f"✓ Label distribution: {dict(zip(le.classes_, np.bincount(y)))}")
    
    # Create optimized models
    models = create_optimized_models()
    
    # Prepare features for cross-validation
    base_features = select_cascade_features(df)
    X = df[base_features].fillna(0)
    
    # Scale features for CV
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Robust evaluation with cross-validation
    cv_results = robust_evaluation(models, X_scaled, y)
    
    # Feature selection experiment
    feature_results, X_best = feature_selection_experiment(df, y)
    
    # Final model training
    final_results = final_model_training(X_best, y)
    
    # Save results
    save_optimized_results(cv_results, feature_results, final_results)
    
    # Final summary
    print("\n" + "="*80)
    print("🔥 OPTIMIZED CASCADE MODEL FINAL SUMMARY")
    print("="*80)
    
    # Best CV model
    best_cv_model = max(cv_results.keys(), key=lambda k: cv_results[k]['mean_accuracy'])
    best_cv_acc = cv_results[best_cv_model]['mean_accuracy']
    
    # Final model performance
    final_acc = final_results['accuracy']
    
    print(f"\n🎯 PERFORMANCE SUMMARY:")
    print(f"   Best CV Model: {best_cv_model}")
    print(f"   CV Accuracy: {best_cv_acc:.3f} ± {cv_results[best_cv_model]['std_accuracy']:.3f}")
    print(f"   Final Model Accuracy: {final_acc:.3f} ({final_acc*100:.1f}%)")
    
    # Achievement assessment
    if final_acc > 0.75:
        print(f"\n🎉 EXCELLENT: {final_acc*100:.1f}% - Outstanding performance!")
        print("   ✅ Ready for production deployment")
    elif final_acc > 0.70:
        print(f"\n🚀 VERY GOOD: {final_acc*100:.1f}% - Strong predictive capability!")
        print("   ✅ Suitable for operational use")
    elif final_acc > 0.65:
        print(f"\n✅ GOOD: {final_acc*100:.1f}% - Solid performance!")
        print("   ⚠️  Consider additional tuning for critical applications")
    else:
        print(f"\n⚠️  MODERATE: {final_acc*100:.1f}% - Baseline performance")
        print("   🔧 Further optimization recommended")
    
    # Historical comparison
    print(f"\n📈 HISTORICAL PROGRESSION:")
    print(f"   Optimized Model: {final_acc*100:.1f}%")
    print(f"   Enhanced Neural Network: 70.0%")
    print(f"   Basic Cascade Models: 56.7%")
    print(f"   Power Grid Models: 51.7%")
    print(f"   Camp Fire Prediction: ✅ 308 days warning (Grid Risk)")
    
    total_improvement = (final_acc - 0.517) * 100
    print(f"\n🚀 Total improvement from baseline: +{total_improvement:.1f}% points")


if __name__ == "__main__":
    main()