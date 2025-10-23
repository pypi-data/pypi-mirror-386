"""NBT (Named Binary Tag) implementation."""
from dataclasses import dataclass
from enum import IntEnum
import struct
from typing import Any, Dict, List, Optional, Union

class TagType(IntEnum):
    """NBT tag types."""
    END = 0
    BYTE = 1
    SHORT = 2
    INT = 3
    LONG = 4
    FLOAT = 5
    DOUBLE = 6
    BYTE_ARRAY = 7
    STRING = 8
    LIST = 9
    COMPOUND = 10
    INT_ARRAY = 11
    LONG_ARRAY = 12

@dataclass
class NBTTag:
    """Base NBT tag."""
    name: str
    tag_type: TagType
    
    def write(self) -> bytes:
        """Write tag to bytes."""
        # Write tag type and name
        result = bytearray([self.tag_type])
        if self.tag_type != TagType.END:
            name_bytes = self.name.encode('utf-8')
            result.extend(struct.pack('>H', len(name_bytes)))
            result.extend(name_bytes)
            result.extend(self._write_payload())
        return bytes(result)
    
    def _write_payload(self) -> bytes:
        """Write tag payload."""
        raise NotImplementedError()
    
    @classmethod
    def read(cls, data: bytes, offset: int = 0) -> tuple['NBTTag', int]:
        """Read tag from bytes."""
        # Read tag type
        tag_type = TagType(data[offset])
        offset += 1
        
        # End tag has no name or payload
        if tag_type == TagType.END:
            return NBTEnd(""), offset
            
        # Read name
        name_length = struct.unpack('>H', data[offset:offset+2])[0]
        offset += 2
        name = data[offset:offset+name_length].decode('utf-8')
        offset += name_length
        
        # Read payload based on type
        return cls._read_payload(tag_type, name, data, offset)
    
    @classmethod
    def _read_payload(
        cls,
        tag_type: TagType,
        name: str,
        data: bytes,
        offset: int
    ) -> tuple['NBTTag', int]:
        """Read tag payload."""
        raise NotImplementedError()

@dataclass
class NBTEnd(NBTTag):
    """NBT end tag."""
    def __init__(self, name: str = ""):
        super().__init__(name, TagType.END)
    
    def _write_payload(self) -> bytes:
        return b""

@dataclass
class NBTByte(NBTTag):
    """NBT byte tag."""
    value: int
    
    def __init__(self, name: str, value: int):
        super().__init__(name, TagType.BYTE)
        self.value = value
    
    def _write_payload(self) -> bytes:
        return struct.pack('b', self.value)
    
    @classmethod
    def _read_payload(cls, tag_type: TagType, name: str,
                     data: bytes, offset: int) -> tuple['NBTByte', int]:
        value = struct.unpack('b', data[offset:offset+1])[0]
        return cls(name, value), offset + 1

@dataclass
class NBTShort(NBTTag):
    """NBT short tag."""
    value: int
    
    def __init__(self, name: str, value: int):
        super().__init__(name, TagType.SHORT)
        self.value = value
    
    def _write_payload(self) -> bytes:
        return struct.pack('>h', self.value)
    
    @classmethod
    def _read_payload(cls, tag_type: TagType, name: str,
                     data: bytes, offset: int) -> tuple['NBTShort', int]:
        value = struct.unpack('>h', data[offset:offset+2])[0]
        return cls(name, value), offset + 2

@dataclass
class NBTInt(NBTTag):
    """NBT int tag."""
    value: int
    
    def __init__(self, name: str, value: int):
        super().__init__(name, TagType.INT)
        self.value = value
    
    def _write_payload(self) -> bytes:
        return struct.pack('>i', self.value)
    
    @classmethod
    def _read_payload(cls, tag_type: TagType, name: str,
                     data: bytes, offset: int) -> tuple['NBTInt', int]:
        value = struct.unpack('>i', data[offset:offset+4])[0]
        return cls(name, value), offset + 4

@dataclass
class NBTLong(NBTTag):
    """NBT long tag."""
    value: int
    
    def __init__(self, name: str, value: int):
        super().__init__(name, TagType.LONG)
        self.value = value
    
    def _write_payload(self) -> bytes:
        return struct.pack('>q', self.value)
    
    @classmethod
    def _read_payload(cls, tag_type: TagType, name: str,
                     data: bytes, offset: int) -> tuple['NBTLong', int]:
        value = struct.unpack('>q', data[offset:offset+8])[0]
        return cls(name, value), offset + 8

@dataclass
class NBTFloat(NBTTag):
    """NBT float tag."""
    value: float
    
    def __init__(self, name: str, value: float):
        super().__init__(name, TagType.FLOAT)
        self.value = value
    
    def _write_payload(self) -> bytes:
        return struct.pack('>f', self.value)
    
    @classmethod
    def _read_payload(cls, tag_type: TagType, name: str,
                     data: bytes, offset: int) -> tuple['NBTFloat', int]:
        value = struct.unpack('>f', data[offset:offset+4])[0]
        return cls(name, value), offset + 4

@dataclass
class NBTDouble(NBTTag):
    """NBT double tag."""
    value: float
    
    def __init__(self, name: str, value: float):
        super().__init__(name, TagType.DOUBLE)
        self.value = value
    
    def _write_payload(self) -> bytes:
        return struct.pack('>d', self.value)
    
    @classmethod
    def _read_payload(cls, tag_type: TagType, name: str,
                     data: bytes, offset: int) -> tuple['NBTDouble', int]:
        value = struct.unpack('>d', data[offset:offset+8])[0]
        return cls(name, value), offset + 8

@dataclass
class NBTByteArray(NBTTag):
    """NBT byte array tag."""
    value: bytes
    
    def __init__(self, name: str, value: bytes):
        super().__init__(name, TagType.BYTE_ARRAY)
        self.value = value
    
    def _write_payload(self) -> bytes:
        result = struct.pack('>I', len(self.value))
        result += self.value
        return result
    
    @classmethod
    def _read_payload(cls, tag_type: TagType, name: str,
                     data: bytes, offset: int) -> tuple['NBTByteArray', int]:
        length = struct.unpack('>I', data[offset:offset+4])[0]
        offset += 4
        value = data[offset:offset+length]
        return cls(name, value), offset + length

@dataclass
class NBTString(NBTTag):
    """NBT string tag."""
    value: str
    
    def __init__(self, name: str, value: str):
        super().__init__(name, TagType.STRING)
        self.value = value
    
    def _write_payload(self) -> bytes:
        string_bytes = self.value.encode('utf-8')
        result = struct.pack('>H', len(string_bytes))
        result += string_bytes
        return result
    
    @classmethod
    def _read_payload(cls, tag_type: TagType, name: str,
                     data: bytes, offset: int) -> tuple['NBTString', int]:
        length = struct.unpack('>H', data[offset:offset+2])[0]
        offset += 2
        value = data[offset:offset+length].decode('utf-8')
        return cls(name, value), offset + length

@dataclass
class NBTList(NBTTag):
    """NBT list tag."""
    element_type: TagType
    values: List[NBTTag]
    
    def __init__(self, name: str, element_type: TagType, values: List[NBTTag]):
        super().__init__(name, TagType.LIST)
        self.element_type = element_type
        self.values = values
    
    def _write_payload(self) -> bytes:
        result = bytearray([self.element_type])
        result.extend(struct.pack('>I', len(self.values)))
        for value in self.values:
            result.extend(value._write_payload())
        return bytes(result)
    
    @classmethod
    def _read_payload(cls, tag_type: TagType, name: str,
                     data: bytes, offset: int) -> tuple['NBTList', int]:
        element_type = TagType(data[offset])
        offset += 1
        length = struct.unpack('>I', data[offset:offset+4])[0]
        offset += 4
        
        values = []
        for _ in range(length):
            tag, offset = TAG_READERS[element_type](
                element_type, "", data, offset)
            values.append(tag)
            
        return cls(name, element_type, values), offset

@dataclass
class NBTCompound(NBTTag):
    """NBT compound tag."""
    value: Dict[str, NBTTag]
    
    def __init__(self, name: str, value: Dict[str, NBTTag]):
        super().__init__(name, TagType.COMPOUND)
        self.value = value
    
    def _write_payload(self) -> bytes:
        result = bytearray()
        for tag in self.value.values():
            result.extend(tag.write())
        result.extend(NBTEnd().write())
        return bytes(result)
    
    @classmethod
    def _read_payload(cls, tag_type: TagType, name: str,
                     data: bytes, offset: int) -> tuple['NBTCompound', int]:
        value = {}
        while True:
            tag, new_offset = NBTTag.read(data, offset)
            if tag.tag_type == TagType.END:
                break
            value[tag.name] = tag
            offset = new_offset
            
        return cls(name, value), offset

@dataclass
class NBTIntArray(NBTTag):
    """NBT int array tag."""
    value: List[int]
    
    def __init__(self, name: str, value: List[int]):
        super().__init__(name, TagType.INT_ARRAY)
        self.value = value
    
    def _write_payload(self) -> bytes:
        result = struct.pack('>I', len(self.value))
        for v in self.value:
            result += struct.pack('>i', v)
        return result
    
    @classmethod
    def _read_payload(cls, tag_type: TagType, name: str,
                     data: bytes, offset: int) -> tuple['NBTIntArray', int]:
        length = struct.unpack('>I', data[offset:offset+4])[0]
        offset += 4
        value = []
        for _ in range(length):
            v = struct.unpack('>i', data[offset:offset+4])[0]
            value.append(v)
            offset += 4
        return cls(name, value), offset

@dataclass
class NBTLongArray(NBTTag):
    """NBT long array tag."""
    value: List[int]
    
    def __init__(self, name: str, value: List[int]):
        super().__init__(name, TagType.LONG_ARRAY)
        self.value = value
    
    def _write_payload(self) -> bytes:
        result = struct.pack('>I', len(self.value))
        for v in self.value:
            result += struct.pack('>q', v)
        return result
    
    @classmethod
    def _read_payload(cls, tag_type: TagType, name: str,
                     data: bytes, offset: int) -> tuple['NBTLongArray', int]:
        length = struct.unpack('>I', data[offset:offset+4])[0]
        offset += 4
        value = []
        for _ in range(length):
            v = struct.unpack('>q', data[offset:offset+8])[0]
            value.append(v)
            offset += 8
        return cls(name, value), offset

# Map tag types to reader functions
TAG_READERS = {
    TagType.END: NBTEnd._read_payload,
    TagType.BYTE: NBTByte._read_payload,
    TagType.SHORT: NBTShort._read_payload,
    TagType.INT: NBTInt._read_payload,
    TagType.LONG: NBTLong._read_payload,
    TagType.FLOAT: NBTFloat._read_payload,
    TagType.DOUBLE: NBTDouble._read_payload,
    TagType.BYTE_ARRAY: NBTByteArray._read_payload,
    TagType.STRING: NBTString._read_payload,
    TagType.LIST: NBTList._read_payload,
    TagType.COMPOUND: NBTCompound._read_payload,
    TagType.INT_ARRAY: NBTIntArray._read_payload,
    TagType.LONG_ARRAY: NBTLongArray._read_payload
}

def read_nbt(data: bytes) -> NBTTag:
    """Read an NBT tag from bytes."""
    tag, _ = NBTTag.read(data)
    return tag

def write_nbt(tag: NBTTag) -> bytes:
    """Write an NBT tag to bytes."""
    return tag.write()