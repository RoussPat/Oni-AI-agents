"""
Binary Reader for ONI Save Files

Low-level binary operations for reading ONI save file data.
Based on RoboPhred's ArrayDataReader implementation.
"""

import struct
import zlib
from io import BytesIO
from typing import Any, Callable, List, Optional


class BinaryReader:
    """
    Binary reader for ONI save file data.
    
    Provides methods for reading various data types from binary streams,
    matching the structure used in ONI save files.
    """
    
    def __init__(self, data: bytes):
        """
        Initialize with binary data.
        
        Args:
            data: Raw binary data from save file
        """
        self.stream = BytesIO(data)
        self.position = 0
    
    def read_bytes(self, count: int) -> bytes:
        """Read a specific number of bytes."""
        data = self.stream.read(count)
        if len(data) != count:
            raise EOFError(f"Expected {count} bytes, got {len(data)}")
        self.position += count
        return data
    
    def read_int8(self) -> int:
        """Read a signed 8-bit integer."""
        return struct.unpack('<b', self.read_bytes(1))[0]
    
    def read_uint8(self) -> int:
        """Read an unsigned 8-bit integer."""
        return struct.unpack('<B', self.read_bytes(1))[0]
    
    def read_int16(self) -> int:
        """Read a signed 16-bit integer (little-endian)."""
        return struct.unpack('<h', self.read_bytes(2))[0]
    
    def read_uint16(self) -> int:
        """Read an unsigned 16-bit integer (little-endian)."""
        return struct.unpack('<H', self.read_bytes(2))[0]
    
    def read_int32(self) -> int:
        """Read a signed 32-bit integer (little-endian)."""
        return struct.unpack('<i', self.read_bytes(4))[0]
    
    def read_uint32(self) -> int:
        """Read an unsigned 32-bit integer (little-endian)."""
        return struct.unpack('<I', self.read_bytes(4))[0]
    
    def read_int64(self) -> int:
        """Read a signed 64-bit integer (little-endian)."""
        return struct.unpack('<q', self.read_bytes(8))[0]
    
    def read_uint64(self) -> int:
        """Read an unsigned 64-bit integer (little-endian)."""
        return struct.unpack('<Q', self.read_bytes(8))[0]
    
    def read_float32(self) -> float:
        """Read a 32-bit float (little-endian)."""
        return struct.unpack('<f', self.read_bytes(4))[0]
    
    def read_float64(self) -> float:
        """Read a 64-bit float (little-endian)."""
        return struct.unpack('<d', self.read_bytes(8))[0]
    
    def read_bool(self) -> bool:
        """Read a boolean value (1 byte)."""
        return self.read_uint8() != 0
    
    def read_string(self) -> str:
        """
        Read a length-prefixed UTF-8 string.
        
        ONI strings are stored as:
        - 4-byte length (int32)
        - UTF-8 encoded string data
        """
        length = self.read_int32()
        if length < 0:
            raise ValueError(f"Invalid string length: {length}")
        if length == 0:
            return ""
        
        string_bytes = self.read_bytes(length)
        return string_bytes.decode('utf-8')
    
    def read_array(self, element_reader: Callable[[], Any]) -> List[Any]:
        """
        Read an array of elements using a provided reader function.
        
        ONI arrays are stored as:
        - 4-byte count (int32)
        - Elements read using element_reader
        
        Args:
            element_reader: Function to read each array element
            
        Returns:
            List of elements read by element_reader
        """
        count = self.read_int32()
        if count < 0:
            raise ValueError(f"Invalid array count: {count}")
        
        elements = []
        for _ in range(count):
            elements.append(element_reader())
        
        return elements
    
    def read_key_value_pairs(self, key_reader: Callable[[], Any], 
                           value_reader: Callable[[], Any]) -> List[tuple]:
        """
        Read an array of key-value pairs.
        
        Used for dictionaries/maps in ONI save files.
        Maintains order as tuples rather than dict to preserve file order.
        
        Args:
            key_reader: Function to read keys
            value_reader: Function to read values
            
        Returns:
            List of (key, value) tuples
        """
        count = self.read_int32()
        if count < 0:
            raise ValueError(f"Invalid key-value pair count: {count}")
        
        pairs = []
        for _ in range(count):
            key = key_reader()
            value = value_reader()
            pairs.append((key, value))
        
        return pairs
    
    def decompress_zlib(self, compressed_size: Optional[int] = None) -> 'BinaryReader':
        """
        Decompress zlib-compressed data and return a new BinaryReader.
        
        Args:
            compressed_size: Size of compressed data to read (if None, read to end)
            
        Returns:
            New BinaryReader with decompressed data
        """
        if compressed_size is None:
            compressed_data = self.stream.read()
        else:
            compressed_data = self.read_bytes(compressed_size)
        
        try:
            decompressed_data = zlib.decompress(compressed_data)
            return BinaryReader(decompressed_data)
        except zlib.error as e:
            raise ValueError(f"Failed to decompress zlib data: {e}")
    
    def skip_bytes(self, count: int):
        """Skip a number of bytes."""
        self.stream.seek(count, 1)  # Seek relative to current position
        self.position += count
    
    def get_position(self) -> int:
        """Get current position in stream."""
        return self.stream.tell()
    
    def seek(self, position: int):
        """Seek to absolute position."""
        self.stream.seek(position)
        self.position = position
    
    def remaining_bytes(self) -> int:
        """Get number of bytes remaining in stream."""
        current = self.stream.tell()
        self.stream.seek(0, 2)  # Seek to end
        end = self.stream.tell()
        self.stream.seek(current)  # Seek back
        return end - current
    
    def is_at_end(self) -> bool:
        """Check if at end of stream."""
        return self.remaining_bytes() == 0
