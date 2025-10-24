"""
Pytest-benchmark tests for allocators.

Run with: pytest tests/test_benchmarks.py --benchmark-only
Compare: pytest tests/test_benchmarks.py --benchmark-only --benchmark-compare
"""

import pytest
import time
from shared_allocator import BumpAllocator, FreeListAllocator, SlabAllocator


# Fixtures for each allocator type
@pytest.fixture
def bump_allocator():
    """Create a bump allocator for testing."""
    name = f"test_bump_{time.time()}"
    allocator = BumpAllocator(name=name, capacity=10 * 1024 * 1024, create=True)
    yield allocator
    allocator.close()
    try:
        allocator.unlink()
    except:
        pass


@pytest.fixture
def freelist_allocator():
    """Create a freelist allocator for testing."""
    name = f"test_freelist_{time.time()}"
    allocator = FreeListAllocator(name=name, capacity=10 * 1024 * 1024, create=True)
    yield allocator
    allocator.close()
    try:
        allocator.unlink()
    except:
        pass


@pytest.fixture
def slab_allocator():
    """Create a slab allocator for testing."""
    name = f"test_slab_{time.time()}"
    allocator = SlabAllocator(name=name, slab_size=256, num_slabs=40960, create=True)
    yield allocator
    allocator.close()
    try:
        allocator.unlink()
    except:
        pass


# Benchmark: Sequential Allocation
def test_bump_sequential_allocation(benchmark, bump_allocator):
    """Benchmark sequential allocation on bump allocator."""
    def allocate():
        offset = bump_allocator.allocate(256)
        return offset

    result = benchmark(allocate)
    assert result is not None or bump_allocator.available_bytes() == 0


def test_freelist_sequential_allocation(benchmark, freelist_allocator):
    """Benchmark sequential allocation on freelist allocator."""
    # Maintain steady state to avoid running out of memory
    allocated = []

    def allocate():
        offset = freelist_allocator.allocate(256)
        if offset is not None:
            allocated.append(offset)
            # Free oldest allocation to maintain steady state
            if len(allocated) > 100:
                freelist_allocator.free(allocated.pop(0))
        return offset

    result = benchmark(allocate)

    # Cleanup
    for offset in allocated:
        freelist_allocator.free(offset)


def test_slab_sequential_allocation(benchmark, slab_allocator):
    """Benchmark sequential allocation on slab allocator."""
    # Pre-allocate to warm up, then free to avoid running out of memory
    allocated = []

    def allocate():
        offset = slab_allocator.allocate()
        if offset is not None:
            allocated.append(offset)
            # Free oldest allocation to maintain steady state
            if len(allocated) > 100:
                slab_allocator.free(allocated.pop(0))
        return offset

    result = benchmark(allocate)

    # Cleanup
    for offset in allocated:
        slab_allocator.free(offset)


# Benchmark: Write Operations
def test_bump_write(benchmark, bump_allocator):
    """Benchmark write operations on bump allocator."""
    offset = bump_allocator.allocate(256)
    data = b"x" * 128

    def write():
        bump_allocator.write(offset, data)

    benchmark(write)


def test_freelist_write(benchmark, freelist_allocator):
    """Benchmark write operations on freelist allocator."""
    offset = freelist_allocator.allocate(256)
    data = b"x" * 128

    def write():
        freelist_allocator.write(offset, data)

    benchmark(write)


def test_slab_write(benchmark, slab_allocator):
    """Benchmark write operations on slab allocator."""
    offset = slab_allocator.allocate()
    data = b"x" * 128

    def write():
        slab_allocator.write(offset, data)

    benchmark(write)


# Benchmark: Read Operations
def test_bump_read(benchmark, bump_allocator):
    """Benchmark read operations on bump allocator."""
    offset = bump_allocator.allocate(256)
    data = b"x" * 128
    bump_allocator.write(offset, data)

    def read():
        return bump_allocator.read(offset, 128)

    result = benchmark(read)
    assert result == data


def test_freelist_read(benchmark, freelist_allocator):
    """Benchmark read operations on freelist allocator."""
    offset = freelist_allocator.allocate(256)
    data = b"x" * 128
    freelist_allocator.write(offset, data)

    def read():
        return freelist_allocator.read(offset, 128)

    result = benchmark(read)
    assert result == data


def test_slab_read(benchmark, slab_allocator):
    """Benchmark read operations on slab allocator."""
    offset = slab_allocator.allocate()
    data = b"x" * 128
    slab_allocator.write(offset, data)

    def read():
        return slab_allocator.read(offset, 128)

    result = benchmark(read)
    assert result == data


# Benchmark: Alloc + Free (for allocators that support it)
def test_freelist_alloc_free(benchmark, freelist_allocator):
    """Benchmark allocation and immediate free on freelist allocator."""
    def alloc_free():
        offset = freelist_allocator.allocate(256)
        if offset is not None:
            freelist_allocator.free(offset)
        return offset

    benchmark(alloc_free)


def test_slab_alloc_free(benchmark, slab_allocator):
    """Benchmark allocation and immediate free on slab allocator."""
    def alloc_free():
        offset = slab_allocator.allocate()
        if offset is not None:
            slab_allocator.free(offset)
        return offset

    benchmark(alloc_free)


# Benchmark: Write + Read combined
def test_bump_write_read(benchmark, bump_allocator):
    """Benchmark combined write and read on bump allocator."""
    offset = bump_allocator.allocate(256)
    data = b"test data" * 10

    def write_read():
        bump_allocator.write(offset, data)
        return bump_allocator.read(offset, len(data))

    result = benchmark(write_read)
    assert result == data


def test_freelist_write_read(benchmark, freelist_allocator):
    """Benchmark combined write and read on freelist allocator."""
    offset = freelist_allocator.allocate(256)
    data = b"test data" * 10

    def write_read():
        freelist_allocator.write(offset, data)
        return freelist_allocator.read(offset, len(data))

    result = benchmark(write_read)
    assert result == data


def test_slab_write_read(benchmark, slab_allocator):
    """Benchmark combined write and read on slab allocator."""
    offset = slab_allocator.allocate()
    data = b"test data" * 10

    def write_read():
        slab_allocator.write(offset, data)
        return slab_allocator.read(offset, len(data))

    result = benchmark(write_read)
    assert result == data


# Benchmark: Reuse pattern (alloc-free-alloc)
def test_freelist_reuse(benchmark, freelist_allocator):
    """Benchmark reuse pattern on freelist allocator."""
    def reuse():
        offset1 = freelist_allocator.allocate(256)
        if offset1 is not None:
            freelist_allocator.free(offset1)
            offset2 = freelist_allocator.allocate(256)
            if offset2 is not None:
                freelist_allocator.free(offset2)
            return offset2
        return None

    benchmark(reuse)


def test_slab_reuse(benchmark, slab_allocator):
    """Benchmark reuse pattern on slab allocator."""
    def reuse():
        offset1 = slab_allocator.allocate()
        if offset1 is not None:
            slab_allocator.free(offset1)
            offset2 = slab_allocator.allocate()
            if offset2 is not None:
                slab_allocator.free(offset2)
            return offset2
        return None

    benchmark(reuse)
