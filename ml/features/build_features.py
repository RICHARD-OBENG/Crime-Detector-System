"""
Feature Engineering Pipeline - Crime Detector System
Transforms validated data into model-ready features for ML models

Key Functions:
1. Encode time/location patterns
2. Bin geocoordinates 
3. Produce training tables
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple, List, Optional
from datetime import datetime, timedelta
import logging
from pathlib import Path
import yaml

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TimePatternEncoder:
    """
    Encode temporal patterns for crime data
    - Hour of day (0-23)
    - Day of week (0-6, Monday=0)
    - Month of year (1-12)
    - Season (Winter, Spring, Summer, Fall)
    - Is weekend (0/1)
    - Time of day categories (morning, afternoon, evening, night)
    """
    
    def __init__(self):
        self.time_bins = {
            'night': (0, 6),      # 00:00-06:00
            'morning': (6, 12),   # 06:00-12:00
            'afternoon': (12, 18),# 12:00-18:00
            'evening': (18, 24)   # 18:00-00:00
        }
        
        self.seasons = {
            12: 'Winter', 1: 'Winter', 2: 'Winter',
            3: 'Spring', 4: 'Spring', 5: 'Spring',
            6: 'Summer', 7: 'Summer', 8: 'Summer',
            9: 'Fall', 10: 'Fall', 11: 'Fall'
        }
    
    def encode(self, timestamp: datetime) -> Dict:
        """
        Encode temporal features from timestamp
        
        Args:
            timestamp: Datetime object
            
        Returns:
            Dictionary of temporal features
        """
        hour = timestamp.hour
        day_of_week = timestamp.weekday()
        month = timestamp.month
        day = timestamp.day
        
        # Determine time of day category
        time_of_day = 'night'
        for period, (start, end) in self.time_bins.items():
            if start <= hour < end:
                time_of_day = period
                break
        
        # Determine if weekend
        is_weekend = 1 if day_of_week >= 5 else 0
        
        # Get season
        season = self.seasons.get(month, 'Unknown')
        
        return {
            'hour_of_day': hour,
            'day_of_week': day_of_week,
            'day_of_month': day,
            'month': month,
            'season': season,
            'is_weekend': is_weekend,
            'time_of_day': time_of_day,
            'is_business_hours': 1 if 9 <= hour < 17 and is_weekend == 0 else 0,
            'day_name': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][day_of_week]
        }


class LocationPatternEncoder:
    """
    Encode spatial patterns and bin geocoordinates
    - Latitude/longitude binning (grid cells)
    - Geocoordinate clustering
    - Proximity features
    - Administrative region encoding
    """
    
    def __init__(self, lat_bins: int = 20, lon_bins: int = 20):
        """
        Initialize location encoder with grid parameters
        
        Args:
            lat_bins: Number of latitude bins (default: 20)
            lon_bins: Number of longitude bins (default: 20)
        """
        self.lat_bins = lat_bins
        self.lon_bins = lon_bins
        self.lat_edges = None
        self.lon_edges = None
    
    def fit(self, latitudes: np.ndarray, longitudes: np.ndarray):
        """
        Fit binning edges based on data distribution
        
        Args:
            latitudes: Array of latitude values
            longitudes: Array of longitude values
        """
        # Create quantile-based bins for better distribution
        self.lat_edges = np.quantile(latitudes, np.linspace(0, 1, self.lat_bins + 1))
        self.lon_edges = np.quantile(longitudes, np.linspace(0, 1, self.lon_bins + 1))
        
        logger.info(f"Location encoder fitted with {self.lat_bins}x{self.lon_bins} grid")
    
    def bin_coordinates(self, lat: float, lon: float) -> Tuple[int, int, str]:
        """
        Bin geocoordinates into grid cells
        
        Args:
            lat: Latitude value
            lon: Longitude value
            
        Returns:
            Tuple of (lat_bin, lon_bin, grid_id)
        """
        if self.lat_edges is None or self.lon_edges is None:
            raise ValueError("Encoder not fitted. Call fit() first.")
        
        lat_bin = np.digitize(lat, self.lat_edges) - 1
        lon_bin = np.digitize(lon, self.lon_edges) - 1
        
        # Ensure bins are within valid range
        lat_bin = np.clip(lat_bin, 0, self.lat_bins - 1)
        lon_bin = np.clip(lon_bin, 0, self.lon_bins - 1)
        
        grid_id = f"GRID_{lat_bin}_{lon_bin}"
        
        return lat_bin, lon_bin, grid_id
    
    def encode(self, lat: float, lon: float, 
               admin_region: Optional[str] = None) -> Dict:
        """
        Encode location features
        
        Args:
            lat: Latitude
            lon: Longitude
            admin_region: Administrative region (e.g., precinct, district)
            
        Returns:
            Dictionary of location features
        """
        lat_bin, lon_bin, grid_id = self.bin_coordinates(lat, lon)
        
        return {
            'latitude': lat,
            'longitude': lon,
            'lat_bin': lat_bin,
            'lon_bin': lon_bin,
            'grid_id': grid_id,
            'admin_region': admin_region or 'Unknown',
            'grid_cell': f"{lat_bin}_{lon_bin}"
        }


class FeatureBuilder:
    """
    Main feature engineering pipeline
    Combines temporal and spatial features to produce training-ready tables
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize feature builder
        
        Args:
            config_path: Path to feature configuration YAML file
        """
        self.time_encoder = TimePatternEncoder()
        self.location_encoder = LocationPatternEncoder()
        self.config = self._load_config(config_path)
    
    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Load feature configuration from YAML"""
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        
        return {
            'lat_bins': 20,
            'lon_bins': 20,
            'normalize_features': True,
            'handle_missing': 'mean'
        }
    
    def fit_location_encoder(self, data: pd.DataFrame, 
                            lat_col: str = 'latitude', 
                            lon_col: str = 'longitude'):
        """
        Fit location encoder on data
        
        Args:
            data: DataFrame with crime data
            lat_col: Latitude column name
            lon_col: Longitude column name
        """
        latitudes = data[lat_col].values
        longitudes = data[lon_col].values
        
        self.location_encoder.fit(latitudes, longitudes)
    
    def build_temporal_features(self, df: pd.DataFrame, 
                               timestamp_col: str = 'occurred_at') -> pd.DataFrame:
        """
        Build temporal features
        
        Args:
            df: DataFrame with crime incidents
            timestamp_col: Column name containing timestamps
            
        Returns:
            DataFrame with temporal features added
        """
        logger.info("Building temporal features...")
        
        temporal_features = []
        
        for idx, timestamp in enumerate(pd.to_datetime(df[timestamp_col])):
            features = self.time_encoder.encode(timestamp)
            temporal_features.append(features)
        
        temporal_df = pd.DataFrame(temporal_features)
        
        return pd.concat([df, temporal_df], axis=1)
    
    def build_spatial_features(self, df: pd.DataFrame,
                              lat_col: str = 'latitude',
                              lon_col: str = 'longitude',
                              region_col: Optional[str] = None) -> pd.DataFrame:
        """
        Build spatial features with binned geocoordinates
        
        Args:
            df: DataFrame with crime incidents
            lat_col: Latitude column name
            lon_col: Longitude column name
            region_col: Optional administrative region column
            
        Returns:
            DataFrame with spatial features added
        """
        logger.info("Building spatial features...")
        
        spatial_features = []
        
        for idx, row in df.iterrows():
            region = row[region_col] if region_col and region_col in df.columns else None
            features = self.location_encoder.encode(
                row[lat_col], 
                row[lon_col], 
                admin_region=region
            )
            spatial_features.append(features)
        
        spatial_df = pd.DataFrame(spatial_features)
        
        return pd.concat([df, spatial_df], axis=1)
    
    def build_interaction_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Build interaction features (time × location patterns)
        
        Args:
            df: DataFrame with temporal and spatial features
            
        Returns:
            DataFrame with interaction features
        """
        logger.info("Building interaction features...")
        
        # Create time-location interaction features
        if 'grid_id' in df.columns and 'time_of_day' in df.columns:
            df['grid_time_pattern'] = df['grid_id'] + '_' + df['time_of_day']
        
        if 'day_of_week' in df.columns and 'admin_region' in df.columns:
            df['region_day_pattern'] = df['admin_region'] + '_' + df['day_of_week'].astype(str)
        
        if 'hour_of_day' in df.columns and 'grid_id' in df.columns:
            df['grid_hour_pattern'] = df['grid_id'] + '_' + df['hour_of_day'].astype(str)
        
        return df
    
    def build_training_table(self, data: pd.DataFrame,
                            timestamp_col: str = 'occurred_at',
                            lat_col: str = 'latitude',
                            lon_col: str = 'longitude',
                            region_col: Optional[str] = None,
                            target_col: Optional[str] = None) -> pd.DataFrame:
        """
        Build complete training table with all features
        
        Args:
            data: Raw validated data
            timestamp_col: Timestamp column name
            lat_col: Latitude column name
            lon_col: Longitude column name
            region_col: Administrative region column name
            target_col: Target variable column name (e.g., crime_type)
            
        Returns:
            Complete feature-engineered training table
        """
        logger.info(f"Building training table from {len(data)} records...")
        
        # Step 1: Fit location encoder
        self.fit_location_encoder(data, lat_col, lon_col)
        
        # Step 2: Build temporal features
        df = self.build_temporal_features(data, timestamp_col)
        
        # Step 3: Build spatial features
        df = self.build_spatial_features(df, lat_col, lon_col, region_col)
        
        # Step 4: Build interaction features
        df = self.build_interaction_features(df)
        
        # Step 5: Handle missing values
        df = self._handle_missing_values(df)
        
        # Step 6: Normalize numerical features
        if self.config.get('normalize_features', True):
            df = self._normalize_features(df)
        
        logger.info(f"Training table built with {len(df.columns)} features")
        
        return df
    
    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle missing values in features"""
        strategy = self.config.get('handle_missing', 'mean')
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        if strategy == 'mean':
            df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].mean())
        elif strategy == 'median':
            df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())
        elif strategy == 'drop':
            df = df.dropna(subset=numeric_cols)
        
        return df
    
    def _normalize_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize numerical features to [0, 1] range"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            if col in ['hour_of_day', 'day_of_week', 'day_of_month', 'month', 
                      'lat_bin', 'lon_bin', 'is_weekend', 'is_business_hours']:
                # Skip already categorical/bounded features
                continue
            
            min_val = df[col].min()
            max_val = df[col].max()
            
            if max_val > min_val:
                df[col] = (df[col] - min_val) / (max_val - min_val)
        
        return df
    
    def build_model_datasets(self, training_table: pd.DataFrame,
                            test_size: float = 0.2,
                            random_state: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Split training table into train/test sets
        
        Args:
            training_table: Complete feature-engineered table
            test_size: Proportion for test set (default: 0.2)
            random_state: Random seed for reproducibility
            
        Returns:
            Tuple of (train_df, test_df)
        """
        from sklearn.model_selection import train_test_split
        
        train_df, test_df = train_test_split(
            training_table,
            test_size=test_size,
            random_state=random_state
        )
        
        logger.info(f"Train set: {len(train_df)} records | Test set: {len(test_df)} records")
        
        return train_df, test_df


# Example usage
if __name__ == "__main__":
    # Initialize feature builder
    feature_builder = FeatureBuilder(config_path="feature_config.yaml")
    
    # Example: Load validated data
    # data = pd.read_csv("data/processed/validated_incidents.csv")
    
    # Build training table
    # training_table = feature_builder.build_training_table(
    #     data,
    #     timestamp_col='occurred_at',
    #     lat_col='latitude',
    #     lon_col='longitude',
    #     region_col='precinct',
    #     target_col='crime_type'
    # )
    
    # Split into train/test
    # train_df, test_df = feature_builder.build_model_datasets(training_table)
    
    # Save
    # training_table.to_csv("data/processed/training_table.csv", index=False)
    # train_df.to_csv("data/processed/train_set.csv", index=False)
    # test_df.to_csv("data/processed/test_set.csv", index=False)
    
    print("Feature engineering pipeline ready!")
