"""RakNet protocol core implementation."""
import asyncio
import time
from typing import Dict, Optional, Set, Any, Callable
from dataclasses import dataclass, field
from enum import IntEnum

class Priority(IntEnum):
    """Packet priority levels."""
    IMMEDIATE = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3

class Reliability(IntEnum):
    """Packet reliability modes."""
    UNRELIABLE = 0
    UNRELIABLE_SEQUENCED = 1
    RELIABLE = 2
    RELIABLE_ORDERED = 3
    RELIABLE_SEQUENCED = 4

@dataclass
class RakPacket:
    """Base RakNet packet structure."""
    data: bytes
    reliability: Reliability = Reliability.RELIABLE_ORDERED
    priority: Priority = Priority.MEDIUM
    channel: int = 0
    sequence: Optional[int] = None
    order: Optional[int] = None

    def serialize(self) -> bytes:
        """Convert packet to bytes."""
        flags = (self.reliability.value << 5) | self.channel
        result = bytearray([flags])
        
        # Add reliability-specific fields
        if self.reliability in (
            Reliability.RELIABLE,
            Reliability.RELIABLE_ORDERED,
            Reliability.RELIABLE_SEQUENCED
        ):
            if self.sequence is None:
                raise ValueError("Sequence number required for reliable packet")
            result.extend(self.sequence.to_bytes(3, 'big'))
        
        if self.reliability in (
            Reliability.UNRELIABLE_SEQUENCED,
            Reliability.RELIABLE_ORDERED,
            Reliability.RELIABLE_SEQUENCED
        ):
            if self.order is None:
                raise ValueError("Order number required for ordered/sequenced packet")
            result.extend(self.order.to_bytes(3, 'big'))
        
        # Add data length and data
        result.extend(len(self.data).to_bytes(2, 'big'))
        result.extend(self.data)
        
        return bytes(result)

    @classmethod
    def deserialize(cls, data: bytes) -> 'RakPacket':
        """Create packet from bytes."""
        if len(data) < 1:
            raise ValueError("Packet too short")
            
        flags = data[0]
        reliability = Reliability(flags >> 5)
        channel = flags & 0x1F
        pos = 1
        
        sequence = None
        order = None
        
        # Read reliability-specific fields
        if reliability in (
            Reliability.RELIABLE,
            Reliability.RELIABLE_ORDERED,
            Reliability.RELIABLE_SEQUENCED
        ):
            if len(data) < pos + 3:
                raise ValueError("Packet too short for sequence number")
            sequence = int.from_bytes(data[pos:pos+3], 'big')
            pos += 3
        
        if reliability in (
            Reliability.UNRELIABLE_SEQUENCED,
            Reliability.RELIABLE_ORDERED,
            Reliability.RELIABLE_SEQUENCED
        ):
            if len(data) < pos + 3:
                raise ValueError("Packet too short for order number")
            order = int.from_bytes(data[pos:pos+3], 'big')
            pos += 3
        
        # Read data length and data
        if len(data) < pos + 2:
            raise ValueError("Packet too short for data length")
        length = int.from_bytes(data[pos:pos+2], 'big')
        pos += 2
        
        if len(data) < pos + length:
            raise ValueError("Packet data truncated")
        packet_data = data[pos:pos+length]
        
        return cls(
            data=packet_data,
            reliability=reliability,
            priority=Priority.MEDIUM,  # Default priority
            channel=channel,
            sequence=sequence,
            order=order
        )

@dataclass
class RakSendQueue:
    """Queue for outbound RakNet packets."""
    reliability: Reliability
    channel: int
    packets: list[RakPacket] = field(default_factory=list)
    next_sequence: int = 0
    next_order: int = 0

    def add(self, data: bytes, priority: Priority = Priority.MEDIUM) -> None:
        """Add data to the queue."""
        packet = RakPacket(
            data=data,
            reliability=self.reliability,
            priority=priority,
            channel=self.channel
        )
        
        if self.reliability in (
            Reliability.RELIABLE,
            Reliability.RELIABLE_ORDERED,
            Reliability.RELIABLE_SEQUENCED
        ):
            packet.sequence = self.next_sequence
            self.next_sequence = (self.next_sequence + 1) & 0xFFFFFF
        
        if self.reliability in (
            Reliability.UNRELIABLE_SEQUENCED,
            Reliability.RELIABLE_ORDERED,
            Reliability.RELIABLE_SEQUENCED
        ):
            packet.order = self.next_order
            self.next_order = (self.next_order + 1) & 0xFFFFFF
        
        self.packets.append(packet)

    def get_packets(self) -> list[RakPacket]:
        """Get all queued packets and clear queue."""
        packets = self.packets.copy()
        self.packets.clear()
        return packets

class RakConnection:
    """RakNet connection state manager."""
    
    MAX_SPLIT_SIZE = 1024
    RESEND_INTERVAL = 0.5  # Seconds
    MAX_RESENDS = 10
    
    def __init__(
        self,
        transport: asyncio.DatagramTransport,
        address: tuple[str, int],
        on_message: Callable[[bytes], None]
    ) -> None:
        self.transport = transport
        self.address = address
        self.on_message = on_message
        
        # Sequence tracking
        self._send_queues: Dict[int, RakSendQueue] = {}
        self._received_packets: Set[int] = set()
        self._split_packets: Dict[int, Dict[int, bytes]] = {}
        self._last_received = 0
        
        # Reliability tracking
        self._unacked_reliable: Dict[int, tuple[float, RakPacket, int]] = {}
        self._resend_task: Optional[asyncio.Task] = None
    
    def start(self) -> None:
        """Start connection management."""
        if not self._resend_task:
            self._resend_task = asyncio.create_task(self._resend_loop())
    
    async def stop(self) -> None:
        """Stop connection management."""
        if self._resend_task:
            self._resend_task.cancel()
            try:
                await self._resend_task
            except asyncio.CancelledError:
                pass
            self._resend_task = None
    
    def queue_send(
        self,
        data: bytes,
        reliability: Reliability = Reliability.RELIABLE_ORDERED,
        priority: Priority = Priority.MEDIUM,
        channel: int = 0
    ) -> None:
        """Queue data for sending."""
        if len(data) > self.MAX_SPLIT_SIZE:
            # Split large packets
            for i in range(0, len(data), self.MAX_SPLIT_SIZE):
                chunk = data[i:i + self.MAX_SPLIT_SIZE]
                self._queue_packet(chunk, reliability, priority, channel)
        else:
            self._queue_packet(data, reliability, priority, channel)
    
    def _queue_packet(
        self,
        data: bytes,
        reliability: Reliability,
        priority: Priority,
        channel: int
    ) -> None:
        """Queue a single packet."""
        queue = self._send_queues.get(channel)
        if not queue:
            queue = RakSendQueue(reliability=reliability, channel=channel)
            self._send_queues[channel] = queue
        queue.add(data, priority)
    
    def process_received(self, data: bytes) -> None:
        """Process received packet data."""
        try:
            packet = RakPacket.deserialize(data)
            
            # Check for duplicate reliable packets
            if packet.reliability in (
                Reliability.RELIABLE,
                Reliability.RELIABLE_ORDERED,
                Reliability.RELIABLE_SEQUENCED
            ):
                if packet.sequence in self._received_packets:
                    return
                self._received_packets.add(packet.sequence)
            
            # Handle ordered/sequenced packets
            if packet.reliability in (
                Reliability.UNRELIABLE_SEQUENCED,
                Reliability.RELIABLE_ORDERED,
                Reliability.RELIABLE_SEQUENCED
            ):
                if packet.order is None:
                    return
                # Skip old ordered packets
                if packet.order < self._last_received:
                    return
                self._last_received = packet.order
            
            # Deliver packet
            self.on_message(packet.data)
            
        except ValueError as e:
            # Log but don't crash on malformed packets
            print(f"Error processing packet: {e}")
    
    def flush_queues(self) -> None:
        """Send all queued packets."""
        for queue in self._send_queues.values():
            packets = queue.get_packets()
            for packet in packets:
                self._send_packet(packet)
    
    def _send_packet(self, packet: RakPacket) -> None:
        """Send a single packet."""
        data = packet.serialize()
        self.transport.sendto(data, self.address)
        
        # Track reliable packets for resending
        if packet.reliability in (
            Reliability.RELIABLE,
            Reliability.RELIABLE_ORDERED,
            Reliability.RELIABLE_SEQUENCED
        ):
            if packet.sequence is not None:
                self._unacked_reliable[packet.sequence] = (
                    time.time(),
                    packet,
                    0  # Resend count
                )
    
    async def _resend_loop(self) -> None:
        """Background task for resending unacked packets."""
        try:
            while True:
                await asyncio.sleep(self.RESEND_INTERVAL)
                current_time = time.time()
                
                # Check for packets needing resend
                to_resend = []
                to_remove = []
                
                for seq, (sent_time, packet, count) in self._unacked_reliable.items():
                    if current_time - sent_time > self.RESEND_INTERVAL:
                        if count >= self.MAX_RESENDS:
                            to_remove.append(seq)
                        else:
                            to_resend.append((seq, packet))
                
                # Remove failed packets
                for seq in to_remove:
                    del self._unacked_reliable[seq]
                
                # Resend packets
                for seq, packet in to_resend:
                    self._send_packet(packet)
                    self._unacked_reliable[seq] = (
                        current_time,
                        packet,
                        self._unacked_reliable[seq][2] + 1
                    )
                    
        except asyncio.CancelledError:
            raise