# Practical Examples: Modifying Feature Configuration

## Example 1: Adding a New Feature

**Scenario**: Add a new feature `crime_severity` (numeric, requires binning)

**Steps**:

1. **Add to feature_config.yaml** under `feature_groups`:

```yaml
feature_groups:
  # ... existing groups ...
  
  numeric_crime_severity:  # New group
    - crime_severity:
        bins: [0, 2, 5, 8, 10]
        labels: ["Low", "Medium", "High", "Critical"]
        encoding: binning
        description: Crime severity score
```

2. **Add to feature_schema_contract**:

```yaml
feature_schema_contract:
  # ... existing features ...
  
  - name: crime_severity_bin
    type: category
    source: crime_severity
    transformation: binning ([Low, Medium, High, Critical])
```

3. **Update monitoring expectations**:

```yaml
monitoring:
  features_expected:
    total_count: 19  # Was 18, now 19
    binned_count: 5  # Was 4, now 5
```

4. **Run pipeline**:

```bash
python ml/features/build_features.py
```

**Result**: New feature automatically engineered, no code changes needed.

---

## Example 2: Changing Encoding Strategy

**Scenario**: Change `day_of_week` from one-hot to label encoding

**Steps**:

1. **Create new encoding strategy** in feature_config.yaml:

```yaml
encoding_strategies:
  # ... existing ...
  
  label:
    type: categorical
    method: ordinal
    description: Label encoding for ordinal categoricals
    rationale: Reduces dimensionality while preserving order
```

2. **Update feature definition**:

```yaml
categorical_ordinal:  # New group
  - day_of_week:
      encoding: label
      order: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
      description: Day of week
```

3. **Remove from old group**:

```yaml
categorical_low_cardinality:
  - weapon_used:  # Keep this
      ...
  # Remove day_of_week from here
```

4. **Update schema contract and monitoring**:

```yaml
feature_schema_contract:
  # Replace one-hot day features with:
  - name: day_of_week_enc
    type: int
    source: day_of_week
    transformation: label encoding

monitoring:
  features_expected:
    total_count: 8  # Was 18 (7 day one-hot + rest), now 8 (1 encoded + rest)
    one_hot_count: 4  # Was 11, now 4 (weapon only)
    ordinal_count: 1  # New
```

5. **Implement handler in code** (if needed):

```python
# In ConfigDrivenFeatureEngineer._apply_categorical_ordinal()
def _apply_categorical_ordinal(self, df, fit=True):
    features = self.config.get('feature_groups', {}).get('categorical_ordinal', [])
    for feature_dict in features:
        for feature_name, config in feature_dict.items():
            if feature_name not in df.columns:
                continue
            order = config.get('order')
            df[f'{feature_name}_enc'] = pd.Categorical(
                df[feature_name], 
                categories=order, 
                ordered=True
            ).codes
            df = df.drop(columns=[feature_name])
    return df
```

6. **Call in build_features()**:

```python
df = self._apply_categorical_ordinal(df, fit=fit)
```

**Result**: Encoding strategy changed, feature count reduced, no hardcoded changes.

---

## Example 3: Enabling Scaling

**Scenario**: Enable StandardScaler for numeric features

**Steps**:

1. **Update scaling config**:

```yaml
scaling:
  enabled: true  # Was false
  method: standard
  features:
    - hour_sin
    - hour_cos
    - lat_bin
    - lon_bin
    - neighborhood_enc
```

2. **Run pipeline**:

```bash
python ml/features/build_features.py
```

**Result**: Features scaled after encoding, scaler saved to metadata.pkl for inference.

---

## Example 4: Grouping Rare Categories More Aggressively

**Scenario**: Increase rare weapon grouping from 1% to 5%

**Steps**:

1. **Update rare_threshold**:

```yaml
categorical_low_cardinality:
  - weapon_used:
      encoding: one_hot
      rare_threshold: 0.05  # Was 0.01 (1%), now 0.05 (5%)
      preserve_unknown: true
```

2. **Run pipeline**:

```bash
python ml/features/build_features.py
```

**Result**: More weapons grouped as 'other', sparser output, no code changes.

---

## Example 5: Adding Bias Mitigation

**Scenario**: Document new bias mitigation for a feature

**Steps**:

1. **Update quality_checks**:

```yaml
quality_checks:
  bias_mitigation:
    # ... existing ...
    - "Day of week one-hot encoding checked for weekend/weekday bias"
    - "Weapon 'unknown' preserved to avoid systematic bias toward certain demographics"
```

2. **Document in schema**:

```yaml
feature_schema_contract:
  # ... existing ...
  
  - name: weapon_unknown
    type: bool
    source: weapon_used
    transformation: one-hot (preserved)
    bias_note: "Preserved to prevent losing information about unknown weapons"
```

**Result**: Bias considerations documented, audit trail maintained.

---

## Example 6: Disabling a Feature

**Scenario**: Remove latitude/longitude binning (use raw coordinates instead)

**Steps**:

1. **Move to pass-through**:

```yaml
feature_groups:
  # Remove from numeric_spatial:
  # - latitude
  # - longitude
  
  numeric_pass_through:
    - latitude:
        encoding: none
        description: Raw latitude coordinate
    - longitude:
        encoding: none
        description: Raw longitude coordinate
    - arrest_made:  # Keep existing
        ...
```

2. **Update schema**:

```yaml
feature_schema_contract:
  # Remove lat_bin, lon_bin
  # Add:
  - name: latitude
    type: float
    source: latitude
    transformation: none (raw)
  
  - name: longitude
    type: float
    source: longitude
    transformation: none (raw)
```

3. **Update monitoring**:

```yaml
monitoring:
  features_expected:
    total_count: 20  # Was 18 (+2 for raw lat/lon)
    binned_count: 4  # Was 4, stays same (no lat/lon bins)
```

4. **Run pipeline**:

```bash
python ml/features/build_features.py
```

**Result**: Features changed, code unchanged.

---

## Example 7: Validating Configuration

**Check if configuration is valid**:

```python
import yaml

with open('ml/features/feature_config.yaml') as f:
    config = yaml.safe_load(f)

# Verify structure
assert 'feature_groups' in config
assert 'encoding_strategies' in config
assert 'scaling' in config
assert 'feature_schema_contract' in config
assert 'monitoring' in config

# Count features
features_expected = config['monitoring']['features_expected']['total_count']
print(f"Expected {features_expected} features after engineering")

# Verify all referenced encodings exist
for group, features in config['feature_groups'].items():
    for feature in features:
        if isinstance(feature, dict):
            for name, cfg in feature.items():
                encoding = cfg.get('encoding')
                if encoding not in ['none']:
                    assert encoding in config['encoding_strategies'], \
                        f"Unknown encoding: {encoding}"

print("✓ Configuration valid!")
```

---

## Workflow Summary

### To Change Features:

| Change | Steps |
|--------|-------|
| **Add feature** | Add to feature_groups + schema_contract + monitoring |
| **Remove feature** | Remove from all three + update counts |
| **Change encoding** | Update feature config + schema + add handler if needed |
| **Change parameters** | Update encoding config (bins, threshold, etc.) |
| **Enable/disable scaling** | Set `scaling.enabled: true/false` |
| **Add bias mitigation** | Document in quality_checks + schema_contract |

### To Validate:

```bash
# Check YAML syntax
python -c "import yaml; yaml.safe_load(open('ml/features/feature_config.yaml'))"

# Run feature pipeline
python ml/features/build_features.py

# Verify outputs exist
ls -la ml/data/processed/
# Should show: features.csv, target.csv, feature_metadata.pkl
```

### Version Control:

```bash
# Track all feature changes via YAML
git diff ml/features/feature_config.yaml

# Shows exactly what changed: features, encodings, parameters, bias notes
```

**Key benefit**: All changes visible and traceable in one YAML file. Code never changes.
