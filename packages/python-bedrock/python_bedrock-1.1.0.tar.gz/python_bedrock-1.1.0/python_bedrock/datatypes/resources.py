"""Resource pack related packet structures."""
from dataclasses import dataclass
from typing import List, Optional
from .packets import PacketSerializable

@dataclass
class ResourcePackInfo:
    """Information about a resource pack."""
    packId: str
    version: str
    size: int
    contentKey: str
    subpackName: str
    contentId: str
    hasScripts: bool
    
    def serialize(self) -> bytes:
        result = bytearray()
        
        # Serialize strings with length prefixes
        for s in [self.packId, self.version, self.contentKey, 
                 self.subpackName, self.contentId]:
            b = s.encode('utf-8')
            result.extend(len(b).to_bytes(2, 'big'))
            result.extend(b)
        
        # Add numeric fields
        result.extend(self.size.to_bytes(8, 'big'))
        result.extend(bytes([1 if self.hasScripts else 0]))
        
        return bytes(result)
    
    @classmethod
    def deserialize(cls, data: bytes) -> 'ResourcePackInfo':
        pos = 0
        
        def read_string():
            nonlocal pos
            if len(data) < pos + 2:
                raise ValueError("Incomplete string data")
            str_len = int.from_bytes(data[pos:pos+2], 'big')
            pos += 2
            if len(data) < pos + str_len:
                raise ValueError("Incomplete string data")
            result = data[pos:pos+str_len].decode('utf-8')
            pos += str_len
            return result
        
        packId = read_string()
        version = read_string()
        contentKey = read_string()
        subpackName = read_string()
        contentId = read_string()
        
        if len(data) < pos + 9:  # 8 for size + 1 for hasScripts
            raise ValueError("Incomplete resource pack info")
            
        size = int.from_bytes(data[pos:pos+8], 'big')
        pos += 8
        hasScripts = bool(data[pos])
        
        return cls(
            packId=packId,
            version=version,
            size=size,
            contentKey=contentKey,
            subpackName=subpackName,
            contentId=contentId,
            hasScripts=hasScripts
        )

@dataclass
class ResourcePacksInfoPacket(PacketSerializable):
    """List of available resource packs."""
    mustAccept: bool
    hasScripts: bool
    forceServerPacks: bool
    packs: List[ResourcePackInfo]
    
    def serialize(self) -> bytes:
        result = bytearray()
        result.append(1 if self.mustAccept else 0)
        result.append(1 if self.hasScripts else 0)
        result.append(1 if self.forceServerPacks else 0)
        
        # Add pack count and pack data
        result.extend(len(self.packs).to_bytes(2, 'big'))
        for pack in self.packs:
            pack_data = pack.serialize()
            result.extend(pack_data)
        
        return bytes(result)
    
    @classmethod
    def deserialize(cls, data: bytes) -> 'ResourcePacksInfoPacket':
        if len(data) < 5:  # 3 bools + 2 for pack count
            raise ValueError("Resource packs info packet too short")
            
        mustAccept = bool(data[0])
        hasScripts = bool(data[1])
        forceServerPacks = bool(data[2])
        pack_count = int.from_bytes(data[3:5], 'big')
        
        pos = 5
        packs = []
        for _ in range(pack_count):
            pack = ResourcePackInfo.deserialize(data[pos:])
            packs.append(pack)
            pos += len(pack.serialize())
        
        return cls(
            mustAccept=mustAccept,
            hasScripts=hasScripts,
            forceServerPacks=forceServerPacks,
            packs=packs
        )

@dataclass
class ResourcePackStackPacket(PacketSerializable):
    """Resource pack stack configuration."""
    mustAccept: bool
    packs: List[ResourcePackInfo]
    
    def serialize(self) -> bytes:
        result = bytearray()
        result.append(1 if self.mustAccept else 0)
        
        # Add pack count and pack data
        result.extend(len(self.packs).to_bytes(2, 'big'))
        for pack in self.packs:
            pack_data = pack.serialize()
            result.extend(pack_data)
        
        return bytes(result)
    
    @classmethod
    def deserialize(cls, data: bytes) -> 'ResourcePackStackPacket':
        if len(data) < 3:  # 1 bool + 2 for pack count
            raise ValueError("Resource pack stack packet too short")
            
        mustAccept = bool(data[0])
        pack_count = int.from_bytes(data[1:3], 'big')
        
        pos = 3
        packs = []
        for _ in range(pack_count):
            pack = ResourcePackInfo.deserialize(data[pos:])
            packs.append(pack)
            pos += len(pack.serialize())
        
        return cls(
            mustAccept=mustAccept,
            packs=packs
        )