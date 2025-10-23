"""Bedrock protocol definition and metadata."""
from dataclasses import dataclass
from enum import IntEnum
from typing import Dict, Any, List, Optional, Union, TypeVar, Type

class ProtocolVersion(IntEnum):
    """Minecraft Bedrock protocol versions."""
    # Latest versions
    v1_20_0 = 589  # 1.20.0
    v1_19_80 = 582  # 1.19.80
    v1_19_70 = 575  # 1.19.70
    v1_19_60 = 567  # 1.19.60
    v1_19_50 = 560  # 1.19.50
    v1_19_40 = 554  # 1.19.40
    v1_19_30 = 544  # 1.19.30
    v1_19_20 = 534  # 1.19.20
    v1_19_10 = 524  # 1.19.10
    v1_19_0 = 503   # 1.19.0
    v1_18_30 = 486  # 1.18.30
    v1_18_0 = 475   # 1.18.0
    v1_17_40 = 465  # 1.17.40
    v1_17_30 = 440  # 1.17.30
    v1_17_0 = 419   # 1.17.0
    v1_16_220 = 408 # 1.16.220

class GameType(IntEnum):
    """Game type/mode constants."""
    SURVIVAL = 0
    CREATIVE = 1
    ADVENTURE = 2
    SURVIVAL_SPECTATOR = 3
    CREATIVE_SPECTATOR = 4
    DEFAULT = 5
    
class Difficulty(IntEnum):
    """Game difficulty levels."""
    PEACEFUL = 0
    EASY = 1
    NORMAL = 2
    HARD = 3

class PlayerPermission(IntEnum):
    """Player permission levels."""
    VISITOR = 0
    MEMBER = 1
    OPERATOR = 2
    CUSTOM = 3
    
class DeviceOS(IntEnum):
    """Client device operating systems."""
    ANDROID = 1
    IOS = 2
    OSX = 3
    AMAZON = 4
    GEAR_VR = 5
    HOLOLENS = 6
    WINDOWS_10 = 7
    WIN32 = 8
    DEDICATED = 9
    ORBIS = 10
    NX = 11
    
class PacketReliability(IntEnum):
    """RakNet packet reliability types."""
    UNRELIABLE = 0
    UNRELIABLE_SEQUENCED = 1
    RELIABLE = 2
    RELIABLE_ORDERED = 3
    RELIABLE_SEQUENCED = 4

class PacketPriority(IntEnum):
    """RakNet packet priority levels."""
    NORMAL = 0
    IMMEDIATE = 1
    
@dataclass
class ProtocolMetadata:
    """Protocol version information and features."""
    version: int
    game_version: str
    version_name: str
    has_new_chunks: bool = False
    has_new_inventories: bool = False
    has_new_items: bool = False
    has_mca_items: bool = False
    has_new_auth: bool = False
    uses_jwt_chain: bool = False

    @property
    def is_modern(self) -> bool:
        """Check if protocol version is modern (1.16.220+)."""
        return self.version >= ProtocolVersion.v1_16_220
        
    @property
    def uses_gcm(self) -> bool:
        """Check if protocol version uses AES-GCM encryption."""
        return self.version >= ProtocolVersion.v1_16_220
        
    @property
    def needs_jwt_chain(self) -> bool:
        """Check if protocol needs JWT chain validation."""
        return self.version >= ProtocolVersion.v1_19_30
        
    @property
    def has_new_login_ids(self) -> bool:
        """Check if protocol uses new login packet structure."""
        return self.version >= ProtocolVersion.v1_19_30

PROTOCOLS: Dict[int, ProtocolMetadata] = {
    ProtocolVersion.v1_20_0: ProtocolMetadata(
        version=589,
        game_version="1.20.0",
        version_name="1.20.0",
        has_new_chunks=True,
        has_new_inventories=True,
        has_new_items=True,
        has_mca_items=True,
        has_new_auth=True,
        uses_jwt_chain=True
    ),
    ProtocolVersion.v1_19_80: ProtocolMetadata(
        version=582,
        game_version="1.19.80",
        version_name="1.19.80",
        has_new_chunks=True,
        has_new_inventories=True,
        has_new_items=True,
        has_mca_items=True,
        has_new_auth=True,
        uses_jwt_chain=True
    ),
    ProtocolVersion.v1_19_30: ProtocolMetadata(
        version=544,
        game_version="1.19.30",
        version_name="1.19.30",
        has_new_chunks=True,
        has_new_inventories=True,
        has_new_items=True,
        has_new_auth=True,
        uses_jwt_chain=True
    ),
    ProtocolVersion.v1_16_220: ProtocolMetadata(
        version=408,
        game_version="1.16.220",
        version_name="1.16.220",
        has_new_items=True
    )
}

def get_protocol(version: int) -> ProtocolMetadata:
    """Get protocol metadata for version."""
    if version not in PROTOCOLS:
        # Find closest lower version
        lower_versions = [v for v in PROTOCOLS if v <= version]
        if not lower_versions:
            raise ValueError(f"Unsupported protocol version: {version}")
        version = max(lower_versions)
    return PROTOCOLS[version]