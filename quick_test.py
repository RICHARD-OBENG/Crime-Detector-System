#!/usr/bin/env python
"""Quick test of configuration-driven feature engineering."""

import sys
import os

# Suppress warnings for cleaner output
os.environ['PYTHONWARNINGS'] = 'ignore'
sys.path.insert(0, 'ml')

try:
    from features.build_features import ConfigDrivenFeatureEngineer
    import pandas as pd
    from pathlib import Path
    
    # Load test data
    interim_path = Path('ml/data/interim/cleaned_data.csv')
    data = pd.read_csv(interim_path)
    
    # Create engineer with config
    config_path = Path('ml/features/feature_config.yaml')
    engineer = ConfigDrivenFeatureEngineer(config_path)
    
    # Engineer features
    features, target = engineer.build_features(data, fit=True)
    
    print('SUCCESS: Configuration-driven feature engineering works!')
    print(f'  Input: {len(data)} rows x {len(data.columns)} cols')
    print(f'  Output: {len(features)} rows x {len(features.columns)} cols')
    print(f'  Target: {len(target)} rows')
    print(f'  Features: {list(features.columns)}')
    
except Exception as e:
    print(f'ERROR: {e}')
    import traceback
    traceback.print_exc()
