"""
Shared memory hashmap for multiprocessing with atomic operations.

This module provides a thread-safe and process-safe hashmap implementation
using shared memory and atomic operations from the atomics package.
"""

import pickle
import struct
import time
from multiprocessing import shared_memory
from typing import Any

import atomics

# Bucket states
EMPTY = 0
OCCUPIED = 1
DELETED = 2

# Type markers for serialization
TYPE_PICKLE = 0  # Complex objects via pickle
TYPE_STR = 1  # UTF-8 encoded strings
TYPE_BYTES = 2  # Raw bytes
TYPE_INT = 3  # Integer as bytes
TYPE_NONE = 4  # None value

# Memory layout constants
METADATA_SIZE = 32  # capacity (8) + size (8) + max_key_size (8) + max_value_size (8)
SIZE_OFFSET = 8  # Offset of size field in metadata (after capacity)
STATE_SIZE = 8  # AtomicInt uses 8 bytes
# Header format: state (8 bytes) + type markers and sizes (struct: BBII)
HEADER_STRUCT_FORMAT = "=BBII"  # = for no padding, B=byte, I=uint32
HEADER_STRUCT_SIZE = struct.calcsize(HEADER_STRUCT_FORMAT)
HEADER_SIZE = STATE_SIZE + HEADER_STRUCT_SIZE


class SharedHashMap:
    """
    A thread-safe and process-safe hashmap using shared memory.

    This hashmap uses open addressing with linear probing for collision resolution
    and atomic operations for synchronization between processes.

    Args:
        name: Name for the shared memory block (must be unique across processes)
        capacity: Number of buckets in the hashmap (default: 1024)
        max_key_size: Maximum size in bytes for serialized keys (default: 256)
        max_value_size: Maximum size in bytes for serialized values (default: 1024)
        create: If True, create new shared memory; if False, attach to existing (default: True)
    """

    def __init__(
        self,
        name: str,
        capacity: int = 1024,
        max_key_size: int = 256,
        max_value_size: int = 1024,
        create: bool = True,
    ):
        self.name = name

        if create:
            # Store parameters for creation
            self.capacity = capacity
            self.max_key_size = max_key_size
            self.max_value_size = max_value_size

            # Calculate bucket size and round up to 8-byte alignment for atomic operations
            raw_bucket_size = HEADER_SIZE + max_key_size + max_value_size
            self.bucket_size = ((raw_bucket_size + 7) // 8) * 8  # Round up to nearest 8 bytes

            # Calculate total memory needed
            self.total_size = METADATA_SIZE + (self.bucket_size * capacity)

            # Create new shared memory
            self.shm = shared_memory.SharedMemory(name=name, create=True, size=self.total_size)
            # Initialize metadata
            self._write_metadata(capacity, 0, max_key_size, max_value_size)

            # Pre-allocate size counter atomic view for performance
            size_buf_slice = self.shm.buf[SIZE_OFFSET : SIZE_OFFSET + 8]
            size_atomic_view = atomics.atomicview(buffer=size_buf_slice, width=8, atype=atomics.UINT)
            self._size_atomic = size_atomic_view.__enter__()
            self._size_atomic_context = size_atomic_view

            # Pre-allocate atomic views for bucket states - use lazy loading for performance
            self._atomic_states = {}  # Change to dict for lazy loading
            self._atomic_contexts = {}

            # Initialize all buckets to EMPTY
            for i in range(capacity):
                self._write_bucket_state(i, EMPTY)
        else:
            # Attach to existing shared memory
            self.shm = shared_memory.SharedMemory(name=name, create=False)

            # Read all parameters from metadata with retry for race condition handling
            # Worker processes might attach before creator finishes writing metadata
            max_retries = 100
            for attempt in range(max_retries):
                self.capacity, _, self.max_key_size, self.max_value_size = self._read_metadata()

                # Validate metadata - if any critical field is 0, metadata isn't ready yet
                if self.capacity > 0 and self.max_key_size > 0 and self.max_value_size > 0:
                    break

                if attempt < max_retries - 1:
                    time.sleep(0.001)  # Wait 1ms before retrying
                else:
                    raise RuntimeError(
                        f"Failed to read valid metadata from shared memory '{name}'. "
                        f"Got: capacity={self.capacity}, max_key_size={self.max_key_size}, "
                        f"max_value_size={self.max_value_size}"
                    )

            # Calculate bucket size using the values from metadata
            raw_bucket_size = HEADER_SIZE + self.max_key_size + self.max_value_size
            self.bucket_size = ((raw_bucket_size + 7) // 8) * 8

            # Calculate total memory needed (for consistency)
            self.total_size = METADATA_SIZE + (self.bucket_size * self.capacity)

            # Pre-allocate size counter atomic view for performance
            size_buf_slice = self.shm.buf[SIZE_OFFSET : SIZE_OFFSET + 8]
            size_atomic_view = atomics.atomicview(buffer=size_buf_slice, width=8, atype=atomics.UINT)
            self._size_atomic = size_atomic_view.__enter__()
            self._size_atomic_context = size_atomic_view

            # Pre-allocate atomic views for bucket states - use lazy loading for performance
            self._atomic_states = {}  # Change to dict for lazy loading
            self._atomic_contexts = {}

    def _write_metadata(self, capacity: int, size: int, max_key_size: int, max_value_size: int) -> None:
        """Write metadata to shared memory."""
        struct.pack_into("QQQQ", self.shm.buf, 0, capacity, size, max_key_size, max_value_size)

    def _read_metadata(self) -> tuple[int, int, int, int]:
        """Read metadata from shared memory."""
        return struct.unpack_from("QQQQ", self.shm.buf, 0)

    def _get_bucket_offset(self, bucket_idx: int) -> int:
        """Calculate the memory offset for a given bucket index."""
        return METADATA_SIZE + (bucket_idx * self.bucket_size)

    def _serialize(self, obj: Any) -> tuple[int, bytes]:
        """
        Serialize an object efficiently.

        Returns:
            (type_marker, serialized_bytes)
        """
        if obj is None:
            return (TYPE_NONE, b"")
        elif isinstance(obj, str):
            return (TYPE_STR, obj.encode("utf-8"))
        elif isinstance(obj, bytes):
            return (TYPE_BYTES, obj)
        elif isinstance(obj, int):
            return (TYPE_INT, str(obj).encode("ascii"))
        else:
            # Fall back to pickle for complex types
            return (TYPE_PICKLE, pickle.dumps(obj))

    def _deserialize(self, type_marker: int, data: bytes) -> Any:
        """
        Deserialize an object.

        Args:
            type_marker: The type marker indicating how to deserialize
            data: The serialized bytes

        Returns:
            The deserialized object
        """
        if type_marker == TYPE_NONE:
            return None
        elif type_marker == TYPE_STR:
            return data.decode("utf-8")
        elif type_marker == TYPE_BYTES:
            return data
        elif type_marker == TYPE_INT:
            return int(data.decode("ascii"))
        elif type_marker == TYPE_PICKLE:
            return pickle.loads(data)
        else:
            raise ValueError(f"Unknown type marker: {type_marker}")

    def _get_bucket_atomic_view(self, bucket_idx: int):
        """Get atomic view for bucket state, creating lazily if needed."""
        if bucket_idx not in self._atomic_states:
            offset = self._get_bucket_offset(bucket_idx)
            buf_slice = self.shm.buf[offset : offset + STATE_SIZE]
            atomic_view = atomics.atomicview(buffer=buf_slice, width=8, atype=atomics.UINT)
            self._atomic_states[bucket_idx] = atomic_view.__enter__()
            self._atomic_contexts[bucket_idx] = atomic_view
        return self._atomic_states[bucket_idx]

    def _write_bucket_state(self, bucket_idx: int, state: int) -> None:
        """Write the state of a bucket using atomic view (lazy-loaded)."""
        atomic_view = self._get_bucket_atomic_view(bucket_idx)
        atomic_view.store(state)

    def _read_bucket_state(self, bucket_idx: int) -> int:
        """Read the state of a bucket atomically using atomic view (lazy-loaded)."""
        atomic_view = self._get_bucket_atomic_view(bucket_idx)
        return atomic_view.load()

    def _write_bucket_data(
        self,
        bucket_idx: int,
        key_type: int,
        key_data: bytes,
        value_type: int,
        value_data: bytes,
    ) -> None:
        """Write key and value data to a bucket with type markers."""
        offset = self._get_bucket_offset(bucket_idx)

        # Write type markers, key size, and value size
        struct.pack_into(
            HEADER_STRUCT_FORMAT,
            self.shm.buf,
            offset + STATE_SIZE,
            key_type,
            value_type,
            len(key_data),
            len(value_data),
        )

        # Write key data
        key_offset = offset + HEADER_SIZE
        self.shm.buf[key_offset : key_offset + len(key_data)] = key_data

        # Write value data
        value_offset = key_offset + self.max_key_size
        self.shm.buf[value_offset : value_offset + len(value_data)] = value_data

    def _read_bucket_data(self, bucket_idx: int) -> tuple[int, bytes, int, bytes]:
        """Read key and value data from a bucket with type markers."""
        offset = self._get_bucket_offset(bucket_idx)

        # Read type markers, key size, and value size
        key_type, value_type, key_size, value_size = struct.unpack_from(HEADER_STRUCT_FORMAT, self.shm.buf, offset + STATE_SIZE)

        # Read key data
        key_offset = offset + HEADER_SIZE
        key_data = bytes(self.shm.buf[key_offset : key_offset + key_size])

        # Read value data
        value_offset = key_offset + self.max_key_size
        value_data = bytes(self.shm.buf[value_offset : value_offset + value_size])

        return key_type, key_data, value_type, value_data

    def _fast_hash(self, data: bytes) -> int:
        """Fast FNV-1a hash function for hash table use."""
        # FNV-1a constants for 64-bit
        FNV_OFFSET_BASIS = 14695981039346656037
        FNV_PRIME = 1099511628211

        hash_value = FNV_OFFSET_BASIS
        for byte in data:
            hash_value ^= byte
            hash_value = (hash_value * FNV_PRIME) & 0xFFFFFFFFFFFFFFFF
        return hash_value % self.capacity

    def _find_bucket(self, key: Any) -> tuple[int, bool]:
        """
        Find the bucket index for a key using optimized linear probing.

        Returns:
            (bucket_index, found): bucket_index is where the key is or should be inserted,
                                   found is True if the key exists, False otherwise
        """
        # Serialize key once and reuse
        key_type, key_data = self._serialize(key)
        start_idx = self._fast_hash(key_data)

        # Remember the first deleted slot we encounter for potential insertion
        first_deleted = None

        for i in range(self.capacity):
            # Quadratic probing: reduces clustering vs linear probing
            bucket_idx = (start_idx + i + i * i) % self.capacity
            state = self._read_bucket_state(bucket_idx)

            if state == EMPTY:
                # Found an empty slot, key doesn't exist
                # Use first_deleted if we found one, otherwise use this empty slot
                return first_deleted if first_deleted is not None else bucket_idx, False
            elif state == OCCUPIED:
                # Check if this bucket contains our key
                stored_key_type, stored_key_data, _, _ = self._read_bucket_data(bucket_idx)
                if stored_key_type == key_type and stored_key_data == key_data:
                    return bucket_idx, True
            elif state == DELETED and first_deleted is None:
                # Remember first deleted slot for potential insertion
                first_deleted = bucket_idx

        # Hash table is full (shouldn't happen with proper sizing)
        raise RuntimeError("Hash table is full")

    def _find_bucket_with_serialized_key(self, key_type: int, key_data: bytes) -> tuple[int, bool]:
        """
        Find bucket using pre-serialized key data to avoid double serialization.

        Returns:
            (bucket_index, found): bucket_index is where the key is or should be inserted,
                                   found is True if the key exists, False otherwise
        """
        start_idx = self._fast_hash(key_data)
        first_deleted = None

        for i in range(self.capacity):
            # Quadratic probing: reduces clustering vs linear probing
            bucket_idx = (start_idx + i + i * i) % self.capacity
            state = self._read_bucket_state(bucket_idx)

            if state == EMPTY:
                return first_deleted if first_deleted is not None else bucket_idx, False
            elif state == OCCUPIED:
                stored_key_type, stored_key_data, _, _ = self._read_bucket_data(bucket_idx)
                if stored_key_type == key_type and stored_key_data == key_data:
                    return bucket_idx, True
            elif state == DELETED and first_deleted is None:
                first_deleted = bucket_idx

        raise RuntimeError("Hash table is full")

    def set(self, key: Any, value: Any) -> None:
        """
        Set a key-value pair in the hashmap.

        Args:
            key: The key (strings, bytes, ints, and None are optimized; others use pickle)
            value: The value (strings, bytes, ints, and None are optimized; others use pickle)

        Raises:
            ValueError: If serialized key or value exceeds maximum size
        """
        key_type, key_data = self._serialize(key)
        value_type, value_data = self._serialize(value)

        if len(key_data) > self.max_key_size:
            raise ValueError(f"Serialized key size {len(key_data)} exceeds maximum {self.max_key_size}")
        if len(value_data) > self.max_value_size:
            raise ValueError(f"Serialized value size {len(value_data)} exceeds maximum {self.max_value_size}")

        bucket_idx, found = self._find_bucket_with_serialized_key(key_type, key_data)

        # Try to acquire the bucket
        if found:
            # Update existing entry
            self._write_bucket_data(bucket_idx, key_type, key_data, value_type, value_data)
        else:
            # Insert new entry
            # Use compare and swap to atomically claim the bucket
            claimed = False
            while not claimed:
                current_state = self._read_bucket_state(bucket_idx)
                expected_state = EMPTY if current_state == EMPTY else DELETED

                atomic_view = self._get_bucket_atomic_view(bucket_idx)
                success, _ = atomic_view.cmpxchg_strong(expected_state, OCCUPIED)

                if success:
                    claimed = True
                else:
                    # Someone else modified this bucket, re-find using pre-serialized key
                    bucket_idx, found = self._find_bucket_with_serialized_key(key_type, key_data)
                    if found:
                        # Key was inserted by another process
                        self._write_bucket_data(bucket_idx, key_type, key_data, value_type, value_data)
                        return

            # We successfully claimed the bucket
            self._write_bucket_data(bucket_idx, key_type, key_data, value_type, value_data)

            # Atomically increment size counter
            self._atomic_increment_size()

    def get(self, key: Any, default: Any = None) -> Any:
        """
        Get a value from the hashmap.

        Args:
            key: The key to look up
            default: Default value to return if key not found

        Returns:
            The value associated with the key, or default if not found
        """
        bucket_idx, found = self._find_bucket(key)

        if not found:
            return default

        _, _, value_type, value_data = self._read_bucket_data(bucket_idx)
        return self._deserialize(value_type, value_data)

    def delete(self, key: Any) -> bool:
        """
        Delete a key from the hashmap.

        Args:
            key: The key to delete

        Returns:
            True if the key was deleted, False if it didn't exist
        """
        bucket_idx, found = self._find_bucket(key)

        if not found:
            return False

        # Mark as deleted
        self._write_bucket_state(bucket_idx, DELETED)

        # Atomically decrement size counter
        self._atomic_decrement_size()

        return True

    def __contains__(self, key: Any) -> bool:
        """Check if a key exists in the hashmap."""
        _, found = self._find_bucket(key)
        return found

    def __getitem__(self, key: Any) -> Any:
        """Get a value using dict-like syntax."""
        value = self.get(key, None)
        if value is None and key not in self:
            raise KeyError(key)
        return value

    def __setitem__(self, key: Any, value: Any) -> None:
        """Set a value using dict-like syntax."""
        self.set(key, value)

    def __delitem__(self, key: Any) -> None:
        """Delete a key using dict-like syntax."""
        if not self.delete(key):
            raise KeyError(key)

    def size(self) -> int:
        """Return the number of key-value pairs in the hashmap."""
        _, size, _, _ = self._read_metadata()
        return size

    def _atomic_increment_size(self) -> None:
        """Atomically increment the size counter using pre-allocated view."""
        self._size_atomic.fetch_add(1)

    def _atomic_decrement_size(self) -> None:
        """Atomically decrement the size counter using pre-allocated view."""
        self._size_atomic.fetch_sub(1)

    def close(self) -> None:
        """Close the shared memory handle and cleanup atomic views."""
        # Cleanup size counter atomic view
        if hasattr(self, "_size_atomic_context"):
            try:
                self._size_atomic_context.__exit__(None, None, None)
            except Exception:
                pass  # Ignore cleanup errors

        # Cleanup bucket atomic views (lazy-loaded)
        if hasattr(self, "_atomic_contexts"):
            for context in self._atomic_contexts.values():
                try:
                    context.__exit__(None, None, None)
                except Exception:
                    pass  # Ignore cleanup errors

        self.shm.close()

    def unlink(self) -> None:
        """Unlink (delete) the shared memory block."""
        self.shm.unlink()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False
