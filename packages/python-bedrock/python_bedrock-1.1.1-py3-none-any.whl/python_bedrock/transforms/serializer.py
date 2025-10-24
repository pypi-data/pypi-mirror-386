from typing import Dict, Type, Any, Optional
from ..datatypes.packets import (
    Packet, PacketHeader, PacketSerializable,
    PacketID, TextPacket, DisconnectPacket
)
from ..datatypes.handshake import (
    LoginPacket, HandshakePacket, PlayStatusPacket
)

# Registry of packet types by ID
PACKET_TYPES: Dict[int, Type[PacketSerializable]] = {
    PacketID.LOGIN: LoginPacket,
    PacketID.PLAY_STATUS: PlayStatusPacket,
    PacketID.SERVER_TO_CLIENT_HANDSHAKE: HandshakePacket,
    PacketID.CLIENT_TO_SERVER_HANDSHAKE: HandshakePacket,
    PacketID.TEXT: TextPacket,
    PacketID.DISCONNECT: DisconnectPacket,
    PacketID.RESOURCE_PACKS_INFO: ResourcePacksInfoPacket,
    PacketID.RESOURCE_PACK_STACK: ResourcePackStackPacket,
}

def serializePacket(
    packetId: int,
    payload: PacketSerializable,
    senderId: int = 0,
    clientId: int = 0
) -> bytes:
    """Serialize a packet with header and payload."""
    header = PacketHeader(
        packetId=packetId,
        senderId=senderId,
        clientId=clientId
    )
    packet = Packet(header=header, payload=payload)
    return packet.serialize()

def deserializePacket(data: bytes) -> Optional[Packet]:
    """Deserialize a complete packet from bytes."""
    if len(data) < 21:  # 4 (length) + 17 (header)
        return None
        
    # Read packet ID to determine payload type
    packet_id = int.from_bytes(data[4:5], 'big')
    payload_type = PACKET_TYPES.get(packet_id)
    if not payload_type:
        raise ValueError(f"Unknown packet ID: {packet_id}")
        
    return Packet.deserialize(data, payload_type)

def serializeMessage(message: str, source: str = "") -> bytes:
    """Helper to create and serialize a text packet."""
    return serializePacket(
        PacketID.TEXT,
        TextPacket(message=message, source=source)
    )

def serializeDisconnect(reason: str) -> bytes:
    """Helper to create and serialize a disconnect packet."""
    return serializePacket(
        PacketID.DISCONNECT,
        DisconnectPacket(reason=reason)
    )
