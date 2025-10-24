"""Bedrock protocol packet definitions and serialization."""
import json
import uuid
import struct
from dataclasses import dataclass
from typing import Any, Dict, Optional, TypeVar, Generic, Protocol, List, Tuple, Union, ClassVar, Type, runtime_checkable
from enum import IntEnum

from .protocol import (
    PacketReliability,
    PacketPriority,
    ProtocolVersion,
    get_protocol
)

class PacketType(IntEnum):
    """Bedrock packet identifiers."""
    # Login sequence
    LOGIN = 0x01
    PLAY_STATUS = 0x02
    SERVER_TO_CLIENT_HANDSHAKE = 0x03
    CLIENT_TO_SERVER_HANDSHAKE = 0x04
    DISCONNECT = 0x05
    
    # Resource packs
    RESOURCE_PACKS_INFO = 0x06
    RESOURCE_PACK_STACK = 0x07
    RESOURCE_PACK_CLIENT_RESPONSE = 0x08
    
    # Game
    TEXT = 0x09
    SET_TIME = 0x0A
    START_GAME = 0x0B
    ADD_PLAYER = 0x0C
    ADD_ENTITY = 0x0D
    REMOVE_ENTITY = 0x0E
    ADD_ITEM_ENTITY = 0x0F
    TAKE_ITEM_ENTITY = 0x11
    MOVE_ENTITY = 0x12
    MOVE_PLAYER = 0x13
    UPDATE_BLOCK = 0x15
    ADD_PAINTING = 0x16
    LEVEL_EVENT = 0x19
    ENTITY_EVENT = 0x1B
    INVENTORY_TRANSACTION = 0x1E
    MOB_EQUIPMENT = 0x1F
    MOB_ARMOR_EQUIPMENT = 0x20
    INTERACT = 0x21
    BLOCK_PICK_REQUEST = 0x22
    PLAYER_ACTION = 0x24
    HURT_ARMOR = 0x26
    SET_ENTITY_DATA = 0x27
    SET_ENTITY_MOTION = 0x28
    SET_ENTITY_LINK = 0x29
    SET_HEALTH = 0x2A
    SET_SPAWN_POSITION = 0x2B
    ANIMATE = 0x2C
    RESPAWN = 0x2D
    CONTAINER_OPEN = 0x2E
    CONTAINER_CLOSE = 0x2F
    PLAYER_HOTBAR = 0x30
    INVENTORY_CONTENT = 0x31
    INVENTORY_SLOT = 0x32
    CONTAINER_SET_DATA = 0x33
    CRAFTING_DATA = 0x34
    CRAFTING_EVENT = 0x35
    ADVENTURE_SETTINGS = 0x37
    BLOCK_ENTITY_DATA = 0x38
    FULL_CHUNK_DATA = 0x3A
    SET_COMMANDS_ENABLED = 0x3B
    SET_DIFFICULTY = 0x3C
    CHANGE_DIMENSION = 0x3D
    SET_PLAYER_GAME_TYPE = 0x3E
    PLAYER_LIST = 0x3F
    EVENT = 0x41
    SPAWN_EXPERIENCE_ORB = 0x42
    CLIENTBOUND_MAP_ITEM_DATA = 0x43
    MAP_INFO_REQUEST = 0x44
    REQUEST_CHUNK_RADIUS = 0x45
    CHUNK_RADIUS_UPDATED = 0x46
    ITEM_FRAME_DROP_ITEM = 0x47
    REPLACE_ITEM_IN_SLOT = 0x48
    GAME_RULES_CHANGED = 0x49
    CAMERA = 0x4A
    ADD_ITEM = 0x4B
    BOSS_EVENT = 0x4C
    SHOW_CREDITS = 0x4D
    AVAILABLE_COMMANDS = 0x4E
    COMMAND_REQUEST = 0x4F
    COMMAND_BLOCK_UPDATE = 0x50
    UPDATE_TRADE = 0x51
    UPDATE_EQUIPMENT = 0x52
    RESOURCE_PACK_DATA_INFO = 0x53
    RESOURCE_PACK_CHUNK_DATA = 0x54
    RESOURCE_PACK_CHUNK_REQUEST = 0x55
    TRANSFER = 0x56
    PLAY_SOUND = 0x57
    STOP_SOUND = 0x58
    SET_TITLE = 0x59
    ADD_BEHAVIOR_TREE = 0x5A
    STRUCTURE_BLOCK_UPDATE = 0x5B
    SHOW_STORE_OFFER = 0x5C
    PURCHASE_RECEIPT = 0x5D
    SUB_CLIENT_LOGIN = 0x5E
    AUTOMATION_CLIENT_CONNECT = 0x5F
    SET_LAST_HURT_BY = 0x60
    BOOK_EDIT = 0x61
    NPC_REQUEST = 0x62
    PHOTO_TRANSFER = 0x63
    MODAL_FORM_REQUEST = 0x64
    MODAL_FORM_RESPONSE = 0x65
    SERVER_SETTINGS_REQUEST = 0x66
    SERVER_SETTINGS_RESPONSE = 0x67
    SHOW_PROFILE = 0x68
    SET_DEFAULT_GAME_TYPE = 0x69
    REMOVE_OBJECTIVE = 0x6A
    SET_DISPLAY_OBJECTIVE = 0x6B
    SET_SCORE = 0x6C
    LAB_TABLE = 0x6D
    UPDATE_BLOCK_SYNCED = 0x6E
    MOVE_ENTITY_DELTA = 0x6F
    SET_SCOREBOARD_IDENTITY = 0x70
    SET_LOCAL_PLAYER_AS_INITIALIZED = 0x71
    UPDATE_SOFT_ENUM = 0x72
    NETWORK_STACK_LATENCY = 0x73
    SCRIPT_CUSTOM_EVENT = 0x75
    SPAWN_PARTICLE_EFFECT = 0x76
    AVAILABLE_ENTITY_IDENTIFIERS = 0x77
    LEVEL_SOUND_EVENT_V2 = 0x78
    NETWORK_CHUNK_PUBLISHER_UPDATE = 0x79
    BIOME_DEFINITION_LIST = 0x7A
    LEVEL_SOUND_EVENT = 0x7B
    LEVEL_EVENT_GENERIC = 0x7C
    LECTERN_UPDATE = 0x7D
    VIDEO_STREAM_CONNECT = 0x7E
    CLIENT_CACHE_STATUS = 0x81
    ON_SCREEN_TEXTURE_ANIMATION = 0x82
    MAP_CREATE_LOCKED_COPY = 0x83
    STRUCTURE_TEMPLATE_DATA_REQUEST = 0x84
    STRUCTURE_TEMPLATE_DATA_RESPONSE = 0x85
    CLIENT_CACHE_BLOB_STATUS = 0x87
    CLIENT_CACHE_MISS_RESPONSE = 0x88
    EDUCATION_SETTINGS = 0x89
    EMOTE = 0x8A
    MULTIPLAYER_SETTINGS = 0x8B
    SETTINGS_COMMAND = 0x8C
    ANVIL_DAMAGE = 0x8D
    COMPLETED_USING_ITEM = 0x8E
    NETWORK_SETTINGS = 0x8F
    PLAYER_AUTH_INPUT = 0x90
    CREATIVE_CONTENT = 0x91
    PLAYER_ENCHANT_OPTIONS = 0x92
    POS_TRACKING_CLIENT_REQUEST = 0x93
    POS_TRACKING_SERVER_BROADCAST = 0x94
    POS_TRACKING_SERVER_REQUEST = 0x95
    DEBUG_INFO = 0x96
    PACKET_VIOLATION_WARNING = 0x97
    MOTION_PREDICTION_HINTS = 0x98
    ANIMATE_ENTITY = 0x99
    CAMERA_SHAKE = 0x9A
    PLAYER_FOG = 0x9B
    CORRECT_PLAYER_MOVE_PREDICTION = 0x9C
    ITEM_COMPONENT = 0x9D
    FILTER_TEXT_PACKET = 0x9E
    SYNC_ACTOR_PROPERTY = 0xA1
    ADD_VOLUME_ENTITY = 0xA2
    REMOVE_VOLUME_ENTITY = 0xA3
    SIMULATION_TYPE = 0xA4

class VarInt:
    """Variable-length integer encoding."""
    @staticmethod
    def encode(value: int) -> bytes:
        """Encode integer as VarInt bytes."""
        result = bytearray()
        value &= 0xffffffffffffffff
        while True:
            byte = value & 0x7f
            value >>= 7
            if value:
                byte |= 0x80
            result.append(byte)
            if not value:
                break
        return bytes(result)
        
    @staticmethod
    def decode(data: bytes, offset: int = 0) -> Tuple[int, int]:
        """Decode VarInt from bytes starting at offset.
        
        Returns:
            Tuple of (decoded value, new offset)
        """
        result = 0
        shift = 0
        
        while True:
            if offset >= len(data):
                raise ValueError("Incomplete VarInt")
                
            byte = data[offset]
            result |= (byte & 0x7f) << shift
            offset += 1
            
            if not (byte & 0x80):
                break
                
            shift += 7
            if shift > 64:
                raise ValueError("VarInt too big")
                
        return result, offset

@runtime_checkable
class PacketSerializable(Protocol):
    """Protocol for objects that can be serialized to/from bytes."""
    def serialize(self) -> bytes:
        """Convert object to bytes."""
        ...
    
    @classmethod
    def deserialize(cls, data: bytes) -> 'PacketSerializable':
        """Create object from bytes."""
        ...

T = TypeVar('T', bound=PacketSerializable)

@dataclass
class PacketHeader:
    """Common packet header structure."""
    packet_id: int
    sender_id: int
    client_id: int
    body_size: int = 0
    
    def serialize(self) -> bytes:
        """Serialize header to bytes."""
        return (
            VarInt.encode(self.packet_id) +
            VarInt.encode(self.sender_id) +
            VarInt.encode(self.client_id) +
            VarInt.encode(self.body_size)
        )
    
    @classmethod
    def deserialize(cls, data: bytes) -> Tuple['PacketHeader', int]:
        """Deserialize header from bytes.
        
        Returns:
            Tuple of (PacketHeader, offset to body start)
        """
        offset = 0
        packet_id, offset = VarInt.decode(data, offset)
        sender_id, offset = VarInt.decode(data, offset)
        client_id, offset = VarInt.decode(data, offset)
        body_size, offset = VarInt.decode(data, offset)
        
        return cls(
            packet_id=packet_id,
            sender_id=sender_id,
            client_id=client_id,
            body_size=body_size
        ), offset

@dataclass
class Packet(Generic[T]):
    """Generic packet container with header and payload."""
    header: PacketHeader
    payload: T
    reliability: PacketReliability = PacketReliability.RELIABLE
    priority: PacketPriority = PacketPriority.NORMAL
    
    @property
    def packet_id(self) -> int:
        """Get packet ID."""
        return self.header.packet_id
        
    def serialize(self) -> bytes:
        """Serialize full packet to bytes."""
        if not isinstance(self.payload, PacketSerializable):
            raise TypeError("Payload must implement PacketSerializable")
            
        # Serialize payload first to get size
        payload_bytes = self.payload.serialize()
        self.header.body_size = len(payload_bytes)
        
        # Then serialize header
        header_bytes = self.header.serialize()
        
        # Combine with total length
        total_size = len(header_bytes) + len(payload_bytes)
        return (
            total_size.to_bytes(4, 'big') +
            header_bytes +
            payload_bytes
        )
    
    @classmethod
    def deserialize(cls, data: bytes, payload_type: Type[T]) -> 'Packet[T]':
        """Deserialize packet from bytes."""
        if len(data) < 4:
            raise ValueError("Packet too short")
            
        # Get total size
        total_size = int.from_bytes(data[0:4], 'big')
        if len(data) < total_size + 4:
            raise ValueError("Incomplete packet")
            
        # Parse header
        packet_data = data[4:4+total_size]
        header, offset = PacketHeader.deserialize(packet_data)
        
        # Parse payload
        payload = payload_type.deserialize(packet_data[offset:])
        
        return cls(header=header, payload=payload)

# Login packets
@dataclass 
class LoginToken:
    """Client authentication token data."""
    chain: List[str]  # Chain of JWTs
    client_data: str  # Client data JWT
    
    def serialize(self) -> bytes:
        """Serialize token data to bytes."""
        # 1.19.30+ format
        chain_data = {
            "chain": self.chain
        }
        return (
            json.dumps(chain_data).encode('utf-8') +
            b'\n' +
            self.client_data.encode('utf-8')
        )
    
    @classmethod
    def deserialize(cls, data: bytes) -> 'LoginToken':
        """Deserialize token data from bytes."""
        parts = data.split(b'\n', 1)
        if len(parts) != 2:
            raise ValueError("Invalid login token format")
            
        chain_data = json.loads(parts[0])
        return cls(
            chain=chain_data["chain"],
            client_data=parts[1].decode('utf-8')
        )

@dataclass
class LoginPacket(PacketSerializable):
    """Initial login packet."""
    PACKET_ID: ClassVar[int] = PacketType.LOGIN
    
    protocol_version: int
    tokens: LoginToken
    
    def serialize(self) -> bytes:
        """Serialize login packet to bytes."""
        return (
            struct.pack('>I', self.protocol_version) +
            self.tokens.serialize()
        )
    
    @classmethod
    def deserialize(cls, data: bytes) -> 'LoginPacket':
        """Deserialize login packet from bytes."""
        if len(data) < 4:
            raise ValueError("Login packet too short")
            
        protocol = struct.unpack('>I', data[:4])[0]
        tokens = LoginToken.deserialize(data[4:])
        
        return cls(
            protocol_version=protocol,
            tokens=tokens
        )

@dataclass 
class PlayStatusPacket(PacketSerializable):
    """Play status update packet."""
    PACKET_ID: ClassVar[int] = PacketType.PLAY_STATUS
    
    class Status(IntEnum):
        LOGIN_SUCCESS = 0
        FAILED_CLIENT = 1
        FAILED_SPAWN = 2
        PLAYER_SPAWN = 3
        FAILED_INVALID_TENANT = 4
        FAILED_VANILLA_EDU = 5
        FAILED_EDU_VANILLA = 6
        FAILED_SERVER_FULL = 7
    
    status: Status
    
    def serialize(self) -> bytes:
        """Serialize play status to bytes."""
        return VarInt.encode(self.status)
    
    @classmethod
    def deserialize(cls, data: bytes) -> 'PlayStatusPacket':
        """Deserialize play status from bytes."""
        status, _ = VarInt.decode(data)
        return cls(status=cls.Status(status))

@dataclass
class DisconnectPacket(PacketSerializable):
    """Disconnect notification packet."""
    PACKET_ID: ClassVar[int] = PacketType.DISCONNECT
    
    reason: str
    hide_screen: bool = False
    
    def serialize(self) -> bytes:
        """Serialize disconnect packet to bytes."""
        message = self.reason.encode('utf-8')
        return (
            VarInt.encode(len(message)) +
            message +
            bytes([1 if self.hide_screen else 0])
        )
    
    @classmethod
    def deserialize(cls, data: bytes) -> 'DisconnectPacket':
        """Deserialize disconnect packet from bytes."""
        message_len, offset = VarInt.decode(data)
        message = data[offset:offset+message_len].decode('utf-8')
        hide = bool(data[offset+message_len])
        
        return cls(
            reason=message,
            hide_screen=hide
        )

@dataclass
class TextPacket(PacketSerializable):
    """Text/chat message packet."""
    PACKET_ID: ClassVar[int] = PacketType.TEXT
    
    class TextType(IntEnum):
        RAW = 0
        CHAT = 1
        TRANSLATION = 2
        POPUP = 3
        JUKEBOX_POPUP = 4
        TIP = 5
        SYSTEM = 6
        WHISPER = 7
        ANNOUNCEMENT = 8
        JSON = 9
        JSON_WHISPER = 10
    
    type: TextType
    needs_translation: bool
    source: Optional[str]
    message: str
    parameters: List[str]
    xuid: str = ""
    platform_chat_id: str = ""
    
    def serialize(self) -> bytes:
        """Serialize text packet to bytes."""
        # Write type and translation flag
        data = bytes([
            self.type,
            1 if self.needs_translation else 0
        ])
        
        # Write source name if needed
        if self.type in (
            self.TextType.CHAT,
            self.TextType.WHISPER,
            self.TextType.ANNOUNCEMENT
        ):
            src = self.source or ""
            src_bytes = src.encode('utf-8')
            data += VarInt.encode(len(src_bytes)) + src_bytes
        
        # Write message
        msg_bytes = self.message.encode('utf-8')
        data += VarInt.encode(len(msg_bytes)) + msg_bytes
        
        # Write parameters
        data += VarInt.encode(len(self.parameters))
        for param in self.parameters:
            param_bytes = param.encode('utf-8')
            data += VarInt.encode(len(param_bytes)) + param_bytes
            
        # Write Xbox data
        xuid_bytes = self.xuid.encode('utf-8')
        platform_bytes = self.platform_chat_id.encode('utf-8')
        data += (
            VarInt.encode(len(xuid_bytes)) + xuid_bytes +
            VarInt.encode(len(platform_bytes)) + platform_bytes
        )
        
        return data
    
    @classmethod
    def deserialize(cls, data: bytes) -> 'TextPacket':
        """Deserialize text packet from bytes."""
        if len(data) < 2:
            raise ValueError("Text packet too short")
            
        # Read type and translation flag
        type_val = data[0]
        needs_translation = bool(data[1])
        offset = 2
        
        # Read source if needed
        source = None
        if type_val in (1, 7, 8):  # Chat, Whisper, Announcement
            src_len, offset = VarInt.decode(data, offset)
            source = data[offset:offset+src_len].decode('utf-8')
            offset += src_len
        
        # Read message
        msg_len, offset = VarInt.decode(data, offset)
        message = data[offset:offset+msg_len].decode('utf-8')
        offset += msg_len
        
        # Read parameters
        param_count, offset = VarInt.decode(data, offset)
        parameters = []
        for _ in range(param_count):
            param_len, offset = VarInt.decode(data, offset)
            param = data[offset:offset+param_len].decode('utf-8')
            parameters.append(param)
            offset += param_len
            
        # Read Xbox data
        xuid_len, offset = VarInt.decode(data, offset)
        xuid = data[offset:offset+xuid_len].decode('utf-8')
        offset += xuid_len
        
        platform_len, offset = VarInt.decode(data, offset)
        platform_id = data[offset:offset+platform_len].decode('utf-8')
        
        return cls(
            type=cls.TextType(type_val),
            needs_translation=needs_translation,
            source=source,
            message=message,
            parameters=parameters,
            xuid=xuid,
            platform_chat_id=platform_id
        )

@dataclass
class NetworkSettingsPacket(PacketSerializable):
    """Network configuration packet."""
    PACKET_ID: ClassVar[int] = PacketType.NETWORK_SETTINGS
    
    compression_threshold: int
    compression_algorithm: int
    client_throttle: bool
    client_throttle_threshold: int
    client_throttle_scalar: float
    
    def serialize(self) -> bytes:
        """Serialize network settings to bytes."""
        return (
            VarInt.encode(self.compression_threshold) +
            VarInt.encode(self.compression_algorithm) +
            bytes([1 if self.client_throttle else 0]) +
            VarInt.encode(self.client_throttle_threshold) +
            struct.pack('f', self.client_throttle_scalar)
        )
    
    @classmethod
    def deserialize(cls, data: bytes) -> 'NetworkSettingsPacket':
        """Deserialize network settings from bytes."""
        compression_threshold, offset = VarInt.decode(data)
        compression_algorithm, offset = VarInt.decode(data, offset)
        client_throttle = bool(data[offset])
        offset += 1
        client_threshold, offset = VarInt.decode(data, offset)
        client_scalar = struct.unpack('f', data[offset:offset+4])[0]
        
        return cls(
            compression_threshold=compression_threshold,
            compression_algorithm=compression_algorithm,
            client_throttle=client_throttle,
            client_throttle_threshold=client_threshold,
            client_throttle_scalar=client_scalar
        )

# Map packet types to implementations
PACKET_TYPES: Dict[int, Type[PacketSerializable]] = {
    PacketType.LOGIN: LoginPacket,
    PacketType.PLAY_STATUS: PlayStatusPacket,
    PacketType.DISCONNECT: DisconnectPacket,
    PacketType.TEXT: TextPacket,
    PacketType.NETWORK_SETTINGS: NetworkSettingsPacket
}

def create_packet(
    packet_id: int,
    sender_id: int,
    client_id: int,
    payload: PacketSerializable,
    reliability: PacketReliability = PacketReliability.RELIABLE,
    priority: PacketPriority = PacketPriority.NORMAL
) -> Packet:
    """Create a new packet with header."""
    header = PacketHeader(
        packet_id=packet_id,
        sender_id=sender_id,
        client_id=client_id
    )
    return Packet(
        header=header,
        payload=payload,
        reliability=reliability,
        priority=priority
    )

def parse_packet(data: bytes) -> Optional[Packet]:
    """Parse a packet from bytes."""
    try:
        # Read header first
        if len(data) < 4:
            return None
            
        total_size = int.from_bytes(data[0:4], 'big')
        if len(data) < total_size + 4:
            return None
            
        packet_data = data[4:4+total_size]
        header, offset = PacketHeader.deserialize(packet_data)
        
        # Find packet type
        packet_type = PACKET_TYPES.get(header.packet_id)
        if not packet_type:
            return None
            
        # Parse payload
        payload = packet_type.deserialize(packet_data[offset:])
        
        return Packet(header=header, payload=payload)
        
    except Exception as e:
        print(f"Failed to parse packet: {e}")
        return None