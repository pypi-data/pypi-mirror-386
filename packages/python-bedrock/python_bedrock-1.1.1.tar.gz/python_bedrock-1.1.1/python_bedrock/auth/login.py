"""Login packet handlers and encryption setup."""
import asyncio
import base64
import json
import struct
from dataclasses import dataclass
from typing import Optional, Dict, Any, List, Tuple, TYPE_CHECKING
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization

from ..raknet.protocol import Reliability, Priority
if TYPE_CHECKING:
    from ..connection import Connection
    from .security import SecurityManager
    from .xbox import XboxLiveAuth

# Login packet IDs
LOGIN_PACKET = 0x01
CLIENT_TO_SERVER_HANDSHAKE = 0x02
SERVER_TO_CLIENT_HANDSHAKE = 0x03
CLIENT_RESPONSE = 0x04
SERVER_RESPONSE = 0x05

@dataclass
class LoginHandler:
    """Handles login sequence and encryption setup."""
    
    connection: 'Connection'
    security: 'SecurityManager'
    xbox_auth: Optional['XboxLiveAuth'] = None
    enforce_auth: bool = True
    
    async def handle_login_request(
        self,
        data: bytes
    ) -> None:
        """Handle initial login request."""
        try:
            # Parse protocol version
            protocol = struct.unpack('>I', data[:4])[0]
            if protocol != self.connection.protocol_version:
                await self._disconnect("Incompatible protocol version")
                return
                
            # Parse login tokens
            payload = json.loads(data[4:].decode('utf-8'))
            chain_data = payload.get('chain', [])
            client_data = payload.get('clientData', '')
            
            # Verify authentication chain
            if not self.security.verify_chain(
                chain_data,
                client_data,
                self.enforce_auth
            ):
                await self._disconnect("Invalid authentication chain")
                return
            
            # Initialize encryption
            self.security.init_encryption()
            
            # Send server handshake
            await self._send_server_handshake()
            
        except Exception as e:
            await self._disconnect(f"Login failed: {e}")
    
    async def handle_client_handshake(
        self,
        data: bytes
    ) -> None:
        """Handle client's encryption handshake."""
        try:
            # Get client's public key
            client_key = data
            
            # Compute shared secret
            secret = self.security.compute_shared_secret(
                client_key,
                self.security.chain_data.client_random
            )
            
            # Enable encryption
            self.security.enable_encryption(secret)
            
            # Send server response
            await self._send_server_response()
            
            # Mark as encrypted
            self.connection.encrypted = True
            
        except Exception as e:
            await self._disconnect(f"Encryption setup failed: {e}")
    
    async def handle_client_response(
        self,
        data: bytes
    ) -> None:
        """Handle client's final response."""
        try:
            # Verify response matches
            if data != self.security.chain_data.client_random:
                await self._disconnect("Invalid client response")
                return
                
            # Login complete
            self.connection.authenticated = True
            if self.connection.on_login_success:
                await self.connection.on_login_success()
                
        except Exception as e:
            await self._disconnect(f"Login completion failed: {e}")
    
    async def _send_server_handshake(self) -> None:
        """Send server encryption handshake."""
        if not self.security.chain_data:
            raise ValueError("Security not initialized")
            
        # Get server's public key
        public_key = self.security.chain_data.identity_private_key.public_key()
        key_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        # Create packet with public key and server random
        data = (
            key_bytes +
            self.security.chain_data.server_random
        )
        
        # Send handshake packet
        await self.connection.send_packet(
            SERVER_TO_CLIENT_HANDSHAKE,
            data,
            Reliability.RELIABLE_ORDERED
        )
    
    async def _send_server_response(self) -> None:
        """Send server's final response."""
        if not self.security.chain_data:
            raise ValueError("Security not initialized")
            
        # Send encrypted server random
        await self.connection.send_packet(
            SERVER_RESPONSE,
            self.security.chain_data.server_random,
            Reliability.RELIABLE_ORDERED
        )
    
    async def _disconnect(self, reason: str) -> None:
        """Disconnect with error."""
        if self.connection.on_login_failed:
            await self.connection.on_login_failed(reason)
        await self.connection.disconnect(reason)

def create_login_packet(
    protocol_version: int,
    chain_data: List[str],
    client_data: str
) -> bytes:
    """Create initial login packet."""
    payload = {
        'chain': chain_data,
        'clientData': client_data
    }
    data = struct.pack('>I', protocol_version)
    data += json.dumps(payload).encode('utf-8')
    return data