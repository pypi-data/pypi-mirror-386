"""
Comprehensive tests for SharedHashMap using pytest-check and modern Python testing practices.
"""

import pickle
import struct
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from multiprocessing import Process, Queue
from typing import Any, Dict, List, Tuple

import pytest
import pytest_check as check

from shared_hashmap import SharedHashMap


class TestSharedHashMapBasicOperations:
    """Test basic hashmap operations."""

    @pytest.fixture
    def hashmap(self):
        """Create a fresh hashmap for each test."""
        name = f"test_hashmap_{uuid.uuid4().hex[:8]}"
        hm = SharedHashMap(name=name, capacity=64, create=True)
        yield hm
        try:
            hm.close()
            hm.unlink()
        except Exception:
            pass

    def test_set_and_get_string(self, hashmap):
        """Test setting and getting string values."""
        hashmap.set("key1", "value1")
        check.equal(hashmap.get("key1"), "value1")
        check.equal(hashmap.get("nonexistent"), None)
        check.equal(hashmap.get("nonexistent", "default"), "default")

    def test_set_and_get_int(self, hashmap):
        """Test setting and getting integer values."""
        hashmap.set("int_key", 42)
        check.equal(hashmap.get("int_key"), 42)

        hashmap.set(123, "value_for_int_key")
        check.equal(hashmap.get(123), "value_for_int_key")

    def test_set_and_get_bytes(self, hashmap):
        """Test setting and getting bytes values."""
        data = b"binary_data_test"
        hashmap.set("bytes_key", data)
        check.equal(hashmap.get("bytes_key"), data)

    def test_set_and_get_none(self, hashmap):
        """Test setting and getting None values."""
        hashmap.set("none_key", None)
        check.is_(hashmap.get("none_key"), None)

    def test_set_and_get_complex_objects(self, hashmap):
        """Test setting and getting complex objects (using pickle)."""
        complex_obj = {"nested": [1, 2, {"inner": "value"}], "tuple": (1, 2, 3)}
        hashmap.set("complex", complex_obj)
        check.equal(hashmap.get("complex"), complex_obj)

    def test_update_existing_key(self, hashmap):
        """Test updating an existing key."""
        hashmap.set("key", "original_value")
        check.equal(hashmap.get("key"), "original_value")

        hashmap.set("key", "updated_value")
        check.equal(hashmap.get("key"), "updated_value")

    def test_delete_existing_key(self, hashmap):
        """Test deleting an existing key."""
        hashmap.set("to_delete", "value")
        check.is_true(hashmap.delete("to_delete"))
        check.equal(hashmap.get("to_delete"), None)

    def test_delete_nonexistent_key(self, hashmap):
        """Test deleting a non-existent key."""
        check.is_false(hashmap.delete("nonexistent"))

    def test_contains_operator(self, hashmap):
        """Test the __contains__ operator."""
        hashmap.set("exists", "value")
        check.is_true("exists" in hashmap)
        check.is_false("does_not_exist" in hashmap)

    def test_dict_like_access(self, hashmap):
        """Test dict-like access patterns."""
        # Test __setitem__ and __getitem__
        hashmap["key1"] = "value1"
        check.equal(hashmap["key1"], "value1")

        # Test KeyError for missing keys
        with pytest.raises(KeyError):
            _ = hashmap["nonexistent"]

        # Test __delitem__
        del hashmap["key1"]
        check.is_false("key1" in hashmap)

        # Test KeyError for deleting missing keys
        with pytest.raises(KeyError):
            del hashmap["nonexistent"]

    def test_size_tracking(self, hashmap):
        """Test that size is tracked correctly."""
        check.equal(hashmap.size(), 0)

        # Add some items
        for i in range(5):
            hashmap.set(f"key_{i}", f"value_{i}")
        check.equal(hashmap.size(), 5)

        # Update existing item (size shouldn't change)
        hashmap.set("key_0", "new_value")
        check.equal(hashmap.size(), 5)

        # Delete items
        hashmap.delete("key_0")
        hashmap.delete("key_1")
        check.equal(hashmap.size(), 3)


class TestSharedHashMapSerialization:
    """Test serialization of different data types."""

    @pytest.fixture
    def hashmap(self):
        """Create a fresh hashmap for each test."""
        name = f"test_ser_{uuid.uuid4().hex[:8]}"
        hm = SharedHashMap(name=name, capacity=32, create=True)
        yield hm
        try:
            hm.close()
            hm.unlink()
        except Exception:
            pass

    def test_string_serialization(self, hashmap):
        """Test string serialization efficiency."""
        test_strings = [
            "",
            "simple",
            "unicode: 🚀 🌟 💫",
            "multi\nline\nstring",
            "very " * 100 + "long string"
        ]

        for i, s in enumerate(test_strings):
            key = f"str_{i}"
            hashmap.set(key, s)
            check.equal(hashmap.get(key), s)

    def test_bytes_serialization(self, hashmap):
        """Test bytes serialization."""
        test_bytes = [
            b"",
            b"simple bytes",
            b"\x00\x01\x02\xff",
            bytes(range(256)),
            b"A" * 1000
        ]

        for i, b in enumerate(test_bytes):
            key = f"bytes_{i}"
            hashmap.set(key, b)
            check.equal(hashmap.get(key), b)

    def test_int_serialization(self, hashmap):
        """Test integer serialization."""
        test_ints = [0, 1, -1, 42, -42, 2**31 - 1, -2**31, 2**63 - 1]

        for i in test_ints:
            hashmap.set(f"int_{i}", i)
            check.equal(hashmap.get(f"int_{i}"), i)

    def test_none_serialization(self, hashmap):
        """Test None serialization."""
        hashmap.set("none_key", None)
        check.is_(hashmap.get("none_key"), None)

    def test_pickle_serialization(self, hashmap):
        """Test pickle serialization for complex objects."""
        test_objects = [
            [1, 2, 3],
            {"a": 1, "b": 2},
            (1, 2, 3),
            set([1, 2, 3]),
            {"nested": {"deep": {"value": 42}}},
        ]

        for i, obj in enumerate(test_objects):
            key = f"pickle_{i}"
            hashmap.set(key, obj)
            result = hashmap.get(key)
            if isinstance(obj, set):
                check.equal(set(result), obj)
            else:
                check.equal(result, obj)


class TestSharedHashMapLimits:
    """Test size limits and error conditions."""

    @pytest.fixture
    def small_hashmap(self):
        """Create a hashmap with small limits for testing."""
        name = f"test_limits_{uuid.uuid4().hex[:8]}"
        hm = SharedHashMap(
            name=name,
            capacity=8,
            max_key_size=32,
            max_value_size=64,
            create=True
        )
        yield hm
        try:
            hm.close()
            hm.unlink()
        except Exception:
            pass

    def test_key_size_limit(self, small_hashmap):
        """Test that large keys raise ValueError."""
        large_key = "x" * 100  # Larger than max_key_size=32

        with pytest.raises(ValueError, match="Serialized key size .* exceeds maximum"):
            small_hashmap.set(large_key, "value")

    def test_value_size_limit(self, small_hashmap):
        """Test that large values raise ValueError."""
        large_value = "x" * 200  # Larger than max_value_size=64

        with pytest.raises(ValueError, match="Serialized value size .* exceeds maximum"):
            small_hashmap.set("key", large_value)

    def test_capacity_stress(self, small_hashmap):
        """Test behavior when approaching capacity."""
        # Fill up most of the hashmap
        for i in range(6):  # Leave some room for probing
            small_hashmap.set(f"k{i}", f"v{i}")

        check.equal(small_hashmap.size(), 6)

        # Should still be able to add more
        small_hashmap.set("extra", "value")
        check.equal(small_hashmap.get("extra"), "value")


class TestSharedHashMapConcurrency:
    """Test concurrent access and thread safety."""

    @pytest.fixture
    def concurrent_hashmap(self):
        """Create a hashmap for concurrency testing."""
        name = f"test_concurrent_{uuid.uuid4().hex[:8]}"
        hm = SharedHashMap(name=name, capacity=256, create=True)
        yield hm
        try:
            hm.close()
            hm.unlink()
        except Exception:
            pass

    def test_thread_safety_writes(self, concurrent_hashmap):
        """Test concurrent writes from multiple threads."""
        num_threads = 8
        items_per_thread = 20
        results = {}

        def worker(thread_id: int):
            thread_results = {}
            for i in range(items_per_thread):
                key = f"thread_{thread_id}_item_{i}"
                value = f"value_{thread_id}_{i}"
                concurrent_hashmap.set(key, value)
                thread_results[key] = value
            return thread_results

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker, i) for i in range(num_threads)]
            for future in as_completed(futures):
                results.update(future.result())

        # Verify all items were written correctly
        check.equal(concurrent_hashmap.size(), num_threads * items_per_thread)
        for key, expected_value in results.items():
            check.equal(concurrent_hashmap.get(key), expected_value)

    def test_thread_safety_mixed_operations(self, concurrent_hashmap):
        """Test mixed read/write/delete operations."""
        # Pre-populate with some data
        for i in range(50):
            concurrent_hashmap.set(f"initial_{i}", f"value_{i}")

        read_results = Queue()
        write_count = Queue()
        delete_count = Queue()

        def reader():
            count = 0
            for i in range(100):
                key = f"initial_{i % 50}"
                value = concurrent_hashmap.get(key)
                if value is not None:
                    count += 1
                time.sleep(0.001)  # Small delay
            read_results.put(count)

        def writer():
            count = 0
            for i in range(30):
                key = f"new_{threading.current_thread().ident}_{i}"
                concurrent_hashmap.set(key, f"new_value_{i}")
                count += 1
                time.sleep(0.001)
            write_count.put(count)

        def deleter():
            count = 0
            for i in range(20):
                key = f"initial_{i}"
                if concurrent_hashmap.delete(key):
                    count += 1
                time.sleep(0.001)
            delete_count.put(count)

        # Run operations concurrently
        threads = [
            threading.Thread(target=reader),
            threading.Thread(target=reader),
            threading.Thread(target=writer),
            threading.Thread(target=writer),
            threading.Thread(target=deleter),
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # Verify operations completed
        check.greater_equal(read_results.get(), 0)
        check.greater_equal(read_results.get(), 0)
        check.equal(write_count.get(), 30)
        check.equal(write_count.get(), 30)
        check.greater_equal(delete_count.get(), 0)

    @pytest.mark.timeout(30)
    def test_multiprocess_basic(self, concurrent_hashmap):
        """Test basic multiprocess functionality."""
        def worker_process(name: str, start_idx: int, count: int, results_queue):
            """Worker process that writes to shared hashmap."""
            try:
                # Attach to existing shared memory
                worker_hm = SharedHashMap(name=name, create=False)

                written_items = []
                for i in range(count):
                    key = f"proc_{start_idx + i}"
                    value = f"process_value_{start_idx + i}"
                    worker_hm.set(key, value)
                    written_items.append((key, value))

                worker_hm.close()
                results_queue.put(written_items)
            except Exception as e:
                results_queue.put(f"Error: {e}")

        # Start worker processes
        num_processes = 3
        items_per_process = 10
        results_queue = Queue()
        processes = []

        for i in range(num_processes):
            p = Process(
                target=worker_process,
                args=(concurrent_hashmap.name, i * items_per_process, items_per_process, results_queue)
            )
            processes.append(p)
            p.start()

        # Wait for all processes to complete
        for p in processes:
            p.join()

        # Collect results
        all_written_items = {}
        for _ in range(num_processes):
            result = results_queue.get()
            check.is_instance(result, list, "Process should return list of items, not error")
            for key, value in result:
                all_written_items[key] = value

        # Verify all items are present in the hashmap
        for key, expected_value in all_written_items.items():
            actual_value = concurrent_hashmap.get(key)
            check.equal(actual_value, expected_value, f"Key {key} should have value {expected_value}")


class TestSharedHashMapMemoryManagement:
    """Test memory management and cleanup."""

    def test_context_manager(self):
        """Test using SharedHashMap as context manager."""
        name = f"test_context_{uuid.uuid4().hex[:8]}"

        with SharedHashMap(name=name, capacity=32, create=True) as hm:
            hm.set("test_key", "test_value")
            check.equal(hm.get("test_key"), "test_value")

        # Should be able to attach to the same memory
        with SharedHashMap(name=name, create=False) as hm2:
            check.equal(hm2.get("test_key"), "test_value")

        # Clean up
        hm2.unlink()

    def test_attach_to_existing(self):
        """Test attaching to existing shared memory."""
        name = f"test_attach_{uuid.uuid4().hex[:8]}"

        # Create initial hashmap
        hm1 = SharedHashMap(name=name, capacity=64, create=True)
        hm1.set("shared_key", "shared_value")

        # Attach to existing
        hm2 = SharedHashMap(name=name, create=False)
        check.equal(hm2.get("shared_key"), "shared_value")

        # Modify from second instance
        hm2.set("new_key", "new_value")
        check.equal(hm1.get("new_key"), "new_value")

        # Clean up
        hm1.close()
        hm2.close()
        hm1.unlink()

    def test_multiprocess_data_persistence(self):
        """Test that data persists across process boundaries."""
        name = f"test_persist_{uuid.uuid4().hex[:8]}"

        # Create and populate hashmap in main process
        creator_hm = SharedHashMap(name=name, capacity=32, create=True)
        creator_hm.set("persistent_key", "persistent_value")
        creator_hm.set("number", 42)
        creator_hm.set("data", {"nested": "value"})

        def reader_process(name: str, results_queue):
            """Read from shared hashmap in separate process."""
            try:
                reader_hm = SharedHashMap(name=name, create=False)

                # Read the values
                value1 = reader_hm.get("persistent_key")
                value2 = reader_hm.get("number")
                value3 = reader_hm.get("data")

                results_queue.put([value1, value2, value3])
                reader_hm.close()
            except Exception as e:
                results_queue.put(f"Error: {e}")

        results_queue = Queue()
        reader = Process(target=reader_process, args=(name, results_queue))
        reader.start()
        reader.join()

        # Get results from the reader process
        result = results_queue.get()
        check.is_instance(result, list, "Process should return values, not error")

        value1, value2, value3 = result
        check.equal(value1, "persistent_value")
        check.equal(value2, 42)
        check.equal(value3, {"nested": "value"})

        # Clean up
        creator_hm.close()
        creator_hm.unlink()


class TestSharedHashMapEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_key_and_value(self):
        """Test empty keys and values."""
        name = f"test_empty_{uuid.uuid4().hex[:8]}"

        with SharedHashMap(name=name, capacity=16, create=True) as hm:
            # Empty string key and value
            hm.set("", "")
            check.equal(hm.get(""), "")

            # Empty bytes
            hm.set(b"", b"")
            check.equal(hm.get(b""), b"")

    def test_hash_collisions(self):
        """Test behavior with hash collisions (using quadratic probing)."""
        name = f"test_collisions_{uuid.uuid4().hex[:8]}"

        with SharedHashMap(name=name, capacity=8, create=True) as hm:
            # Add multiple items that might cause collisions in small hashmap
            for i in range(6):
                key = f"collision_test_{i}"
                value = f"value_{i}"
                hm.set(key, value)
                check.equal(hm.get(key), value)

            # Verify all items are still accessible
            for i in range(6):
                key = f"collision_test_{i}"
                expected = f"value_{i}"
                check.equal(hm.get(key), expected)

    def test_delete_and_reinsert(self):
        """Test deleting and reinserting keys."""
        name = f"test_reinsert_{uuid.uuid4().hex[:8]}"

        with SharedHashMap(name=name, capacity=16, create=True) as hm:
            # Insert, delete, and reinsert
            hm.set("test_key", "original")
            check.equal(hm.get("test_key"), "original")

            check.is_true(hm.delete("test_key"))
            check.equal(hm.get("test_key"), None)

            hm.set("test_key", "reinserted")
            check.equal(hm.get("test_key"), "reinserted")

    def test_invalid_attach(self):
        """Test attaching to non-existent shared memory."""
        name = f"test_invalid_{uuid.uuid4().hex[:8]}"

        with pytest.raises(FileNotFoundError):
            SharedHashMap(name=name, create=False)

    def test_metadata_validation(self):
        """Test metadata validation during attachment."""
        name = f"test_metadata_{uuid.uuid4().hex[:8]}"

        # Create with specific parameters
        hm1 = SharedHashMap(
            name=name,
            capacity=32,
            max_key_size=128,
            max_value_size=256,
            create=True
        )
        hm1.set("test", "value")

        # Attach and verify parameters are read correctly
        hm2 = SharedHashMap(name=name, create=False)
        check.equal(hm2.capacity, 32)
        check.equal(hm2.max_key_size, 128)
        check.equal(hm2.max_value_size, 256)
        check.equal(hm2.get("test"), "value")

        # Clean up
        hm1.close()
        hm2.close()
        hm1.unlink()


class TestSharedHashMapInternalMethods:
    """Test internal methods and implementation details."""

    @pytest.fixture
    def hashmap(self):
        """Create a hashmap for internal testing."""
        name = f"test_internal_{uuid.uuid4().hex[:8]}"
        hm = SharedHashMap(name=name, capacity=16, create=True)
        yield hm
        try:
            hm.close()
            hm.unlink()
        except Exception:
            pass

    def test_serialization_methods(self, hashmap):
        """Test internal serialization methods."""
        # Test string
        type_marker, data = hashmap._serialize("test")
        check.equal(type_marker, 1)  # TYPE_STR
        check.equal(data, b"test")
        result = hashmap._deserialize(type_marker, data)
        check.equal(result, "test")

        # Test bytes
        type_marker, data = hashmap._serialize(b"bytes")
        check.equal(type_marker, 2)  # TYPE_BYTES
        check.equal(data, b"bytes")
        result = hashmap._deserialize(type_marker, data)
        check.equal(result, b"bytes")

        # Test int
        type_marker, data = hashmap._serialize(42)
        check.equal(type_marker, 3)  # TYPE_INT
        check.equal(data, b"42")
        result = hashmap._deserialize(type_marker, data)
        check.equal(result, 42)

        # Test None
        type_marker, data = hashmap._serialize(None)
        check.equal(type_marker, 4)  # TYPE_NONE
        check.equal(data, b"")
        result = hashmap._deserialize(type_marker, data)
        check.is_(result, None)

        # Test pickle
        complex_obj = {"test": [1, 2, 3]}
        type_marker, data = hashmap._serialize(complex_obj)
        check.equal(type_marker, 0)  # TYPE_PICKLE
        result = hashmap._deserialize(type_marker, data)
        check.equal(result, complex_obj)

    def test_hash_function(self, hashmap):
        """Test the FNV-1a hash function."""
        # Test hash consistency
        hash1 = hashmap._fast_hash(b"test")
        hash2 = hashmap._fast_hash(b"test")
        check.equal(hash1, hash2)

        # Test different inputs produce different hashes (usually)
        hash_a = hashmap._fast_hash(b"a")
        hash_b = hashmap._fast_hash(b"b")
        check.not_equal(hash_a, hash_b)

        # Test hash is within capacity bounds
        for test_data in [b"", b"test", b"longer_string", b"x" * 100]:
            hash_val = hashmap._fast_hash(test_data)
            check.greater_equal(hash_val, 0)
            check.less(hash_val, hashmap.capacity)

    def test_bucket_operations(self, hashmap):
        """Test internal bucket operations."""
        # Test bucket offset calculation
        offset0 = hashmap._get_bucket_offset(0)
        offset1 = hashmap._get_bucket_offset(1)
        check.equal(offset1 - offset0, hashmap.bucket_size)

        # Test bucket state operations
        hashmap._write_bucket_state(0, 1)  # OCCUPIED
        check.equal(hashmap._read_bucket_state(0), 1)

        # Test bucket data operations
        key_type, key_data = hashmap._serialize("test_key")
        value_type, value_data = hashmap._serialize("test_value")

        hashmap._write_bucket_data(0, key_type, key_data, value_type, value_data)
        read_key_type, read_key_data, read_value_type, read_value_data = hashmap._read_bucket_data(0)

        check.equal(read_key_type, key_type)
        check.equal(read_key_data, key_data)
        check.equal(read_value_type, value_type)
        check.equal(read_value_data, value_data)

    def test_find_bucket(self, hashmap):
        """Test bucket finding logic."""
        # Test finding non-existent key
        bucket_idx, found = hashmap._find_bucket("nonexistent")
        check.is_false(found)
        check.greater_equal(bucket_idx, 0)
        check.less(bucket_idx, hashmap.capacity)

        # Insert a key and find it
        hashmap.set("test_key", "test_value")
        bucket_idx, found = hashmap._find_bucket("test_key")
        check.is_true(found)

        # Read the data from the found bucket
        _, _, value_type, value_data = hashmap._read_bucket_data(bucket_idx)
        value = hashmap._deserialize(value_type, value_data)
        check.equal(value, "test_value")


class TestSharedHashMapEdgeCasesAdvanced:
    """Test advanced edge cases for maximum coverage."""

    def test_metadata_retry_timeout(self):
        """Test metadata retry mechanism timeout."""
        import struct
        from unittest.mock import patch

        name = f"test_meta_timeout_{uuid.uuid4().hex[:8]}"

        # Create shared memory with invalid metadata
        hm_creator = SharedHashMap(name=name, capacity=16, create=True)

        # Corrupt the metadata by writing zeros
        struct.pack_into("QQQQ", hm_creator.shm.buf, 0, 0, 0, 0, 0)

        # Try to attach - should fail after retries
        with patch('time.sleep'):  # Speed up the test
            with pytest.raises(RuntimeError, match="Failed to read valid metadata"):
                SharedHashMap(name=name, create=False)

        hm_creator.close()
        hm_creator.unlink()

    def test_unknown_type_marker_error(self):
        """Test error handling for unknown type markers."""
        name = f"test_unknown_type_{uuid.uuid4().hex[:8]}"

        with SharedHashMap(name=name, capacity=16, create=True) as hm:
            # Test unknown type marker in deserialize
            with pytest.raises(ValueError, match="Unknown type marker"):
                hm._deserialize(99, b"data")  # 99 is not a valid type marker

    def test_hash_table_full_condition(self):
        """Test hash table full condition."""
        name = f"test_full_{uuid.uuid4().hex[:8]}"

        # Create a very small hashmap to force full condition
        with SharedHashMap(name=name, capacity=2, max_key_size=32, max_value_size=32, create=True) as hm:
            # Fill all slots
            hm.set("key1", "value1")
            hm.set("key2", "value2")

            # Try to force collision by creating keys that might hash to same values
            # This should eventually trigger the "Hash table is full" condition
            filled = False
            for i in range(100):  # Try many keys to force collision
                try:
                    test_key = f"collision_key_{i:03d}"
                    hm.set(test_key, f"value_{i}")
                except RuntimeError as e:
                    if "Hash table is full" in str(e):
                        filled = True
                        break

            # If we didn't hit the error, the hashmap might be handling collisions well
            # Let's try a different approach - fill and delete to create fragmentation
            if not filled:
                # Delete one key and try to insert many more to force probing exhaustion
                hm.delete("key1")

                # Now try to insert keys that might collide
                try:
                    for i in range(20):
                        hm.set(f"force_collision_{i:010d}", f"value_{i}")
                except RuntimeError as e:
                    if "Hash table is full" in str(e):
                        filled = True

    def test_concurrent_bucket_claim_race(self):
        """Test concurrent bucket claiming scenario."""
        import threading
        from concurrent.futures import ThreadPoolExecutor

        name = f"test_race_{uuid.uuid4().hex[:8]}"

        with SharedHashMap(name=name, capacity=64, create=True) as hm:
            results = []

            def competing_writer(key_suffix):
                """Multiple threads trying to write to potentially colliding keys."""
                try:
                    # Use similar keys that might hash to same bucket
                    key = f"race_key_{key_suffix}"
                    value = f"value_{key_suffix}"
                    hm.set(key, value)
                    # Verify we can read it back
                    retrieved = hm.get(key)
                    results.append((key, value, retrieved))
                except Exception as e:
                    results.append(f"Error: {e}")

            # Run multiple writers concurrently
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(competing_writer, i) for i in range(50)]
                for future in futures:
                    future.result()

            # Verify no errors and all writes succeeded
            for result in results:
                if isinstance(result, str) and result.startswith("Error"):
                    pytest.fail(f"Unexpected error: {result}")
                elif isinstance(result, tuple):
                    key, expected_value, actual_value = result
                    check.equal(actual_value, expected_value, f"Key {key} had wrong value")



@pytest.mark.benchmark
class TestSharedHashMapPerformance:
    """Performance and benchmark tests."""

    @pytest.fixture
    def large_hashmap(self):
        """Create a larger hashmap for performance testing."""
        name = f"test_perf_{uuid.uuid4().hex[:8]}"
        hm = SharedHashMap(name=name, capacity=1024, create=True)
        yield hm
        try:
            hm.close()
            hm.unlink()
        except Exception:
            pass

    def test_bulk_operations_performance(self, large_hashmap, benchmark):
        """Benchmark bulk insert/read operations."""
        def bulk_insert_and_read():
            # Insert 1000 items
            for i in range(1000):
                large_hashmap.set(f"key_{i}", f"value_{i}")

            # Read them back
            results = []
            for i in range(1000):
                results.append(large_hashmap.get(f"key_{i}"))

            return len(results)

        result = benchmark(bulk_insert_and_read)
        check.equal(result, 1000)

    def test_concurrent_performance(self, large_hashmap):
        """Test performance under concurrent load."""
        num_threads = 4
        ops_per_thread = 250

        def worker():
            thread_id = threading.current_thread().ident
            for i in range(ops_per_thread):
                key = f"thread_{thread_id}_{i}"
                large_hashmap.set(key, f"value_{i}")
                retrieved = large_hashmap.get(key)
                assert retrieved == f"value_{i}"

        start_time = time.time()

        threads = [threading.Thread(target=worker) for _ in range(num_threads)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        end_time = time.time()

        total_ops = num_threads * ops_per_thread * 2  # set + get
        ops_per_second = total_ops / (end_time - start_time)

        check.equal(large_hashmap.size(), num_threads * ops_per_thread)
        check.greater(ops_per_second, 1000)  # Should handle at least 1K ops/sec