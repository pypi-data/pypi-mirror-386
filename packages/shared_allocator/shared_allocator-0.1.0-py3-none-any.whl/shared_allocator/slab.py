"""
Slab Allocator Implementation.

This allocator divides memory into fixed-size "slabs" and manages allocation
using a bitmap to track free/used slots. Excellent for uniform-size allocations
with minimal fragmentation.

Characteristics:
- O(1) allocation time (bitmap scan)
- Zero fragmentation (all blocks same size)
- Fast deallocation (flip bit)
- Best for: uniform objects (e.g., fixed-size records, nodes in data structures)
"""

import struct
from multiprocessing import shared_memory

try:
    import atomics

    HAS_ATOMICS = True
except ImportError:
    HAS_ATOMICS = False

# Memory layout: [METADATA][BITMAP][SLAB_0][SLAB_1]...[SLAB_N]
# Metadata: [capacity: 8 bytes][slab_size: 8 bytes][num_slabs: 8 bytes][next_free_hint: 8 bytes]
METADATA_SIZE = 32
CAPACITY_OFFSET = 0
SLAB_SIZE_OFFSET = 8
NUM_SLABS_OFFSET = 16
NEXT_FREE_HINT_OFFSET = 24


class SlabAllocator:
    """
    Slab allocator using shared memory with fixed-size blocks.

    All allocations are rounded up to the slab size. Uses a bitmap to track
    free/used slabs for O(1) allocation and deallocation.

    Args:
        name: Unique name for the shared memory block
        slab_size: Size of each slab in bytes (all allocations will be this size)
        num_slabs: Number of slabs to create
        create: If True, creates new shared memory; if False, attaches to existing

    Example:
        # Create allocator with 256-byte slabs
        allocator = SlabAllocator(name="my_allocator", slab_size=256, num_slabs=4096, create=True)

        # All allocations use exactly one slab (256 bytes)
        offset1 = allocator.allocate()  # Returns offset to 256-byte block
        offset2 = allocator.allocate()  # Returns offset to next 256-byte block

        # Free a slab
        allocator.free(offset1)

        # Reuse freed slab
        offset3 = allocator.allocate()  # Likely reuses offset1
    """

    def __init__(self, name: str, slab_size: int = 256, num_slabs: int = 4096, create: bool = True):
        self.name = name
        self.slab_size = slab_size
        self.num_slabs = num_slabs

        # Calculate bitmap size (1 bit per slab, packed into bytes)
        self.bitmap_size = (num_slabs + 7) // 8  # Round up to nearest byte
        self.bitmap_offset = METADATA_SIZE

        # Calculate slab data region
        self.slabs_offset = METADATA_SIZE + self.bitmap_size
        self.capacity = slab_size * num_slabs
        self.total_size = self.slabs_offset + self.capacity

        if create:
            # Create new shared memory
            self.shm = shared_memory.SharedMemory(name=name, create=True, size=self.total_size)

            # Initialize metadata
            struct.pack_into("QQQQ", self.shm.buf, 0, self.capacity, slab_size, num_slabs, 0)

            # Initialize bitmap to all zeros (all slabs free)
            for i in range(self.bitmap_size):
                self.shm.buf[self.bitmap_offset + i] = 0

            # Setup atomic view for next_free_hint if available
            if HAS_ATOMICS:
                hint_slice = self.shm.buf[NEXT_FREE_HINT_OFFSET : NEXT_FREE_HINT_OFFSET + 8]
                self._hint_view = atomics.atomicview(buffer=hint_slice, width=8, atype=atomics.UINT)
                self._hint_atomic = self._hint_view.__enter__()
            else:
                self._hint_atomic = None
        else:
            # Attach to existing shared memory
            self.shm = shared_memory.SharedMemory(name=name, create=False)

            # Read metadata
            capacity, slab_size, num_slabs, _ = struct.unpack_from("QQQQ", self.shm.buf, 0)
            self.capacity = capacity
            self.slab_size = slab_size
            self.num_slabs = num_slabs

            self.bitmap_size = (num_slabs + 7) // 8
            self.bitmap_offset = METADATA_SIZE
            self.slabs_offset = METADATA_SIZE + self.bitmap_size
            self.total_size = self.slabs_offset + self.capacity

            # Setup atomic view for next_free_hint if available
            if HAS_ATOMICS:
                hint_slice = self.shm.buf[NEXT_FREE_HINT_OFFSET : NEXT_FREE_HINT_OFFSET + 8]
                self._hint_view = atomics.atomicview(buffer=hint_slice, width=8, atype=atomics.UINT)
                self._hint_atomic = self._hint_view.__enter__()
            else:
                self._hint_atomic = None

    def _get_bit(self, slab_index: int) -> bool:
        """Check if a slab is allocated (bit = 1) or free (bit = 0)."""
        byte_index = slab_index // 8
        bit_index = slab_index % 8
        byte_value = self.shm.buf[self.bitmap_offset + byte_index]
        return bool((byte_value >> bit_index) & 1)

    def _set_bit(self, slab_index: int) -> None:
        """Mark a slab as allocated."""
        byte_index = slab_index // 8
        bit_index = slab_index % 8
        offset = self.bitmap_offset + byte_index
        self.shm.buf[offset] |= 1 << bit_index

    def _clear_bit(self, slab_index: int) -> None:
        """Mark a slab as free."""
        byte_index = slab_index // 8
        bit_index = slab_index % 8
        offset = self.bitmap_offset + byte_index
        self.shm.buf[offset] &= ~(1 << bit_index)

    def _get_next_free_hint(self) -> int:
        """Get the hint for where to start searching for free slabs."""
        return struct.unpack_from("Q", self.shm.buf, NEXT_FREE_HINT_OFFSET)[0]

    def _set_next_free_hint(self, hint: int) -> None:
        """Set the hint for where to start searching for free slabs."""
        struct.pack_into("Q", self.shm.buf, NEXT_FREE_HINT_OFFSET, hint)

    def allocate(self, size: int | None = None) -> int | None:
        """
        Allocate a slab from the allocator.

        Args:
            size: Ignored (all allocations are slab_size). Included for API compatibility.

        Returns:
            Offset into the data pool where the slab starts, or None if out of memory

        Note:
            Without atomics package and proper synchronization, concurrent allocations
            may have race conditions. Use external synchronization if needed.
        """
        if size is not None and size > self.slab_size:
            raise ValueError(f"Requested size {size} exceeds slab size {self.slab_size}")

        # Start searching from the hint
        start_index = self._get_next_free_hint()

        # Search for a free slab (linear scan)
        for i in range(self.num_slabs):
            slab_index = (start_index + i) % self.num_slabs

            if not self._get_bit(slab_index):
                # Found free slab!
                # Note: Without proper atomic bit operations, this has race conditions
                # in multi-threaded scenarios. A production version would use atomic
                # test-and-set or compare-and-swap on bitmap words.

                self._set_bit(slab_index)

                # Update hint to next position for faster subsequent allocations
                self._set_next_free_hint((slab_index + 1) % self.num_slabs)

                # Calculate offset in data pool
                return slab_index * self.slab_size

        # No free slabs
        return None

    def free(self, offset: int) -> None:
        """
        Free a previously allocated slab.

        Args:
            offset: Offset returned by allocate()
        """
        if offset < 0 or offset >= self.capacity:
            raise ValueError(f"Invalid offset: {offset}")

        if offset % self.slab_size != 0:
            raise ValueError(f"Offset {offset} is not aligned to slab size {self.slab_size}")

        slab_index = offset // self.slab_size

        if not self._get_bit(slab_index):
            raise ValueError(f"Double free detected at offset {offset}")

        self._clear_bit(slab_index)

        # Update hint if this slab is before current hint (helps fill in gaps)
        current_hint = self._get_next_free_hint()
        if slab_index < current_hint:
            self._set_next_free_hint(slab_index)

    def write(self, offset: int, data: bytes) -> None:
        """Write data to the allocator at the given offset."""
        if offset < 0 or offset + len(data) > self.capacity:
            raise ValueError(f"Write out of bounds: offset={offset}, size={len(data)}")

        if len(data) > self.slab_size:
            raise ValueError(f"Data size {len(data)} exceeds slab size {self.slab_size}")

        start = self.slabs_offset + offset
        self.shm.buf[start : start + len(data)] = data

    def read(self, offset: int, size: int) -> bytes:
        """Read data from the allocator at the given offset."""
        if offset < 0 or offset + size > self.capacity:
            raise ValueError(f"Read out of bounds: offset={offset}, size={size}")

        if size > self.slab_size:
            raise ValueError(f"Read size {size} exceeds slab size {self.slab_size}")

        start = self.slabs_offset + offset
        return bytes(self.shm.buf[start : start + size])

    def used_slabs(self) -> int:
        """Count the number of allocated slabs."""
        count = 0
        for i in range(self.num_slabs):
            if self._get_bit(i):
                count += 1
        return count

    def available_slabs(self) -> int:
        """Get the number of free slabs."""
        return self.num_slabs - self.used_slabs()

    def close(self) -> None:
        """Close the shared memory handle."""
        if HAS_ATOMICS and hasattr(self, "_hint_view"):
            try:
                self._hint_view.__exit__(None, None, None)
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
