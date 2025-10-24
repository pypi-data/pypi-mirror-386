"""RakNet datagram handling and packet types."""
from dataclasses import dataclass
from enum import IntEnum
from typing import Optional, Union, List

class PacketIdentifier(IntEnum):
    """RakNet packet identifiers."""
    CONNECTED_PING = 0x00
    UNCONNECTED_PING = 0x01
    UNCONNECTED_PING_OPEN_CONNECTIONS = 0x02
    CONNECTED_PONG = 0x03
    OPEN_CONNECTION_REQUEST_1 = 0x05
    OPEN_CONNECTION_REPLY_1 = 0x06
    OPEN_CONNECTION_REQUEST_2 = 0x07
    OPEN_CONNECTION_REPLY_2 = 0x08
    CONNECTION_REQUEST = 0x09
    CONNECTION_REQUEST_ACCEPTED = 0x10
    CONNECTION_REQUEST_FAILED = 0x11
    ALREADY_CONNECTED = 0x12
    NEW_INCOMING_CONNECTION = 0x13
    NO_FREE_INCOMING_CONNECTIONS = 0x14
    DISCONNECTION_NOTIFICATION = 0x15
    CONNECTION_LOST = 0x16
    INCOMPATIBLE_PROTOCOL_VERSION = 0x19
    GAME_PACKET = 0xfe

# Magic values used in RakNet
MAGIC = b'\x00\xff\xff\x00\xfe\xfe\xfe\xfe\xfd\xfd\xfd\xfd\x12\x34\x56\x78'
PROTOCOL_VERSION = 10

@dataclass
class Datagram:
    """Base class for RakNet datagrams."""
    identifier: PacketIdentifier
    
    def serialize(self) -> bytes:
        """Convert datagram to bytes."""
        return bytes([self.identifier])
    
    @classmethod
    def deserialize(cls, data: bytes) -> 'Datagram':
        """Create datagram from bytes."""
        if not data:
            raise ValueError("Empty datagram")
        return cls(PacketIdentifier(data[0]))

@dataclass
class UnconnectedPing(Datagram):
    """Unconnected ping datagram."""
    time: int
    client_guid: int
    
    def __init__(self, time: int, client_guid: int):
        super().__init__(PacketIdentifier.UNCONNECTED_PING)
        self.time = time
        self.client_guid = client_guid
    
    def serialize(self) -> bytes:
        result = super().serialize()
        result += self.time.to_bytes(8, 'big')
        result += MAGIC
        result += self.client_guid.to_bytes(8, 'big')
        return result
    
    @classmethod
    def deserialize(cls, data: bytes) -> 'UnconnectedPing':
        if len(data) < 25:
            raise ValueError("UnconnectedPing too short")
        
        _ = super().deserialize(data)  # Validate identifier
        time = int.from_bytes(data[1:9], 'big')
        if data[9:25] != MAGIC:
            raise ValueError("Invalid magic")
        client_guid = int.from_bytes(data[25:33], 'big')
        
        return cls(time, client_guid)

@dataclass
class UnconnectedPingOpenConnections(UnconnectedPing):
    """Unconnected ping open connections datagram."""
    def __init__(self, time: int, client_guid: int):
        Datagram.__init__(self, PacketIdentifier.UNCONNECTED_PING_OPEN_CONNECTIONS)
        self.time = time
        self.client_guid = client_guid

@dataclass
class UnconnectedPong(Datagram):
    """Unconnected pong datagram."""
    time: int
    server_guid: int
    server_name: str
    
    def __init__(self, time: int, server_guid: int, server_name: str):
        super().__init__(PacketIdentifier.CONNECTED_PONG)
        self.time = time
        self.server_guid = server_guid
        self.server_name = server_name
    
    def serialize(self) -> bytes:
        result = super().serialize()
        result += self.time.to_bytes(8, 'big')
        result += self.server_guid.to_bytes(8, 'big')
        result += MAGIC
        name_bytes = self.server_name.encode('utf-8')
        result += len(name_bytes).to_bytes(2, 'big')
        result += name_bytes
        return result
    
    @classmethod
    def deserialize(cls, data: bytes) -> 'UnconnectedPong':
        if len(data) < 35:
            raise ValueError("UnconnectedPong too short")
        
        _ = super().deserialize(data)  # Validate identifier
        time = int.from_bytes(data[1:9], 'big')
        server_guid = int.from_bytes(data[9:17], 'big')
        if data[17:33] != MAGIC:
            raise ValueError("Invalid magic")
        name_len = int.from_bytes(data[33:35], 'big')
        if len(data) < 35 + name_len:
            raise ValueError("Server name truncated")
        name = data[35:35+name_len].decode('utf-8')
        
        return cls(time, server_guid, name)

@dataclass
class OpenConnectionRequest1(Datagram):
    """Open connection request 1 datagram."""
    protocol_version: int
    mtu_size: int
    
    def __init__(self, protocol_version: int, mtu_size: int):
        super().__init__(PacketIdentifier.OPEN_CONNECTION_REQUEST_1)
        self.protocol_version = protocol_version
        self.mtu_size = mtu_size
    
    def serialize(self) -> bytes:
        result = super().serialize()
        result += MAGIC
        result += bytes([self.protocol_version])
        result += b'\x00' * (self.mtu_size - len(result))
        return result
    
    @classmethod
    def deserialize(cls, data: bytes) -> 'OpenConnectionRequest1':
        if len(data) < 18:
            raise ValueError("OpenConnectionRequest1 too short")
            
        _ = super().deserialize(data)  # Validate identifier
        if data[1:17] != MAGIC:
            raise ValueError("Invalid magic")
        protocol_version = data[17]
        mtu_size = len(data)
        
        return cls(protocol_version, mtu_size)

@dataclass
class OpenConnectionReply1(Datagram):
    """Open connection reply 1 datagram."""
    server_guid: int
    security: bool
    mtu_size: int
    
    def __init__(self, server_guid: int, security: bool, mtu_size: int):
        super().__init__(PacketIdentifier.OPEN_CONNECTION_REPLY_1)
        self.server_guid = server_guid
        self.security = security
        self.mtu_size = mtu_size
    
    def serialize(self) -> bytes:
        result = super().serialize()
        result += MAGIC
        result += self.server_guid.to_bytes(8, 'big')
        result += bytes([1 if self.security else 0])
        result += self.mtu_size.to_bytes(2, 'big')
        return result
    
    @classmethod
    def deserialize(cls, data: bytes) -> 'OpenConnectionReply1':
        if len(data) < 28:
            raise ValueError("OpenConnectionReply1 too short")
            
        _ = super().deserialize(data)  # Validate identifier
        if data[1:17] != MAGIC:
            raise ValueError("Invalid magic")
        server_guid = int.from_bytes(data[17:25], 'big')
        security = bool(data[25])
        mtu_size = int.from_bytes(data[26:28], 'big')
        
        return cls(server_guid, security, mtu_size)

@dataclass
class OpenConnectionRequest2(Datagram):
    """Open connection request 2 datagram."""
    server_address: tuple[str, int]
    mtu_size: int
    client_guid: int
    
    def __init__(self, server_address: tuple[str, int], mtu_size: int, client_guid: int):
        super().__init__(PacketIdentifier.OPEN_CONNECTION_REQUEST_2)
        self.server_address = server_address
        self.mtu_size = mtu_size
        self.client_guid = client_guid
    
    def serialize(self) -> bytes:
        result = super().serialize()
        result += MAGIC
        # Serialize address
        addr, port = self.server_address
        addr_bytes = addr.encode('utf-8')
        result += len(addr_bytes).to_bytes(2, 'big')
        result += addr_bytes
        result += port.to_bytes(2, 'big')
        result += self.mtu_size.to_bytes(2, 'big')
        result += self.client_guid.to_bytes(8, 'big')
        return result
    
    @classmethod
    def deserialize(cls, data: bytes) -> 'OpenConnectionRequest2':
        if len(data) < 31:
            raise ValueError("OpenConnectionRequest2 too short")
            
        _ = super().deserialize(data)  # Validate identifier
        if data[1:17] != MAGIC:
            raise ValueError("Invalid magic")
        pos = 17
        
        addr_len = int.from_bytes(data[pos:pos+2], 'big')
        pos += 2
        if len(data) < pos + addr_len + 12:
            raise ValueError("Address truncated")
        addr = data[pos:pos+addr_len].decode('utf-8')
        pos += addr_len
        
        port = int.from_bytes(data[pos:pos+2], 'big')
        pos += 2
        mtu_size = int.from_bytes(data[pos:pos+2], 'big')
        pos += 2
        client_guid = int.from_bytes(data[pos:pos+8], 'big')
        
        return cls((addr, port), mtu_size, client_guid)

@dataclass
class OpenConnectionReply2(Datagram):
    """Open connection reply 2 datagram."""
    server_guid: int
    client_address: tuple[str, int]
    mtu_size: int
    encryption_enabled: bool
    
    def __init__(
        self,
        server_guid: int,
        client_address: tuple[str, int],
        mtu_size: int,
        encryption_enabled: bool
    ):
        super().__init__(PacketIdentifier.OPEN_CONNECTION_REPLY_2)
        self.server_guid = server_guid
        self.client_address = client_address
        self.mtu_size = mtu_size
        self.encryption_enabled = encryption_enabled
    
    def serialize(self) -> bytes:
        result = super().serialize()
        result += MAGIC
        result += self.server_guid.to_bytes(8, 'big')
        # Serialize address
        addr, port = self.client_address
        addr_bytes = addr.encode('utf-8')
        result += len(addr_bytes).to_bytes(2, 'big')
        result += addr_bytes
        result += port.to_bytes(2, 'big')
        result += self.mtu_size.to_bytes(2, 'big')
        result += bytes([1 if self.encryption_enabled else 0])
        return result
    
    @classmethod
    def deserialize(cls, data: bytes) -> 'OpenConnectionReply2':
        if len(data) < 30:
            raise ValueError("OpenConnectionReply2 too short")
            
        _ = super().deserialize(data)  # Validate identifier
        if data[1:17] != MAGIC:
            raise ValueError("Invalid magic")
        pos = 17
        
        server_guid = int.from_bytes(data[pos:pos+8], 'big')
        pos += 8
        
        addr_len = int.from_bytes(data[pos:pos+2], 'big')
        pos += 2
        if len(data) < pos + addr_len + 5:
            raise ValueError("Address truncated")
        addr = data[pos:pos+addr_len].decode('utf-8')
        pos += addr_len
        
        port = int.from_bytes(data[pos:pos+2], 'big')
        pos += 2
        mtu_size = int.from_bytes(data[pos:pos+2], 'big')
        pos += 2
        encryption_enabled = bool(data[pos])
        
        return cls(server_guid, (addr, port), mtu_size, encryption_enabled)

@dataclass
class ConnectionRequest(Datagram):
    """Connection request datagram."""
    client_guid: int
    request_timestamp: int
    security: bool
    
    def __init__(self, client_guid: int, request_timestamp: int, security: bool):
        super().__init__(PacketIdentifier.CONNECTION_REQUEST)
        self.client_guid = client_guid
        self.request_timestamp = request_timestamp
        self.security = security
    
    def serialize(self) -> bytes:
        result = super().serialize()
        result += self.client_guid.to_bytes(8, 'big')
        result += self.request_timestamp.to_bytes(8, 'big')
        result += bytes([1 if self.security else 0])
        return result
    
    @classmethod
    def deserialize(cls, data: bytes) -> 'ConnectionRequest':
        if len(data) < 18:
            raise ValueError("ConnectionRequest too short")
            
        _ = super().deserialize(data)  # Validate identifier
        client_guid = int.from_bytes(data[1:9], 'big')
        request_timestamp = int.from_bytes(data[9:17], 'big')
        security = bool(data[17])
        
        return cls(client_guid, request_timestamp, security)

@dataclass
class ConnectionRequestAccepted(Datagram):
    """Connection request accepted datagram."""
    client_address: tuple[str, int]
    system_index: int
    request_timestamp: int
    accepted_timestamp: int
    
    def __init__(
        self,
        client_address: tuple[str, int],
        system_index: int,
        request_timestamp: int,
        accepted_timestamp: int
    ):
        super().__init__(PacketIdentifier.CONNECTION_REQUEST_ACCEPTED)
        self.client_address = client_address
        self.system_index = system_index
        self.request_timestamp = request_timestamp
        self.accepted_timestamp = accepted_timestamp
    
    def serialize(self) -> bytes:
        result = super().serialize()
        # Serialize address
        addr, port = self.client_address
        addr_bytes = addr.encode('utf-8')
        result += len(addr_bytes).to_bytes(2, 'big')
        result += addr_bytes
        result += port.to_bytes(2, 'big')
        result += self.system_index.to_bytes(2, 'big')
        result += self.request_timestamp.to_bytes(8, 'big')
        result += self.accepted_timestamp.to_bytes(8, 'big')
        return result
    
    @classmethod
    def deserialize(cls, data: bytes) -> 'ConnectionRequestAccepted':
        if len(data) < 22:
            raise ValueError("ConnectionRequestAccepted too short")
            
        _ = super().deserialize(data)  # Validate identifier
        pos = 1
        
        addr_len = int.from_bytes(data[pos:pos+2], 'big')
        pos += 2
        if len(data) < pos + addr_len + 20:
            raise ValueError("Address truncated")
        addr = data[pos:pos+addr_len].decode('utf-8')
        pos += addr_len
        
        port = int.from_bytes(data[pos:pos+2], 'big')
        pos += 2
        system_index = int.from_bytes(data[pos:pos+2], 'big')
        pos += 2
        request_timestamp = int.from_bytes(data[pos:pos+8], 'big')
        pos += 8
        accepted_timestamp = int.from_bytes(data[pos:pos+8], 'big')
        
        return cls((addr, port), system_index, request_timestamp, accepted_timestamp)