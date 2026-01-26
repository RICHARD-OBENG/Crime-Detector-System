# pipelines/data_pipeline.py
"""
Data Pipeline Orchestration

Purpose: Orchestrate the complete data flow from raw → cleaned

Flow:
  1. Load raw data (ml/data/raw/)
  2. Apply cleaning/validation (data quality checks)
  3. Save cleaned data (ml/data/interim/cleaned_data.csv)

Cleaning steps (from EDA/01_schema_and_quality.ipynb):
  - Handle missing values
  - Remove duplicates
  - Validate data types
  - Remove outliers/invalid records
  - Standardize formatting
"""

import logging
import pandas as pd
from pathlib import Path
from typing import Tuple

logger = logging.getLogger(__name__)


class DataPipeline:
    """Orchestrate raw data → cleaned data pipeline."""

    def __init__(self, raw_dir: str, interim_dir: str):
        """
        Initialize pipeline with data directories.

        Args:
            raw_dir: Directory containing raw data
            interim_dir: Directory to save cleaned data
        """
        self.raw_dir = Path(raw_dir)
        self.interim_dir = Path(interim_dir)
        self.interim_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Data pipeline initialized")
        logger.info(f"  Raw data dir: {self.raw_dir}")
        logger.info(f"  Interim output dir: {self.interim_dir}")

    def load_raw_data(self) -> pd.DataFrame:
        """
        Load raw data from raw data directory.

        Returns:
            DataFrame with raw data
        """
        # Find raw data file (CSV)
        raw_files = list(self.raw_dir.glob("*.csv"))
        
        if not raw_files:
            raise FileNotFoundError(f"No CSV files found in {self.raw_dir}")
        
        raw_file = raw_files[0]  # Take first CSV found
        logger.info(f"Loading raw data from {raw_file}")
        
        df = pd.read_csv(raw_file)
        logger.info(f"✓ Loaded {len(df)} records with {len(df.columns)} columns")
        logger.info(f"  Columns: {df.columns.tolist()}")
        
        return df

    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply data cleaning and validation.

        Cleaning steps (from EDA/01_schema_and_quality.ipynb):
        - Remove duplicates
        - Handle missing values
        - Validate data types
        - Remove invalid records
        - Standardize formatting

        Args:
            df: Raw DataFrame

        Returns:
            Cleaned DataFrame
        """
        df = df.copy()
        initial_rows = len(df)

        # Step 1: Remove duplicates
        before_dedup = len(df)
        df = df.drop_duplicates()
        duplicates_removed = before_dedup - len(df)
        if duplicates_removed > 0:
            logger.info(f"✓ Removed {duplicates_removed} duplicate rows")

        # Step 2: Handle missing values
        logger.info("Checking for missing values...")
        missing_counts = df.isnull().sum()
        if missing_counts.sum() > 0:
            logger.info(f"  Found missing values:")
            for col, count in missing_counts[missing_counts > 0].items():
                logger.info(f"    {col}: {count} ({100*count/len(df):.1f}%)")
            
            # Drop rows with missing values in critical columns
            critical_cols = [col for col in df.columns if col not in ['neighborhood']]
            df = df.dropna(subset=critical_cols)
            logger.info(f"✓ Removed rows with missing critical values")

        # Step 3: Validate data types
        logger.info("Validating data types...")
        
        # Numeric columns
        numeric_cols = ['crime_id', 'hour', 'latitude', 'longitude', 'victim_age', 'suspect_age']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Categorical columns
        categorical_cols = ['crime_type', 'weapon_used', 'day_of_week']
        for col in categorical_cols:
            if col in df.columns:
                df[col] = df[col].astype('category')
        
        # Binary columns
        if 'arrest_made' in df.columns:
            df['arrest_made'] = df['arrest_made'].astype('int')
        
        logger.info(f"✓ Data types validated")

        # Step 4: Remove invalid records (null after coercion)
        before_invalid = len(df)
        df = df.dropna()
        invalid_removed = before_invalid - len(df)
        if invalid_removed > 0:
            logger.info(f"✓ Removed {invalid_removed} invalid records")

        # Step 5: Validate value ranges
        logger.info("Validating value ranges...")
        
        # Hour should be 0-23
        if 'hour' in df.columns:
            invalid_hour = ((df['hour'] < 0) | (df['hour'] > 23)).sum()
            if invalid_hour > 0:
                df = df[(df['hour'] >= 0) & (df['hour'] <= 23)]
                logger.info(f"✓ Removed {invalid_hour} records with invalid hour")
        
        # Age should be positive
        for age_col in ['victim_age', 'suspect_age']:
            if age_col in df.columns:
                invalid_age = (df[age_col] < 0).sum()
                if invalid_age > 0:
                    df = df[df[age_col] >= 0]
                    logger.info(f"✓ Removed {invalid_age} records with invalid {age_col}")
        
        # Lat/lon should be reasonable ranges
        if 'latitude' in df.columns:
            df = df[(df['latitude'] >= -90) & (df['latitude'] <= 90)]
        if 'longitude' in df.columns:
            df = df[(df['longitude'] >= -180) & (df['longitude'] <= 180)]

        # Step 6: Standardize formatting
        logger.info("Standardizing formatting...")
        
        # Lowercase categorical columns
        for col in categorical_cols:
            if col in df.columns:
                df[col] = df[col].str.lower().str.strip()
        
        if 'weapon_used' in df.columns:
            df['weapon_used'] = df['weapon_used'].str.lower().str.strip()
        
        logger.info(f"✓ Formatting standardized")

        # Summary
        rows_removed = initial_rows - len(df)
        rows_retained = len(df)
        pct_retained = 100 * rows_retained / initial_rows
        
        logger.info(f"\nCleaning Summary:")
        logger.info(f"  Initial rows: {initial_rows}")
        logger.info(f"  Rows removed: {rows_removed}")
        logger.info(f"  Rows retained: {rows_retained} ({pct_retained:.1f}%)")
        logger.info(f"  Final columns: {len(df.columns)}")

        return df

    def validate_cleaned_data(self, df: pd.DataFrame) -> bool:
        """
        Validate cleaned data quality.

        Args:
            df: Cleaned DataFrame

        Returns:
            True if valid, raises exception otherwise
        """
        logger.info("Validating cleaned data...")
        
        # Check no missing values
        missing = df.isnull().sum().sum()
        assert missing == 0, f"Cleaned data contains {missing} missing values"
        
        # Check required columns
        required_cols = ['crime_id', 'crime_type', 'hour', 'latitude', 'longitude',
                        'victim_age', 'suspect_age', 'weapon_used', 'day_of_week', 'arrest_made']
        for col in required_cols:
            assert col in df.columns, f"Missing required column: {col}"
        
        # Check data types
        assert df['crime_id'].dtype in ['int64', 'int32'], "crime_id should be numeric"
        assert df['hour'].dtype in ['int64', 'int32', 'float64'], "hour should be numeric"
        assert df['arrest_made'].dtype in ['int64', 'int32'], "arrest_made should be numeric"
        
        # Check value ranges
        assert (df['hour'] >= 0).all() and (df['hour'] <= 23).all(), "hour out of range [0-23]"
        assert (df['victim_age'] >= 0).all(), "victim_age should be non-negative"
        assert (df['suspect_age'] >= 0).all(), "suspect_age should be non-negative"
        
        logger.info(f"✓ Data validation passed")
        return True

    def save_cleaned_data(self, df: pd.DataFrame, filename: str = "cleaned_data.csv") -> Path:
        """
        Save cleaned data to interim directory.

        Args:
            df: Cleaned DataFrame
            filename: Output filename

        Returns:
            Path to saved file
        """
        output_path = self.interim_dir / filename
        
        logger.info(f"Saving cleaned data to {output_path}")
        df.to_csv(output_path, index=False)
        
        logger.info(f"✓ Saved {len(df)} records to {output_path}")
        return output_path

    def run(self) -> Tuple[pd.DataFrame, Path]:
        """
        Execute complete data pipeline.

        Steps:
          1. Load raw data
          2. Clean and validate
          3. Save to interim

        Returns:
            Tuple of (cleaned DataFrame, output path)
        """
        logger.info("=" * 60)
        logger.info("STARTING DATA PIPELINE")
        logger.info("=" * 60)
        
        # Load
        df = self.load_raw_data()
        
        # Clean
        df = self.clean_data(df)
        
        # Validate
        self.validate_cleaned_data(df)
        
        # Save
        output_path = self.save_cleaned_data(df)
        
        logger.info("=" * 60)
        logger.info("DATA PIPELINE COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)
        
        return df, output_path


def main():
    """Execute data pipeline from command line."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s'
    )
    
    # Setup paths
    project_root = Path(__file__).parent.parent
    raw_dir = project_root / "data" / "raw"
    interim_dir = project_root / "data" / "interim"
    
    # Check raw data exists
    if not raw_dir.exists() or not list(raw_dir.glob("*.csv")):
        logger.error(f"Raw data not found in {raw_dir}")
        raise FileNotFoundError(f"No CSV files in {raw_dir}")
    
    # Run pipeline
    pipeline = DataPipeline(raw_dir, interim_dir)
    df_cleaned, output_path = pipeline.run()
    
    logger.info(f"\nOutput: {output_path}")


if __name__ == "__main__":
    main()
