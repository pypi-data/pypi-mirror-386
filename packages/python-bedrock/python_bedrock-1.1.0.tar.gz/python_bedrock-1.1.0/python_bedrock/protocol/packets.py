"""Bedrock protocol packet definitions."""
from dataclasses import dataclass
from enum import IntEnum
from typing import Any, Dict, List, Optional, Union, ClassVar
from .types import (
    Boolean, Byte, UnsignedByte, Short, UnsignedShort,
    Int, UnsignedInt, Long, UnsignedLong, Float, Double,
    String, UUID, ByteArray, VarInt, VarLong,
    Vector2f, Vector3f, Vector3i, MetadataDictionary
)

class PacketID(IntEnum):
    """Packet identifiers."""
    LOGIN = 0x01
    PLAY_STATUS = 0x02
    SERVER_TO_CLIENT_HANDSHAKE = 0x03
    CLIENT_TO_SERVER_HANDSHAKE = 0x04
    DISCONNECT = 0x05
    RESOURCE_PACKS_INFO = 0x06
    RESOURCE_PACK_STACK = 0x07
    RESOURCE_PACK_CLIENT_RESPONSE = 0x08
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
    RIDER_JUMP = 0x14
    UPDATE_BLOCK = 0x15
    ADD_PAINTING = 0x16
    TICK_SYNC = 0x17
    LEVEL_SOUND_EVENT = 0x18
    LEVEL_EVENT = 0x19
    BLOCK_EVENT = 0x1A
    ENTITY_EVENT = 0x1B
    MOB_EFFECT = 0x1C
    UPDATE_ATTRIBUTES = 0x1D
    INVENTORY_TRANSACTION = 0x1E
    MOB_EQUIPMENT = 0x1F
    MOB_ARMOR_EQUIPMENT = 0x20
    INTERACT = 0x21
    BLOCK_PICK_REQUEST = 0x22
    ENTITY_PICK_REQUEST = 0x23
    PLAYER_ACTION = 0x24
    ENTITY_FALL = 0x25
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
    GUI_DATA_PICK_ITEM = 0x36
    ADVENTURE_SETTINGS = 0x37
    BLOCK_ENTITY_DATA = 0x38
    PLAYER_INPUT = 0x39
    LEVEL_CHUNK = 0x3A
    SET_COMMANDS_ENABLED = 0x3B
    SET_DIFFICULTY = 0x3C
    CHANGE_DIMENSION = 0x3D
    SET_PLAYER_GAME_TYPE = 0x3E
    PLAYER_LIST = 0x3F
    SIMPLE_EVENT = 0x40
    TELEMETRY_EVENT = 0x41
    SPAWN_EXPERIENCE_ORB = 0x42
    CLIENTBOUND_MAP_ITEM_DATA = 0x43
    MAP_INFO_REQUEST = 0x44
    REQUEST_CHUNK_RADIUS = 0x45
    CHUNK_RADIUS_UPDATED = 0x46
    ITEM_FRAME_DROP_ITEM = 0x47
    GAME_RULES_CHANGED = 0x48
    CAMERA = 0x49
    BOSS_EVENT = 0x4A
    SHOW_CREDITS = 0x4B
    AVAILABLE_COMMANDS = 0x4C
    COMMAND_REQUEST = 0x4D
    COMMAND_BLOCK_UPDATE = 0x4E
    COMMAND_OUTPUT = 0x4F
    UPDATE_TRADE = 0x50
    UPDATE_EQUIPMENT = 0x51
    RESOURCE_PACK_DATA_INFO = 0x52
    RESOURCE_PACK_CHUNK_DATA = 0x53
    RESOURCE_PACK_CHUNK_REQUEST = 0x54
    TRANSFER = 0x55
    PLAY_SOUND = 0x56
    STOP_SOUND = 0x57
    SET_TITLE = 0x58
    ADD_BEHAVIOR_TREE = 0x59
    STRUCTURE_BLOCK_UPDATE = 0x5A
    SHOW_STORE_OFFER = 0x5B
    PURCHASE_RECEIPT = 0x5C
    PLAYER_SKIN = 0x5D
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

class Packet:
    """Base packet class."""
    packet_id: ClassVar[PacketID]
    
    @classmethod
    def read(cls, data: bytes, offset: int = 0) -> tuple['Packet', int]:
        """Read packet from bytes."""
        raise NotImplementedError()
    
    def write(self) -> bytes:
        """Write packet to bytes."""
        raise NotImplementedError()

@dataclass
class LoginPacket(Packet):
    """Login packet."""
    packet_id = PacketID.LOGIN
    protocol_version: int
    tokens: Dict[str, Any]
    
    @classmethod
    def read(cls, data: bytes, offset: int = 0) -> tuple['LoginPacket', int]:
        protocol, offset = Int.read(data, offset)
        tokens_str, offset = ByteArray.read(data, offset)
        tokens = json.loads(tokens_str.decode('utf-8'))
        return cls(protocol, tokens), offset
    
    def write(self) -> bytes:
        result = Int.write(self.protocol_version)
        tokens_bytes = json.dumps(self.tokens).encode('utf-8')
        result += ByteArray.write(tokens_bytes)
        return result

@dataclass
class PlayStatusPacket(Packet):
    """Play status packet."""
    packet_id = PacketID.PLAY_STATUS
    
    class Status(IntEnum):
        LOGIN_SUCCESS = 0
        LOGIN_FAILED_CLIENT = 1
        LOGIN_FAILED_SERVER = 2
        PLAYER_SPAWN = 3
        LOGIN_FAILED_INVALID_TENANT = 4
        LOGIN_FAILED_VANILLA_EDU = 5
        LOGIN_FAILED_EDU_VANILLA = 6
        LOGIN_FAILED_SERVER_FULL = 7
    
    status: Status
    
    @classmethod
    def read(cls, data: bytes, offset: int = 0) -> tuple['PlayStatusPacket', int]:
        status, offset = Int.read(data, offset)
        return cls(cls.Status(status)), offset
    
    def write(self) -> bytes:
        return Int.write(self.status.value)

@dataclass
class StartGamePacket(Packet):
    """Start game packet."""
    packet_id = PacketID.START_GAME
    
    entity_id: int
    runtime_entity_id: UnsignedLong
    game_mode: int
    spawn_position: Vector3f
    rotation: Vector2f
    seed: int
    dimension: int
    generator: int
    game_rules: Dict[str, Any]
    difficulty: int
    spawn_position_world: Vector3i
    achieved_using_cheats: bool
    rain_level: float
    lightning_level: float
    has_confirmed_platform_locked_content: bool
    is_multiplayer: bool
    broadcast_to_lan: bool
    xbox_live_broadcast_mode: int
    platform_broadcast_mode: int
    enable_commands: bool
    is_texturepacks_required: bool
    game_rules_updated: bool
    experiments: List[Dict[str, Any]]
    has_locked_behavior_pack: bool
    has_locked_resource_pack: bool
    is_from_locked_world_template: bool
    is_from_world_template: bool
    is_world_template_option_locked: bool
    spawn_biome_type: int
    custom_biome_name: str
    education_shared_resource_uri: str
    
    @classmethod
    def read(cls, data: bytes, offset: int = 0) -> tuple['StartGamePacket', int]:
        # Read all fields
        entity_id, offset = VarLong.read(data, offset)
        runtime_entity_id, offset = UnsignedLong.read(data, offset)
        game_mode, offset = VarInt.read(data, offset)
        spawn_position, offset = Vector3f.read(data, offset)
        rotation, offset = Vector2f.read(data, offset)
        seed, offset = Int.read(data, offset)
        dimension, offset = VarInt.read(data, offset)
        generator, offset = VarInt.read(data, offset)
        
        # Read game rules
        game_rules = {}
        count, offset = VarInt.read(data, offset)
        for _ in range(count):
            name, offset = String.read(data, offset)
            value_type, offset = UnsignedByte.read(data, offset)
            if value_type == 1:  # Boolean
                value, offset = Boolean.read(data, offset)
            elif value_type == 2:  # Int
                value, offset = VarInt.read(data, offset)
            elif value_type == 3:  # Float
                value, offset = Float.read(data, offset)
            game_rules[name] = value
        
        difficulty, offset = VarInt.read(data, offset)
        spawn_position_world, offset = Vector3i.read(data, offset)
        achieved_using_cheats, offset = Boolean.read(data, offset)
        rain_level, offset = Float.read(data, offset)
        lightning_level, offset = Float.read(data, offset)
        has_confirmed_platform_locked_content, offset = Boolean.read(data, offset)
        is_multiplayer, offset = Boolean.read(data, offset)
        broadcast_to_lan, offset = Boolean.read(data, offset)
        xbox_live_broadcast_mode, offset = VarInt.read(data, offset)
        platform_broadcast_mode, offset = VarInt.read(data, offset)
        enable_commands, offset = Boolean.read(data, offset)
        is_texturepacks_required, offset = Boolean.read(data, offset)
        game_rules_updated, offset = Boolean.read(data, offset)
        
        # Read experiments
        experiments = []
        count, offset = VarInt.read(data, offset)
        for _ in range(count):
            name, offset = String.read(data, offset)
            enabled, offset = Boolean.read(data, offset)
            experiments.append({"name": name, "enabled": enabled})
        
        has_locked_behavior_pack, offset = Boolean.read(data, offset)
        has_locked_resource_pack, offset = Boolean.read(data, offset)
        is_from_locked_world_template, offset = Boolean.read(data, offset)
        is_from_world_template, offset = Boolean.read(data, offset)
        is_world_template_option_locked, offset = Boolean.read(data, offset)
        spawn_biome_type, offset = VarInt.read(data, offset)
        custom_biome_name, offset = String.read(data, offset)
        education_shared_resource_uri, offset = String.read(data, offset)
        
        return cls(
            entity_id=entity_id,
            runtime_entity_id=runtime_entity_id,
            game_mode=game_mode,
            spawn_position=spawn_position,
            rotation=rotation,
            seed=seed,
            dimension=dimension,
            generator=generator,
            game_rules=game_rules,
            difficulty=difficulty,
            spawn_position_world=spawn_position_world,
            achieved_using_cheats=achieved_using_cheats,
            rain_level=rain_level,
            lightning_level=lightning_level,
            has_confirmed_platform_locked_content=has_confirmed_platform_locked_content,
            is_multiplayer=is_multiplayer,
            broadcast_to_lan=broadcast_to_lan,
            xbox_live_broadcast_mode=xbox_live_broadcast_mode,
            platform_broadcast_mode=platform_broadcast_mode,
            enable_commands=enable_commands,
            is_texturepacks_required=is_texturepacks_required,
            game_rules_updated=game_rules_updated,
            experiments=experiments,
            has_locked_behavior_pack=has_locked_behavior_pack,
            has_locked_resource_pack=has_locked_resource_pack,
            is_from_locked_world_template=is_from_locked_world_template,
            is_from_world_template=is_from_world_template,
            is_world_template_option_locked=is_world_template_option_locked,
            spawn_biome_type=spawn_biome_type,
            custom_biome_name=custom_biome_name,
            education_shared_resource_uri=education_shared_resource_uri
        ), offset
    
    def write(self) -> bytes:
        result = bytearray()
        
        # Write all fields
        result.extend(VarLong.write(self.entity_id))
        result.extend(UnsignedLong.write(self.runtime_entity_id))
        result.extend(VarInt.write(self.game_mode))
        result.extend(self.spawn_position.write())
        result.extend(self.rotation.write())
        result.extend(Int.write(self.seed))
        result.extend(VarInt.write(self.dimension))
        result.extend(VarInt.write(self.generator))
        
        # Write game rules
        result.extend(VarInt.write(len(self.game_rules)))
        for name, value in self.game_rules.items():
            result.extend(String.write(name))
            if isinstance(value, bool):
                result.extend(UnsignedByte.write(1))
                result.extend(Boolean.write(value))
            elif isinstance(value, int):
                result.extend(UnsignedByte.write(2))
                result.extend(VarInt.write(value))
            elif isinstance(value, float):
                result.extend(UnsignedByte.write(3))
                result.extend(Float.write(value))
        
        result.extend(VarInt.write(self.difficulty))
        result.extend(self.spawn_position_world.write())
        result.extend(Boolean.write(self.achieved_using_cheats))
        result.extend(Float.write(self.rain_level))
        result.extend(Float.write(self.lightning_level))
        result.extend(Boolean.write(self.has_confirmed_platform_locked_content))
        result.extend(Boolean.write(self.is_multiplayer))
        result.extend(Boolean.write(self.broadcast_to_lan))
        result.extend(VarInt.write(self.xbox_live_broadcast_mode))
        result.extend(VarInt.write(self.platform_broadcast_mode))
        result.extend(Boolean.write(self.enable_commands))
        result.extend(Boolean.write(self.is_texturepacks_required))
        result.extend(Boolean.write(self.game_rules_updated))
        
        # Write experiments
        result.extend(VarInt.write(len(self.experiments)))
        for exp in self.experiments:
            result.extend(String.write(exp["name"]))
            result.extend(Boolean.write(exp["enabled"]))
        
        result.extend(Boolean.write(self.has_locked_behavior_pack))
        result.extend(Boolean.write(self.has_locked_resource_pack))
        result.extend(Boolean.write(self.is_from_locked_world_template))
        result.extend(Boolean.write(self.is_from_world_template))
        result.extend(Boolean.write(self.is_world_template_option_locked))
        result.extend(VarInt.write(self.spawn_biome_type))
        result.extend(String.write(self.custom_biome_name))
        result.extend(String.write(self.education_shared_resource_uri))
        
        return bytes(result)

# Add more packet definitions here as needed

PACKETS = {
    PacketID.LOGIN: LoginPacket,
    PacketID.PLAY_STATUS: PlayStatusPacket,
    PacketID.START_GAME: StartGamePacket,
    # Add more packet mappings here
}

def create_packet(packet_id: int, data: bytes) -> Optional[Packet]:
    """Create a packet instance from ID and data."""
    packet_class = PACKETS.get(packet_id)
    if not packet_class:
        return None
    
    packet, _ = packet_class.read(data)
    return packet