"""
Feature Extractor - Extract behavioral features from device activity.
"""

import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import Counter
import logging

from app.utils.logger import get_logger

logger = get_logger(__name__)


class FeatureExtractor:
    """Extract features from device behavior for ML models."""
    
    FEATURE_NAMES = [
        'connection_count',
        'avg_session_duration',
        'std_session_duration',
        'unique_ips',
        'ip_change_frequency',
        'avg_rssi',
        'rssi_variance',
        'hour_entropy',
        'day_of_week_entropy',
        'connection_regularity',
        'time_since_first_seen',
        'avg_response_time',
        'offline_frequency',
        'is_trusted',
        'vendor_known'
    ]
    
    def __init__(self):
        self.feature_stats = {}
    
    def extract_features(
        self,
        scan_results: List[Dict],
        activities: List[Dict],
        device_info: Dict
    ) -> np.ndarray:
        """
        Extract feature vector from device data.
        
        Args:
            scan_results: List of scan results for the device
            activities: List of device activities
            device_info: Device metadata
            
        Returns:
            Feature vector as numpy array
        """
        features = {}
        
        features['connection_count'] = len(scan_results)
        
        session_durations = self._calculate_session_durations(activities)
        features['avg_session_duration'] = np.mean(session_durations) if session_durations else 0
        features['std_session_duration'] = np.std(session_durations) if len(session_durations) > 1 else 0
        
        unique_ips = set(sr.get('ip_address') for sr in scan_results if sr.get('ip_address'))
        features['unique_ips'] = len(unique_ips)
        
        ip_changes = sum(1 for a in activities if a.get('event_type') == 'ip_changed')
        features['ip_change_frequency'] = ip_changes / max(len(scan_results), 1)
        
        rssi_values = [sr.get('rssi') for sr in scan_results if sr.get('rssi') is not None]
        features['avg_rssi'] = np.mean(rssi_values) if rssi_values else -70
        features['rssi_variance'] = np.var(rssi_values) if len(rssi_values) > 1 else 0
        
        timestamps = self._parse_timestamps(scan_results)
        features['hour_entropy'] = self._calculate_hour_entropy(timestamps)
        features['day_of_week_entropy'] = self._calculate_dow_entropy(timestamps)
        features['connection_regularity'] = self._calculate_regularity(timestamps)
        
        first_seen = device_info.get('first_seen')
        if isinstance(first_seen, str):
            first_seen = datetime.fromisoformat(first_seen.replace('Z', '+00:00'))
        if first_seen:
            features['time_since_first_seen'] = (datetime.utcnow() - first_seen.replace(tzinfo=None)).days
        else:
            features['time_since_first_seen'] = 0
        
        response_times = [sr.get('response_time_ms') for sr in scan_results if sr.get('response_time_ms')]
        features['avg_response_time'] = np.mean(response_times) if response_times else 0
        
        disconnections = sum(1 for a in activities if a.get('event_type') == 'disconnected')
        features['offline_frequency'] = disconnections / max(len(activities), 1)
        
        features['is_trusted'] = 1 if device_info.get('is_trusted') else 0
        features['vendor_known'] = 1 if device_info.get('vendor') else 0
        
        feature_vector = np.array([features.get(name, 0) for name in self.FEATURE_NAMES])
        
        return feature_vector
    
    def _calculate_session_durations(self, activities: List[Dict]) -> List[float]:
        """Calculate session durations from connect/disconnect events."""
        durations = []
        connect_time = None
        
        sorted_activities = sorted(
            activities, 
            key=lambda x: x.get('event_timestamp', '')
        )
        
        for activity in sorted_activities:
            event_type = activity.get('event_type')
            timestamp = activity.get('event_timestamp')
            
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            
            if event_type == 'connected':
                connect_time = timestamp
            elif event_type == 'disconnected' and connect_time:
                if timestamp:
                    duration = (timestamp.replace(tzinfo=None) - connect_time.replace(tzinfo=None)).total_seconds()
                    if duration > 0:
                        durations.append(duration / 3600)
                connect_time = None
        
        return durations
    
    def _parse_timestamps(self, scan_results: List[Dict]) -> List[datetime]:
        """Parse timestamps from scan results."""
        timestamps = []
        for sr in scan_results:
            ts = sr.get('scan_timestamp')
            if ts:
                if isinstance(ts, str):
                    ts = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                timestamps.append(ts.replace(tzinfo=None) if ts.tzinfo else ts)
        return timestamps
    
    def _calculate_hour_entropy(self, timestamps: List[datetime]) -> float:
        """Calculate entropy of activity hours."""
        if not timestamps:
            return 0
        
        hours = [ts.hour for ts in timestamps]
        return self._calculate_entropy(hours, 24)
    
    def _calculate_dow_entropy(self, timestamps: List[datetime]) -> float:
        """Calculate entropy of days of week."""
        if not timestamps:
            return 0
        
        days = [ts.weekday() for ts in timestamps]
        return self._calculate_entropy(days, 7)
    
    def _calculate_entropy(self, values: List[int], num_bins: int) -> float:
        """Calculate normalized entropy."""
        if not values:
            return 0
        
        counts = Counter(values)
        probs = np.array([counts.get(i, 0) / len(values) for i in range(num_bins)])
        probs = probs[probs > 0]
        
        if len(probs) == 0:
            return 0
        
        entropy = -np.sum(probs * np.log2(probs))
        max_entropy = np.log2(num_bins)
        
        return entropy / max_entropy if max_entropy > 0 else 0
    
    def _calculate_regularity(self, timestamps: List[datetime]) -> float:
        """Calculate connection time regularity (0=irregular, 1=regular)."""
        if len(timestamps) < 2:
            return 0.5
        
        sorted_ts = sorted(timestamps)
        intervals = [(sorted_ts[i+1] - sorted_ts[i]).total_seconds() 
                    for i in range(len(sorted_ts)-1)]
        
        if not intervals:
            return 0.5
        
        mean_interval = np.mean(intervals)
        std_interval = np.std(intervals)
        
        if mean_interval == 0:
            return 0.5
        
        cv = std_interval / mean_interval
        regularity = 1 / (1 + cv)
        
        return regularity
    
    def normalize_features(self, features: np.ndarray) -> np.ndarray:
        """Normalize feature vector using z-score normalization."""
        if not self.feature_stats:
            return features
        
        normalized = np.zeros_like(features, dtype=float)
        
        for i, name in enumerate(self.FEATURE_NAMES):
            stats = self.feature_stats.get(name, {'mean': 0, 'std': 1})
            mean = stats['mean']
            std = stats['std'] if stats['std'] > 0 else 1
            normalized[i] = (features[i] - mean) / std
        
        return normalized
    
    def fit_normalizer(self, feature_matrix: np.ndarray):
        """Fit normalizer on training data."""
        for i, name in enumerate(self.FEATURE_NAMES):
            self.feature_stats[name] = {
                'mean': np.mean(feature_matrix[:, i]),
                'std': np.std(feature_matrix[:, i])
            }


feature_extractor = FeatureExtractor()
