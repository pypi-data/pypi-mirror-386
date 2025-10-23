import logging
import asyncio
import uuid
from typing import Optional, Final, Dict, Any
from contextlib import asynccontextmanager

from .types import AsyncConnection, PacketData, AsyncContextManager, ProtocolError, BaseConnectionState, ConnectionState
from .protocol.logging import protocol_logger
from .protocol.compression import PacketCompressor, CompressionLevel
from .protocol.batching import PacketBatcher, PacketUnbatcher
from .protocol.versions import protocol_registry, ProtocolVersion

class Connection(AsyncConnection):
    """Async connection abstraction for protocol I/O with compression and batching."""
    
    DEFAULT_READ_TIMEOUT: Final[float] = 30.0
    DEFAULT_WRITE_TIMEOUT: Final[float] = 30.0
    
    def __init__(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        *, 
        readTimeout: float = DEFAULT_READ_TIMEOUT,
        writeTimeout: float = DEFAULT_WRITE_TIMEOUT,
        protocol_version: int = ProtocolVersion.LATEST,
        compression_level: int = CompressionLevel.DEFAULT,
        batching_interval: float = 0.02
    ) -> None:
        self.reader: Final[asyncio.StreamReader] = reader
        self.writer: Final[asyncio.StreamWriter] = writer
        self._state: ConnectionState = BaseConnectionState()
        self.readTimeout: float = readTimeout
        self.writeTimeout: float = writeTimeout
        self._closeLock: Final[asyncio.Lock] = asyncio.Lock()
        self._closed: bool = False
        self._id: Final[str] = str(uuid.uuid4())[:8]  # Short unique ID
        
        # Protocol version and features
        self.protocol_version = protocol_version
        self.features = protocol_registry.get_features(protocol_version)
        if not self.features:
            raise ProtocolError(f"Unsupported protocol version: {protocol_version}")
        
        # Compression setup
        self._compressor = PacketCompressor(
            level=compression_level,
            header_in_packet=self.features.compressor_in_header
        )
        
        # Packet batching setup
        self._batcher = PacketBatcher(
            self._raw_send,
            compressor=self._compressor,
            interval=batching_interval
        )
        self._unbatcher = PacketUnbatcher(self._compressor)
        
        # Statistics tracking
        self._bytesReceived: int = 0
        self._bytesSent: int = 0
        self._packetsReceived: int = 0
        self._packetsSent: int = 0
        self._createdAt: Final[float] = asyncio.get_event_loop().time()
        self._lastActivity: float = self._createdAt
        
        # Set up logging context
        protocol_logger.set_context(
            connection_id=self._id,
            protocol_version=self.protocol_version,
            peer_info=self._get_peer_info()
        )
        
        logging.logger.info("New connection %s established from %s", self._id, self._get_peer_info())

    async def __aenter__(self) -> 'Connection':
        return self

    async def __aexit__(self, exc_type: Optional[type], exc_val: Optional[Exception], 
                        exc_tb: Optional[object]) -> None:
        await self.close()

    @property
    def isClosed(self) -> bool:
        """Check if connection is closed."""
        return self._closed

    def _update_activity(self) -> None:
        """Update last activity timestamp."""
        self._lastActivity = asyncio.get_event_loop().time()
    
    def _get_peer_info(self) -> str:
        """Get formatted peer address and port."""
        try:
            peer = self.writer.get_extra_info('peername')
            return f"{peer[0]}:{peer[1]}" if peer else "unknown"
        except Exception:
            return "unknown"
            
    def get_stats(self) -> dict:
        """Get connection statistics."""
        current_time = asyncio.get_event_loop().time()
        uptime = current_time - self._createdAt
        idle_time = current_time - self._lastActivity
        
        return {
            'id': self._id,
            'peer': self._get_peer_info(),
            'state': str(self._state),
            'protocol_version': self.protocol_version,
            'uptime': f"{uptime:.1f}s",
            'idle_time': f"{idle_time:.1f}s",
            'bytes_sent': self._bytesSent,
            'bytes_received': self._bytesReceived,
            'packets_sent': self._packetsSent,
            'packets_received': self._packetsReceived,
            'compression_stats': self._compressor.stats,
            'features': {
                'compression_in_header': self.features.compressor_in_header,
                'new_login_identity': self.features.new_login_identity,
                'new_network_settings': self.features.new_network_settings,
                'new_item_registry': self.features.new_item_registry
            }
        }
    
    async def _raw_send(self, data: PacketData) -> None:
        """Low-level send without batching/compression."""
        if self._closed:
            raise ProtocolError("Connection is closed")
            
        try:
            with protocol_logger.timer("raw_send"):
                self.writer.write(data)
                async with asyncio.timeout(self.writeTimeout):
                    await self.writer.drain()
                
                self._bytesSent += len(data)
                self._update_activity()
                
        except asyncio.TimeoutError:
            protocol_logger.error(
                "Write timeout after %.1f seconds to %s",
                self.writeTimeout, self._get_peer_info()
            )
            await self.close()
            raise ProtocolError(f"Write timeout after {self.writeTimeout:.1f}s")
        except Exception as e:
            protocol_logger.error("Write error to %s: %s", self._get_peer_info(), str(e))
            await self.close()
            raise ProtocolError(f"Write error: {e}")

    async def send(self, data: PacketData) -> None:
        """Send data with batching and compression."""
        if self._closed:
            raise ProtocolError("Connection is closed")
        if not self._state.canSend():
            raise ProtocolError("Connection cannot send data in current state")
        
        with protocol_logger.connection_context(connection_id=self._id):
            try:
                protocol_logger.debug(
                    "Queueing packet of %d bytes to %s",
                    len(data), self._get_peer_info()
                )
                
                with protocol_logger.timer("packet_send"):
                    await self._batcher.queue(data)
                    self._packetsSent += 1
                
                protocol_logger.debug(
                    "Packet queued (total sent: %d packets/%d bytes)",
                    self._packetsSent, self._bytesSent
                )
                
            except Exception as e:
                protocol_logger.error(
                    "Error queueing packet to %s: %s",
                    self._get_peer_info(), str(e)
                )
                await self.close()
                raise ProtocolError(f"Send error: {e}")

    async def _raw_receive(self, n: int = -1, exactSize: bool = False) -> PacketData:
        """Low-level receive without batching/compression."""
        if self._closed:
            raise ProtocolError("Connection is closed")
            
        try:
            with protocol_logger.timer("raw_receive"):
                async with asyncio.timeout(self.readTimeout):
                    if exactSize and n > 0:
                        data = await self.reader.readexactly(n)
                    else:
                        data = await self.reader.read(n)
                        
                    if not data:  # EOF
                        protocol_logger.info(
                            "Connection %s closed by peer %s",
                            self._id, self._get_peer_info()
                        )
                        await self.close()
                        raise ProtocolError("Connection closed by peer")
                    
                    self._bytesReceived += len(data)
                    self._update_activity()
                    return data
                    
        except asyncio.TimeoutError:
            protocol_logger.error(
                "Read timeout after %.1f seconds from %s",
                self.readTimeout, self._get_peer_info()
            )
            await self.close()
            raise ProtocolError(f"Read timeout after {self.readTimeout:.1f}s")
            
        except asyncio.IncompleteReadError as e:
            protocol_logger.error(
                "Incomplete read from %s: got %d bytes",
                self._get_peer_info(), len(e.partial)
            )
            await self.close()
            raise ProtocolError(
                f"Incomplete read: got {len(e.partial)} bytes, expected {n}"
            )
            
        except Exception as e:
            protocol_logger.error(
                "Read error from %s: %s",
                self._get_peer_info(), str(e)
            )
            await self.close()
            raise ProtocolError(f"Read error: {e}")

    async def receive(self, n: int = -1, exactSize: bool = False) -> PacketData:
        """Receive data with batching and compression."""
        if self._closed:
            raise ProtocolError("Connection is closed")
        if not self._state.canReceive():
            raise ProtocolError("Connection cannot receive data in current state")
        
        with protocol_logger.connection_context(connection_id=self._id):
            try:
                protocol_logger.debug(
                    "Receiving%s data (n=%d) from %s",
                    " exact" if exactSize else "", n, self._get_peer_info()
                )
                
                with protocol_logger.timer("packet_receive"):
                    raw_data = await self._raw_receive(n, exactSize)
                    packets = self._unbatcher.unbatch(raw_data)
                    
                    # For now, return first packet - batching handled at higher level
                    if packets:
                        self._packetsReceived += len(packets)
                        protocol_logger.debug(
                            "Received %d packets (%d bytes total) from %s",
                            len(packets), len(raw_data), self._get_peer_info()
                        )
                        return packets[0]
                    return raw_data
                    
            except Exception as e:
                protocol_logger.error(
                    "Error receiving from %s: %s",
                    self._get_peer_info(), str(e)
                )
                await self.close()
                raise

    async def close(self) -> None:
        """Close the connection safely."""
        async with self._closeLock:
            if self._closed:
                return
                
            peer = self._get_peer_info()
            stats = self.get_stats()
            
            try:
                # Stop batching
                await self._batcher.stop()
                
                # Log final stats
                protocol_logger.info(
                    "Closing connection %s to %s (stats: sent=%d bytes/%d packets, "
                    "received=%d bytes/%d packets, uptime=%s, compression_ratio=%.2f)", 
                    self._id, peer,
                    stats['bytes_sent'], stats['packets_sent'],
                    stats['bytes_received'], stats['packets_received'],
                    stats['uptime'],
                    stats['compression_stats']['compression_ratio']
                )
                
                self.writer.close()
                await self.writer.wait_closed()
                
                protocol_logger.debug(
                    "Connection %s to %s closed successfully",
                    self._id, peer
                )
                
            except Exception as e:
                protocol_logger.warning(
                    "Error while closing connection %s to %s: %s",
                    self._id, peer, str(e)
                )
            finally:
                self._closed = True

    async def drain(self) -> None:
        """Wait for all buffered data to be sent."""
        if self._closed:
            raise ProtocolError("Connection is closed")
        if not self._state.canSend():
            raise ProtocolError("Connection cannot send data in current state")
            
        try:
            async with asyncio.timeout(self.writeTimeout):
                await self.writer.drain()
        except Exception as e:
            await self.close()
            raise ProtocolError(f"Drain error: {e}")
            
    @property
    def state(self) -> ConnectionState:
        """Get the current connection state."""
        return self._state
