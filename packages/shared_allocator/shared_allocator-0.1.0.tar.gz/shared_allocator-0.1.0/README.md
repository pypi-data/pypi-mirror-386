# shared_allocator

High-performance shared memory allocation for Python multiprocessing.

Provides multiple allocator strategies optimized for different use cases:

- **BumpAllocator**: Ultra-fast (2-3x faster), reset-based allocation
- **FreeListAllocator**: General-purpose with individual deallocation support
- **SlabAllocator**: Fixed-size slot allocation with bitmap tracking

## Features

- 🚀 **High Performance**: 2-7 million operations per second
- 🔒 **Process-Safe**: Safe concurrent access from multiple processes
- 💾 **Zero-Copy**: Uses POSIX shared memory for efficient IPC
- 🎯 **Multiple Strategies**: Choose the right allocator for your use case

## Installation

```bash
uv pip install -e .
```

## Quick Start

### FreeListAllocator (Recommended for general use)

```python
from shared_allocator import FreeListAllocator

# Create allocator
allocator = FreeListAllocator(name="my_allocator", capacity=10*1024*1024, create=True)

# Allocate and write
offset = allocator.allocate(256)
allocator.write(offset, b"Hello from shared memory!")

# Read back
data = allocator.read(offset, 25)
print(data)  # b"Hello from shared memory!"

# Free when done
allocator.free(offset)

# Cleanup
allocator.close()
allocator.unlink()
```

### BumpAllocator (Fastest for temporary allocations)

```python
from shared_allocator import BumpAllocator

# Create allocator
allocator = BumpAllocator(name="fast_allocator", capacity=10*1024*1024, create=True)

# Allocate lots of temporary data
for i in range(1000):
    offset = allocator.allocate(128)
    allocator.write(offset, f"Record {i}".encode())

# Reset all at once (much faster than individual frees)
allocator.reset()

# Memory is available again
print(f"Available: {allocator.available_bytes()} bytes")

allocator.close()
allocator.unlink()
```

## Performance Benchmarks

Based on pytest-benchmark results:

| Operation | BumpAllocator | FreeListAllocator | Winner |
|-----------|---------------|-------------------|--------|
| Write | 7,122 Kops/s | 4,216 Kops/s | Bump (1.7x) |
| Read | 5,958 Kops/s | 5,016 Kops/s | Bump (1.2x) |
| Sequential Alloc | 2,927 Kops/s | 1,040 Kops/s | Bump (2.8x) |
| Alloc+Free | N/A | 1,227 Kops/s | FreeList |
| Reuse Pattern | N/A | 596 Kops/s | FreeList |

**Recommendation**: Use `BumpAllocator` for 2-3x better performance when you can bulk-reset. Use `FreeListAllocator` when you need individual deallocation.

## Use Cases

### BumpAllocator
- Request-scoped allocations (allocate during request, reset after)
- Temporary buffers in data processing pipelines
- Phase-based computations
- Scenarios where all allocations have similar lifetimes

### FreeListAllocator
- Long-lived objects with mixed allocation/deallocation
- Dynamic data structures
- When you need fine-grained memory management
- General-purpose shared memory allocation

## Development

```bash
# Install dependencies
uv sync

# Run tests
pytest

# Run benchmarks
pytest tests/test_benchmarks.py --benchmark-only

# Run tests with coverage
pytest --cov=shared_allocator

# Run examples
python examples/basic_usage.py
```

## Architecture

All allocators use POSIX shared memory with the following structure:

```
[METADATA] [ALLOCATOR-SPECIFIC DATA] [DATA POOL]
```

- **BumpAllocator**: Simple offset counter, O(1) allocation
- **FreeListAllocator**: Stack of free slot indices, O(1) alloc/free
- **SlabAllocator**: Bitmap for slot tracking, O(n) allocation

Learned from [`shared_hashmap`](https://github.com/user/shared_hashmap):
- 8-byte alignment for atomic operations
- Lazy atomic view loading for performance
- Clean separation of metadata and data regions

## License

MIT