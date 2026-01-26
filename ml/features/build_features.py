# features/build_features.py
"""
Configuration-driven feature engineering pipeline for Crime Detector System.

This pipeline reads feature definitions from feature_config.yaml, making it:
- Stable: Code doesn't change when features change
- Auditable: All feature decisions declared in one place
- Maintainable: Feature list, encoding strategies, and scaling are centralized

Data flow:
  Config:  ml/features/feature_config.yaml (feature definitions)
  Input:   ml/data/interim/cleaned_data.csv (raw cleaned data)
  Output:  ml/data/processed/features.csv (engineered features)
           ml/data/processed/target.csv (target variable)
           ml/data/processed/feature_metadata.pkl (encoders/scalers for inference)
"""

import os
import pickle
import logging
import numpy as np
import pandas as pd
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Any
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)


class ConfigDrivenFeatureEngineer:
    """
    Configuration-driven feature engineering.
    
    Reads all feature definitions from feature_config.yaml and applies
    transformations declaratively without hardcoded logic.
    """

    def __init__(self, config_path: str):
        """
        Initialize feature engineer with configuration.
        
        Args:
            config_path: Path to feature_config.yaml
        """
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        logger.info(f"Loaded feature configuration v{self.config.get('version', 'unknown')}")
        
        self.label_encoders = {}
        self.scalers = {}
        self.feature_names = None
        self.target_col = self._get_target_col()

    def _get_target_col(self) -> str:
        """Extract target column name from config."""
        targets = self.config.get('feature_groups', {}).get('target', [])
        return targets[0] if targets else 'crime_type'

    def build_features(self, crime_data: pd.DataFrame, fit=True) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Build engineered features from raw cleaned data using config.

        Args:
            crime_data: DataFrame with cleaned crime data
            fit: If True, fit encoders on data (training). If False, use existing (inference).

        Returns:
            Tuple of (features DataFrame, target Series)
        """
        df = crime_data.copy()

        # Drop identifiers
        identifiers = self.config.get('feature_groups', {}).get('identifiers', [])
        df = df.drop(columns=[col for col in identifiers if col in df.columns])
        
        # Separate target
        target = df.pop(self.target_col) if self.target_col in df.columns else None

        # Apply transformations in order
        df = self._apply_cyclical_encoding(df, fit=fit)
        df = self._apply_spatial_binning(df, fit=fit)
        df = self._apply_age_binning(df, fit=fit)
        df = self._apply_categorical_low_card(df, fit=fit)
        df = self._apply_categorical_high_card(df, fit=fit)
        df = self._apply_pass_through(df, fit=fit)
        df = self._apply_scaling(df, fit=fit)

        # Store feature names
        if fit:
            self.feature_names = df.columns.tolist()

        logger.info(f"Engineered {len(df.columns)} features")
        return df, target

    def _apply_cyclical_encoding(self, df: pd.DataFrame, fit=True) -> pd.DataFrame:
        """Apply sin/cos encoding to cyclical features."""
        features = self.config.get('feature_groups', {}).get('numeric_cyclical', [])
        
        for feature_dict in features:
            for feature_name, config in feature_dict.items():
                if feature_name not in df.columns:
                    continue
                
                bins = config.get('bins', 24)
                df[f'{feature_name}_sin'] = np.sin(2 * np.pi * df[feature_name] / bins)
                df[f'{feature_name}_cos'] = np.cos(2 * np.pi * df[feature_name] / bins)
                df = df.drop(columns=[feature_name])
                logger.info(f"Applied sin/cos encoding to {feature_name}")
        
        return df

    def _apply_spatial_binning(self, df: pd.DataFrame, fit=True) -> pd.DataFrame:
        """Apply spatial binning to location features."""
        features = self.config.get('feature_groups', {}).get('numeric_spatial', [])
        
        for feature_dict in features:
            for feature_name, config in feature_dict.items():
                if feature_name not in df.columns:
                    continue
                
                bins = config.get('bins', 10)
                df[f'{feature_name}_bin'] = pd.cut(df[feature_name], bins=bins, labels=False)
                df = df.drop(columns=[feature_name])
                logger.info(f"Applied spatial binning ({bins} bins) to {feature_name}")
        
        return df

    def _apply_age_binning(self, df: pd.DataFrame, fit=True) -> pd.DataFrame:
        """Apply age binning to age features."""
        features = self.config.get('feature_groups', {}).get('numeric_age', [])
        
        for feature_dict in features:
            for feature_name, config in feature_dict.items():
                if feature_name not in df.columns:
                    continue
                
                bins = config.get('bins', [0, 18, 35, 50, 65, 150])
                labels = config.get('labels', False)
                df[f'{feature_name}_bin'] = pd.cut(df[feature_name], bins=bins, labels=labels)
                df = df.drop(columns=[feature_name])
                logger.info(f"Applied age binning to {feature_name}")
        
        return df

    def _apply_categorical_low_card(self, df: pd.DataFrame, fit=True) -> pd.DataFrame:
        """Apply one-hot encoding to low-cardinality categorical features."""
        features = self.config.get('feature_groups', {}).get('categorical_low_cardinality', [])
        
        for feature_dict in features:
            for feature_name, config in feature_dict.items():
                if feature_name not in df.columns:
                    continue
                
                # Group rare values
                rare_threshold = config.get('rare_threshold', 0.01)
                rare_threshold_count = rare_threshold * len(df)
                
                value_counts = df[feature_name].value_counts()
                rare_values = value_counts[value_counts < rare_threshold_count].index.tolist()
                
                if rare_values:
                    df[feature_name] = df[feature_name].replace(rare_values, 'other')
                
                # One-hot encode
                df = pd.get_dummies(df, columns=[feature_name], prefix=feature_name, drop_first=False)
                logger.info(f"Applied one-hot encoding to {feature_name} (grouped rare: {len(rare_values)})")
        
        return df

    def _apply_categorical_high_card(self, df: pd.DataFrame, fit=True) -> pd.DataFrame:
        """Apply frequency encoding to high-cardinality categorical features."""
        features = self.config.get('feature_groups', {}).get('categorical_high_cardinality', [])
        
        for feature_dict in features:
            for feature_name, config in feature_dict.items():
                if feature_name not in df.columns:
                    continue
                
                if fit:
                    freq_map = df[feature_name].value_counts(normalize=True).to_dict()
                    self.label_encoders[f'{feature_name}_freq'] = freq_map
                
                freq_map = self.label_encoders.get(f'{feature_name}_freq', {})
                df[f'{feature_name}_enc'] = df[feature_name].map(freq_map)
                df = df.drop(columns=[feature_name])
                logger.info(f"Applied frequency encoding to {feature_name}")
        
        return df

    def _apply_pass_through(self, df: pd.DataFrame, fit=True) -> pd.DataFrame:
        """Keep pass-through numeric features unchanged."""
        features = self.config.get('feature_groups', {}).get('numeric_pass_through', [])
        
        for feature_dict in features:
            for feature_name in feature_dict.keys():
                if feature_name in df.columns:
                    logger.info(f"Pass-through (no encoding): {feature_name}")
        
        return df

    def _apply_scaling(self, df: pd.DataFrame, fit=True) -> pd.DataFrame:
        """Apply scaling to specified features if enabled."""
        scaling_config = self.config.get('scaling', {})
        
        if not scaling_config.get('enabled', False):
            logger.info("Scaling disabled (per config)")
            return df
        
        features_to_scale = scaling_config.get('features', [])
        if not features_to_scale:
            return df
        
        method = scaling_config.get('method', 'standard')
        
        if method == 'standard':
            if fit:
                scaler = StandardScaler()
                df[features_to_scale] = scaler.fit_transform(df[features_to_scale])
                self.scalers['standard'] = scaler
            else:
                scaler = self.scalers.get('standard')
                if scaler:
                    df[features_to_scale] = scaler.transform(df[features_to_scale])
            
            logger.info(f"Applied StandardScaler to {len(features_to_scale)} features")
        
        return df

    def save_metadata(self, output_dir: str) -> None:
        """Save feature metadata for inference pipeline."""
        metadata_path = Path(output_dir) / "feature_metadata.pkl"
        metadata = {
            "feature_names": self.feature_names,
            "label_encoders": self.label_encoders,
            "scalers": self.scalers,
            "config_version": self.config.get('version'),
        }
        with open(metadata_path, "wb") as f:
            pickle.dump(metadata, f)
        logger.info(f"Saved feature metadata to {metadata_path}")

    def load_metadata(self, metadata_path: str) -> None:
        """Load feature metadata for inference."""
        with open(metadata_path, "rb") as f:
            metadata = pickle.load(f)
        self.feature_names = metadata["feature_names"]
        self.label_encoders = metadata["label_encoders"]
        self.scalers = metadata["scalers"]
        logger.info(f"Loaded feature metadata from {metadata_path}")


def main():
    """
    Execute configuration-driven feature engineering pipeline.
    
    Reads: ml/features/feature_config.yaml (configuration)
           ml/data/interim/cleaned_data.csv (raw data)
    Writes: ml/data/processed/features.csv
            ml/data/processed/target.csv
            ml/data/processed/feature_metadata.pkl
    """
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    
    # Setup paths
    project_root = Path(__file__).parent.parent
    config_path = project_root / "features" / "feature_config.yaml"
    interim_dir = project_root / "data" / "interim"
    processed_dir = project_root / "data" / "processed"
    
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Load cleaned data
    input_path = interim_dir / "cleaned_data.csv"
    logger.info(f"Loading cleaned data from {input_path}")
    crime_data = pd.read_csv(input_path)
    logger.info(f"Loaded {len(crime_data)} records with columns: {crime_data.columns.tolist()}")

    # Engineer features (configuration-driven)
    engineer = ConfigDrivenFeatureEngineer(config_path)
    features, target = engineer.build_features(crime_data, fit=True)

    # Save features and target
    output_path = processed_dir / "features.csv"
    features.to_csv(output_path, index=False)
    logger.info(f"Saved {len(features)} feature rows to {output_path}")

    target_path = processed_dir / "target.csv"
    target.to_csv(target_path, index=False, header=["crime_type"])
    logger.info(f"Saved {len(target)} target rows to {target_path}")

    # Save metadata for inference
    engineer.save_metadata(processed_dir)

    logger.info("✓ Feature engineering pipeline completed successfully")
    logger.info(f"Output features: {len(features.columns)} x {len(features)} (rows x cols)")
    
    return features, target


if __name__ == "__main__":
    main()