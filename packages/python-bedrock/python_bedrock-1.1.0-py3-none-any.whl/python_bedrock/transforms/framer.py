def framePacket(data: bytes) -> bytes:
    length = len(data)
    return length.to_bytes(2, 'big') + data
