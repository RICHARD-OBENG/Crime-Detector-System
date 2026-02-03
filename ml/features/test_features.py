#!/usr/bin/env python
"""Test feature engineering pipeline."""

import sys
sys.path.insert(0, 'ml')

from features.build_features import CrimeFeatureEngineer
import pandas as pd
from pathlib import Path

# Load test data
interim_path = Path('ml/data/interim/cleaned_data.csv')
data = pd.read_csv(interim_path)
print(f'✓ Loaded {len(data)} records')
print(f'Input columns: {data.columns.tolist()}')

# Engineer features
engineer = CrimeFeatureEngineer()
features, target = engineer.build_features(data, fit=True)
print(f'\n✓ Engineered {len(features.columns)} features')
print(f'Output columns: {features.columns.tolist()}')
print(f'\n✓ Target shape: {target.shape}')
print(f'Target unique values: {sorted(target.unique())}')

print('\nFirst 3 rows of engineered features:')
print(features.head(3))
print(f'\nFeature dtypes:\n{features.dtypes}')
