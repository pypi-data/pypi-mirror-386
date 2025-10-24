"""RakNet client implementation."""
import asyncio
import time
import random
from typing import Optional, Callable, Any
from .protocol import RakConnection, Reliability, Priority
from .datagrams import (
    Datagram, UnconnectedPing, UnconnectedPong,
    OpenConnectionRequest1, OpenConnectionReply1,
    OpenConnectionRequest2, OpenConnectionReply2,
    ConnectionRequest, ConnectionRequestAccepted,
    PacketIdentifier, PROTOCOL_VERSION
)

class RakNetClient(asyncio.DatagramProtocol):
    """RakNet protocol client implementation."""
    
    PING_INTERVAL = 1.0  # Seconds between ping attempts
    TIMEOUT = 30.0  # Seconds before giving up
    
    def __init__(self, client_guid: int = None) -> None:
        if client_guid is None:
            client_guid = random.randint(0, 0xFFFFFFFFFFFFFFFF)
        self.client_guid = client_guid
        
        self.transport: Optional[asyncio.DatagramTransport] = None
        self.server_address: Optional[tuple[str, int]] = None
        self.server_guid: Optional[int] = None
        self.mtu_size: int = 1400
        self.connection: Optional[RakConnection] = None
        
        # State tracking
        self.connecting = False
        self.connected = False
        self.last_ping_time = 0
        self.connect_start_time = 0
        
        # Connection handlers
        self.on_connect: Optional[Callable[[], None]] = None
        self.on_disconnect: Optional[Callable[[], None]] = None
        self.on_message: Optional[Callable[[bytes], None]] = None
        
        # Tasks
        self._ping_task: Optional[asyncio.Task] = None
    
    def connection_made(self, transport: asyncio.DatagramTransport) -> None:
        """Called when transport is ready."""
        self.transport = transport
    
    def connection_lost(self, exc: Exception) -> None:
        """Called when transport is closed."""
        if self.connected and self.on_disconnect:
            self.on_disconnect()
        self.connected = False
        self._stop_ping_task()
    
    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        """Handle received datagram."""
        try:
            if not data or addr != self.server_address:
                return
                
            # Get packet type
            packet_type = data[0]
            
            # Handle connection sequence packets
            if packet_type == PacketIdentifier.CONNECTED_PONG:
                self._handle_pong(data)
                
            elif packet_type == PacketIdentifier.OPEN_CONNECTION_REPLY_1:
                self._handle_connection_reply_1(data)
                
            elif packet_type == PacketIdentifier.OPEN_CONNECTION_REPLY_2:
                self._handle_connection_reply_2(data)
                
            elif packet_type == PacketIdentifier.CONNECTION_REQUEST_ACCEPTED:
                self._handle_connection_accepted(data)
                
            # Handle game packets from connected server
            elif self.connection and packet_type == PacketIdentifier.GAME_PACKET:
                self.connection.process_received(data[1:])
                
        except Exception as e:
            print(f"Error processing packet: {e}")
    
    def _start_ping_task(self) -> None:
        """Start background ping task."""
        if not self._ping_task:
            self._ping_task = asyncio.create_task(self._ping_loop())
    
    def _stop_ping_task(self) -> None:
        """Stop background ping task."""
        if self._ping_task:
            self._ping_task.cancel()
            self._ping_task = None
    
    async def _ping_loop(self) -> None:
        """Background task for sending pings."""
        try:
            while True:
                await asyncio.sleep(self.PING_INTERVAL)
                current_time = time.time()
                
                if self.connecting:
                    # Check for connection timeout
                    if current_time - self.connect_start_time > self.TIMEOUT:
                        self.disconnect()
                        return
                        
                # Send ping if needed
                if current_time - self.last_ping_time > self.PING_INTERVAL:
                    self._send_ping()
                    
        except asyncio.CancelledError:
            raise
    
    def _send_ping(self) -> None:
        """Send ping to server."""
        if not self.transport or not self.server_address:
            return
            
        ping = UnconnectedPing(
            time=int(time.time() * 1000),
            client_guid=self.client_guid
        )
        self.transport.sendto(ping.serialize(), self.server_address)
        self.last_ping_time = time.time()
    
    def _handle_pong(self, data: bytes) -> None:
        """Handle pong response."""
        try:
            pong = UnconnectedPong.deserialize(data)
            if not self.server_guid:
                self.server_guid = pong.server_guid
                
        except ValueError:
            pass  # Ignore malformed packets
    
    def _handle_connection_reply_1(self, data: bytes) -> None:
        """Handle first connection reply."""
        try:
            reply = OpenConnectionReply1.deserialize(data)
            
            if not self.connecting:
                return
                
            # Update MTU size
            self.mtu_size = min(self.mtu_size, reply.mtu_size)
            
            # Send second connection request
            if self.transport and self.server_address:
                request = OpenConnectionRequest2(
                    server_address=self.server_address,
                    mtu_size=self.mtu_size,
                    client_guid=self.client_guid
                )
                self.transport.sendto(request.serialize(), self.server_address)
                
        except ValueError:
            pass  # Ignore malformed packets
    
    def _handle_connection_reply_2(self, data: bytes) -> None:
        """Handle second connection reply."""
        try:
            reply = OpenConnectionReply2.deserialize(data)
            
            if not self.connecting:
                return
                
            # Update MTU size
            self.mtu_size = min(self.mtu_size, reply.mtu_size)
            
            # Create RakNet connection
            if self.transport and self.server_address:
                self.connection = RakConnection(
                    transport=self.transport,
                    address=self.server_address,
                    on_message=lambda data: self._handle_message(data)
                )
                self.connection.start()
                
                # Send connection request
                request = ConnectionRequest(
                    client_guid=self.client_guid,
                    request_timestamp=int(time.time() * 1000),
                    security=False  # No encryption for now
                )
                self.transport.sendto(request.serialize(), self.server_address)
                
        except ValueError:
            pass  # Ignore malformed packets
    
    def _handle_connection_accepted(self, data: bytes) -> None:
        """Handle connection accepted."""
        try:
            _ = ConnectionRequestAccepted.deserialize(data)
            
            if not self.connecting:
                return
                
            # Connection complete
            self.connecting = False
            self.connected = True
            if self.on_connect:
                self.on_connect()
                
        except ValueError:
            pass  # Ignore malformed packets
    
    def _handle_message(self, data: bytes) -> None:
        """Handle decrypted message from server."""
        if self.on_message:
            self.on_message(data)
    
    async def connect(self, address: tuple[str, int]) -> None:
        """Connect to a RakNet server."""
        if self.connecting or self.connected:
            return
            
        self.server_address = address
        self.connecting = True
        self.connect_start_time = time.time()
        
        # Start ping task
        self._start_ping_task()
        
        # Send initial connection request
        if self.transport:
            request = OpenConnectionRequest1(
                protocol_version=PROTOCOL_VERSION,
                mtu_size=self.mtu_size
            )
            self.transport.sendto(request.serialize(), address)
    
    def disconnect(self) -> None:
        """Disconnect from the server."""
        if self.connection:
            asyncio.create_task(self.connection.stop())
            self.connection = None
            
        self.connecting = False
        if self.connected:
            self.connected = False
            if self.on_disconnect:
                self.on_disconnect()
                
        self._stop_ping_task()
    
    def send_message(
        self,
        data: bytes,
        reliability: Reliability = Reliability.RELIABLE_ORDERED,
        priority: Priority = Priority.MEDIUM,
        channel: int = 0
    ) -> None:
        """Send message to server."""
        if not self.connected or not self.connection:
            return
            
        # Queue in RakNet connection
        self.connection.queue_send(data, reliability, priority, channel)
    
    def flush_queues(self) -> None:
        """Flush send queues."""
        if self.connection:
            self.connection.flush_queues()
    
    def close(self) -> None:
        """Close the client."""
        self.disconnect()
        if self.transport:
            self.transport.close()
            
async def create_client(
    host: str = "127.0.0.1",
    port: int = 0,  # Use random port
    client_guid: Optional[int] = None
) -> tuple[RakNetClient, asyncio.BaseTransport]:
    """Create and start a RakNet client."""
    loop = asyncio.get_running_loop()
    client = RakNetClient(client_guid=client_guid)
    transport, _ = await loop.create_datagram_endpoint(
        lambda: client,
        local_addr=(host, port)
    )
    return client, transport