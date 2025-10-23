import asyncio
from typing import Any, Dict, Optional, Final

from .connection import Connection
from .types import (
    EventName, EventCallback, EventEmitter, PacketHandler,
    PacketData, AsyncCloseable, ProtocolError, TaskCallback
)

class Client(EventEmitter, PacketHandler, AsyncCloseable):
    """Async Bedrock protocol client implementation."""
    def __init__(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        options: Optional[Dict[str, Any]] = None
    ) -> None:
        self.conn: Final[Connection] = Connection(reader, writer)
        self.options: Final[Dict[str, Any]] = options or {}
        self.username: str = self.options.get('username', 'Player')
        self._listeners: Dict[EventName, list[EventCallback]] = {}
        self._running: bool = False
        self._task: Optional[asyncio.Task] = None
        self._closeLock: Final[asyncio.Lock] = asyncio.Lock()

    async def __aenter__(self) -> 'Client':
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()

    async def start(self):
        """Start the client and begin processing packets."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(
            self._readerLoop(),
            name=f"client-{self.username}-reader"
        )
        self._task.add_done_callback(self._onReaderDone)

    async def _readerLoop(self):
        """Main packet processing loop."""
        from .transforms.serializer import deserializePacket
        from .datatypes.packets import TextPacket, DisconnectPacket
        
        try:
            while self._running and not self.conn.isClosed:
                try:
                    # Read packet length
                    lenBytes = await self.conn.receive(4, exactSize=True)
                    length = int.from_bytes(lenBytes, 'big')
                    if length > 0:
                        # Read complete packet
                        data = await self.conn.receive(length, exactSize=True)
                        packet = deserializePacket(lenBytes + data)
                        
                        if packet is None:
                            continue
                            
                        # Emit specific events based on packet type
                        if isinstance(packet.payload, TextPacket):
                            await self._emit('text', packet.payload.message, packet.payload.source)
                        elif isinstance(packet.payload, DisconnectPacket):
                            await self._emit('disconnect', packet.payload.reason)
                            break
                        
                        # Also emit raw packet for custom handlers
                        await self._emit('packet', packet)
                        
                except ConnectionError as e:
                    await self._emit('error', e)
                    break
        except Exception as e:
            await self._emit('error', e)
        finally:
            await self.disconnect("Reader loop ended")

    def _onReaderDone(self, task: asyncio.Task):
        """Handle reader task completion."""
        try:
            task.result()  # Raise any error that occurred
        except Exception as e:
            asyncio.create_task(self._emit('error', e))

    async def queue(self, packetId: int, payload: Any):
        """Queue a packet for sending."""
        from .transforms.serializer import serializePacket
        
        if self.conn.isClosed:
            raise ConnectionError("Cannot send on closed connection")
            
        try:
            data = serializePacket(packetId, payload)
            await self.conn.send(data)
        except Exception as e:
            await self._emit('error', e)
            raise

    async def sendMessage(self, message: str, source: str = ""):
        """Helper to send a text message."""
        from .transforms.serializer import serializeMessage
        await self.conn.send(serializeMessage(message, source))

    async def disconnect(self, reason: str = ""):
        """Disconnect with optional reason."""
        if reason and not self.conn.isClosed:
            try:
                from .transforms.serializer import serializeDisconnect
                await self.conn.send(serializeDisconnect(reason))
            except Exception:
                pass  # Best effort to send reason
        
        async with self._closeLock:
            if not self._running:
                return
            self._running = False
            
            if self._task and not self._task.done():
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass
            
            await self.conn.close()
            await self._emit('disconnect', reason)

    def on(self, event: str, callback: EventCallback):
        """Register an event handler."""
        self._listeners.setdefault(event, []).append(callback)
        return self  # Allow chaining

    def off(self, event: str, callback: Optional[EventCallback] = None):
        """Remove an event handler."""
        if callback is None:
            self._listeners.pop(event, None)
        else:
            handlers = self._listeners.get(event, [])
            self._listeners[event] = [cb for cb in handlers if cb != callback]
        return self

    async def _emit(self, event: str, *args, **kwargs):
        """Emit an event to all registered handlers."""
        for cb in self._listeners.get(event, []):
            try:
                if asyncio.iscoroutinefunction(cb):
                    await cb(*args, **kwargs)
                else:
                    cb(*args, **kwargs)
            except Exception as e:
                await self._emit('error', e)

    async def disconnect(self, reason: str = ''):
        """Disconnect the client and cleanup resources."""
        async with self._closeLock:
            if not self._running:
                return
            self._running = False
            
            # Cancel and await reader task
            if self._task and not self._task.done():
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass
            
            # Close connection
            await self.conn.close()
            
            # Emit disconnect event
            if reason:
                await self._emit('disconnect', reason)
