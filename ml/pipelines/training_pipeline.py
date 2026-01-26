# pipelines/training_pipeline.py
"""
Training Pipeline Orchestration

Purpose: Main entry point for model training workflow

Performs:
  1. Load processed features (from data/processed/)
  2. Split data (train/validation/test)
  3. Train model
  4. Evaluate model (metrics, performance)
  5. Validate model (quality checks, bias checks)
  6. Register artifacts (model, metadata, metrics)

Flow:
  processed/features.csv + processed/target.csv
        ↓
  [Split train/val/test]
        ↓
  [Train model]
        ↓
  [Evaluate on all splits]
        ↓
  [Validate quality]
        ↓
  [Register artifacts]
        ↓
  models/registry/ (model, metadata, metrics)
"""

import logging
import pickle
import json
from pathlib import Path
from typing import Tuple, Dict, Any
from datetime import datetime

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, f1_score

logger = logging.getLogger(__name__)


class TrainingPipeline:
    """Orchestrate complete model training workflow."""

    def __init__(self, processed_dir: str, models_dir: str, test_size: float = 0.2, val_size: float = 0.1):
        """
        Initialize training pipeline.

        Args:
            processed_dir: Directory with processed features
            models_dir: Directory to save model artifacts
            test_size: Proportion for test set (0.2 = 20%)
            val_size: Proportion for validation set (0.1 = 10%)
        """
        self.processed_dir = Path(processed_dir)
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        self.test_size = test_size
        self.val_size = val_size
        
        self.model = None
        self.metrics = {}
        self.metadata = {}
        
        logger.info("Training pipeline initialized")
        logger.info(f"  Processed data dir: {self.processed_dir}")
        logger.info(f"  Models output dir: {self.models_dir}")
        logger.info(f"  Train/Val/Test split: {1-test_size-val_size:.1%} / {val_size:.1%} / {test_size:.1%}")

    def load_processed_features(self) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Load processed features and target from processed directory.

        Returns:
            Tuple of (features DataFrame, target Series)
        """
        logger.info("Loading processed features...")
        
        # Load features
        features_path = self.processed_dir / "features.csv"
        if not features_path.exists():
            raise FileNotFoundError(f"Features file not found: {features_path}")
        
        features = pd.read_csv(features_path)
        logger.info(f"✓ Loaded features: {features.shape[0]} rows × {features.shape[1]} cols")
        
        # Load target
        target_path = self.processed_dir / "target.csv"
        if not target_path.exists():
            raise FileNotFoundError(f"Target file not found: {target_path}")
        
        target = pd.read_csv(target_path).squeeze()
        logger.info(f"✓ Loaded target: {target.shape[0]} rows")
        logger.info(f"  Target distribution:\n{target.value_counts()}")
        
        # Validate
        assert len(features) == len(target), "Features and target have different lengths"
        assert features.isnull().sum().sum() == 0, "Features contain missing values"
        assert target.isnull().sum() == 0, "Target contains missing values"
        
        return features, target

    def split_data(self, features: pd.DataFrame, target: pd.Series) -> Dict[str, Any]:
        """
        Split data into train/validation/test sets.

        Args:
            features: Feature DataFrame
            target: Target Series

        Returns:
            Dict with X_train, y_train, X_val, y_val, X_test, y_test
        """
        logger.info("Splitting data...")
        
        # First split: train+val vs test
        X_temp, X_test, y_temp, y_test = train_test_split(
            features, target,
            test_size=self.test_size,
            random_state=42,
            stratify=target
        )
        
        # Second split: train vs val (from remaining data)
        val_size_adjusted = self.val_size / (1 - self.test_size)
        X_train, X_val, y_train, y_val = train_test_split(
            X_temp, y_temp,
            test_size=val_size_adjusted,
            random_state=42,
            stratify=y_temp
        )
        
        splits = {
            'X_train': X_train, 'y_train': y_train,
            'X_val': X_val, 'y_val': y_val,
            'X_test': X_test, 'y_test': y_test,
        }
        
        logger.info(f"✓ Data split:")
        logger.info(f"  Train: {len(X_train)} samples ({100*len(X_train)/len(features):.1f}%)")
        logger.info(f"  Val:   {len(X_val)} samples ({100*len(X_val)/len(features):.1f}%)")
        logger.info(f"  Test:  {len(X_test)} samples ({100*len(X_test)/len(features):.1f}%)")
        
        return splits

    def train_model(self, X_train: pd.DataFrame, y_train: pd.Series) -> RandomForestClassifier:
        """
        Train model on training data.

        Args:
            X_train: Training features
            y_train: Training target

        Returns:
            Trained model
        """
        logger.info("Training model...")
        
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=15,
            min_samples_split=10,
            min_samples_leaf=5,
            random_state=42,
            n_jobs=-1,
            class_weight='balanced'  # Handle class imbalance
        )
        
        model.fit(X_train, y_train)
        logger.info(f"✓ Model trained (classes: {model.classes_.tolist()})")
        
        return model

    def evaluate_model(self, model, splits: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate model on all splits.

        Args:
            model: Trained model
            splits: Dict with train/val/test data

        Returns:
            Dict with metrics for each split
        """
        logger.info("Evaluating model on all splits...")
        
        metrics = {}
        
        for split_name in ['train', 'val', 'test']:
            X = splits[f'X_{split_name}']
            y = splits[f'y_{split_name}']
            
            # Predict
            y_pred = model.predict(X)
            
            # Calculate metrics
            accuracy = accuracy_score(y, y_pred)
            f1_macro = f1_score(y, y_pred, average='macro', zero_division=0)
            
            metrics[split_name] = {
                'accuracy': float(accuracy),
                'f1_macro': float(f1_macro),
                'samples': len(y)
            }
            
            logger.info(f"  {split_name.upper():5s}: accuracy={accuracy:.4f}, f1_macro={f1_macro:.4f}")
        
        self.metrics = metrics
        return metrics

    def validate_model(self, model, splits: Dict[str, Any]) -> bool:
        """
        Validate model quality and fairness.

        Checks:
        - Model achieves minimum accuracy on test set
        - No significant overfitting (train/test gap)
        - Reasonable performance across classes

        Args:
            model: Trained model
            splits: Dict with train/val/test data

        Returns:
            True if valid, raises exception otherwise
        """
        logger.info("Validating model...")
        
        X_test, y_test = splits['X_test'], splits['y_test']
        X_train, y_train = splits['X_train'], splits['y_train']
        
        # Predict
        y_train_pred = model.predict(X_train)
        y_test_pred = model.predict(X_test)
        
        train_acc = accuracy_score(y_train, y_train_pred)
        test_acc = accuracy_score(y_test, y_test_pred)
        
        # Check: Minimum test accuracy
        min_accuracy = 0.60
        assert test_acc >= min_accuracy, \
            f"Test accuracy {test_acc:.4f} below minimum {min_accuracy:.4f}"
        logger.info(f"✓ Minimum accuracy check passed ({test_acc:.4f} >= {min_accuracy})")
        
        # Check: Overfitting (train/test gap)
        max_overfit = 0.15
        overfit_gap = train_acc - test_acc
        assert overfit_gap <= max_overfit, \
            f"Overfitting detected: gap={overfit_gap:.4f} > {max_overfit}"
        logger.info(f"✓ Overfitting check passed (gap={overfit_gap:.4f} <= {max_overfit})")
        
        # Check: Per-class performance (no severe class imbalance issues)
        per_class_acc = {}
        for cls in model.classes_:
            mask = y_test == cls
            if mask.sum() > 0:
                acc = accuracy_score(y_test[mask], y_test_pred[mask])
                per_class_acc[cls] = acc
        
        min_per_class_acc = 0.50
        for cls, acc in per_class_acc.items():
            assert acc >= min_per_class_acc, \
                f"Class '{cls}' accuracy {acc:.4f} below {min_per_class_acc}"
        
        logger.info(f"✓ Per-class accuracy check passed (min={min(per_class_acc.values()):.4f})")
        
        logger.info("✓ Model validation passed all checks")
        return True

    def register_artifacts(self, model, splits: Dict[str, Any]) -> Path:
        """
        Register/save model artifacts.

        Saves:
        - Trained model (pickle)
        - Metrics (JSON)
        - Metadata (JSON)
        - Feature names (JSON)

        Args:
            model: Trained model
            splits: Dict with data splits

        Returns:
            Path to model registry directory
        """
        logger.info("Registering artifacts...")
        
        # Create timestamped registry directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        registry_dir = self.models_dir / f"model_{timestamp}"
        registry_dir.mkdir(parents=True, exist_ok=True)
        
        # Save model
        model_path = registry_dir / "model.pkl"
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
        logger.info(f"✓ Saved model to {model_path}")
        
        # Save metrics
        metrics_path = registry_dir / "metrics.json"
        with open(metrics_path, 'w') as f:
            json.dump(self.metrics, f, indent=2)
        logger.info(f"✓ Saved metrics to {metrics_path}")
        
        # Save metadata
        metadata = {
            'timestamp': timestamp,
            'model_type': type(model).__name__,
            'n_classes': len(model.classes_),
            'classes': model.classes_.tolist(),
            'n_features': model.n_features_in_,
            'feature_names': splits['X_train'].columns.tolist(),
            'train_samples': len(splits['X_train']),
            'val_samples': len(splits['X_val']),
            'test_samples': len(splits['X_test']),
        }
        
        metadata_path = registry_dir / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"✓ Saved metadata to {metadata_path}")
        
        # Save feature importance
        if hasattr(model, 'feature_importances_'):
            importances = pd.DataFrame({
                'feature': splits['X_train'].columns,
                'importance': model.feature_importances_
            }).sort_values('importance', ascending=False)
            
            importance_path = registry_dir / "feature_importance.csv"
            importances.to_csv(importance_path, index=False)
            logger.info(f"✓ Saved feature importance to {importance_path}")
        
        # Save latest symlink
        latest_link = self.models_dir / "latest"
        if latest_link.exists():
            latest_link.unlink()
        latest_link.symlink_to(registry_dir.name)
        logger.info(f"✓ Updated latest symlink")
        
        logger.info(f"✓ Artifacts registered at {registry_dir}")
        return registry_dir

    def run(self) -> Tuple[RandomForestClassifier, Path]:
        """
        Execute complete training pipeline.

        Steps:
          1. Load processed features
          2. Split data (train/val/test)
          3. Train model
          4. Evaluate model
          5. Validate model
          6. Register artifacts

        Returns:
            Tuple of (trained model, registry path)
        """
        logger.info("=" * 70)
        logger.info("STARTING TRAINING PIPELINE")
        logger.info("=" * 70)
        
        try:
            # Load
            features, target = self.load_processed_features()
            
            # Split
            splits = self.split_data(features, target)
            
            # Train
            self.model = self.train_model(splits['X_train'], splits['y_train'])
            
            # Evaluate
            self.evaluate_model(self.model, splits)
            
            # Validate
            self.validate_model(self.model, splits)
            
            # Register
            registry_path = self.register_artifacts(self.model, splits)
            
            logger.info("=" * 70)
            logger.info("TRAINING PIPELINE COMPLETED SUCCESSFULLY")
            logger.info("=" * 70)
            
            return self.model, registry_path
            
        except Exception as e:
            logger.error(f"TRAINING PIPELINE FAILED: {e}")
            raise


def main():
    """Execute training pipeline from command line."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s'
    )
    
    # Setup paths
    project_root = Path(__file__).parent.parent
    processed_dir = project_root / "data" / "processed"
    models_dir = project_root / "models" / "registry"
    
    # Validate input data exists
    if not (processed_dir / "features.csv").exists():
        logger.error(f"Features not found: {processed_dir / 'features.csv'}")
        raise FileNotFoundError("Run feature engineering pipeline first")
    
    if not (processed_dir / "target.csv").exists():
        logger.error(f"Target not found: {processed_dir / 'target.csv'}")
        raise FileNotFoundError("Run feature engineering pipeline first")
    
    # Run training
    pipeline = TrainingPipeline(processed_dir, models_dir)
    model, registry_path = pipeline.run()
    
    logger.info(f"\nModel registered at: {registry_path}")


if __name__ == "__main__":
    main()
