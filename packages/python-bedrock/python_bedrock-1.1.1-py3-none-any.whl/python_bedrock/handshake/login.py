import asyncio
from typing import Dict, Any, Tuple
from ..auth import AuthSession
from ..connection import Connection
from ..types import AuthenticationError
from ..datatypes.handshake import LoginPacket, PlayStatusPacket
from ..datatypes.packets import PacketID

async def performLogin(
    conn: Connection,
    credentials: Dict[str, Any]
) -> Tuple[AuthSession, str]:
    """Perform login handshake with Xbox Live authentication."""
    try:
        # Create auth session
        session = AuthSession()
        
        # Send login packet
        login = LoginPacket(
            protocol=credentials.get('protocol', 0),
            username=credentials.get('username', ''),
            clientUUID=credentials.get('clientId', ''),
            clientId=credentials.get('deviceId', ''),
            xuid=credentials.get('xuid', ''),
            identityPublicKey=credentials.get('identityPublicKey', ''),
            serverAddress=credentials.get('serverAddress', ''),
            languageCode=credentials.get('language', 'en_US')
        )
        
        # If chain data is provided, validate it
        chain_data = credentials.get('chain')
        if chain_data:
            session.setChain(chain_data)
            login.chainData = chain_data
            
        # Send login and await response
        await conn.send(login.serialize())
        
        # Wait for play status response
        response_data = await conn.receive()
        response = PlayStatusPacket.deserialize(response_data)
        
        if response.status != 0:  # 0 = OK
            raise AuthenticationError(f"Login failed with status {response.status}")
        
        # Mark connection as authenticated
        conn.state.markAuthenticated()
        
        return session, login.username
        
    except Exception as e:
        raise AuthenticationError(f"Login failed: {e}")
