"""Core type definitions for the Bedrock protocol implementation."""
from typing import (
    TypeVar, Protocol, Callable, Awaitable, Union, Dict, Any,
    AsyncIterator, TypeAlias, runtime_checkable
)
from asyncio import StreamReader, StreamWriter
import asyncio

# Basic types
PacketData = bytes
JsonDict: TypeAlias = Dict[str, Any]

# Callback types
SyncCallback = Callable[..., Any]
AsyncCallback = Callable[..., Awaitable[Any]]
EventCallback = Union[SyncCallback, AsyncCallback]

# Event handling
EventName: TypeAlias = str
EventHandlers = Dict[EventName, list[EventCallback]]

@runtime_checkable
class EventEmitter(Protocol):
    """Protocol for objects that can emit events."""
    def on(self, event: EventName, callback: EventCallback) -> None: ...
    def off(self, event: EventName, callback: EventCallback) -> None: ...
    async def _emit(self, event: EventName, *args: Any, **kwargs: Any) -> None: ...

@runtime_checkable
class PacketHandler(Protocol):
    """Protocol for objects that can handle protocol packets."""
    async def handlePacket(self, packet_id: int, data: PacketData) -> None: ...
    async def sendPacket(self, packet_id: int, data: PacketData) -> None: ...

@runtime_checkable
class AsyncCloseable(Protocol):
    """Protocol for objects that can be closed asynchronously."""
    @property
    def isClosed(self) -> bool: ...
    async def close(self) -> None: ...

@runtime_checkable
class AsyncConnection(AsyncCloseable, Protocol):
    """Protocol for async network connections."""
    reader: StreamReader
    writer: StreamWriter
    
    async def send(self, data: PacketData) -> None: ...
    async def receive(self, n: int = -1, exactSize: bool = False) -> PacketData: ...
    async def drain(self) -> None: ...

# Type variables for generics
T_Packet = TypeVar('T_Packet')
T_Handler = TypeVar('T_Handler', bound=PacketHandler)

@runtime_checkable
class PacketStream(Protocol):
    """Protocol for packet streams that can be iterated asynchronously."""
    def __aiter__(self) -> AsyncIterator[PacketData]: ...
    async def __anext__(self) -> PacketData: ...
    async def close(self) -> None: ...

# Exception types
class ProtocolError(Exception):
    """Base class for protocol-related errors."""

class PacketError(ProtocolError):
    """Error in packet handling."""

class HandshakeError(ProtocolError):
    """Error during handshake process."""

class AuthenticationError(ProtocolError):
    """Authentication-related error."""

# Connection state types
class ConnectionState(Protocol):
    """Protocol for connection state tracking."""
    def canSend(self) -> bool: ...
    def canReceive(self) -> bool: ...
    def isAuthenticated(self) -> bool: ...
    def markAuthenticated(self) -> None: ...

class BaseConnectionState:
    """Basic implementation of ConnectionState."""
    def __init__(self) -> None:
        self._authenticated = False
        self._canSend = True
        self._canReceive = True
    
    def canSend(self) -> bool:
        return self._canSend
    
    def canReceive(self) -> bool:
        return self._canReceive
    
    def isAuthenticated(self) -> bool:
        return self._authenticated
    
    def markAuthenticated(self) -> None:
        self._authenticated = True

# Async context manager types
class AsyncContextManager(Protocol[T_Packet]):
    """Protocol for async context managers."""
    async def __aenter__(self) -> T_Packet: ...
    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None: ...

# Task management types
TaskCallback = Callable[[asyncio.Task], None]