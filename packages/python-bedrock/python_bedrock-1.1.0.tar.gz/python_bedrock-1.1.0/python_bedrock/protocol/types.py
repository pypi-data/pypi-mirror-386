"""Bedrock protocol data types and structures."""
from dataclasses import dataclass
from enum import IntEnum
import struct
import uuid
from typing import Any, List, Optional, Union, Dict, Tuple

class DataType:
    """Base class for protocol data types."""
    
    @classmethod
    def read(cls, data: bytes, offset: int = 0) -> tuple[Any, int]:
        """Read value from bytes."""
        raise NotImplementedError()
    
    @classmethod
    def write(cls, value: Any) -> bytes:
        """Write value to bytes."""
        raise NotImplementedError()

class Boolean(DataType):
    """Boolean data type (1 byte)."""
    
    @classmethod
    def read(cls, data: bytes, offset: int = 0) -> tuple[bool, int]:
        return bool(data[offset]), offset + 1
    
    @classmethod
    def write(cls, value: bool) -> bytes:
        return bytes([1 if value else 0])

class Byte(DataType):
    """Signed byte data type (1 byte)."""
    
    @classmethod
    def read(cls, data: bytes, offset: int = 0) -> tuple[int, int]:
        return struct.unpack('b', data[offset:offset+1])[0], offset + 1
    
    @classmethod
    def write(cls, value: int) -> bytes:
        return struct.pack('b', value)

class UnsignedByte(DataType):
    """Unsigned byte data type (1 byte)."""
    
    @classmethod
    def read(cls, data: bytes, offset: int = 0) -> tuple[int, int]:
        return struct.unpack('B', data[offset:offset+1])[0], offset + 1
    
    @classmethod
    def write(cls, value: int) -> bytes:
        return struct.pack('B', value)

class Short(DataType):
    """Signed short data type (2 bytes)."""
    
    @classmethod
    def read(cls, data: bytes, offset: int = 0) -> tuple[int, int]:
        return struct.unpack('>h', data[offset:offset+2])[0], offset + 2
    
    @classmethod
    def write(cls, value: int) -> bytes:
        return struct.pack('>h', value)

class UnsignedShort(DataType):
    """Unsigned short data type (2 bytes)."""
    
    @classmethod
    def read(cls, data: bytes, offset: int = 0) -> tuple[int, int]:
        return struct.unpack('>H', data[offset:offset+2])[0], offset + 2
    
    @classmethod
    def write(cls, value: int) -> bytes:
        return struct.pack('>H', value)

class Int(DataType):
    """Signed integer data type (4 bytes)."""
    
    @classmethod
    def read(cls, data: bytes, offset: int = 0) -> tuple[int, int]:
        return struct.unpack('>i', data[offset:offset+4])[0], offset + 4
    
    @classmethod
    def write(cls, value: int) -> bytes:
        return struct.pack('>i', value)

class UnsignedInt(DataType):
    """Unsigned integer data type (4 bytes)."""
    
    @classmethod
    def read(cls, data: bytes, offset: int = 0) -> tuple[int, int]:
        return struct.unpack('>I', data[offset:offset+4])[0], offset + 4
    
    @classmethod
    def write(cls, value: int) -> bytes:
        return struct.pack('>I', value)

class Long(DataType):
    """Signed long data type (8 bytes)."""
    
    @classmethod
    def read(cls, data: bytes, offset: int = 0) -> tuple[int, int]:
        return struct.unpack('>q', data[offset:offset+8])[0], offset + 8
    
    @classmethod
    def write(cls, value: int) -> bytes:
        return struct.pack('>q', value)

class UnsignedLong(DataType):
    """Unsigned long data type (8 bytes)."""
    
    @classmethod
    def read(cls, data: bytes, offset: int = 0) -> tuple[int, int]:
        return struct.unpack('>Q', data[offset:offset+8])[0], offset + 8
    
    @classmethod
    def write(cls, value: int) -> bytes:
        return struct.pack('>Q', value)

class Float(DataType):
    """Float data type (4 bytes)."""
    
    @classmethod
    def read(cls, data: bytes, offset: int = 0) -> tuple[float, int]:
        return struct.unpack('>f', data[offset:offset+4])[0], offset + 4
    
    @classmethod
    def write(cls, value: float) -> bytes:
        return struct.pack('>f', value)

class Double(DataType):
    """Double data type (8 bytes)."""
    
    @classmethod
    def read(cls, data: bytes, offset: int = 0) -> tuple[float, int]:
        return struct.unpack('>d', data[offset:offset+8])[0], offset + 8
    
    @classmethod
    def write(cls, value: float) -> bytes:
        return struct.pack('>d', value)

class String(DataType):
    """String data type (prefixed with length)."""
    
    @classmethod
    def read(cls, data: bytes, offset: int = 0) -> tuple[str, int]:
        length, new_offset = VarInt.read(data, offset)
        string = data[new_offset:new_offset+length].decode('utf-8')
        return string, new_offset + length
    
    @classmethod
    def write(cls, value: str) -> bytes:
        string_bytes = value.encode('utf-8')
        return VarInt.write(len(string_bytes)) + string_bytes

class UUID(DataType):
    """UUID data type (16 bytes)."""
    
    @classmethod
    def read(cls, data: bytes, offset: int = 0) -> tuple[uuid.UUID, int]:
        return uuid.UUID(bytes=data[offset:offset+16]), offset + 16
    
    @classmethod
    def write(cls, value: uuid.UUID) -> bytes:
        return value.bytes

class ByteArray(DataType):
    """Byte array data type (prefixed with length)."""
    
    @classmethod
    def read(cls, data: bytes, offset: int = 0) -> tuple[bytes, int]:
        length, new_offset = VarInt.read(data, offset)
        return data[new_offset:new_offset+length], new_offset + length
    
    @classmethod
    def write(cls, value: bytes) -> bytes:
        return VarInt.write(len(value)) + value

class VarInt(DataType):
    """Variable-length integer data type."""
    
    @classmethod
    def read(cls, data: bytes, offset: int = 0) -> tuple[int, int]:
        value = 0
        position = 0
        current_offset = offset
        
        while True:
            byte = data[current_offset]
            value |= (byte & 0x7F) << position
            current_offset += 1
            
            if not (byte & 0x80):
                break
                
            position += 7
            if position > 35:
                raise ValueError("VarInt is too big")
                
        return value, current_offset
    
    @classmethod
    def write(cls, value: int) -> bytes:
        result = bytearray()
        
        while True:
            byte = value & 0x7F
            value >>= 7
            
            if value:
                byte |= 0x80
            
            result.append(byte)
            
            if not value:
                break
                
        return bytes(result)

class VarLong(DataType):
    """Variable-length long data type."""
    
    @classmethod
    def read(cls, data: bytes, offset: int = 0) -> tuple[int, int]:
        value = 0
        position = 0
        current_offset = offset
        
        while True:
            byte = data[current_offset]
            value |= (byte & 0x7F) << position
            current_offset += 1
            
            if not (byte & 0x80):
                break
                
            position += 7
            if position > 70:
                raise ValueError("VarLong is too big")
                
        return value, current_offset
    
    @classmethod
    def write(cls, value: int) -> bytes:
        result = bytearray()
        
        while True:
            byte = value & 0x7F
            value >>= 7
            
            if value:
                byte |= 0x80
            
            result.append(byte)
            
            if not value:
                break
                
        return bytes(result)

@dataclass
class Vector2f:
    """2D float vector."""
    x: float
    y: float
    
    @classmethod
    def read(cls, data: bytes, offset: int = 0) -> tuple['Vector2f', int]:
        x, offset = Float.read(data, offset)
        y, offset = Float.read(data, offset)
        return cls(x, y), offset
    
    def write(self) -> bytes:
        return Float.write(self.x) + Float.write(self.y)

@dataclass
class Vector3f:
    """3D float vector."""
    x: float
    y: float
    z: float
    
    @classmethod
    def read(cls, data: bytes, offset: int = 0) -> tuple['Vector3f', int]:
        x, offset = Float.read(data, offset)
        y, offset = Float.read(data, offset)
        z, offset = Float.read(data, offset)
        return cls(x, y, z), offset
    
    def write(self) -> bytes:
        return Float.write(self.x) + Float.write(self.y) + Float.write(self.z)

@dataclass
class Vector3i:
    """3D integer vector."""
    x: int
    y: int
    z: int
    
    @classmethod
    def read(cls, data: bytes, offset: int = 0) -> tuple['Vector3i', int]:
        x, offset = VarInt.read(data, offset)
        y, offset = VarInt.read(data, offset)
        z, offset = VarInt.read(data, offset)
        return cls(x, y, z), offset
    
    def write(self) -> bytes:
        return VarInt.write(self.x) + VarInt.write(self.y) + VarInt.write(self.z)

@dataclass
class MetadataValue:
    """Entity metadata value."""
    type: int
    value: Any
    
    TYPE_BYTE = 0
    TYPE_SHORT = 1
    TYPE_INT = 2
    TYPE_FLOAT = 3
    TYPE_STRING = 4
    TYPE_ITEM = 5
    TYPE_POS = 6
    TYPE_ROTATION = 7
    TYPE_LONG = 8
    
    @classmethod
    def read(cls, data: bytes, offset: int = 0) -> tuple['MetadataValue', int]:
        type_id, offset = UnsignedByte.read(data, offset)
        
        if type_id == cls.TYPE_BYTE:
            value, offset = Byte.read(data, offset)
        elif type_id == cls.TYPE_SHORT:
            value, offset = Short.read(data, offset)
        elif type_id == cls.TYPE_INT:
            value, offset = Int.read(data, offset)
        elif type_id == cls.TYPE_FLOAT:
            value, offset = Float.read(data, offset)
        elif type_id == cls.TYPE_STRING:
            value, offset = String.read(data, offset)
        elif type_id == cls.TYPE_ITEM:
            # TODO: Implement item reading
            value = None
        elif type_id == cls.TYPE_POS:
            value, offset = Vector3i.read(data, offset)
        elif type_id == cls.TYPE_ROTATION:
            value, offset = Vector3f.read(data, offset)
        elif type_id == cls.TYPE_LONG:
            value, offset = Long.read(data, offset)
        else:
            raise ValueError(f"Unknown metadata type: {type_id}")
            
        return cls(type_id, value), offset
    
    def write(self) -> bytes:
        result = UnsignedByte.write(self.type)
        
        if self.type == self.TYPE_BYTE:
            result += Byte.write(self.value)
        elif self.type == self.TYPE_SHORT:
            result += Short.write(self.value)
        elif self.type == self.TYPE_INT:
            result += Int.write(self.value)
        elif self.type == self.TYPE_FLOAT:
            result += Float.write(self.value)
        elif self.type == self.TYPE_STRING:
            result += String.write(self.value)
        elif self.type == self.TYPE_ITEM:
            # TODO: Implement item writing
            pass
        elif self.type == self.TYPE_POS:
            result += self.value.write()
        elif self.type == self.TYPE_ROTATION:
            result += self.value.write()
        elif self.type == self.TYPE_LONG:
            result += Long.write(self.value)
            
        return result

@dataclass
class MetadataDictionary:
    """Entity metadata dictionary."""
    values: Dict[int, MetadataValue]
    
    @classmethod
    def read(cls, data: bytes, offset: int = 0) -> tuple['MetadataDictionary', int]:
        values = {}
        
        while True:
            key, offset = UnsignedByte.read(data, offset)
            if key == 0xFF:  # End marker
                break
                
            value, offset = MetadataValue.read(data, offset)
            values[key] = value
            
        return cls(values), offset
    
    def write(self) -> bytes:
        result = bytearray()
        
        for key, value in self.values.items():
            result.extend(UnsignedByte.write(key))
            result.extend(value.write())
            
        result.append(0xFF)  # End marker
        return bytes(result)