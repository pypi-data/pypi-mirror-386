"""
Bump/Linear Allocator Implementation.

This is the simplest and fastest allocation strategy - memory is allocated
sequentially from a pool by bumping an offset pointer forward. No individual
deallocation is supported; the entire allocator must be reset at once.

Characteristics:
- O(1) allocation time
- Zero fragmentation
- No deallocation overhead
- Best for: temporary allocations, request-scoped memory
"""

import struct
from multiprocessing import shared_memory

try:
    import atomics

    HAS_ATOMICS = True
except ImportError:
    HAS_ATOMICS = False

# Memory layout: [METADATA][DATA_POOL]
# Metadata: [capacity: 8 bytes][offset: 8 bytes]
METADATA_SIZE = 16
CAPACITY_OFFSET = 0
OFFSET_OFFSET = 8


class BumpAllocator:
    """
    Bump/linear allocator using shared memory.

    Memory is allocated by atomically incrementing an offset pointer.
    No individual deallocations - only bulk reset is supported.

    Args:
        name: Unique name for the shared memory block
        capacity: Total size of the data pool in bytes
        create: If True, creates new shared memory; if False, attaches to existing

    Example:
        # Process 1: Create allocator
        allocator = BumpAllocator(name="my_allocator", capacity=1024*1024, create=True)
        offset1 = allocator.allocate(256)  # Returns offset in shared memory
        offset2 = allocator.allocate(512)  # Returns next offset

        # Process 2: Attach to allocator
        allocator = BumpAllocator(name="my_allocator", create=False)
        offset3 = allocator.allocate(128)  # Thread-safe allocation
    """

    def __init__(self, name: str, capacity: int = 1024 * 1024, create: bool = True):
        self.name = name
        self.capacity = capacity
        self.total_size = METADATA_SIZE + capacity

        if create:
            # Create new shared memory
            self.shm = shared_memory.SharedMemory(name=name, create=True, size=self.total_size)

            # Initialize metadata
            struct.pack_into("QQ", self.shm.buf, 0, capacity, 0)

            # Setup atomic view for offset if available
            if HAS_ATOMICS:
                offset_slice = self.shm.buf[OFFSET_OFFSET : OFFSET_OFFSET + 8]
                self._offset_view = atomics.atomicview(buffer=offset_slice, width=8, atype=atomics.UINT)
                self._offset_atomic = self._offset_view.__enter__()
            else:
                self._offset_atomic = None
        else:
            # Attach to existing shared memory
            self.shm = shared_memory.SharedMemory(name=name, create=False)

            # Read capacity from metadata
            self.capacity = struct.unpack_from("Q", self.shm.buf, CAPACITY_OFFSET)[0]
            self.total_size = METADATA_SIZE + self.capacity

            # Setup atomic view for offset if available
            if HAS_ATOMICS:
                offset_slice = self.shm.buf[OFFSET_OFFSET : OFFSET_OFFSET + 8]
                self._offset_view = atomics.atomicview(buffer=offset_slice, width=8, atype=atomics.UINT)
                self._offset_atomic = self._offset_view.__enter__()
            else:
                self._offset_atomic = None

    def allocate(self, size: int, alignment: int = 8) -> int | None:
        """
        Allocate a block of memory from the allocator.

        Args:
            size: Number of bytes to allocate
            alignment: Alignment requirement in bytes (must be power of 2)

        Returns:
            Offset into the data pool where the allocation starts, or None if out of memory

        Thread Safety:
            Safe for concurrent access when atomics package is available.
            Without atomics, caller must provide external synchronization.
        """
        if size <= 0:
            raise ValueError(f"Size must be positive, got {size}")

        if alignment & (alignment - 1) != 0:
            raise ValueError(f"Alignment must be power of 2, got {alignment}")

        if HAS_ATOMICS and self._offset_atomic:
            # Lock-free allocation using atomic fetch-add
            while True:
                current_offset = self._offset_atomic.load()

                # Calculate aligned offset
                aligned_offset = (current_offset + alignment - 1) & ~(alignment - 1)
                new_offset = aligned_offset + size

                # Check if we have space
                if new_offset > self.capacity:
                    return None

                # Try to claim this space atomically
                success, _ = self._offset_atomic.cmpxchg_strong(current_offset, new_offset)
                if success:
                    return aligned_offset
        else:
            # Non-atomic fallback (requires external synchronization)
            current_offset = struct.unpack_from("Q", self.shm.buf, OFFSET_OFFSET)[0]

            # Calculate aligned offset
            aligned_offset = (current_offset + alignment - 1) & ~(alignment - 1)
            new_offset = aligned_offset + size

            if new_offset > self.capacity:
                return None

            # Update offset
            struct.pack_into("Q", self.shm.buf, OFFSET_OFFSET, new_offset)
            return aligned_offset

    def write(self, offset: int, data: bytes) -> None:
        """
        Write data to the allocator at the given offset.

        Args:
            offset: Offset returned by allocate()
            data: Bytes to write
        """
        if offset < 0 or offset + len(data) > self.capacity:
            raise ValueError(f"Write out of bounds: offset={offset}, size={len(data)}, capacity={self.capacity}")

        start = METADATA_SIZE + offset
        self.shm.buf[start : start + len(data)] = data

    def read(self, offset: int, size: int) -> bytes:
        """
        Read data from the allocator at the given offset.

        Args:
            offset: Offset to read from
            size: Number of bytes to read

        Returns:
            The data as bytes
        """
        if offset < 0 or offset + size > self.capacity:
            raise ValueError(f"Read out of bounds: offset={offset}, size={size}, capacity={self.capacity}")

        start = METADATA_SIZE + offset
        return bytes(self.shm.buf[start : start + size])

    def used_bytes(self) -> int:
        """Get the number of bytes currently allocated."""
        return struct.unpack_from("Q", self.shm.buf, OFFSET_OFFSET)[0]

    def available_bytes(self) -> int:
        """Get the number of bytes available for allocation."""
        return self.capacity - self.used_bytes()

    def reset(self) -> None:
        """
        Reset the allocator, making all memory available again.

        Warning: This does not zero the memory, just resets the offset pointer.
                 Any existing pointers/offsets become invalid.
        """
        if HAS_ATOMICS and self._offset_atomic:
            self._offset_atomic.store(0)
        else:
            struct.pack_into("Q", self.shm.buf, OFFSET_OFFSET, 0)

    def close(self) -> None:
        """Close the shared memory handle."""
        if HAS_ATOMICS and hasattr(self, "_offset_view"):
            try:
                self._offset_view.__exit__(None, None, None)
            except Exception:
                pass
        self.shm.close()

    def unlink(self) -> None:
        """Destroy the shared memory block."""
        self.shm.unlink()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
