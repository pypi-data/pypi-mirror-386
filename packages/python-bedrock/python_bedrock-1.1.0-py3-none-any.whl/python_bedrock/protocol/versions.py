"""Protocol version management."""
from typing import Dict, Optional, Set
from dataclasses import dataclass
from enum import IntEnum

class ProtocolVersion(IntEnum):
    """Bedrock protocol versions."""
    LEGACY = 0
    V1_19_30 = 554  # First version with new network settings
    V1_19_50 = 560
    V1_19_60 = 567
    V1_19_70 = 575
    V1_19_80 = 582
    V1_20_0 = 589
    V1_20_10 = 594
    V1_20_15 = 618
    V1_20_30 = 622
    V1_20_40 = 630
    LATEST = V1_20_40

@dataclass
class ProtocolFeatures:
    """Feature flags for protocol versions."""
    compressor_in_header: bool = False
    new_login_identity: bool = False
    new_network_settings: bool = False
    new_item_registry: bool = False

class ProtocolRegistry:
    """Protocol version and feature registry."""
    
    def __init__(self) -> None:
        self._features: Dict[int, ProtocolFeatures] = {}
        self._supported: Set[int] = set()
        self._init_versions()
    
    def _init_versions(self) -> None:
        """Initialize supported versions and their features."""
        # Pre-1.19.30
        self.add_version(ProtocolVersion.V1_19_30, ProtocolFeatures(
            compressor_in_header=False,
            new_login_identity=True,
            new_network_settings=True,
            new_item_registry=False
        ))
        
        # 1.19.50+
        self.add_version(ProtocolVersion.V1_19_50, ProtocolFeatures(
            compressor_in_header=True,
            new_login_identity=True,
            new_network_settings=True,
            new_item_registry=False
        ))
        
        # 1.20.0+
        self.add_version(ProtocolVersion.V1_20_0, ProtocolFeatures(
            compressor_in_header=True,
            new_login_identity=True,
            new_network_settings=True,
            new_item_registry=True
        ))
        
        # Add latest version
        self.add_version(ProtocolVersion.LATEST, ProtocolFeatures(
            compressor_in_header=True,
            new_login_identity=True,
            new_network_settings=True,
            new_item_registry=True
        ))
    
    def add_version(self, version: int, features: ProtocolFeatures) -> None:
        """Add a protocol version with its features."""
        self._features[version] = features
        self._supported.add(version)
    
    def get_features(self, version: int) -> Optional[ProtocolFeatures]:
        """Get features for a specific version."""
        return self._features.get(version)
    
    def is_supported(self, version: int) -> bool:
        """Check if a version is supported."""
        return version in self._supported
    
    def supports_feature(self, version: int, feature: str) -> bool:
        """Check if a version supports a specific feature."""
        features = self.get_features(version)
        if not features:
            return False
        return getattr(features, feature, False)
    
    def get_latest_version(self) -> int:
        """Get the latest supported protocol version."""
        return max(self._supported)
    
    def get_min_version(self) -> int:
        """Get the minimum supported protocol version."""
        return min(self._supported)

# Global protocol registry instance
protocol_registry = ProtocolRegistry()