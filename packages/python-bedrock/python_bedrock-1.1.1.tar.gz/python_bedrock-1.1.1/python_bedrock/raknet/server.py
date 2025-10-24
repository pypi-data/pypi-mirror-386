"""RakNet server implementation."""
import asyncio
import time
from typing import Dict, Optional, Set, Any, Callable
from dataclasses import dataclass
from .protocol import RakConnection, Reliability, Priority
from .datagrams import (
    Datagram, UnconnectedPing, UnconnectedPingOpenConnections,
    UnconnectedPong, OpenConnectionRequest1, OpenConnectionReply1,
    OpenConnectionRequest2, OpenConnectionReply2, ConnectionRequest,
    ConnectionRequestAccepted, PacketIdentifier, PROTOCOL_VERSION
)

@dataclass
class Client:
    """RakNet client state."""
    address: tuple[str, int]
    guid: Optional[int] = None
    connection: Optional[RakConnection] = None
    mtu_size: int = 1400
    last_ping: float = 0
    connected: bool = False

class RakNetServer(asyncio.DatagramProtocol):
    """RakNet protocol server implementation."""

    def __init__(
        self,
        server_guid: int,
        server_name: str = "MCPE;Dedicated Server;390;1.14.60;0;10;13253860892328930865;Bedrock level;Survival;1;19132;19133;"
    ) -> None:
        self.server_guid = server_guid
        self.server_name = server_name
        self.clients: Dict[tuple[str, int], Client] = {}
        self.transport: Optional[asyncio.DatagramTransport] = None
        
        # Connection handlers
        self.on_connect: Optional[Callable[[tuple[str, int]], None]] = None
        self.on_disconnect: Optional[Callable[[tuple[str, int]], None]] = None
        self.on_message: Optional[Callable[[tuple[str, int], bytes], None]] = None
    
    def connection_made(self, transport: asyncio.DatagramTransport) -> None:
        """Called when transport is ready."""
        self.transport = transport
    
    def connection_lost(self, exc: Exception) -> None:
        """Called when transport is closed."""
        for client in self.clients.values():
            if client.connected and self.on_disconnect:
                self.on_disconnect(client.address)
    
    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        """Handle received datagram."""
        try:
            if not data:
                return
                
            # Get packet type
            packet_type = data[0]
            
            # Handle connection sequence packets
            if packet_type in (
                PacketIdentifier.UNCONNECTED_PING,
                PacketIdentifier.UNCONNECTED_PING_OPEN_CONNECTIONS
            ):
                self._handle_ping(data, addr)
                
            elif packet_type == PacketIdentifier.OPEN_CONNECTION_REQUEST_1:
                self._handle_connection_request_1(data, addr)
                
            elif packet_type == PacketIdentifier.OPEN_CONNECTION_REQUEST_2:
                self._handle_connection_request_2(data, addr)
                
            elif packet_type == PacketIdentifier.CONNECTION_REQUEST:
                self._handle_connection_request(data, addr)
                
            # Handle connected client packets
            else:
                client = self.clients.get(addr)
                if not client or not client.connection:
                    return
                    
                if packet_type == PacketIdentifier.GAME_PACKET:
                    # Process RakNet packet through connection
                    client.connection.process_received(data[1:])
                
        except Exception as e:
            print(f"Error processing packet from {addr}: {e}")
    
    def _handle_ping(self, data: bytes, addr: tuple[str, int]) -> None:
        """Handle ping packets."""
        try:
            # Parse ping
            if data[0] == PacketIdentifier.UNCONNECTED_PING:
                ping = UnconnectedPing.deserialize(data)
            else:
                ping = UnconnectedPingOpenConnections.deserialize(data)
                
            # Create and send pong
            pong = UnconnectedPong(
                time=ping.time,
                server_guid=self.server_guid,
                server_name=self.server_name
            )
            if self.transport:
                self.transport.sendto(pong.serialize(), addr)
                
        except ValueError:
            pass  # Ignore malformed packets
    
    def _handle_connection_request_1(self, data: bytes, addr: tuple[str, int]) -> None:
        """Handle first connection request."""
        try:
            request = OpenConnectionRequest1.deserialize(data)
            
            # Verify protocol version
            if request.protocol_version != PROTOCOL_VERSION:
                return  # Incompatible version
            
            # Create client entry if needed
            if addr not in self.clients:
                self.clients[addr] = Client(address=addr)
            
            client = self.clients[addr]
            client.mtu_size = min(request.mtu_size, 1400)  # Cap MTU size
            
            # Send reply
            reply = OpenConnectionReply1(
                server_guid=self.server_guid,
                security=False,  # No encryption for now
                mtu_size=client.mtu_size
            )
            if self.transport:
                self.transport.sendto(reply.serialize(), addr)
                
        except ValueError:
            pass  # Ignore malformed packets
    
    def _handle_connection_request_2(self, data: bytes, addr: tuple[str, int]) -> None:
        """Handle second connection request."""
        try:
            request = OpenConnectionRequest2.deserialize(data)
            
            # Verify client exists
            client = self.clients.get(addr)
            if not client:
                return
                
            # Update client info
            client.guid = request.client_guid
            client.mtu_size = min(request.mtu_size, client.mtu_size)
            
            # Create RakNet connection
            if self.transport:
                client.connection = RakConnection(
                    transport=self.transport,
                    address=addr,
                    on_message=lambda data: self._handle_client_message(addr, data)
                )
                client.connection.start()
            
            # Send reply
            reply = OpenConnectionReply2(
                server_guid=self.server_guid,
                client_address=addr,
                mtu_size=client.mtu_size,
                encryption_enabled=False  # No encryption for now
            )
            if self.transport:
                self.transport.sendto(reply.serialize(), addr)
                
        except ValueError:
            pass  # Ignore malformed packets
    
    def _handle_connection_request(self, data: bytes, addr: tuple[str, int]) -> None:
        """Handle final connection request."""
        try:
            request = ConnectionRequest.deserialize(data)
            
            # Verify client exists with matching GUID
            client = self.clients.get(addr)
            if not client or client.guid != request.client_guid:
                return
            
            # Accept connection
            reply = ConnectionRequestAccepted(
                client_address=addr,
                system_index=0,  # Only single server supported
                request_timestamp=request.request_timestamp,
                accepted_timestamp=int(time.time() * 1000)
            )
            if self.transport:
                self.transport.sendto(reply.serialize(), addr)
            
            # Mark as connected and notify
            client.connected = True
            if self.on_connect:
                self.on_connect(addr)
                
        except ValueError:
            pass  # Ignore malformed packets
    
    def _handle_client_message(self, addr: tuple[str, int], data: bytes) -> None:
        """Handle decrypted message from connected client."""
        if self.on_message:
            self.on_message(addr, data)
    
    def send_message(
        self,
        addr: tuple[str, int],
        data: bytes,
        reliability: Reliability = Reliability.RELIABLE_ORDERED,
        priority: Priority = Priority.MEDIUM,
        channel: int = 0
    ) -> None:
        """Send message to connected client."""
        client = self.clients.get(addr)
        if not client or not client.connected or not client.connection:
            return
            
        # Queue in RakNet connection
        client.connection.queue_send(data, reliability, priority, channel)
    
    def flush_queues(self) -> None:
        """Flush all client send queues."""
        for client in self.clients.values():
            if client.connected and client.connection:
                client.connection.flush_queues()
    
    def disconnect_client(self, addr: tuple[str, int]) -> None:
        """Disconnect a client."""
        client = self.clients.get(addr)
        if not client:
            return
            
        if client.connection:
            asyncio.create_task(client.connection.stop())
        
        if client.connected and self.on_disconnect:
            self.on_disconnect(addr)
            
        del self.clients[addr]
    
    def close(self) -> None:
        """Close the server."""
        if self.transport:
            self.transport.close()
            
async def create_server(
    server_guid: int,
    host: str = "0.0.0.0",
    port: int = 19132,
    server_name: str = "MCPE;Dedicated Server;390;1.14.60;0;10;13253860892328930865;Bedrock level;Survival;1;19132;19133;"
) -> tuple[RakNetServer, asyncio.BaseTransport]:
    """Create and start a RakNet server."""
    loop = asyncio.get_running_loop()
    server = RakNetServer(server_guid=server_guid, server_name=server_name)
    transport, _ = await loop.create_datagram_endpoint(
        lambda: server,
        local_addr=(host, port)
    )
    return server, transport