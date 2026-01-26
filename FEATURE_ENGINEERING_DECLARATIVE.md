# Feature Engineering: Declarative Configuration

## Overview

The feature engineering pipeline is now **configuration-driven** and **declarative**. This means:

1. **Code is stable**: Feature engineering logic doesn't change when features change
2. **Single source of truth**: All feature decisions are in `feature_config.yaml`
3. **Auditable**: Every feature is declared with encoding strategy, bins, and rationale
4. **Maintainable**: Adding/removing features requires only YAML changes

## Architecture

```
feature_config.yaml (declarative control)
        ↓
build_features.py (reads config, applies transformations)
        ↓
data/interim/cleaned_data.csv (input)
        ↓
data/processed/features.csv (output)
```

## Configuration Structure

### 1. Feature Groups (Feature Lists)

Organized by type and transformation strategy:

```yaml
feature_groups:
  identifiers:           # Drop these
    - crime_id
  
  target:               # Exclude from features
    - crime_type
  
  numeric_cyclical:     # sin/cos encoding
    - hour: {bins: 24, encoding: sin_cos}
  
  numeric_spatial:      # Spatial binning
    - latitude: {bins: 10, encoding: binning}
    - longitude: {bins: 10, encoding: binning}
  
  numeric_age:          # Age binning
    - victim_age: {bins: [0, 18, 35, 50, 65, 150], ...}
    - suspect_age: {bins: [0, 18, 35, 50, 65, 150], ...}
  
  categorical_low_cardinality:   # One-hot
    - weapon_used: {rare_threshold: 0.01, preserve_unknown: true}
    - day_of_week: {encoding: one_hot}
  
  categorical_high_cardinality:  # Frequency encoding
    - neighborhood: {encoding: frequency}
  
  numeric_pass_through:  # No transformation
    - arrest_made: {encoding: none}
```

### 2. Encoding Strategies

Defines parameters for each encoding type:

```yaml
encoding_strategies:
  sin_cos:
    type: cyclical
    components: [sin, cos]
    description: Cyclical sin/cos encoding for periodic features
  
  one_hot:
    type: categorical
    sparse: false
    drop_first: false
  
  frequency:
    type: categorical
    method: proportion
  
  binning:
    type: numeric
    method: pd.cut
  
  none:
    type: pass_through
```

### 3. Scaling Configuration

Optional StandardScaler for post-encoding:

```yaml
scaling:
  enabled: false
  method: standard
  features:  # Empty when disabled
    - hour_sin
    - hour_cos
```

### 4. Output Schema Contract

Documents expected output features:

```yaml
feature_schema_contract:
  - name: hour_sin
    type: float
    source: hour
    transformation: sin_cos encoding
  
  - name: lat_bin
    type: int
    source: latitude
    transformation: binning (10 bins)
  
  # ... etc
```

### 5. Quality Assurance & Monitoring

Quality checks and monitoring configuration:

```yaml
quality_checks:
  leakage_prevention:
    - No feature derived from target variable
    - No post-outcome attributes included
  
  stability:
    - Rare weapon types grouped to avoid sparsity
  
  bias_mitigation:
    - Age features binned to reduce individual-level impact
    - Geographic features binned to reduce spatial proxy bias

monitoring:
  features_expected:
    total_count: 18
    cyclical_count: 2
    binned_count: 4
    one_hot_count: 11
    frequency_encoded_count: 1
```

## Code: Configuration-Driven Engineer

The `ConfigDrivenFeatureEngineer` class reads configuration and applies transformations:

```python
# Initialize with config
engineer = ConfigDrivenFeatureEngineer('ml/features/feature_config.yaml')

# Build features (reads config, applies transformations)
features, target = engineer.build_features(crime_data, fit=True)

# Each feature group is processed by dedicated method:
engineer._apply_cyclical_encoding()        # hour → hour_sin, hour_cos
engineer._apply_spatial_binning()          # lat/lon → binned
engineer._apply_age_binning()              # ages → age bins
engineer._apply_categorical_low_card()     # one-hot with rare grouping
engineer._apply_categorical_high_card()    # frequency encoding
engineer._apply_pass_through()             # keep as-is
engineer._apply_scaling()                  # optional StandardScaler
```

## Benefits

### Stability
- **Change features without touching code**: Add/remove features only in YAML
- **Backward compatible**: Old code still works with new configurations
- **Version control**: Track feature changes via YAML diffs

### Auditability
- **Single source of truth**: All decisions documented in one place
- **Traceability**: Each feature has rationale, bins, encoding strategy
- **Reproducibility**: Same config = same transformations

### Maintainability
- **Declarative**: What to do (not how)
- **Flexible**: Add encoding types without modifying core code
- **Testable**: Validate config independently of logic

### Governance
- **Approval control**: Config version tied to notebook approval
- **Change management**: Rules for adding/modifying features
- **Monitoring**: Expected feature counts and distributions

## Workflow

### To Add a Feature:

1. Approve in `EDA/05_feature_decisions.ipynb`
2. Add to `feature_config.yaml` with:
   - Feature name
   - Feature group (type)
   - Encoding strategy
   - Transformation parameters
3. Add to `feature_schema_contract` describing output
4. Update `monitoring.features_expected` counts
5. Run pipeline: `python ml/features/build_features.py`

### To Change Encoding:

1. Update encoding parameters in `feature_config.yaml`
2. No code changes needed
3. Run pipeline
4. Validate via monitoring config

### To Remove a Feature:

1. Remove from feature group
2. Remove from schema contract
3. Update monitoring counts
4. Run pipeline

## Data Flow

```
ml/data/interim/cleaned_data.csv (input)
  ├─ 10,000 rows
  ├─ 10 columns: crime_id, crime_type, latitude, longitude, hour, 
  │              day_of_week, victim_age, suspect_age, weapon_used, 
  │              arrest_made
  
  → [ConfigDrivenFeatureEngineer reads feature_config.yaml]
  
  → ml/data/processed/features.csv (output)
    ├─ 10,000 rows
    ├─ 18 columns (engineered)
    ├─ Excludes: crime_id (identifier), crime_type (target)
  
  → ml/data/processed/target.csv (output)
    ├─ 10,000 rows
    ├─ 1 column: crime_type
  
  → ml/data/processed/feature_metadata.pkl (output)
    ├─ Feature names
    ├─ Label encoders (for inference)
    ├─ Scalers (for inference)
    ├─ Config version
```

## Output Features (18 total)

| Feature | Type | Source | Encoding |
|---------|------|--------|----------|
| hour_sin | float | hour | sin component |
| hour_cos | float | hour | cos component |
| lat_bin | int | latitude | binned (10 bins) |
| lon_bin | int | longitude | binned (10 bins) |
| victim_age_bin | category | victim_age | binned (5 bins) |
| suspect_age_bin | category | suspect_age | binned (5 bins) |
| weapon_blunt object | bool | weapon_used | one-hot |
| weapon_gun | bool | weapon_used | one-hot |
| weapon_knife | bool | weapon_used | one-hot |
| weapon_unknown | bool | weapon_used | one-hot (preserved) |
| day_Mon | bool | day_of_week | one-hot |
| day_Tue | bool | day_of_week | one-hot |
| day_Wed | bool | day_of_week | one-hot |
| day_Thu | bool | day_of_week | one-hot |
| day_Fri | bool | day_of_week | one-hot |
| day_Sat | bool | day_of_week | one-hot |
| day_Sun | bool | day_of_week | one-hot |
| neighborhood_enc | float | neighborhood | frequency encoding |

**Note**: `arrest_made` is passed through as-is (not in feature decisions)

## Testing & Validation

Run the feature pipeline:

```bash
python ml/features/build_features.py
```

Outputs:
- `ml/data/processed/features.csv` ✓
- `ml/data/processed/target.csv` ✓
- `ml/data/processed/feature_metadata.pkl` ✓

## Change Control

Any deviation requires:
1. Notebook re-approval (EDA/05_feature_decisions.ipynb)
2. Config version update
3. Monitoring expectations update
4. Documentation update (this file)
