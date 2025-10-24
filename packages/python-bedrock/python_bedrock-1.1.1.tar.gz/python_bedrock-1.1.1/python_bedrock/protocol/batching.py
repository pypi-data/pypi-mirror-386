"""Packet batching and bundling support."""
import asyncio
from typing import List, Optional, Tuple, Any
from dataclasses import dataclass, field
from .compression import PacketCompressor
from ..types import PacketData, ProtocolError

@dataclass
class PacketBatch:
    """A batch of packets to be sent together."""
    packets: List[PacketData] = field(default_factory=list)
    total_size: int = 0
    
    def add(self, packet: PacketData) -> bool:
        """Add a packet to the batch. Returns False if batch is full."""
        packet_size = len(packet)
        if self.total_size + packet_size > MAX_BATCH_SIZE:
            return False
        
        self.packets.append(packet)
        self.total_size += packet_size
        return True
    
    def clear(self) -> None:
        """Clear the batch."""
        self.packets.clear()
        self.total_size = 0

class PacketBatcher:
    """Handles packet batching and sending."""
    
    # Constants
    MAX_BATCH_SIZE = 1024 * 512  # 512KB max batch size
    DEFAULT_INTERVAL = 0.02  # 20ms default batching interval
    
    def __init__(
        self,
        send_callback: Any,  # Callable that sends the batch
        *,
        compressor: Optional[PacketCompressor] = None,
        interval: float = DEFAULT_INTERVAL,
        max_size: int = MAX_BATCH_SIZE
    ) -> None:
        self.send_callback = send_callback
        self.compressor = compressor
        self.interval = interval
        self.max_size = max_size
        
        self._current_batch = PacketBatch()
        self._batch_lock = asyncio.Lock()
        self._flush_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def start(self) -> None:
        """Start the batching process."""
        if self._running:
            return
        
        self._running = True
        self._flush_task = asyncio.create_task(self._flush_loop())
    
    async def stop(self) -> None:
        """Stop the batching process."""
        if not self._running:
            return
        
        self._running = False
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
            self._flush_task = None
    
    async def queue(self, packet: PacketData) -> None:
        """Queue a packet for batched sending."""
        async with self._batch_lock:
            if not self._current_batch.add(packet):
                # Batch is full, flush it first
                await self._flush_current_batch()
                if not self._current_batch.add(packet):
                    raise ProtocolError("Packet too large for batching")
    
    async def flush(self) -> None:
        """Force flush the current batch."""
        async with self._batch_lock:
            await self._flush_current_batch()
    
    async def _flush_loop(self) -> None:
        """Background task that periodically flushes the batch."""
        try:
            while self._running:
                await asyncio.sleep(self.interval)
                async with self._batch_lock:
                    await self._flush_current_batch()
        except asyncio.CancelledError:
            # Final flush on cancel
            async with self._batch_lock:
                await self._flush_current_batch()
            raise
    
    async def _flush_current_batch(self) -> None:
        """Flush the current batch if not empty."""
        if not self._current_batch.packets:
            return
        
        # Prepare batch data
        if len(self._current_batch.packets) == 1:
            # Single packet - no need for batching
            data = self._current_batch.packets[0]
        else:
            # Multiple packets - create batch
            data = self._create_batch_payload()
        
        # Compress if needed
        if self.compressor:
            data, _ = self.compressor.pack(data)
        
        # Send and clear
        await self.send_callback(data)
        self._current_batch.clear()
    
    def _create_batch_payload(self) -> bytes:
        """Create a batched payload from current packets."""
        result = bytearray()
        
        # Format: count(4) + [length(4) + packet_data] * count
        result.extend(len(self._current_batch.packets).to_bytes(4, 'little'))
        
        for packet in self._current_batch.packets:
            result.extend(len(packet).to_bytes(4, 'little'))
            result.extend(packet)
        
        return bytes(result)

class PacketUnbatcher:
    """Handles unbatching received packet data."""
    
    def __init__(self, compressor: Optional[PacketCompressor] = None) -> None:
        self.compressor = compressor
    
    def unbatch(self, data: bytes) -> List[PacketData]:
        """Unbatch received data into individual packets."""
        # Decompress if needed
        if self.compressor:
            data, _ = self.compressor.unpack(data)
        
        # Single packet check
        try:
            # Try reading batch count
            count = int.from_bytes(data[0:4], 'little')
            pos = 4
        except (IndexError, ValueError):
            # Not a batch, return as single packet
            return [data]
        
        # Process batch
        packets = []
        for _ in range(count):
            if pos + 4 > len(data):
                raise ProtocolError("Truncated batch data")
            
            packet_len = int.from_bytes(data[pos:pos+4], 'little')
            pos += 4
            
            if pos + packet_len > len(data):
                raise ProtocolError("Truncated packet in batch")
            
            packets.append(data[pos:pos+packet_len])
            pos += packet_len
        
        return packets