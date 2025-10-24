"""Compression handling for Bedrock protocol."""
import zlib
from typing import Tuple, Optional

class CompressionLevel:
    """Compression level constants."""
    NONE = 0
    FAST = 1
    NORMAL = 6
    BEST = 9
    DEFAULT = 7

class Compressor:
    """Protocol packet compression handler."""
    
    def __init__(self, level: int = CompressionLevel.DEFAULT) -> None:
        """Initialize compressor with compression level."""
        self.level = level
        # Initialize zlib objects with specified compression level
        self._compressor = zlib.compressobj(level)
        self._decompressor = zlib.decompressobj()
        
        # Track compression statistics
        self._total_compressed = 0
        self._total_uncompressed = 0
        self._compression_ratio = 0.0
    
    def compress(self, data: bytes) -> bytes:
        """Compress data with current settings."""
        try:
            compressed = self._compressor.compress(data)
            compressed += self._compressor.flush(zlib.Z_SYNC_FLUSH)
            
            # Update statistics
            self._total_uncompressed += len(data)
            self._total_compressed += len(compressed)
            self._update_ratio()
            
            return compressed
        except zlib.error as e:
            raise CompressionError(f"Compression failed: {e}")
    
    def decompress(self, data: bytes) -> bytes:
        """Decompress data with current settings."""
        try:
            decompressed = self._decompressor.decompress(data)
            decompressed += self._decompressor.flush(zlib.Z_SYNC_FLUSH)
            
            # Update statistics
            self._total_compressed += len(data)
            self._total_uncompressed += len(decompressed)
            self._update_ratio()
            
            return decompressed
        except zlib.error as e:
            raise CompressionError(f"Decompression failed: {e}")
    
    def _update_ratio(self) -> None:
        """Update compression ratio statistics."""
        if self._total_uncompressed > 0:
            self._compression_ratio = (
                self._total_compressed / self._total_uncompressed
            )
    
    def reset(self) -> None:
        """Reset compression state."""
        self._compressor = zlib.compressobj(self.level)
        self._decompressor = zlib.decompressobj()
    
    @property
    def stats(self) -> dict:
        """Get compression statistics."""
        return {
            'level': self.level,
            'total_compressed': self._total_compressed,
            'total_uncompressed': self._total_uncompressed,
            'compression_ratio': self._compression_ratio
        }

class PacketCompressor:
    """Packet-level compression handler with header support."""
    
    def __init__(
        self,
        level: int = CompressionLevel.DEFAULT,
        threshold: int = 256,  # Only compress packets larger than this
        header_in_packet: bool = True  # Whether compression header is in packet
    ) -> None:
        self.compressor = Compressor(level)
        self.threshold = threshold
        self.header_in_packet = header_in_packet
    
    def pack(self, data: bytes) -> Tuple[bytes, bool]:
        """Pack data with optional compression.
        
        Returns:
            Tuple[bytes, bool]: (packed data, whether compressed)
        """
        if len(data) > self.threshold:
            compressed = self.compressor.compress(data)
            if self.header_in_packet:
                # Format: compressed(1) + compressed_size(4) + data
                header = bytes([1]) + len(compressed).to_bytes(4, 'little')
                return header + compressed, True
            return compressed, True
        
        if self.header_in_packet:
            # Format: compressed(1) + original_data
            return bytes([0]) + data, False
        return data, False
    
    def unpack(self, data: bytes) -> Tuple[bytes, bool]:
        """Unpack potentially compressed data.
        
        Returns:
            Tuple[bytes, bool]: (unpacked data, whether was compressed)
        """
        if self.header_in_packet:
            if len(data) < 1:
                raise CompressionError("Data too short for compression header")
            
            compressed = bool(data[0])
            if compressed:
                if len(data) < 5:
                    raise CompressionError("Compressed data too short")
                size = int.from_bytes(data[1:5], 'little')
                compressed_data = data[5:]
                if len(compressed_data) != size:
                    raise CompressionError(
                        f"Compressed data size mismatch: {len(compressed_data)} != {size}"
                    )
                return self.compressor.decompress(compressed_data), True
            return data[1:], False
        
        # No header - try decompressing if over threshold
        if len(data) > self.threshold:
            try:
                return self.compressor.decompress(data), True
            except CompressionError:
                return data, False
        return data, False
    
    @property
    def stats(self) -> dict:
        """Get compression statistics."""
        return {
            **self.compressor.stats,
            'threshold': self.threshold,
            'header_in_packet': self.header_in_packet
        }

class CompressionError(Exception):
    """Compression-related errors."""
    pass