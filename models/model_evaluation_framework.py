"""
Comprehensive Model Testing Framework for Cable Risk Classification
==================================================================
Evaluates all optimized models for cable infrastructure monitoring.

Features:
- Automated model training and evaluation
- Cross-validation with stratified folds
- Comprehensive metrics (accuracy, precision, recall, F1, confusion matrix)
- Performance comparison and ranking
- Model selection recommendations
- Real-time prediction speed testing
"""

import numpy as np
import pandas as pd
import time
from datetime import datetime
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score, 
                           classification_report, confusion_matrix, roc_auc_score)
from sklearn.preprocessing import LabelEncoder
import warnings
warnings.filterwarnings('ignore')

# Import our models
from cable_dataset_generator import CableDatasetGenerator
from optimized_cable_models import create_all_models

class ModelEvaluator:
    """Comprehensive evaluation framework for cable risk models"""
    
    def __init__(self, test_size=0.2, cv_folds=5, random_state=42):
        self.test_size = test_size
        self.cv_folds = cv_folds
        self.random_state = random_state
        self.results = {}
        self.best_model = None
        self.best_score = 0
        
        # Label encoding for sklearn compatibility
        self.label_encoder = LabelEncoder()
        
    def prepare_data(self, n_samples=10000):
        """Generate and prepare cable monitoring dataset"""
        print("🔧 Generating cable monitoring dataset...")
        
        generator = CableDatasetGenerator(random_seed=self.random_state)
        
        # Generate balanced dataset
        df = generator.generate_balanced_dataset(
            n_samples=n_samples,
            green_ratio=0.60,    # 60% normal operation
            yellow_ratio=0.25,   # 25% warning conditions
            red_ratio=0.15       # 15% critical conditions
        )
        
        # Prepare features and labels
        X = df[['temperature', 'vibration', 'strain', 'power']]
        y = self.label_encoder.fit_transform(df['risk_zone'])  # Convert to numeric
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=self.test_size, stratify=y, random_state=self.random_state
        )
        
        print(f"✅ Dataset prepared:")
        print(f"   Training samples: {len(X_train)}")
        print(f"   Test samples: {len(X_test)}")
        print(f"   Classes: {list(self.label_encoder.classes_)}")
        
        return X_train, X_test, y_train, y_test, df
    
    def evaluate_model(self, model, X_train, X_test, y_train, y_test, model_name):
        """Comprehensive evaluation of a single model"""
        print(f"\\n🧪 Evaluating {model_name}...")
        
        results = {
            'model_name': model_name,
            'training_time': 0,
            'prediction_time': 0,
            'test_accuracy': 0,
            'test_f1_macro': 0,
            'test_f1_weighted': 0,
            'cv_accuracy_mean': 0,
            'cv_accuracy_std': 0,
            'cv_f1_mean': 0,
            'cv_f1_std': 0,
            'confusion_matrix': None,
            'classification_report': None,
            'predictions': None,
            'probabilities': None
        }
        
        try:
            # Training
            start_time = time.time()
            model.train(X_train, y_train)
            training_time = time.time() - start_time
            results['training_time'] = training_time
            
            # Cross-validation
            print(f"   🔄 Cross-validation ({self.cv_folds} folds)...")
            cv_scores_acc = cross_val_score(
                model.model, 
                model.scaler.transform(model.engineer_features(X_train)), 
                y_train, 
                cv=StratifiedKFold(n_splits=self.cv_folds, shuffle=True, random_state=self.random_state),
                scoring='accuracy',
                n_jobs=-1
            )
            
            cv_scores_f1 = cross_val_score(
                model.model,
                model.scaler.transform(model.engineer_features(X_train)),
                y_train,
                cv=StratifiedKFold(n_splits=self.cv_folds, shuffle=True, random_state=self.random_state),
                scoring='f1_macro',
                n_jobs=-1
            )
            
            results['cv_accuracy_mean'] = cv_scores_acc.mean()
            results['cv_accuracy_std'] = cv_scores_acc.std()
            results['cv_f1_mean'] = cv_scores_f1.mean()
            results['cv_f1_std'] = cv_scores_f1.std()
            
            # Test set evaluation
            print(f"   📊 Test set evaluation...")
            start_time = time.time()
            predictions, probabilities = model.predict(X_test)
            prediction_time = (time.time() - start_time) / len(X_test) * 1000  # ms per prediction
            results['prediction_time'] = prediction_time
            
            # Metrics
            results['test_accuracy'] = accuracy_score(y_test, predictions)
            results['test_f1_macro'] = f1_score(y_test, predictions, average='macro')
            results['test_f1_weighted'] = f1_score(y_test, predictions, average='weighted')
            results['confusion_matrix'] = confusion_matrix(y_test, predictions)
            results['classification_report'] = classification_report(y_test, predictions, 
                                                                   target_names=self.label_encoder.classes_,
                                                                   output_dict=True)
            results['predictions'] = predictions
            results['probabilities'] = probabilities
            
            # Per-class metrics
            precision_per_class = precision_score(y_test, predictions, average=None)
            recall_per_class = recall_score(y_test, predictions, average=None)
            f1_per_class = f1_score(y_test, predictions, average=None)
            
            results['per_class_metrics'] = {
                'precision': dict(zip(self.label_encoder.classes_, precision_per_class)),
                'recall': dict(zip(self.label_encoder.classes_, recall_per_class)),
                'f1': dict(zip(self.label_encoder.classes_, f1_per_class))
            }
            
            print(f"   ✅ Accuracy: {results['test_accuracy']:.4f}")
            print(f"   ✅ F1-macro: {results['test_f1_macro']:.4f}")
            print(f"   ⏱️ Training time: {training_time:.2f}s")
            print(f"   ⚡ Prediction time: {prediction_time:.3f}ms per sample")
            
        except Exception as e:
            print(f"   ❌ Failed: {str(e)}")
            results['error'] = str(e)
        
        return results
    
    def run_comprehensive_evaluation(self, n_samples=10000):
        """Run evaluation on all models"""
        print("🚀 Starting Comprehensive Cable Risk Model Evaluation")
        print("=" * 60)
        
        # Prepare data
        X_train, X_test, y_train, y_test, df = self.prepare_data(n_samples)
        
        # Create all models
        models = create_all_models()
        
        print(f"\\n🤖 Evaluating {len(models)} models...")
        
        # Evaluate each model
        for model_key, model in models.items():
            try:
                results = self.evaluate_model(model, X_train, X_test, y_train, y_test, model.model_name)
                self.results[model_key] = results
                
                # Track best model
                current_score = results['test_f1_macro']
                if current_score > self.best_score:
                    self.best_score = current_score
                    self.best_model = model_key
                    
            except Exception as e:
                print(f"❌ Failed to evaluate {model.model_name}: {str(e)}")
        
        return X_train, X_test, y_train, y_test, df
    
    def generate_comparison_report(self):
        """Generate comprehensive comparison report"""
        if not self.results:
            print("❌ No results to compare. Run evaluation first.")
            return
        
        print("\\n" + "=" * 80)
        print("📊 COMPREHENSIVE MODEL COMPARISON REPORT")
        print("=" * 80)
        
        # Create comparison DataFrame
        comparison_data = []
        for model_key, results in self.results.items():
            if 'error' not in results:
                comparison_data.append({
                    'Model': results['model_name'],
                    'Test Accuracy': results['test_accuracy'],
                    'Test F1-Macro': results['test_f1_macro'],
                    'Test F1-Weighted': results['test_f1_weighted'],
                    'CV Accuracy': f"{results['cv_accuracy_mean']:.4f} ± {results['cv_accuracy_std']:.4f}",
                    'CV F1-Macro': f"{results['cv_f1_mean']:.4f} ± {results['cv_f1_std']:.4f}",
                    'Training Time (s)': results['training_time'],
                    'Prediction Time (ms)': results['prediction_time']
                })
        
        comparison_df = pd.DataFrame(comparison_data)
        comparison_df = comparison_df.sort_values('Test F1-Macro', ascending=False)
        
        print("\\n🏆 OVERALL RANKING (by Test F1-Macro Score):")
        print("-" * 80)
        for i, row in comparison_df.iterrows():
            rank = comparison_df.index.get_loc(i) + 1
            emoji = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else "📊"
            print(f"{emoji} #{rank:2d}. {row['Model']:30s} | F1: {row['Test F1-Macro']:.4f} | Acc: {row['Test Accuracy']:.4f}")
        
        # Best model detailed analysis
        if self.best_model:
            best_results = self.results[self.best_model]
            print(f"\\n🎯 BEST MODEL: {best_results['model_name']}")
            print("-" * 50)
            print(f"✅ Test Accuracy: {best_results['test_accuracy']:.4f} ({best_results['test_accuracy']*100:.2f}%)")
            print(f"✅ Test F1-Macro: {best_results['test_f1_macro']:.4f}")
            print(f"✅ Test F1-Weighted: {best_results['test_f1_weighted']:.4f}")
            print(f"⏱️ Training Time: {best_results['training_time']:.2f}s")
            print(f"⚡ Prediction Speed: {best_results['prediction_time']:.3f}ms per sample")
            
            # Per-class performance
            print(f"\\n📈 PER-CLASS PERFORMANCE:")
            for class_name in self.label_encoder.classes_:
                precision = best_results['per_class_metrics']['precision'][class_name]
                recall = best_results['per_class_metrics']['recall'][class_name]
                f1 = best_results['per_class_metrics']['f1'][class_name]
                
                zone_emoji = "🟢" if class_name == 'green' else "🟡" if class_name == 'yellow' else "🔴"
                print(f"   {zone_emoji} {class_name.upper():7s}: Precision={precision:.3f}, Recall={recall:.3f}, F1={f1:.3f}")
            
            # Confusion matrix
            print(f"\\n🔍 CONFUSION MATRIX:")
            cm = best_results['confusion_matrix']
            classes = self.label_encoder.classes_
            
            print("      Predicted")
            print(f"     {' '.join([f'{c:>6s}' for c in classes])}")
            for i, true_class in enumerate(classes):
                row = ' '.join([f'{cm[i, j]:6d}' for j in range(len(classes))])
                if i == 0:
                    print(f"True {true_class:>6s} {row}")
                else:
                    print(f"     {true_class:>6s} {row}")
        
        return comparison_df
    
    def get_best_model_for_deployment(self):
        """Get the best model for Raspberry Pi deployment"""
        if not self.best_model:
            print("❌ No best model found. Run evaluation first.")
            return None
        
        best_results = self.results[self.best_model]
        
        print(f"\\n🎯 RECOMMENDED MODEL FOR RASPBERRY PI DEPLOYMENT:")
        print("=" * 60)
        print(f"🤖 Model: {best_results['model_name']}")
        print(f"📊 Accuracy: {best_results['test_accuracy']:.4f} ({best_results['test_accuracy']*100:.2f}%)")
        print(f"⚡ Speed: {best_results['prediction_time']:.3f}ms per prediction")
        print(f"🎯 F1-Score: {best_results['test_f1_macro']:.4f}")
        
        return self.best_model, best_results


# Main evaluation script
def main():
    """Run comprehensive model evaluation"""
    print("🧪 Cable Risk Classification Model Evaluation")
    print("=" * 50)
    
    # Initialize evaluator
    evaluator = ModelEvaluator(test_size=0.2, cv_folds=5, random_state=42)
    
    # Run evaluation
    X_train, X_test, y_train, y_test, df = evaluator.run_comprehensive_evaluation(n_samples=8000)
    
    # Generate comparison report
    comparison_df = evaluator.generate_comparison_report()
    
    # Get best model recommendation
    best_model_key, best_results = evaluator.get_best_model_for_deployment()
    
    print(f"\\n✅ Evaluation complete! Best model: {best_results['model_name']}")
    
    return evaluator, comparison_df


if __name__ == "__main__":
    evaluator, comparison_df = main()