# Quick Reference: Declarative Feature Engineering

## Architecture at a Glance

```
┌─────────────────────────────────────────┐
│  feature_config.yaml                    │ ← Single Source of Truth
│  • Feature lists (by type)              │
│  • Encoding strategies                  │
│  • Scaling flags                        │
│  • Quality checks                       │
│  • Monitoring rules                     │
└─────────────┬───────────────────────────┘
              │
              ↓
┌─────────────────────────────────────────┐
│  ConfigDrivenFeatureEngineer            │
│  • Reads YAML                           │
│  • Applies transformations              │
│  • Saves metadata                       │
└─────────────┬───────────────────────────┘
              │
    ┌─────────┴──────────┐
    ↓                    ↓
Input Data          Feature Metadata
  (10 cols)         • Encoders
  10,000 rows       • Scalers
                    • Feature names
    │                │
    └────────┬───────┘
             ↓
    ┌─────────────────────────────┐
    │  Output Features (18 cols)  │
    │  10,000 rows                │
    └─────────────────────────────┘
```

## Feature Groups Quick Lookup

```yaml
numeric_cyclical:        # sin/cos encoding for periodic
  - hour

numeric_spatial:         # binning for location
  - latitude
  - longitude

numeric_age:             # binning for ages
  - victim_age
  - suspect_age

categorical_low_card:    # one-hot
  - weapon_used          (with rare grouping)
  - day_of_week

categorical_high_card:   # frequency encoding
  - neighborhood

numeric_pass_through:    # no encoding
  - arrest_made

identifiers:             # drop
  - crime_id

target:                  # exclude from features
  - crime_type
```

## Output Features Reference

| # | Feature | Type | Source | How |
|---|---------|------|--------|-----|
| 1 | hour_sin | float | hour | sin(2π·hour/24) |
| 2 | hour_cos | float | hour | cos(2π·hour/24) |
| 3 | lat_bin | int | latitude | pd.cut(10 bins) |
| 4 | lon_bin | int | longitude | pd.cut(10 bins) |
| 5 | victim_age_bin | category | victim_age | binned: 0-18, 18-35, 35-50, 50-65, 65+ |
| 6 | suspect_age_bin | category | suspect_age | binned: 0-18, 18-35, 35-50, 50-65, 65+ |
| 7 | weapon_blunt object | bool | weapon_used | one-hot |
| 8 | weapon_gun | bool | weapon_used | one-hot |
| 9 | weapon_knife | bool | weapon_used | one-hot |
| 10 | weapon_unknown | bool | weapon_used | one-hot (preserved) |
| 11-17 | day_Mon through day_Sun | bool | day_of_week | one-hot |
| 18 | neighborhood_enc | float | neighborhood | frequency |

**Total: 18 features**

## Encoding Strategies Quick Reference

| Strategy | Type | Use Case | Parameters |
|----------|------|----------|------------|
| **sin_cos** | cyclical | Periodic features (hour, month) | bins (e.g., 24 for hours) |
| **one_hot** | categorical | Low cardinality | rare_threshold (0.01 = 1%) |
| **frequency** | categorical | High cardinality | method (proportion) |
| **binning** | numeric | Reduce noise, handle outliers | bins (number or edges) |
| **none** | pass-through | Already suitable | (none) |

## Configuration Template: Adding a Feature

```yaml
# 1. Choose feature group based on type
feature_groups:
  numeric_cyclical:  # For periodic numeric
    - new_feature:
        bins: 24                    # Num cycles
        encoding: sin_cos
        description: Feature description
  
  numeric_spatial:   # For location numeric
    - new_feature:
        bins: 10                    # Num regions
        encoding: binning
        description: Feature description
  
  numeric_age:       # For age numeric
    - new_feature:
        bins: [0, 18, 35, 50, 65, 150]  # Bin edges
        labels: ["Young", "Adult", ...]  # Category names
        encoding: binning
        description: Feature description
  
  categorical_low_cardinality:      # For few unique values
    - new_feature:
        encoding: one_hot
        rare_threshold: 0.01        # 1% threshold
        preserve_unknown: true      # Keep 'unknown'
        description: Feature description
  
  categorical_high_cardinality:     # For many unique values
    - new_feature:
        encoding: frequency
        description: Feature description

# 2. Add to schema contract
feature_schema_contract:
  - name: new_feature_OUTPUT_NAME
    type: (float|int|bool|category)
    source: new_feature
    transformation: (description)

# 3. Update monitoring
monitoring:
  features_expected:
    total_count: 19                 # Increment
    CATEGORY_count: X               # Increment appropriate category
```

## Workflow Decisions

```
Is it a NEW feature?
├─ YES: Add to feature_groups (choose type) + schema + monitoring
└─ NO: Is it an EXISTING feature?
   ├─ YES: Is ENCODING changing?
   │  ├─ YES: Update encoding params + schema if output changed
   │  └─ NO: Is it being REMOVED?
   │     ├─ YES: Remove from all three places
   │     └─ NO: Change PARAMETERS? (bins, threshold, etc.)
   │        └─ Just update config values
   └─ NO: Is SCALING changing?
      ├─ YES: Set scaling.enabled = true/false
      └─ NO: Is QUALITY CHECK needed?
         └─ YES: Update quality_checks section
```

## Commands Quick Reference

```bash
# Load and check YAML syntax
python -c "import yaml; yaml.safe_load(open('ml/features/feature_config.yaml')); print('✓ Valid')"

# Run feature pipeline
python ml/features/build_features.py

# Check outputs exist
ls -la ml/data/processed/
# Should show: features.csv, target.csv, feature_metadata.pkl

# Quick feature count check
python -c "import pandas as pd; f = pd.read_csv('ml/data/processed/features.csv'); print(f'Features: {len(f.columns)}, Rows: {len(f)}')"

# Inspect encoders
python -c "import pickle; m = pickle.load(open('ml/data/processed/feature_metadata.pkl', 'rb')); print(m['feature_names'])"
```

## Troubleshooting

| Issue | Check |
|-------|-------|
| YAML won't load | `python -c "import yaml; yaml.safe_load(open('feature_config.yaml'))"` |
| Feature count wrong | Verify feature_groups (all features there?), check output schema |
| Encoding not applied | Verify column name matches in data, encoding exists in encoding_strategies |
| Metadata not saved | Check output directory exists, permissions ok |
| Scaling not applied | Verify scaling.enabled = true, features in scaling.features list |

## Key Principles

1. **Single Source of Truth**: All decisions in feature_config.yaml
2. **Declarative**: Describe what (not how)
3. **Stable Code**: Change features without modifying code
4. **Auditable**: Every decision documented with rationale
5. **Maintainable**: Clear separation of config vs implementation
6. **Quality-First**: Checks and monitoring built-in
7. **Reversible**: All changes tracked in YAML (git diff)

## File Locations Reference

```
ml/
├── features/
│   ├── build_features.py           ← ConfigDrivenFeatureEngineer
│   ├── feature_config.yaml         ← All decisions (edit this!)
│   └── __pycache__/
├── data/
│   ├── interim/
│   │   └── cleaned_data.csv        ← Input (10,000 rows, 10 cols)
│   └── processed/
│       ├── features.csv            ← Output (10,000 rows, 18 cols)
│       ├── target.csv              ← Output (10,000 rows, 1 col)
│       └── feature_metadata.pkl    ← Encoders, scalers, metadata
└── EDA/
    └── 05_feature_decisions.ipynb  ← Approved decisions
```

## Data Flow: Input → Output

```
Input: cleaned_data.csv (10,000 × 10)
    crime_id                    → DROP
    crime_type                  → TARGET (separate)
    latitude, longitude         → binned (2→2)
    hour                        → sin/cos (1→2)
    victim_age, suspect_age     → binned (2→2)
    weapon_used                 → one-hot (1→4)
    day_of_week                 → one-hot (1→7)
    neighborhood                → frequency (1→1)
    arrest_made                 → pass-through (1→1)
                                ──────────────
Output: features.csv (10,000 × 18)
        target.csv (10,000 × 1)
        feature_metadata.pkl
```

## Scaling Configuration Quick Reference

```yaml
scaling:
  enabled: false                     # Set to true to enable
  method: standard                   # StandardScaler
  features:
    - hour_sin                       # Only these get scaled
    - hour_cos
    # Add more if needed
```

When enabled: features normalized to mean=0, std=1
When disabled: features as-is

## Change Management: Before/After Example

**Before change**: YAML 1.0

```yaml
feature_groups:
  categorical_low_cardinality:
    - weapon_used:
        encoding: one_hot
        rare_threshold: 0.01
```

**Change needed**: Increase rare threshold from 1% to 5%

**After change**: YAML 1.1 (only this one line changed)

```yaml
feature_groups:
  categorical_low_cardinality:
    - weapon_used:
        encoding: one_hot
        rare_threshold: 0.05           # ← Changed: 0.01 → 0.05
```

**Git diff shows**:
```
- rare_threshold: 0.01
+ rare_threshold: 0.05
```

**Track everything!** All changes visible, traceable, reversible.

---

**Ready to use?** 

```bash
python ml/features/build_features.py
```

Check your outputs:
- ✅ `ml/data/processed/features.csv` exists
- ✅ `ml/data/processed/target.csv` exists
- ✅ `ml/data/processed/feature_metadata.pkl` exists

Done! 🎉
