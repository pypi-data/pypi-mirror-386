"""Handshake and login packet structures for Bedrock protocol."""
from dataclasses import dataclass
from typing import List, Optional
from .packets import PacketSerializable

@dataclass
class ChainData:
    """JWT chain data for Xbox Live authentication."""
    chain: List[str]
    
    def serialize(self) -> bytes:
        chain_bytes = [c.encode('utf-8') for c in self.chain]
        result = len(self.chain).to_bytes(4, 'big')
        for cb in chain_bytes:
            result += len(cb).to_bytes(4, 'big') + cb
        return result
    
    @classmethod
    def deserialize(cls, data: bytes) -> 'ChainData':
        if len(data) < 4:
            raise ValueError("Chain data too short")
        chain_count = int.from_bytes(data[0:4], 'big')
        chains = []
        pos = 4
        for _ in range(chain_count):
            if len(data) < pos + 4:
                raise ValueError("Incomplete chain data")
            chain_len = int.from_bytes(data[pos:pos+4], 'big')
            pos += 4
            if len(data) < pos + chain_len:
                raise ValueError("Incomplete chain data")
            chain = data[pos:pos+chain_len].decode('utf-8')
            chains.append(chain)
            pos += chain_len
        return cls(chain=chains)

@dataclass
class LoginPacket(PacketSerializable):
    """Initial login packet with protocol version and tokens."""
    protocol: int
    username: str
    clientUUID: str
    clientId: str
    xuid: str
    identityPublicKey: str
    serverAddress: str
    languageCode: str
    chainData: Optional[ChainData] = None
    
    def serialize(self) -> bytes:
        result = bytearray()
        result.extend(self.protocol.to_bytes(4, 'big'))
        
        # Serialize strings with length prefixes
        for s in [self.username, self.clientUUID, self.clientId, self.xuid,
                 self.identityPublicKey, self.serverAddress, self.languageCode]:
            b = s.encode('utf-8')
            result.extend(len(b).to_bytes(2, 'big'))
            result.extend(b)
            
        # Add chain data if present
        if self.chainData:
            chain_bytes = self.chainData.serialize()
            result.extend(len(chain_bytes).to_bytes(4, 'big'))
            result.extend(chain_bytes)
        else:
            result.extend((0).to_bytes(4, 'big'))
            
        return bytes(result)
    
    @classmethod
    def deserialize(cls, data: bytes) -> 'LoginPacket':
        if len(data) < 4:
            raise ValueError("Login packet too short")
            
        pos = 0
        protocol = int.from_bytes(data[pos:pos+4], 'big')
        pos += 4
        
        # Helper to read length-prefixed UTF-8 strings
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
            
        # Read all strings
        username = read_string()
        clientUUID = read_string()
        clientId = read_string()
        xuid = read_string()
        identityPublicKey = read_string()
        serverAddress = read_string()
        languageCode = read_string()
        
        # Read chain data if present
        chainData = None
        if len(data) > pos + 4:
            chain_len = int.from_bytes(data[pos:pos+4], 'big')
            pos += 4
            if chain_len > 0:
                chainData = ChainData.deserialize(data[pos:pos+chain_len])
        
        return cls(
            protocol=protocol,
            username=username,
            clientUUID=clientUUID,
            clientId=clientId,
            xuid=xuid,
            identityPublicKey=identityPublicKey,
            serverAddress=serverAddress,
            languageCode=languageCode,
            chainData=chainData
        )

@dataclass
class HandshakePacket(PacketSerializable):
    """Server-client handshake packet with token."""
    token: str
    
    def serialize(self) -> bytes:
        token_bytes = self.token.encode('utf-8')
        return len(token_bytes).to_bytes(2, 'big') + token_bytes
    
    @classmethod
    def deserialize(cls, data: bytes) -> 'HandshakePacket':
        if len(data) < 2:
            raise ValueError("Handshake packet too short")
        token_len = int.from_bytes(data[0:2], 'big')
        if len(data) < 2 + token_len:
            raise ValueError("Incomplete handshake packet")
        token = data[2:2+token_len].decode('utf-8')
        return cls(token=token)

@dataclass
class PlayStatusPacket(PacketSerializable):
    """Server response indicating login/spawn status."""
    status: int  # 0: OK, 1: Outdated Client, etc.
    
    def serialize(self) -> bytes:
        return self.status.to_bytes(4, 'big')
    
    @classmethod
    def deserialize(cls, data: bytes) -> 'PlayStatusPacket':
        if len(data) < 4:
            raise ValueError("Play status packet too short")
        status = int.from_bytes(data[0:4], 'big')
        return cls(status=status)