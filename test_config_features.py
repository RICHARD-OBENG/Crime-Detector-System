#!/usr/bin/env python
"""Test configuration-driven feature engineering pipeline."""

import sys
sys.path.insert(0, 'ml')

from features.build_features import ConfigDrivenFeatureEngineer
import pandas as pd
from pathlib import Path

# Load test data
interim_path = Path('ml/data/interim/cleaned_data.csv')
data = pd.read_csv(interim_path)
print(f'✓ Loaded {len(data)} records')
print(f'Input columns: {data.columns.tolist()}\n')

# Create engineer with config
config_path = Path('ml/features/feature_config.yaml')
engineer = ConfigDrivenFeatureEngineer(config_path)

# Engineer features
features, target = engineer.build_features(data, fit=True)
print(f'\n✓ Engineered {len(features.columns)} features')
print(f'Output columns: {features.columns.tolist()}')
print(f'\n✓ Target shape: {target.shape}')
print(f'Target unique values: {sorted(target.unique())}')

print('\nFirst 3 rows of engineered features:')
print(features.head(3))
print(f'\nFeature dtypes:\n{features.dtypes}')

# Verify config expectations
expected_count = 18
print(f'\n✓ Feature count matches config expectation: {len(features.columns)} == {expected_count}? {len(features.columns) == expected_count}')
