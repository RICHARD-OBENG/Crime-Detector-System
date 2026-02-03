#!/usr/bin/env python
"""Run full feature engineering pipeline and save output."""

import sys
import logging
sys.path.insert(0, 'ml')

logging.basicConfig(level=logging.INFO, format='%(message)s')

from features.build_features import main

# Execute pipeline
features, target = main()
print(f'\n✓ Pipeline complete!')
print(f'Saved features: {len(features)} rows x {len(features.columns)} cols')
print(f'Saved target: {len(target)} rows')
