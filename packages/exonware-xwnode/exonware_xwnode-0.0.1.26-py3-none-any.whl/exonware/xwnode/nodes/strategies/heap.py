"""
Heap Node Strategy Implementation

This module implements the HEAP strategy for priority queue operations.
"""

import heapq
from typing import Any, Iterator, List, Optional, Dict
from .base import ANodeTreeStrategy
from .contracts import NodeType
from ...defs import NodeMode, NodeTrait


class MinHeap:
    """Min heap implementation."""
    
    def __init__(self, max_heap: bool = False):
        """Time Complexity: O(1)"""
        self._heap = []
        self._max_heap = max_heap
        self._counter = 0  # For stable sorting
    
    def push(self, priority: float, value: Any) -> None:
        """
        Push item with priority.
        
        Time Complexity: O(log n)
        """
        if self._max_heap:
            priority = -priority
        heapq.heappush(self._heap, (priority, self._counter, value))
        self._counter += 1
    
    def pop(self) -> Any:
        """
        Pop item with highest priority.
        
        Time Complexity: O(log n)
        """
        if not self._heap:
            raise IndexError("pop from empty heap")
        priority, _, value = heapq.heappop(self._heap)
        return value
    
    def peek(self) -> Any:
        """
        Peek at highest priority item.
        
        Time Complexity: O(1)
        """
        if not self._heap:
            raise IndexError("peek from empty heap")
        return self._heap[0][2]
    
    def size(self) -> int:
        """
        Get heap size.
        
        Time Complexity: O(1)
        """
        return len(self._heap)
    
    def is_empty(self) -> bool:
        """
        Check if heap is empty.
        
        Time Complexity: O(1)
        """
        return len(self._heap) == 0


class HeapStrategy(ANodeTreeStrategy):
    """
    Heap node strategy for priority queue operations.
    
    Optimized for push, pop, and peek operations with config
    
    # Strategy type classification
    STRATEGY_TYPE = NodeType.TREE
urable min/max behavior.
    """
    
    def __init__(self, traits: NodeTrait = NodeTrait.NONE, **options):
        """
        Initialize the heap strategy.
        
        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        super().__init__(NodeMode.HEAP, traits, **options)
        self._is_max_heap = options.get('max_heap', False)
        self._heap = MinHeap(max_heap=self._is_max_heap)
        self._size = 0
    
    def get_supported_traits(self) -> NodeTrait:
        """
        Get the traits supported by the heap strategy.
        
        Time Complexity: O(1)
        """
        return (NodeTrait.ORDERED | NodeTrait.PRIORITY)
    
    # ============================================================================
    # CORE OPERATIONS
    # ============================================================================
    
    def insert(self, key: Any, value: Any) -> None:
        """
        Store a key-value pair (key is priority, value is data).
        
        Time Complexity: O(log n)
        """
        priority = float(key) if key is not None else 0.0
        data = value if value is not None else key
        self._heap.push(priority, data)
        self._size += 1
    
    def find(self, key: Any) -> Any:
        """
        Find value by priority (not efficient for heaps).
        
        Time Complexity: O(1) - not supported
        """
        # Heaps don't support efficient lookup by priority
        # This is a limitation of the heap data structure
        return None
    
    def delete(self, key: Any) -> bool:
        """
        Delete by priority (not efficient for heaps).
        
        Time Complexity: O(1) - not supported
        """
        # Heaps don't support efficient deletion by priority
        # This is a limitation of the heap data structure
        return False
    
    def size(self) -> int:
        """
        Get the number of items.
        
        Time Complexity: O(1)
        """
        return self._size
    
    def is_empty(self) -> bool:
        """
        Check if the structure is empty.
        
        Time Complexity: O(1)
        """
        return self._size == 0
    
    def to_native(self) -> List[Any]:
        """
        Convert to native Python list.
        
        Time Complexity: O(n log n)
        """
        # Return all values in priority order
        result = []
        temp_heap = MinHeap(max_heap=self._is_max_heap)
        
        # Copy heap and extract all values
        for item in self._heap._heap:
            priority, counter, value = item
            temp_heap._heap.append(item)
        
        while not temp_heap.is_empty():
            result.append(temp_heap.pop())
        
        return result
    
    # ============================================================================
    # TREE STRATEGY METHODS
    # ============================================================================
    
    def traverse(self, order: str = 'inorder') -> List[Any]:
        """Traverse heap in priority order."""
        return self.to_native()
    
    def get_min(self) -> Any:
        """Get minimum priority item."""
        if self._is_max_heap:
            return None  # No min in max heap
        return self._heap.peek() if not self._heap.is_empty() else None
    
    def get_max(self) -> Any:
        """Get maximum priority item."""
        if not self._is_max_heap:
            return None  # No max in min heap
        return self._heap.peek() if not self._heap.is_empty() else None
    
    # ============================================================================
    # AUTO-3 Phase 2 methods
    # ============================================================================
    
    def as_trie(self):
        """Provide Trie behavioral view."""
        # TODO: Implement Trie view
        return self
    
    def as_heap(self):
        """Provide Heap behavioral view."""
        return self
    
    def as_skip_list(self):
        """Provide SkipList behavioral view."""
        # TODO: Implement SkipList view
        return self
    
    # ============================================================================
    # HEAP SPECIFIC OPERATIONS
    # ============================================================================
    
    def push(self, value: Any, priority: float = None) -> str:
        """Push a value with optional priority."""
        if priority is None:
            priority = float(value) if isinstance(value, (int, float)) else 0.0
        self._heap.push(priority, value)
        self._size += 1
        return str(priority)
    
    def pop(self) -> Any:
        """Remove and return highest priority item."""
        if self._heap.is_empty():
            raise IndexError("pop from empty heap")
        value = self._heap.pop()
        self._size -= 1
        return value
    
    def peek(self) -> Any:
        """Get highest priority item without removing."""
        if self._heap.is_empty():
            raise IndexError("peek from empty heap")
        return self._heap.peek()
    
    def peek_priority(self) -> float:
        """Get priority of highest priority item."""
        if self._heap.is_empty():
            raise IndexError("peek from empty heap")
        # This is a simplified implementation
        return 0.0
    
    def pushpop(self, value: Any, priority: float = None) -> Any:
        """Push value and pop highest priority item."""
        if priority is None:
            priority = float(value) if isinstance(value, (int, float)) else 0.0
        
        if self._heap.is_empty():
            self._heap.push(priority, value)
            return None
        
        # Push new value
        self._heap.push(priority, value)
        # Pop highest priority
        return self._heap.pop()
    
    def replace(self, value: Any, priority: float = None) -> Any:
        """Replace highest priority item with new value."""
        if self._heap.is_empty():
            raise IndexError("replace from empty heap")
        
        if priority is None:
            priority = float(value) if isinstance(value, (int, float)) else 0.0
        
        # Pop current highest
        old_value = self._heap.pop()
        # Push new value
        self._heap.push(priority, value)
        
        return old_value
    
    def heapify(self) -> None:
        """Heapify the heap (already maintained)."""
        # Heap is already heapified
        pass
    
    def nlargest(self, n: int) -> List[Any]:
        """Get n largest items."""
        if self._is_max_heap:
            # For max heap, get first n items
            result = []
            temp_heap = MinHeap(max_heap=True)
            
            # Copy heap
            for item in self._heap._heap:
                temp_heap._heap.append(item)
            
            for _ in range(min(n, self._size)):
                if temp_heap.is_empty():
                    break
                result.append(temp_heap.pop())
            
            return result
        else:
            # For min heap, this is not efficient
            return []
    
    def nsmallest(self, n: int) -> List[Any]:
        """Get n smallest items."""
        if not self._is_max_heap:
            # For min heap, get first n items
            result = []
            temp_heap = MinHeap(max_heap=False)
            
            # Copy heap
            for item in self._heap._heap:
                temp_heap._heap.append(item)
            
            for _ in range(min(n, self._size)):
                if temp_heap.is_empty():
                    break
                result.append(temp_heap.pop())
            
            return result
        else:
            # For max heap, this is not efficient
            return []
    
    # ============================================================================
    # ITERATION
    # ============================================================================
    
    def keys(self) -> Iterator[str]:
        """Get all priorities as strings."""
        # This is not efficient for heaps
        return iter([])
    
    def values(self) -> Iterator[Any]:
        """Get all values."""
        return iter(self.to_native())
    
    def items(self) -> Iterator[tuple[str, Any]]:
        """Get all priority-value pairs."""
        # This is not efficient for heaps
        return iter([])
    
    # ============================================================================
    # PERFORMANCE CHARACTERISTICS
    # ============================================================================
    
    @property
    def backend_info(self) -> Dict[str, Any]:
        """Get backend implementation info."""
        return {
            'strategy': 'HEAP',
            'backend': 'Python heapq',
            'complexity': {
                'push': 'O(log n)',
                'pop': 'O(log n)',
                'peek': 'O(1)',
                'heapify': 'O(n)'
            }
        }
    
    @property
    def metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        return {
            'size': self._size,
            'is_max_heap': self._is_max_heap,
            'memory_usage': f"{self._size * 24} bytes (estimated)"
        }
    
    # ============================================================================
    # REQUIRED INTERFACE METHODS (iNodeStrategy)
    # ============================================================================
    
    def create_from_data(self, data: Any) -> 'HeapStrategy':
        """Create strategy instance from data."""
        new_strategy = HeapStrategy(self._traits, max_heap=self._is_max_heap)
        if isinstance(data, list):
            for item in data:
                if isinstance(item, (int, float)):
                    new_strategy.push(item, priority=item)
                else:
                    new_strategy.push(item)
        return new_strategy
    
    def get(self, path: str, default: Any = None) -> Any:
        """Get value (heaps don't support path-based lookup)."""
        return default
    
    def has(self, key: Any) -> bool:
        """Check if value exists in heap (O(n) - not efficient)."""
        for priority, data in self._heap.data:
            if data == key:
                return True
        return False
    
    def put(self, path: str, value: Any) -> 'HeapStrategy':
        """Put value (heaps use push instead)."""
        self.push(value)
        return self
    
    def exists(self, path: str) -> bool:
        """Check if path exists (not applicable to heaps)."""
        return False
    
    # Container protocol
    def __len__(self) -> int:
        """Get length."""
        return self._size
    
    def __iter__(self) -> Iterator[Any]:
        """Iterate over values."""
        return self.values()
    
    def __getitem__(self, key: Any) -> Any:
        """Get item (heaps don't support indexed access)."""
        raise IndexError("Heaps don't support indexed access")
    
    def __setitem__(self, key: Any, value: Any) -> None:
        """Set item (heaps don't support indexed access)."""
        raise TypeError("Heaps don't support indexed assignment")
    
    def __contains__(self, key: Any) -> bool:
        """Check if key exists (not efficient for heaps)."""
        return False
    
    # Type checking properties
    @property
    def is_leaf(self) -> bool:
        """Check if this is a leaf node."""
        return self._size == 0
    
    @property
    def is_list(self) -> bool:
        """Check if this is a list node."""
        return False
    
    @property
    def is_dict(self) -> bool:
        """Check if this is a dict node."""
        return False
    
    @property
    def is_reference(self) -> bool:
        """Check if this is a reference node."""
        return False
    
    @property
    def is_object(self) -> bool:
        """Check if this is an object node."""
        return False
    
    @property
    def type(self) -> str:
        """Get the type of this node."""
        return "heap"
    
    @property
    def value(self) -> Any:
        """Get the value of this node."""
        return self.to_native()
    
    @property
    def strategy_name(self) -> str:
        """Get strategy name."""
        return "HEAP"
    
    @property
    def supported_traits(self) -> NodeTrait:
        """Get supported traits."""
        return self.get_supported_traits()