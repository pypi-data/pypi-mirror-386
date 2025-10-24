"""Framer compatible with bedrock-protocol-master JS implementation.

Features implemented:
- varint-length prefixed packets inside a batch
- optional batch header byte
- optional compressor-in-header handling
- deflate (raw) compression/decompression

This mirrors the behavior in `src/transforms/framer.js` so Python code
can interoperate with the JS implementation.
"""
from __future__ import annotations

import zlib
from typing import List, Optional

from ..protocol.types import VarInt


class Framer:
    def __init__(self, client: Optional[object] = None):
        # Encoding state
        self.packets: List[bytes] = []
        # Mirror JS client-driven configuration when provided
        self.batchHeader = getattr(client, 'batchHeader', None) if client is not None else None
        self.compressor = getattr(client, 'compressionAlgorithm', 'none') if client is not None else 'none'
        self.compressionLevel = getattr(client, 'compressionLevel', 6) if client is not None else 6
        self.compressionThreshold = getattr(client, 'compressionThreshold', 1000) if client is not None else 1000
        self.compressionHeader = getattr(client, 'compressionHeader', 0) if client is not None else 0
        self.writeCompressor = bool(getattr(client, 'features', None) and getattr(client.features, 'compressorInHeader', False) and getattr(client, 'compressionReady', False)) if client is not None else False

    def compress(self, buffer: bytes) -> bytes:
        """Compress buffer according to selected compressor (only deflate/none supported)."""
        if self.compressor == 'deflate':
            # Raw deflate (no zlib header) — use negative wbits
            comp = zlib.compressobj(self.compressionLevel, zlib.DEFLATED, -zlib.MAX_WBITS)
            return comp.compress(buffer) + comp.flush()
        if self.compressor in (None, 'none'):
            return buffer
        raise NotImplementedError('Snappy compression not implemented')

    @staticmethod
    def decompress(algorithm, buffer: bytes) -> bytes:
        """Decompress buffer according to algorithm (0/'deflate' or 255/'none')."""
        if algorithm in (0, 'deflate'):
            # raw inflate
            return zlib.decompress(buffer, -zlib.MAX_WBITS)
        if algorithm in (1, 'snappy'):
            raise NotImplementedError('Snappy compression not implemented')
        if algorithm in ('none', 255):
            return buffer
        raise ValueError(f'Unknown compression type {algorithm}')

    @staticmethod
    def decode(client: object, buf: bytes) -> List[bytes]:
        """Decode a batch buffer into inner packets.

        Expects the same header/compression rules as the JS framer.
        """
        # If a batch header is configured, verify it
        if getattr(client, 'batchHeader', None) is not None:
            if len(buf) == 0 or buf[0] != client.batchHeader:
                raise ValueError(f'bad batch packet header, received: {buf[0] if buf else None}, expected: {client.batchHeader}')
            buffer = buf[1:]
        else:
            buffer = buf

        # Decompress according to compressor-in-header or session-wide algorithm
        decompressed: bytes
        if getattr(client, 'features', None) and getattr(client.features, 'compressorInHeader', False) and getattr(client, 'compressionReady', False):
            # First byte is compressor id
            if len(buffer) == 0:
                decompressed = b''
            else:
                algorithm = buffer[0]
                decompressed = Framer.decompress(algorithm, buffer[1:])
        else:
            # Try session-wide algorithm; fall back to raw buffer on failure (like JS)
            try:
                decompressed = Framer.decompress(getattr(client, 'compressionAlgorithm', 'none'), buffer)
            except Exception:
                decompressed = buffer

        return Framer.getPackets(decompressed)

    def encode(self) -> bytes:
        buf = b''.join(self.packets)
        shouldCompress = len(buf) > self.compressionThreshold
        header_bytes = b''
        if self.batchHeader is not None:
            header_bytes += bytes([self.batchHeader])
        if self.writeCompressor:
            header_bytes += bytes([self.compressionHeader if shouldCompress else 255])

        body = self.compress(buf) if shouldCompress else buf
        return header_bytes + body

    def addEncodedPacket(self, chunk: bytes) -> None:
        varint = VarInt.write(len(chunk))
        self.packets.append(varint + chunk)

    def addEncodedPackets(self, packets: List[bytes]) -> None:
        parts: List[bytes] = []
        for p in packets:
            parts.append(VarInt.write(len(p)) + p)
        self.packets.append(b''.join(parts))

    def getBuffer(self) -> bytes:
        return b''.join(self.packets)

    @staticmethod
    def getPackets(buffer: bytes) -> List[bytes]:
        packets: List[bytes] = []
        offset = 0
        total = len(buffer)
        while offset < total:
            length, new_offset = VarInt.read(buffer, offset)
            # VarInt.read returns the value and the new offset
            packet_start = new_offset
            packet_end = packet_start + length
            if packet_end > total:
                raise ValueError('Incomplete packet in batch')
            packets.append(buffer[packet_start:packet_end])
            offset = packet_end
        return packets


__all__ = ['Framer']
