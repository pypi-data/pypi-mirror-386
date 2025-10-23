"""
Benchmarks for SharedHashMap with realistic workloads.

Run with: pytest tests/test_shared_hashmap_benchmarks.py -v --benchmark-only
"""

import multiprocessing as mp
import random
import time

import pytest

from shared_hashmap import SharedHashMap


class TestSharedHashMapSingleProcess:
    """Benchmark single-process operations (baseline)."""

    @pytest.fixture
    def hashmap(self):
        """Create a fresh hashmap for each test."""
        shm = SharedHashMap(name="benchmark_single", capacity=10000, create=True)
        yield shm
        shm.close()
        shm.unlink()

    def test_write_strings_sequential(self, benchmark, hashmap):
        """Benchmark sequential string writes."""
        def write_strings():
            for i in range(1000):
                hashmap.set(f"key_{i}", f"value_{i}")

        benchmark(write_strings)

    def test_read_strings_sequential(self, benchmark, hashmap):
        """Benchmark sequential string reads."""
        # Pre-populate
        for i in range(1000):
            hashmap.set(f"key_{i}", f"value_{i}")

        def read_strings():
            for i in range(1000):
                _ = hashmap.get(f"key_{i}")

        benchmark(read_strings)

    def test_write_integers_sequential(self, benchmark, hashmap):
        """Benchmark sequential integer writes."""
        def write_integers():
            for i in range(1000):
                hashmap.set(i, i * 1000)

        benchmark(write_integers)

    def test_read_integers_sequential(self, benchmark, hashmap):
        """Benchmark sequential integer reads."""
        # Pre-populate
        for i in range(1000):
            hashmap.set(i, i * 1000)

        def read_integers():
            for i in range(1000):
                _ = hashmap.get(i)

        benchmark(read_integers)

    def test_mixed_read_write_80_20(self, benchmark, hashmap):
        """Benchmark mixed workload: 80% reads, 20% writes."""
        # Pre-populate with some data
        for i in range(500):
            hashmap.set(f"key_{i}", f"value_{i}")

        def mixed_workload():
            for i in range(1000):
                if random.random() < 0.8:
                    # Read (80%)
                    key = f"key_{random.randint(0, 499)}"
                    _ = hashmap.get(key)
                else:
                    # Write (20%)
                    hashmap.set(f"key_{i}", f"value_{i}")

        benchmark(mixed_workload)


class TestSharedHashMapConcurrency:
    """Benchmark cross-process concurrency (the main feature)."""

    def test_concurrent_writers_2_processes(self, benchmark):
        """Benchmark SharedHashMap with 2 processes writing concurrently."""
        shm_name = "benchmark_concurrent"

        def worker(worker_id: int, num_ops: int):
            """Worker process that writes to shared hashmap."""
            # Each worker connects to the existing shared hashmap
            worker_shm = SharedHashMap(name=shm_name, create=False)
            try:
                for i in range(num_ops):
                    # Use worker_id prefix to avoid key conflicts
                    key = f"worker_{worker_id}_key_{i}"
                    worker_shm.set(key, f"value_{i}")
            finally:
                worker_shm.close()

        def run_concurrent_writers():
            # Create shared hashmap
            main_shm = SharedHashMap(name=shm_name, capacity=5000, create=True)
            try:
                processes = []
                for i in range(2):
                    p = mp.Process(target=worker, args=(i, 500))
                    p.start()
                    processes.append(p)

                for p in processes:
                    p.join()

                # Verify all data was written
                assert main_shm.size() == 1000  # 2 workers * 500 ops each

            finally:
                main_shm.close()
                main_shm.unlink()

        benchmark(run_concurrent_writers)

    def test_concurrent_readers_writers(self, benchmark):
        """Benchmark SharedHashMap with mixed readers and writers."""
        shm_name = "benchmark_mixed_concurrent"

        def reader_worker(num_ops: int):
            """Worker that reads from shared hashmap."""
            reader_shm = SharedHashMap(name=shm_name, create=False)
            try:
                for i in range(num_ops):
                    # Read random pre-populated keys
                    key = f"initial_key_{random.randint(0, 99)}"
                    _ = reader_shm.get(key)
                    time.sleep(0.0001)  # Small delay to interleave with writers
            finally:
                reader_shm.close()

        def writer_worker(worker_id: int, num_ops: int):
            """Worker that writes to shared hashmap."""
            writer_shm = SharedHashMap(name=shm_name, create=False)
            try:
                for i in range(num_ops):
                    key = f"writer_{worker_id}_key_{i}"
                    writer_shm.set(key, f"value_{i}")
                    time.sleep(0.0002)  # Small delay to interleave with readers
            finally:
                writer_shm.close()

        def run_mixed_concurrent():
            # Create and pre-populate shared hashmap
            main_shm = SharedHashMap(name=shm_name, capacity=5000, create=True)
            try:
                # Pre-populate with data for readers
                for i in range(100):
                    main_shm.set(f"initial_key_{i}", f"initial_value_{i}")

                processes = []

                # Start reader processes
                for i in range(2):
                    p = mp.Process(target=reader_worker, args=(250,))
                    p.start()
                    processes.append(p)

                # Start writer processes
                for i in range(2):
                    p = mp.Process(target=writer_worker, args=(i, 250))
                    p.start()
                    processes.append(p)

                # Wait for all processes
                for p in processes:
                    p.join()

            finally:
                main_shm.close()
                main_shm.unlink()

        benchmark(run_mixed_concurrent)

    def test_high_contention_single_key(self, benchmark):
        """Benchmark high contention on a single key across processes."""
        shm_name = "benchmark_contention"

        def contention_worker(worker_id: int, num_ops: int):
            """Worker that updates the same key repeatedly."""
            worker_shm = SharedHashMap(name=shm_name, create=False)
            try:
                for i in range(num_ops):
                    # All workers update the same key - high contention!
                    worker_shm.set("contested_key", f"worker_{worker_id}_update_{i}")
            finally:
                worker_shm.close()

        def run_high_contention():
            main_shm = SharedHashMap(name=shm_name, capacity=1000, create=True)
            try:
                # Initialize the contested key
                main_shm.set("contested_key", "initial_value")

                processes = []
                for i in range(4):  # 4 processes fighting over 1 key
                    p = mp.Process(target=contention_worker, args=(i, 100))
                    p.start()
                    processes.append(p)

                for p in processes:
                    p.join()

                # Verify the key still exists and has some final value
                final_value = main_shm.get("contested_key")
                assert final_value is not None
                assert "worker_" in final_value

            finally:
                main_shm.close()
                main_shm.unlink()

        benchmark(run_high_contention)


class TestSharedHashMapStressTests:
    """Stress tests to verify stability under load."""

    def test_large_dataset_performance(self, benchmark):
        """Benchmark performance with large datasets."""
        shm_name = "benchmark_large"

        def large_dataset_test():
            shm = SharedHashMap(name=shm_name, capacity=50000, create=True)
            try:
                # Write 10,000 items
                for i in range(10000):
                    shm.set(f"large_key_{i}", f"large_value_{i}_with_some_extra_data_to_make_it_realistic")

                # Read all items back
                for i in range(10000):
                    value = shm.get(f"large_key_{i}")
                    assert value is not None

                # Mixed workload on large dataset
                for i in range(5000):
                    if random.random() < 0.7:
                        # Read
                        key = f"large_key_{random.randint(0, 9999)}"
                        _ = shm.get(key)
                    else:
                        # Update
                        key = f"large_key_{random.randint(0, 9999)}"
                        shm.set(key, f"updated_value_{i}")

            finally:
                shm.close()
                shm.unlink()

        benchmark(large_dataset_test)

    def test_memory_churn_with_deletions(self, benchmark):
        """Test memory management with lots of insertions and deletions."""
        shm_name = "benchmark_churn"

        def memory_churn_test():
            shm = SharedHashMap(name=shm_name, capacity=5000, create=True)
            try:
                # Cycles of insert and delete to test memory reclamation
                for cycle in range(10):
                    # Insert 500 items
                    for i in range(500):
                        key = f"cycle_{cycle}_key_{i}"
                        shm.set(key, f"value_{i}")

                    # Delete half of them
                    for i in range(0, 500, 2):
                        key = f"cycle_{cycle}_key_{i}"
                        shm.delete(key)

                    # Verify correct state
                    assert shm.size() == (cycle + 1) * 250  # 250 items per cycle remain

            finally:
                shm.close()
                shm.unlink()

        benchmark(memory_churn_test)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--benchmark-only", "--benchmark-sort=mean"])