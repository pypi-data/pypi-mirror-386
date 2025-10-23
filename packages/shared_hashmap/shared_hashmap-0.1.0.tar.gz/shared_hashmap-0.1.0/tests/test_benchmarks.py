"""Tests for SharedHashMap."""

import multiprocessing as mp
import time

import pytest

from shared_hashmap import SharedHashMap


class TestBasicOperations:
    """Test basic hashmap operations in a single process."""

    def test_create_and_close(self):
        """Test creating and closing a hashmap."""
        shm = SharedHashMap(name="test_create", capacity=64, create=True)
        assert shm.size() == 0
        shm.close()
        shm.unlink()

    def test_set_and_get(self):
        """Test setting and getting values."""
        with SharedHashMap(name="test_set_get", capacity=64, create=True) as shm:
            shm.set("key1", "value1")
            assert shm.get("key1") == "value1"
            assert shm.size() == 1
            shm.unlink()

    def test_set_multiple(self):
        """Test setting multiple key-value pairs."""
        with SharedHashMap(name="test_set_multiple", capacity=64, create=True) as shm:
            for i in range(10):
                shm.set(f"key{i}", f"value{i}")

            assert shm.size() == 10

            for i in range(10):
                assert shm.get(f"key{i}") == f"value{i}"
            shm.unlink()

    def test_update_existing_key(self):
        """Test updating an existing key."""
        with SharedHashMap(name="test_update", capacity=64, create=True) as shm:
            shm.set("key1", "value1")
            assert shm.get("key1") == "value1"
            assert shm.size() == 1

            shm.set("key1", "value2")
            assert shm.get("key1") == "value2"
            assert shm.size() == 1  # Size shouldn't change
            shm.unlink()

    def test_delete(self):
        """Test deleting keys."""
        with SharedHashMap(name="test_delete", capacity=64, create=True) as shm:
            shm.set("key1", "value1")
            shm.set("key2", "value2")
            assert shm.size() == 2

            assert shm.delete("key1") is True
            assert shm.size() == 1
            assert shm.get("key1") is None

            assert shm.delete("key1") is False  # Already deleted
            assert shm.size() == 1
            shm.unlink()

    def test_contains(self):
        """Test the __contains__ method."""
        with SharedHashMap(name="test_contains", capacity=64, create=True) as shm:
            shm.set("key1", "value1")

            assert "key1" in shm
            assert "key2" not in shm

            shm.delete("key1")
            assert "key1" not in shm
            shm.unlink()

    def test_dict_like_interface(self):
        """Test dict-like interface."""
        with SharedHashMap(name="test_dict", capacity=64, create=True) as shm:
            # Test __setitem__
            shm["key1"] = "value1"
            assert shm.size() == 1

            # Test __getitem__
            assert shm["key1"] == "value1"

            # Test __delitem__
            del shm["key1"]
            assert shm.size() == 0

            # Test KeyError on missing key
            with pytest.raises(KeyError):
                _ = shm["nonexistent"]

            with pytest.raises(KeyError):
                del shm["nonexistent"]
            shm.unlink()

    def test_get_with_default(self):
        """Test get with default value."""
        with SharedHashMap(name="test_default", capacity=64, create=True) as shm:
            assert shm.get("nonexistent", "default") == "default"
            assert shm.get("nonexistent") is None
            shm.unlink()

    def test_various_types(self):
        """Test storing various data types."""
        with SharedHashMap(name="test_types", capacity=64, create=True) as shm:
            # String keys and values
            shm.set("string_key", "string_value")
            assert shm.get("string_key") == "string_value"

            # Integer keys and values
            shm.set(42, 100)
            assert shm.get(42) == 100

            # Tuple keys
            shm.set((1, 2, 3), "tuple_key")
            assert shm.get((1, 2, 3)) == "tuple_key"

            # List values
            shm.set("list", [1, 2, 3, 4, 5])
            assert shm.get("list") == [1, 2, 3, 4, 5]

            # Dict values
            shm.set("dict", {"nested": "value"})
            assert shm.get("dict") == {"nested": "value"}
            shm.unlink()

    def test_size_limits(self):
        """Test size limit enforcement."""
        with SharedHashMap(name="test_limits", capacity=64, max_key_size=10, max_value_size=10, create=True) as shm:
            # This should work
            shm.set("a", "b")

            # This should fail (key too large)
            with pytest.raises(ValueError):
                shm.set("x" * 100, "value")

            # This should fail (value too large)
            with pytest.raises(ValueError):
                shm.set("key", "y" * 100)
            shm.unlink()


class TestMultiprocessing:
    """Test multiprocessing safety."""

    def test_concurrent_writes(self):
        """Test concurrent writes from multiple processes."""

        def writer(name: str, process_id: int, num_writes: int):
            """Write process function."""
            shm = SharedHashMap(name=name, create=False)
            for i in range(num_writes):
                shm.set(f"proc{process_id}_key{i}", f"proc{process_id}_value{i}")
            shm.close()

        name = "test_concurrent_writes"
        num_processes = 4
        num_writes = 25

        # Create the hashmap in the main process
        with SharedHashMap(name=name, capacity=256, create=True) as shm:
            # Start writer processes
            processes = []
            for i in range(num_processes):
                p = mp.Process(target=writer, args=(name, i, num_writes))
                p.start()
                processes.append(p)

            # Wait for all processes to complete
            for p in processes:
                p.join()

            # Verify all writes succeeded
            total_expected = num_processes * num_writes
            actual_size = shm.size()

            # Check that we have approximately the right number of entries
            # (might be slightly less due to hash collisions in extreme cases)
            assert actual_size >= total_expected * 0.95, f"Expected ~{total_expected}, got {actual_size}"

            # Verify we can read all the values
            for proc_id in range(num_processes):
                for i in range(num_writes):
                    key = f"proc{proc_id}_key{i}"
                    expected_value = f"proc{proc_id}_value{i}"
                    actual_value = shm.get(key)
                    assert actual_value == expected_value, f"Key {key}: expected {expected_value}, got {actual_value}"
            shm.unlink()

    def test_concurrent_reads_and_writes(self):
        """Test concurrent reads and writes."""

        def reader_writer(name: str, process_id: int, iterations: int):
            """Process that both reads and writes."""
            shm = SharedHashMap(name=name, create=False)
            for i in range(iterations):
                # Write
                shm.set(f"proc{process_id}_key{i}", process_id * 1000 + i)

                # Read own writes
                value = shm.get(f"proc{process_id}_key{i}")
                assert value == process_id * 1000 + i

                # Read shared key
                shared_value = shm.get("shared_key")
                if shared_value is not None:
                    assert isinstance(shared_value, str)

            shm.close()

        name = "test_read_write"
        num_processes = 4
        iterations = 20

        with SharedHashMap(name=name, capacity=256, create=True) as shm:
            # Write a shared key
            shm.set("shared_key", "shared_value")

            # Start processes
            processes = []
            for i in range(num_processes):
                p = mp.Process(target=reader_writer, args=(name, i, iterations))
                p.start()
                processes.append(p)

            # Wait for completion
            for p in processes:
                p.join()

            # Verify the shared key is still intact
            assert shm.get("shared_key") == "shared_value"
            shm.unlink()

    def test_attach_to_existing(self):
        """Test attaching to existing shared memory from another process."""

        def writer(name: str):
            """Writer process."""
            shm = SharedHashMap(name=name, create=False)
            shm.set("from_child", "child_value")
            shm.close()

        def reader(name: str, result_queue: mp.Queue):
            """Reader process."""
            shm = SharedHashMap(name=name, create=False)
            value = shm.get("from_parent")
            result_queue.put(value)
            shm.close()

        name = "test_attach"

        with SharedHashMap(name=name, capacity=64, create=True) as shm:
            # Write from parent
            shm.set("from_parent", "parent_value")

            # Start writer process
            p_writer = mp.Process(target=writer, args=(name,))
            p_writer.start()
            p_writer.join()

            # Verify child's write
            assert shm.get("from_child") == "child_value"

            # Start reader process
            result_queue = mp.Queue()
            p_reader = mp.Process(target=reader, args=(name, result_queue))
            p_reader.start()
            p_reader.join()

            # Verify reader got the correct value
            assert result_queue.get() == "parent_value"
            shm.unlink()

    def test_stress_test(self):
        """Stress test with many concurrent operations."""

        def stress_worker(name: str, worker_id: int, operations: int):
            """Worker that performs random operations."""
            try:
                shm = SharedHashMap(name=name, create=False)
                for i in range(operations):
                    operation = i % 3
                    key = f"worker{worker_id}_key{i % 10}"  # Reuse keys to test updates

                    try:
                        if operation == 0:
                            # Write
                            shm.set(key, worker_id * 10000 + i)
                        elif operation == 1:
                            # Read
                            _ = shm.get(key)
                        else:
                            # Delete
                            shm.delete(key)
                    except Exception:
                        # Continue with other operations if one fails
                        pass
                shm.close()
            except Exception as e:
                # Exit with error code if we can't even connect
                import sys

                print(f"Worker {worker_id} failed to connect: {e}", file=sys.stderr)
                sys.exit(1)

        name = "test_stress"
        num_workers = 8
        operations_per_worker = 100

        with SharedHashMap(name=name, capacity=512, create=True) as shm:
            processes = []
            for i in range(num_workers):
                p = mp.Process(target=stress_worker, args=(name, i, operations_per_worker))
                p.start()
                processes.append(p)
                # Small delay to reduce connection race conditions
                time.sleep(0.01)

            for p in processes:
                p.join(timeout=30)  # 30 second timeout
                assert p.exitcode == 0, f"Process failed with exit code {p.exitcode}"

            # Just verify the hashmap is still functional
            shm.set("final_test", "success")
            assert shm.get("final_test") == "success"
            shm.unlink()


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_collision_handling(self):
        """Test that collisions are handled correctly."""
        # Use a small capacity to force collisions
        with SharedHashMap(name="test_collisions", capacity=8, create=True) as shm:
            # Insert more items than capacity to test probing
            for i in range(6):  # Don't fill completely to avoid full table
                shm.set(f"key{i}", f"value{i}")

            # Verify all items can be retrieved
            for i in range(6):
                assert shm.get(f"key{i}") == f"value{i}"
            shm.unlink()

    def test_none_value(self):
        """Test storing None as a value."""
        with SharedHashMap(name="test_none", capacity=64, create=True) as shm:
            shm.set("none_key", None)
            assert "none_key" in shm
            assert shm.get("none_key") is None

            # Test get with default when value is None
            # This is a known limitation - None values can't be distinguished from missing keys with get()
            shm.unlink()

    def test_empty_strings(self):
        """Test empty string keys and values."""
        with SharedHashMap(name="test_empty", capacity=64, create=True) as shm:
            shm.set("", "empty_key")
            assert shm.get("") == "empty_key"

            shm.set("empty_value", "")
            assert shm.get("empty_value") == ""
            shm.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
