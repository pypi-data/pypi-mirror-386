import asyncio
from typing import Tuple, Optional
from ..encryption import KeyExchange, SessionCrypto, generate_session_key
from ..connection import Connection
from ..types import HandshakeError
from ..datatypes.handshake import HandshakePacket

async def performKeyExchange(conn: Connection) -> Tuple[SessionCrypto, bytes]:
    """Perform key exchange and establish session encryption."""
    try:
        # Initialize key exchange
        exchange = KeyExchange()
        
        # Send our public key
        public_key = exchange.public_key_bytes
        await conn.send(HandshakePacket(token=public_key.hex()).serialize())
        
        # Receive peer's public key
        data = await conn.receive()
        peer_packet = HandshakePacket.deserialize(data)
        peer_key = bytes.fromhex(peer_packet.token)
        
        # Compute shared secret and derive session key
        shared = exchange.compute_shared(peer_key)
        session_key, salt = generate_session_key()
        
        # Create session crypto
        crypto = SessionCrypto(session_key)
        
        # Return the session crypto and salt
        return crypto, salt
        
    except Exception as e:
        raise HandshakeError(f"Key exchange failed: {e}")
