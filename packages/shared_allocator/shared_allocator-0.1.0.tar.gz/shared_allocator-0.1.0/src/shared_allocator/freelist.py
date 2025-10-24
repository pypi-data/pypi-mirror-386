"""
Free List Allocator Implementation - Simplified.

This allocator maintains a stack of fixed-size free slots. Much simpler than
a traditional variable-size free list, but still supports deallocation.

Characteristics:
- O(1) allocation time (pop from stack)
- O(1) deallocation (push to stack)
- Fixed slot sizes (like slab but with explicit free list)
- Best for: scenarios where you need deallocation with predictable sizes
"""

import struct
from multiprocessing import shared_memory

try:
    import atomics

    HAS_ATOMICS = True
except ImportError:
    HAS_ATOMICS = False

# Memory layout: [METADATA][FREE_STACK][DATA_POOL]
# Metadata: [capacity: 8 bytes][slot_size: 8 bytes][num_slots: 8 bytes][stack_top: 8 bytes]
METADATA_SIZE = 32
CAPACITY_OFFSET = 0
SLOT_SIZE_OFFSET = 8
NUM_SLOTS_OFFSET = 16
STACK_TOP_OFFSET = 24


class FreeListAllocator:
    """
    Simple free list allocator using a stack of free slots.

    Uses fixed-size slots and maintains a stack (in shared memory) of
    free slot indices for O(1) allocation and deallocation.

    Args:
        name: Unique name for the shared memory block
        slot_size: Size of each slot in bytes (default: 256)
        num_slots: Number of slots to create (default: 40960)
        capacity: Ignored if slot_size and num_slots provided
        create: If True, creates new shared memory; if False, attaches to existing

    Example:
        allocator = FreeListAllocator(name="my_allocator", slot_size=256, num_slots=4096, create=True)

        # Allocate slots
        offset1 = allocator.allocate(200)  # Uses one 256-byte slot
        offset2 = allocator.allocate(256)  # Uses one 256-byte slot

        # Free a slot
        allocator.free(offset1)

        # Reuse freed slot
        offset3 = allocator.allocate(100)  # Likely reuses offset1
    """

    def __init__(self, name: str, capacity: int = 10 * 1024 * 1024, slot_size: int = 256, num_slots: int | None = None, create: bool = True):
        self.name = name
        self.slot_size = slot_size

        # Calculate num_slots if not provided
        if num_slots is None:
            self.num_slots = capacity // slot_size
        else:
            self.num_slots = num_slots

        self.capacity = self.slot_size * self.num_slots

        # Free stack stores slot indices (4 bytes each)
        self.free_stack_size = self.num_slots * 4  # 4 bytes per index
        self.data_pool_offset = METADATA_SIZE + self.free_stack_size
        self.total_size = self.data_pool_offset + self.capacity

        if create:
            # Create new shared memory
            self.shm = shared_memory.SharedMemory(name=name, create=True, size=self.total_size)

            # Initialize metadata
            struct.pack_into("QQQQ", self.shm.buf, 0, self.capacity, slot_size, self.num_slots, self.num_slots)

            # Initialize free stack with all slot indices (LIFO stack)
            # Stack grows down: stack_top points to next free slot
            # All slots start as free
            for i in range(self.num_slots):
                offset = METADATA_SIZE + (i * 4)
                struct.pack_into("I", self.shm.buf, offset, i)

            # Setup atomic view for stack top if available
            if HAS_ATOMICS:
                top_slice = self.shm.buf[STACK_TOP_OFFSET : STACK_TOP_OFFSET + 8]
                self._top_view = atomics.atomicview(buffer=top_slice, width=8, atype=atomics.UINT)
                self._top_atomic = self._top_view.__enter__()
            else:
                self._top_atomic = None
        else:
            # Attach to existing shared memory
            self.shm = shared_memory.SharedMemory(name=name, create=False)

            # Read metadata
            capacity, slot_size, num_slots, _ = struct.unpack_from("QQQQ", self.shm.buf, 0)
            self.capacity = capacity
            self.slot_size = slot_size
            self.num_slots = num_slots

            self.free_stack_size = self.num_slots * 4
            self.data_pool_offset = METADATA_SIZE + self.free_stack_size
            self.total_size = self.data_pool_offset + self.capacity

            # Setup atomic view for stack top if available
            if HAS_ATOMICS:
                top_slice = self.shm.buf[STACK_TOP_OFFSET : STACK_TOP_OFFSET + 8]
                self._top_view = atomics.atomicview(buffer=top_slice, width=8, atype=atomics.UINT)
                self._top_atomic = self._top_view.__enter__()
            else:
                self._top_atomic = None

    def _get_stack_top(self) -> int:
        """Get current stack top (number of free slots)."""
        return struct.unpack_from("Q", self.shm.buf, STACK_TOP_OFFSET)[0]

    def _set_stack_top(self, top: int) -> None:
        """Set stack top."""
        struct.pack_into("Q", self.shm.buf, STACK_TOP_OFFSET, top)

    def _pop_free_slot(self) -> int | None:
        """Pop a free slot index from the stack."""
        top = self._get_stack_top()

        if top == 0:
            return None  # Stack empty - no free slots

        # Pop from stack
        new_top = top - 1
        self._set_stack_top(new_top)

        # Read slot index from stack
        stack_offset = METADATA_SIZE + (new_top * 4)
        slot_index = struct.unpack_from("I", self.shm.buf, stack_offset)[0]

        return slot_index

    def _push_free_slot(self, slot_index: int) -> None:
        """Push a free slot index onto the stack."""
        top = self._get_stack_top()

        if top >= self.num_slots:
            raise RuntimeError("Free stack overflow - double free?")

        # Write slot index to stack
        stack_offset = METADATA_SIZE + (top * 4)
        struct.pack_into("I", self.shm.buf, stack_offset, slot_index)

        # Increment stack top
        self._set_stack_top(top + 1)

    def allocate(self, size: int = 0, alignment: int = 8) -> int | None:
        """
        Allocate a slot from the allocator.

        Args:
            size: Requested size (must fit in slot_size)
            alignment: Ignored (all slots are naturally aligned)

        Returns:
            Offset into the data pool where the slot starts, or None if out of memory
        """
        if size > self.slot_size:
            raise ValueError(f"Requested size {size} exceeds slot size {self.slot_size}")

        slot_index = self._pop_free_slot()

        if slot_index is None:
            return None

        # Calculate offset in data pool
        return slot_index * self.slot_size

    def free(self, offset: int) -> None:
        """
        Free a previously allocated slot.

        Args:
            offset: Offset returned by allocate()
        """
        if offset < 0 or offset >= self.capacity:
            raise ValueError(f"Invalid offset: {offset}")

        if offset % self.slot_size != 0:
            raise ValueError(f"Offset {offset} is not aligned to slot size {self.slot_size}")

        slot_index = offset // self.slot_size

        self._push_free_slot(slot_index)

    def write(self, offset: int, data: bytes) -> None:
        """Write data to the allocator at the given offset."""
        if offset < 0 or offset + len(data) > self.capacity:
            raise ValueError(f"Write out of bounds: offset={offset}, size={len(data)}")

        if len(data) > self.slot_size:
            raise ValueError(f"Data size {len(data)} exceeds slot size {self.slot_size}")

        start = self.data_pool_offset + offset
        self.shm.buf[start : start + len(data)] = data

    def read(self, offset: int, size: int) -> bytes:
        """Read data from the allocator at the given offset."""
        if offset < 0 or offset + size > self.capacity:
            raise ValueError(f"Read out of bounds: offset={offset}, size={size}")

        if size > self.slot_size:
            raise ValueError(f"Read size {size} exceeds slot size {self.slot_size}")

        start = self.data_pool_offset + offset
        return bytes(self.shm.buf[start : start + size])

    def available_slots(self) -> int:
        """Get the number of free slots."""
        return self._get_stack_top()

    def used_slots(self) -> int:
        """Get the number of allocated slots."""
        return self.num_slots - self.available_slots()

    def close(self) -> None:
        """Close the shared memory handle."""
        if HAS_ATOMICS and hasattr(self, "_top_view"):
            try:
                self._top_view.__exit__(None, None, None)
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
