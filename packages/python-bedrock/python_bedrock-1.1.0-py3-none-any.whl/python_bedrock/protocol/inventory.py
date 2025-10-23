"""Inventory system implementation."""
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Dict, List, Optional, Set, Any
from .nbt import NBTCompound

class WindowType(IntEnum):
    """Container window types."""
    INVENTORY = 0
    CONTAINER = 1
    WORKBENCH = 2
    FURNACE = 3
    ENCHANTMENT = 4
    BREWING_STAND = 5
    ANVIL = 6
    DISPENSER = 7
    DROPPER = 8
    HOPPER = 9
    CAULDRON = 10
    MINECART_CHEST = 11
    MINECART_HOPPER = 12
    HORSE = 13
    BEACON = 14
    STRUCTURE_EDITOR = 15
    TRADING = 16
    COMMAND_BLOCK = 17
    JUKEBOX = 18
    ARMOR = 19
    HAND = 20
    COMPOUND_CREATOR = 21
    MATERIAL_REDUCER = 22
    LAB_TABLE = 23
    LOOM = 24
    LECTERN = 25
    GRINDSTONE = 26
    BLAST_FURNACE = 27
    SMOKER = 28
    STONECUTTER = 29
    CARTOGRAPHY = 30
    HUD = 31
    JIGSAW_EDITOR = 32
    SMITHING_TABLE = 33

@dataclass
class ItemStack:
    """Item stack data."""
    item_id: int
    count: int = 1
    metadata: int = 0
    nbt: Optional[NBTCompound] = None
    
    def is_empty(self) -> bool:
        """Check if stack is empty."""
        return self.item_id == 0 or self.count == 0
    
    def matches(self, other: 'ItemStack') -> bool:
        """Check if items can stack together."""
        if self.is_empty() or other.is_empty():
            return True
        return (
            self.item_id == other.item_id and
            self.metadata == other.metadata and
            self.nbt == other.nbt
        )
    
    def copy(self) -> 'ItemStack':
        """Create a copy of this stack."""
        return ItemStack(
            item_id=self.item_id,
            count=self.count,
            metadata=self.metadata,
            nbt=self.nbt
        )

@dataclass
class Slot:
    """Inventory slot."""
    index: int
    item: Optional[ItemStack] = None
    
    def is_empty(self) -> bool:
        """Check if slot is empty."""
        return not self.item or self.item.is_empty()
    
    def set_item(self, item: Optional[ItemStack]) -> None:
        """Set slot contents."""
        self.item = item
    
    def take_items(self, count: int) -> Optional[ItemStack]:
        """Take items from slot."""
        if not self.item or self.item.count < count:
            return None
            
        if self.item.count == count:
            item = self.item
            self.item = None
            return item
            
        item = self.item.copy()
        item.count = count
        self.item.count -= count
        return item
    
    def can_add(self, item: ItemStack) -> bool:
        """Check if item can be added."""
        if self.is_empty():
            return True
        if not self.item.matches(item):
            return False
        return self.item.count + item.count <= 64  # Max stack size
    
    def add_items(self, item: ItemStack) -> int:
        """Add items to slot, returns number of items that couldn't fit."""
        if not item or item.count == 0:
            return 0
            
        if self.is_empty():
            self.item = item
            return 0
            
        if not self.item.matches(item):
            return item.count
            
        total = self.item.count + item.count
        if total <= 64:
            self.item.count = total
            return 0
            
        overflow = total - 64
        self.item.count = 64
        return overflow

@dataclass
class Container:
    """Base container class."""
    window_id: int
    window_type: WindowType
    size: int
    title: str
    slots: List[Slot] = field(default_factory=list)
    
    def __post_init__(self):
        """Initialize slots."""
        self.slots = [Slot(i) for i in range(self.size)]
    
    def get_slot(self, index: int) -> Optional[Slot]:
        """Get slot at index."""
        if 0 <= index < len(self.slots):
            return self.slots[index]
        return None
    
    def set_slot(self, index: int, item: Optional[ItemStack]) -> bool:
        """Set item in slot."""
        slot = self.get_slot(index)
        if not slot:
            return False
        slot.set_item(item)
        return True
    
    def add_item(self, item: ItemStack) -> int:
        """Add item to container, returns number of items that couldn't fit."""
        remaining = item.count
        
        # Try to stack with existing items first
        for slot in self.slots:
            if not slot.is_empty() and slot.item.matches(item):
                remaining = slot.add_items(ItemStack(
                    item_id=item.item_id,
                    count=remaining,
                    metadata=item.metadata,
                    nbt=item.nbt
                ))
                if remaining == 0:
                    return 0
        
        # Try empty slots
        for slot in self.slots:
            if slot.is_empty():
                remaining = slot.add_items(ItemStack(
                    item_id=item.item_id,
                    count=remaining,
                    metadata=item.metadata,
                    nbt=item.nbt
                ))
                if remaining == 0:
                    return 0
        
        return remaining
    
    def remove_item(self, item_id: int, count: int) -> int:
        """Remove items from container, returns number of items removed."""
        remaining = count
        
        for slot in self.slots:
            if not slot.is_empty() and slot.item.item_id == item_id:
                if slot.item.count <= remaining:
                    remaining -= slot.item.count
                    slot.item = None
                else:
                    slot.item.count -= remaining
                    remaining = 0
                    
                if remaining == 0:
                    break
        
        return count - remaining
    
    def has_item(self, item_id: int, count: int = 1) -> bool:
        """Check if container has items."""
        total = 0
        for slot in self.slots:
            if not slot.is_empty() and slot.item.item_id == item_id:
                total += slot.item.count
                if total >= count:
                    return True
        return False
    
    def count_item(self, item_id: int) -> int:
        """Count total of an item type."""
        total = 0
        for slot in self.slots:
            if not slot.is_empty() and slot.item.item_id == item_id:
                total += slot.item.count
        return total

@dataclass
class PlayerInventory(Container):
    """Player inventory container."""
    
    def __init__(self, window_id: int):
        super().__init__(
            window_id=window_id,
            window_type=WindowType.INVENTORY,
            size=36,  # Main inventory
            title="Inventory"
        )
        # Additional slots
        self.armor = [Slot(i) for i in range(4)]  # Armor slots
        self.offhand = Slot(40)  # Offhand slot
        self.crafting = [Slot(i) for i in range(4)]  # Crafting grid
        self.crafting_result = Slot(44)  # Crafting result
    
    def get_hotbar_slot(self, index: int) -> Optional[Slot]:
        """Get hotbar slot (0-8)."""
        if 0 <= index < 9:
            return self.slots[index]
        return None
    
    def get_inventory_slot(self, index: int) -> Optional[Slot]:
        """Get main inventory slot (9-35)."""
        if 9 <= index < 36:
            return self.slots[index]
        return None
    
    def get_armor_slot(self, index: int) -> Optional[Slot]:
        """Get armor slot (0-3)."""
        if 0 <= index < 4:
            return self.armor[index]
        return None
    
    def get_crafting_slot(self, index: int) -> Optional[Slot]:
        """Get crafting grid slot (0-3)."""
        if 0 <= index < 4:
            return self.crafting[index]
        return None

class WindowManager:
    """Manages inventory windows."""
    
    def __init__(self):
        self.windows: Dict[int, Container] = {}
        self.next_window_id: int = 1
    
    def create_window(
        self,
        window_type: WindowType,
        size: int,
        title: str
    ) -> Container:
        """Create a new window."""
        window_id = self.next_window_id
        self.next_window_id += 1
        
        container = Container(window_id, window_type, size, title)
        self.windows[window_id] = container
        return container
    
    def remove_window(self, window_id: int) -> Optional[Container]:
        """Remove a window."""
        return self.windows.pop(window_id, None)
    
    def get_window(self, window_id: int) -> Optional[Container]:
        """Get window by ID."""
        return self.windows.get(window_id)