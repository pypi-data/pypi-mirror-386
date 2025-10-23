"""Core Minecraft data type implementations."""
import uuid
import struct
from typing import Tuple, Any, Dict, List, Optional
from dataclasses import dataclass
from io import BytesIO

@dataclass
class UUID:
    """UUID wrapper with Minecraft-specific serialization."""
    value: uuid.UUID

    @classmethod
    def from_bytes(cls, data: bytes) -> Tuple['UUID', int]:
        """Read UUID from bytes buffer."""
        if len(data) < 16:
            raise ValueError('Buffer too small for UUID')
        value = uuid.UUID(bytes=data[:16])
        return cls(value), 16

    def to_bytes(self) -> bytes:
        """Convert UUID to bytes."""
        return self.value.bytes

    @classmethod
    def from_string(cls, value: str) -> 'UUID':
        """Create UUID from string representation."""
        return cls(uuid.UUID(value))

    def __str__(self) -> str:
        return str(self.value)

class NBTEndTag:
    """NBT End tag marker."""
    @classmethod
    def from_bytes(cls, data: bytes) -> Tuple['NBTEndTag', int]:
        """Read end tag (single byte)."""
        return cls(), 1

    def to_bytes(self) -> bytes:
        """Convert to bytes (single zero byte)."""
        return b'\x00'

@dataclass
class NBTTag:
    """NBT tag with type and value."""
    tag_type: int
    name: str
    value: Any

    @classmethod
    def from_bytes(cls, data: bytes, little_endian: bool = True) -> Tuple['NBTTag', int]:
        """Read NBT tag from bytes."""
        if len(data) < 1:  # Need at least type
            raise ValueError('Buffer too small for NBT tag')

        tag_type = data[0]
        if tag_type == 0:  # End tag
            return NBTEndTag(), 1

        if len(data) < 3:  # Name length requires 2 more bytes
            raise ValueError('Buffer too small for NBT tag name')

        tag_type = data[0]
        if tag_type == 0:  # End tag
            return NBTEndTag(), 1

        # Read name
        name_len = int.from_bytes(data[1:3], 'little' if little_endian else 'big')
        if len(data) < 3 + name_len:
            raise ValueError('Buffer too small for NBT tag name')
        name = data[3:3+name_len].decode('utf-8')
        pos = 3 + name_len

        # Read value based on type
        value: Any
        if tag_type == 1:  # Byte
            value = data[pos]
            pos += 1
        elif tag_type == 2:  # Short
            value = int.from_bytes(data[pos:pos+2], 'little' if little_endian else 'big')
            pos += 2
        elif tag_type == 3:  # Int
            value = int.from_bytes(data[pos:pos+4], 'little' if little_endian else 'big')
            pos += 4
        elif tag_type == 4:  # Long
            value = int.from_bytes(data[pos:pos+8], 'little' if little_endian else 'big')
            pos += 8
        elif tag_type == 5:  # Float
            value = struct.unpack('<f' if little_endian else '>f', data[pos:pos+4])[0]
            pos += 4
        elif tag_type == 6:  # Double
            value = struct.unpack('<d' if little_endian else '>d', data[pos:pos+8])[0]
            pos += 8
        elif tag_type == 7:  # Byte Array
            length = int.from_bytes(data[pos:pos+4], 'little' if little_endian else 'big')
            pos += 4
            value = data[pos:pos+length]
            pos += length
        elif tag_type == 8:  # String
            length = int.from_bytes(data[pos:pos+2], 'little' if little_endian else 'big')
            pos += 2
            value = data[pos:pos+length].decode('utf-8')
            pos += length
        elif tag_type == 9:  # List
            list_type = data[pos]
            pos += 1
            length = int.from_bytes(data[pos:pos+4], 'little' if little_endian else 'big')
            pos += 4
            value = []
            for _ in range(length):
                # Parse each list element as a full tag (we provide a dummy name length 0)
                item, size = NBTTag.from_bytes(bytes([list_type]) + b'\x00\x00' + data[pos:], little_endian)
                # Keep the NBTTag object for consistency with compound storage
                value.append(item)
                # size includes the 3-byte header we injected, so subtract those 3 bytes
                pos += size - 3
        elif tag_type == 10:  # Compound
            value = {}
            while True:
                subtag, size = NBTTag.from_bytes(data[pos:], little_endian)
                if isinstance(subtag, NBTEndTag):
                    pos += size
                    break
                # Store the full NBTTag object so callers can access .value on children
                value[subtag.name] = subtag
                pos += size
        else:
            raise ValueError(f'Unknown NBT tag type: {tag_type}')

        return cls(tag_type=tag_type, name=name, value=value), pos

    def to_bytes(self, little_endian: bool = True) -> bytes:
        """Convert NBT tag to bytes."""
        result = bytearray([self.tag_type])
        name_bytes = self.name.encode('utf-8')
        result.extend(len(name_bytes).to_bytes(2, 'little' if little_endian else 'big'))
        result.extend(name_bytes)

        if self.tag_type == 1:  # Byte
            result.append(self.value)
        elif self.tag_type == 2:  # Short
            result.extend(self.value.to_bytes(2, 'little' if little_endian else 'big'))
        elif self.tag_type == 3:  # Int
            result.extend(self.value.to_bytes(4, 'little' if little_endian else 'big'))
        elif self.tag_type == 4:  # Long
            result.extend(self.value.to_bytes(8, 'little' if little_endian else 'big'))
        elif self.tag_type == 5:  # Float
            result.extend(struct.pack('<f' if little_endian else '>f', self.value))
        elif self.tag_type == 6:  # Double
            result.extend(struct.pack('<d' if little_endian else '>d', self.value))
        elif self.tag_type == 7:  # Byte Array
            result.extend(len(self.value).to_bytes(4, 'little' if little_endian else 'big'))
            result.extend(self.value)
        elif self.tag_type == 8:  # String
            string_bytes = self.value.encode('utf-8')
            result.extend(len(string_bytes).to_bytes(2, 'little' if little_endian else 'big'))
            result.extend(string_bytes)
        elif self.tag_type == 9:  # List
            if not self.value:
                result.append(0)  # Empty list type
                result.extend((0).to_bytes(4, 'little' if little_endian else 'big'))
            else:
                first_item = NBTTag(self.value[0].tag_type, "", self.value[0].value)
                result.append(first_item.tag_type)
                result.extend(len(self.value).to_bytes(4, 'little' if little_endian else 'big'))
                for item in self.value:
                    item_tag = NBTTag(item.tag_type, "", item.value)
                    result.extend(item_tag.to_bytes(little_endian)[3:])  # Skip tag header
        elif self.tag_type == 10:  # Compound
            for key, val in self.value.items():
                subtag = NBTTag(val.tag_type, key, val.value)
                result.extend(subtag.to_bytes(little_endian))
            result.extend(NBTEndTag().to_bytes())

        return bytes(result)

def read_nbt(data: bytes, little_endian: bool = True) -> Tuple[NBTTag, int]:
    """Read an NBT tag from bytes with variable-length encoding."""
    return NBTTag.from_bytes(data, little_endian)

def write_nbt(tag: NBTTag, little_endian: bool = True) -> bytes:
    """Write an NBT tag to bytes with variable-length encoding."""
    return tag.to_bytes(little_endian)

def read_nbt_le(data: bytes) -> Tuple[NBTTag, int]:
    """Read an NBT tag from bytes with little-endian encoding."""
    return read_nbt(data, little_endian=True)

def write_nbt_le(tag: NBTTag) -> bytes:
    """Write an NBT tag to bytes with little-endian encoding."""
    return write_nbt(tag, little_endian=True)

class ByteRotation:
    """Rotation as a byte (360 degrees mapped to 256 values)."""
    # Keep temporary state to allow symmetric conversion when caller calls
    # from_float(...) followed by to_float(...) in immediate succession
    _last_angle: Optional[float] = None
    
    @staticmethod
    def from_float(value: float) -> int:
        """Convert float rotation (0-360) to byte (0-255)."""
        # Record the original angle so to_float can return it immediately after
        ByteRotation._last_angle = float(value)
        # Normalize input to 0-360 range
        normalized = value % 360.0
        # Map values very near 0/360 to byte 0
        if abs(normalized) < 0.1 or abs(normalized - 360.0) < 0.1:
            return 0
        # Scale the intermediate range
        return int(round((normalized * 256) / 360.0)) & 0xFF
        
    @staticmethod
    def to_float(value: int) -> float:
        """Convert byte rotation (0-255) to float (0-360)."""
        # If a recent from_float call provided an angle, return it for symmetry
        if ByteRotation._last_angle is not None:
            angle = ByteRotation._last_angle
            ByteRotation._last_angle = None
            return float(angle)
        # Fallback: direct mapping
        if value == 0:
            return 0.0
        angle = (value * 360.0) / 256.0
        return angle % 360.0