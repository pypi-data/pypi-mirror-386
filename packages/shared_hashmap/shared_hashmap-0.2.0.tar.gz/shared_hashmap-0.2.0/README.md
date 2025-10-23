# SharedHashMap

A high-performance, thread-safe and process-safe hashmap implementation for Python multiprocessing using shared memory and atomic operations.

## Features

- **Process-safe**: Uses atomic operations from the `atomics` package for lock-free synchronization
- **Shared memory**: Built on Python's `multiprocessing.shared_memory` for efficient cross-process data sharing
- **Optimized serialization**: Avoids pickle overhead for common types (strings, bytes, integers, None)
- **Dict-like interface**: Familiar Python dictionary API
- **Open addressing**: Linear probing for collision resolution
- **Fully tested**: Comprehensive test suite including multiprocess stress tests

## Installation

```bash
# Install dependencies
pip install atomics

# Or install the entire project
pip install .
```

## Quick Start

```python
from shared_hashmap import SharedHashMap

# Create a shared hashmap
with SharedHashMap(name="my_hashmap", capacity=1024, create=True) as shm:
    # Set values
    shm["key1"] = "value1"
    shm["key2"] = 42

    # Get values
    print(shm["key1"])  # "value1"
    print(shm.get("key2"))  # 42

    # Check existence
    if "key1" in shm:
        print("key1 exists!")

    # Delete keys
    del shm["key1"]

    # Size
    print(f"Hashmap size: {shm.size()}")

    # Cleanup
    shm.unlink()  # Delete shared memory
```

## Multiprocess Usage

### Producer-Consumer Pattern

```python
import multiprocessing as mp
from shared_hashmap import SharedHashMap

def producer(hashmap_name, producer_id, num_items):
    # Attach to existing shared memory
    shm = SharedHashMap(name=hashmap_name, create=False)

    for i in range(num_items):
        shm[f"item_{producer_id}_{i}"] = f"data from producer {producer_id}"

    shm.close()

def consumer(hashmap_name, producer_id, num_items):
    shm = SharedHashMap(name=hashmap_name, create=False)

    for i in range(num_items):
        value = shm.get(f"item_{producer_id}_{i}")
        print(f"Consumed: {value}")

    shm.close()

# Main process
if __name__ == "__main__":
    hashmap_name = "producer_consumer_example"

    # Create the shared hashmap
    with SharedHashMap(name=hashmap_name, capacity=256, create=True) as shm:
        # Start producer and consumer processes
        p1 = mp.Process(target=producer, args=(hashmap_name, 0, 10))
        p2 = mp.Process(target=consumer, args=(hashmap_name, 0, 10))

        p1.start()
        p2.start()

        p1.join()
        p2.join()

        shm.unlink()
```

## API Reference

### Constructor

```python
SharedHashMap(
    name: str,
    capacity: int = 1024,
    max_key_size: int = 256,
    max_value_size: int = 1024,
    create: bool = True
)
```

**Parameters:**
- `name`: Unique name for the shared memory block
- `capacity`: Number of buckets in the hashmap
- `max_key_size`: Maximum size in bytes for serialized keys
- `max_value_size`: Maximum size in bytes for serialized values
- `create`: If True, create new shared memory; if False, attach to existing

### Methods

#### `set(key, value)`
Set a key-value pair in the hashmap.

#### `get(key, default=None)`
Get a value from the hashmap. Returns `default` if key not found.

#### `delete(key)`
Delete a key from the hashmap. Returns `True` if deleted, `False` if key didn't exist.

#### `size()`
Return the number of key-value pairs in the hashmap.

#### `close()`
Close the shared memory handle (keeps shared memory alive for other processes).

#### `unlink()`
Delete the shared memory block (should be called by the last process using it).

### Dict-like Operations

```python
shm["key"] = "value"  # Set
value = shm["key"]     # Get (raises KeyError if not found)
del shm["key"]         # Delete (raises KeyError if not found)
"key" in shm           # Check existence
```

## Serialization

SharedHashMap optimizes serialization for common types:

| Type | Serialization Method | Notes |
|------|---------------------|-------|
| `str` | UTF-8 encoding | No pickle overhead |
| `bytes` | Direct storage | No pickle overhead |
| `int` | ASCII encoding | No pickle overhead |
| `None` | Empty bytes | No pickle overhead |
| Other | `pickle.dumps()` | Fallback for complex types |

## Performance

SharedHashMap delivers exceptional performance for cross-process data sharing:

**Key Metrics:**
- **String reads**: ~2,600 ops/sec (382μs mean)
- **String writes**: ~1,200 ops/sec (826μs mean)
- **Integer operations**: ~6,000+ ops/sec
- **Mixed workloads**: ~1,170 ops/sec (854μs mean)
- **Concurrent writers**: Scales to multiple processes with minimal contention

**Run benchmarks:**
```bash
pytest tests/test_shared_hashmap_benchmarks.py --benchmark-only -v
```

## Performance Considerations

1. **Capacity**: Choose a capacity larger than your expected number of items to minimize collisions
2. **Max sizes**: Set `max_key_size` and `max_value_size` appropriately for your data
3. **Alignment**: Buckets are automatically aligned to 8-byte boundaries for optimal atomic operations
4. **Serialization**: Use strings, bytes, or integers when possible for best performance

## Thread Safety

SharedHashMap uses atomic compare-and-swap operations to ensure thread safety:
- Multiple processes can safely read and write concurrently
- No locks or mutexes required
- Lock-free design for high concurrency

## Limitations

1. **Fixed capacity**: The hashmap size is fixed at creation time
2. **No iteration**: Currently doesn't support iterating over keys/values
3. **No resizing**: Cannot dynamically grow the hashmap
4. **Size limits**: Keys and values must fit within configured max sizes

## Examples

See `examples/basic_usage.py` for complete examples including:
- Basic operations
- Producer-consumer pattern
- Distributed computation
- Stress testing

Run the examples:
```bash
python examples/basic_usage.py
```
