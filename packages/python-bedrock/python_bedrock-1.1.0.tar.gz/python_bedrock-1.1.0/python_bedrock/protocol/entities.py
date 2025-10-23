"""Entity system implementation."""
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Dict, List, Optional, Set, Any
import uuid
from .types import Vector2f, Vector3f, MetadataDictionary
from .nbt import NBTCompound

class EntityType(IntEnum):
    """Entity type identifiers."""
    PLAYER = 0x01
    ITEM = 0x40
    PAINTING = 0x41
    FALLING_BLOCK = 0x42
    EXPERIENCE_ORB = 0x43
    TNT = 0x44
    SHULKER_BULLET = 0x45
    EGG = 0x46
    ENDER_PEARL = 0x47
    FISHING_HOOK = 0x48
    DRAGON_FIREBALL = 0x49
    ARROW = 0x4A
    SNOWBALL = 0x4B
    THROWN_TRIDENT = 0x4C
    SPLASH_POTION = 0x4D
    THROWN_EXP_BOTTLE = 0x4E
    LIGHTNING_BOLT = 0x4F
    EVOCATION_FANG = 0x50
    ARMOR_STAND = 0x51
    BOAT = 0x52
    MINECART = 0x53
    CHEST_MINECART = 0x54
    HOPPER_MINECART = 0x55
    TNT_MINECART = 0x56
    COMMAND_BLOCK_MINECART = 0x57
    ZOMBIE = 0x80
    CREEPER = 0x81
    SKELETON = 0x82
    SPIDER = 0x83
    ZOMBIE_PIGMAN = 0x84
    SLIME = 0x85
    ENDERMAN = 0x86
    SILVERFISH = 0x87
    CAVE_SPIDER = 0x88
    GHAST = 0x89
    MAGMA_CUBE = 0x8A
    BLAZE = 0x8B
    ZOMBIE_VILLAGER = 0x8C
    WITCH = 0x8D
    STRAY = 0x8E
    HUSK = 0x8F
    WITHER_SKELETON = 0x90
    GUARDIAN = 0x91
    ELDER_GUARDIAN = 0x92
    NPC = 0x93
    WITHER = 0x94
    ENDER_DRAGON = 0x95
    SHULKER = 0x96
    ENDERMITE = 0x97
    VINDICATOR = 0x98
    PHANTOM = 0x99
    RAVAGER = 0x9A
    ARMOR_STAND = 0x9B
    VILLAGER = 0xB0
    WANDERING_TRADER = 0xB1
    HORSE = 0xC0
    DONKEY = 0xC1
    MULE = 0xC2
    SKELETON_HORSE = 0xC3
    ZOMBIE_HORSE = 0xC4
    LLAMA = 0xC5
    TRADER_LLAMA = 0xC6
    POLAR_BEAR = 0xC7
    PARROT = 0xC8
    DOLPHIN = 0xC9
    ZOMBIE_VILLAGER_V2 = 0xCA
    COW = 0xD0
    PIG = 0xD1
    SHEEP = 0xD2
    WOLF = 0xD3
    CHICKEN = 0xD4
    SQUID = 0xD5
    RABBIT = 0xD6
    BAT = 0xD7
    IRON_GOLEM = 0xD8
    SNOW_GOLEM = 0xD9
    OCELOT = 0xDA
    HORSE = 0xDB
    CAT = 0xDC
    PUFFERFISH = 0xDD
    SALMON = 0xDE
    DROWNED = 0xDF
    TROPICAL_FISH = 0xE0
    COD = 0xE1
    PANDA = 0xE2
    PILLAGER = 0xE3
    VILLAGER_V2 = 0xE4
    ZOMBIE_VILLAGER_V2 = 0xE5
    SHIELD = 0xF0
    ELDER_GUARDIAN_GHOST = 0xF1

@dataclass
class Entity:
    """Base entity class."""
    entity_id: int
    entity_type: EntityType
    position: Vector3f
    rotation: Vector2f
    velocity: Vector3f = field(default_factory=lambda: Vector3f(0, 0, 0))
    metadata: MetadataDictionary = field(default_factory=lambda: MetadataDictionary({}))
    on_ground: bool = False
    nbt: Optional[NBTCompound] = None
    uuid: uuid.UUID = field(default_factory=uuid.uuid4)

@dataclass
class Player(Entity):
    """Player entity."""
    username: str = ""
    skin_data: Dict[str, Any] = field(default_factory=dict)
    game_mode: int = 0
    ping: int = 0
    
    def __init__(
        self,
        entity_id: int,
        position: Vector3f,
        rotation: Vector2f,
        username: str,
        skin_data: Dict[str, Any]
    ):
        super().__init__(
            entity_id=entity_id,
            entity_type=EntityType.PLAYER,
            position=position,
            rotation=rotation
        )
        self.username = username
        self.skin_data = skin_data

@dataclass
class LivingEntity(Entity):
    """Base class for living entities."""
    health: float = 20.0
    max_health: float = 20.0
    absorption: float = 0.0
    scale: float = 1.0
    effects: Dict[int, tuple[int, int, bool]] = field(default_factory=dict)  # effect_id -> (amplifier, duration, particles)

@dataclass
class Mob(LivingEntity):
    """Base class for mobs."""
    name_tag: str = ""
    always_show_name: bool = False
    no_ai: bool = False
    silent: bool = False
    is_baby: bool = False

@dataclass
class ItemEntity(Entity):
    """Item entity."""
    item_data: Dict[str, Any]
    owner: Optional[uuid.UUID] = None
    throw_force: float = 0.0
    
    def __init__(
        self,
        entity_id: int,
        position: Vector3f,
        rotation: Vector2f,
        item_data: Dict[str, Any]
    ):
        super().__init__(
            entity_id=entity_id,
            entity_type=EntityType.ITEM,
            position=position,
            rotation=rotation
        )
        self.item_data = item_data

class EntityManager:
    """Manages entities in the world."""
    
    def __init__(self):
        self.entities: Dict[int, Entity] = {}
        self.players: Dict[str, Player] = {}
        self.entity_by_uuid: Dict[uuid.UUID, Entity] = {}
        self.next_entity_id: int = 1
    
    def add_entity(self, entity: Entity) -> None:
        """Add an entity to the world."""
        self.entities[entity.entity_id] = entity
        self.entity_by_uuid[entity.uuid] = entity
        
        if isinstance(entity, Player):
            self.players[entity.username] = entity
    
    def remove_entity(self, entity_id: int) -> Optional[Entity]:
        """Remove an entity from the world."""
        entity = self.entities.pop(entity_id, None)
        if entity:
            self.entity_by_uuid.pop(entity.uuid, None)
            if isinstance(entity, Player):
                self.players.pop(entity.username, None)
        return entity
    
    def get_entity(self, entity_id: int) -> Optional[Entity]:
        """Get entity by ID."""
        return self.entities.get(entity_id)
    
    def get_entity_by_uuid(self, uuid: uuid.UUID) -> Optional[Entity]:
        """Get entity by UUID."""
        return self.entity_by_uuid.get(uuid)
    
    def get_player(self, username: str) -> Optional[Player]:
        """Get player by username."""
        return self.players.get(username)
    
    def get_entities_in_range(
        self,
        position: Vector3f,
        radius: float,
        entity_type: Optional[EntityType] = None
    ) -> List[Entity]:
        """Get entities within radius of position."""
        entities = []
        for entity in self.entities.values():
            if entity_type and entity.entity_type != entity_type:
                continue
            
            dx = entity.position.x - position.x
            dy = entity.position.y - position.y
            dz = entity.position.z - position.z
            
            if (dx * dx + dy * dy + dz * dz) <= radius * radius:
                entities.append(entity)
                
        return entities
    
    def update_entity_position(
        self,
        entity_id: int,
        position: Vector3f,
        rotation: Optional[Vector2f] = None,
        on_ground: Optional[bool] = None
    ) -> bool:
        """Update entity position and rotation."""
        entity = self.entities.get(entity_id)
        if not entity:
            return False
            
        entity.position = position
        if rotation:
            entity.rotation = rotation
        if on_ground is not None:
            entity.on_ground = on_ground
            
        return True
    
    def update_entity_metadata(
        self,
        entity_id: int,
        metadata: MetadataDictionary
    ) -> bool:
        """Update entity metadata."""
        entity = self.entities.get(entity_id)
        if not entity:
            return False
            
        entity.metadata = metadata
        return True
    
    def get_next_entity_id(self) -> int:
        """Get next available entity ID."""
        entity_id = self.next_entity_id
        self.next_entity_id += 1
        return entity_id