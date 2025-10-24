"""
Fenwick Tree (Binary Indexed Tree) Node Strategy Implementation

This module implements the FENWICK_TREE strategy for efficient prefix sum
queries and point updates with O(log n) complexity.
"""

from typing import Any, Iterator, List, Dict, Union
from .base import ANodeTreeStrategy
from .contracts import NodeType
from ...defs import NodeMode, NodeTrait


class FenwickTreeStrategy(ANodeTreeStrategy):
    """
    Fenwick Tree (Binary Indexed Tree) strategy for efficient prefix sums.
    
    WHY Fenwick Tree:
    - Simpler than Segment Tree for prefix sum queries
    - O(log n) for both query and update (vs O(n) for naive)
    - Minimal memory overhead: just O(n) array
    - Elegant bit manipulation (lowest set bit operations)
    - Industry standard for competitive programming
    
    WHY this implementation:
    - 1-indexed array (standard for Fenwick/BIT - simplifies bit ops)
    - Lowest set bit technique: `idx & -idx` for parent/child navigation
    - Delta-based updates (add/subtract differences)
    - Supports cumulative frequency applications
    
    Time Complexity:
    - Prefix Sum: O(log n) - traverse parents via bit operations
    - Range Sum: O(log n) - difference of two prefix sums
    - Point Update: O(log n) - update ancestors via bit operations
    - Build: O(n log n) - n updates
    
    Space Complexity: O(n) - single array, very memory efficient
    
    Trade-offs:
    - Advantage: Simpler than Segment Tree (fewer lines of code)
    - Advantage: Lower memory overhead than Segment Tree
    - Limitation: Only supports PREFIX operations (not arbitrary ranges as efficiently)
    - Limitation: Requires associative, invertible operations (sum, XOR work; min/max don't)
    - Compared to Segment Tree: Simpler and faster for prefix sums, less flexible
    - Compared to prefix sum array: Dynamic updates O(log n) vs O(n)
    
    Best for:
    - Prefix sum queries (cumulative frequencies)
    - Competitive programming problems
    - When space is limited (O(n) vs O(4n) for Segment Tree)
    - Invertible operations (sum, XOR, but NOT min/max)
    - Dynamic arrays requiring frequent sum queries
    
    Not recommended for:
    - Non-invertible operations (min, max, GCD) - use Segment Tree
    - When arbitrary range operations are primary need
    - When simpler solutions suffice (e.g., static prefix array)
    - 2D/multidimensional ranges (use 2D Fenwick or Segment Tree)
    
    Following eXonware Priorities:
    1. Usability: Clean API for prefix/range sums
    2. Maintainability: Simple bit manipulation logic, well-documented
    3. Performance: O(log n) operations with low constants
    4. Extensibility: Can extend to 2D Fenwick Tree
    5. Security: Input validation on all operations
    
    Industry Best Practices:
    - Follows Peter Fenwick's original paper (1994)
    - Uses 1-indexed array (standard for BIT)
    - Lowest set bit operations: `i & -i`
    - Parent navigation: `i += i & -i`
    - Child navigation: `i -= i & -i`
    
    Performance Note:
    Fenwick Trees excel at prefix sums with O(log n) query and update.
    For arbitrary range operations (especially min/max), use Segment Tree.
    Trade-off: Simplicity (Fenwick) vs Flexibility (Segment Tree).
    """
    
    # Strategy type classification
    STRATEGY_TYPE = NodeType.TREE
    
    def __init__(self, traits: NodeTrait = NodeTrait.NONE, **options):
        """Initialize the Fenwick Tree strategy."""
        super().__init__(NodeMode.FENWICK_TREE, traits, **options)
        
        self.initial_size = options.get('initial_size', 1000)
        
        # Fenwick tree (1-indexed for easier bit operations)
        self._tree: List[float] = [0.0] * (self.initial_size + 1)
        self._values: Dict[str, Any] = {}  # Key-value storage for compatibility  
        self._indices: Dict[str, int] = {}  # Map keys to tree indices
        self._reverse_indices: Dict[int, str] = {}  # Map indices to keys
        self._next_index = 1  # 1-indexed
        self._size = 0
    
    def get_supported_traits(self) -> NodeTrait:
        """Get the traits supported by the Fenwick tree strategy."""
        return (NodeTrait.INDEXED | NodeTrait.ORDERED | NodeTrait.STREAMING)
    
    # ============================================================================
    # CORE OPERATIONS (Key-based interface for compatibility)
    # ============================================================================
    
    def put(self, key: Any, value: Any = None) -> None:
        """Store a value at the given key."""
        key_str = str(key)
        
        # Convert value to numeric for tree operations
        try:
            numeric_value = float(value) if value is not None else 0.0
        except (ValueError, TypeError):
            numeric_value = 0.0
        
        if key_str in self._indices:
            # Update existing
            idx = self._indices[key_str]
            old_value = self._get_point_value(idx)
            delta = numeric_value - old_value
            self._update_point(idx, delta)
        else:
            # Add new
            if self._next_index >= len(self._tree):
                self._resize_tree()
            
            idx = self._next_index
            self._indices[key_str] = idx
            self._reverse_indices[idx] = key_str
            self._next_index += 1
            self._size += 1
            
            self._update_point(idx, numeric_value)
        
        self._values[key_str] = value
    
    def get(self, key: Any, default: Any = None) -> Any:
        """Retrieve a value by key."""
        key_str = str(key)
        return self._values.get(key_str, default)
    
    def has(self, key: Any) -> bool:
        """Check if key exists."""
        return str(key) in self._values
    
    def remove(self, key: Any) -> bool:
        """Remove value by key."""
        key_str = str(key)
        if key_str not in self._indices:
            return False
        
        idx = self._indices[key_str]
        old_value = self._get_point_value(idx)
        self._update_point(idx, -old_value)  # Set to 0
        
        del self._indices[key_str]
        del self._reverse_indices[idx]
        del self._values[key_str]
        self._size -= 1
        
        return True
    
    def delete(self, key: Any) -> bool:
        """Remove value by key (alias for remove)."""
        return self.remove(key)
    
    def clear(self) -> None:
        """Clear all data."""
        self._tree = [0.0] * (self.initial_size + 1)
        self._values.clear()
        self._indices.clear()
        self._reverse_indices.clear()
        self._next_index = 1
        self._size = 0
    
    def keys(self) -> Iterator[str]:
        """Get all keys in index order."""
        # Sort by index to maintain order
        sorted_items = sorted(self._indices.items(), key=lambda x: x[1])
        return (key for key, _ in sorted_items)
    
    def values(self) -> Iterator[Any]:
        """Get all values in index order."""
        for key in self.keys():
            yield self._values[key]
    
    def items(self) -> Iterator[tuple[str, Any]]:
        """Get all key-value pairs in index order."""
        for key in self.keys():
            yield (key, self._values[key])
    
    def __len__(self) -> int:
        """Get the number of items."""
        return self._size
    
    def to_native(self) -> List[Any]:
        """Convert to native Python list (preserving order)."""
        return [self._values[key] for key in self.keys()]
    
    @property
    def is_list(self) -> bool:
        """This behaves like a list (indexed)."""
        return True
    
    @property
    def is_dict(self) -> bool:
        """This can behave like a dict."""
        return True
    
    # ============================================================================
    # FENWICK TREE SPECIFIC OPERATIONS
    # ============================================================================
    
    def _resize_tree(self) -> None:
        """Resize the internal tree when needed."""
        old_size = len(self._tree)
        new_size = old_size * 2
        self._tree.extend([0.0] * (new_size - old_size))
    
    def update(self, index: int, value: float) -> None:
        """
        Update value at specific index (1-indexed).
        
        Sets the value at index to the new value by calculating delta.
        """
        if index < 1:
            raise ValueError(f"Fenwick Tree indices must be >= 1, got {index}")
        
        # Ensure tree is large enough
        while index >= len(self._tree):
            self._resize_tree()
        
        # Calculate delta from current value
        current = self._get_point_value(index)
        delta = value - current
        
        # Update tree with delta
        self._update_point(index, delta)
        
        # Store for retrieval
        key = str(index)
        if key not in self._indices:
            self._indices[key] = index
            self._reverse_indices[index] = key
            self._size += 1
        self._values[key] = value
    
    def _update_point(self, idx: int, delta: float) -> None:
        """Add delta to position idx (1-indexed)."""
        while idx < len(self._tree):
            self._tree[idx] += delta
            idx += idx & (-idx)  # Add lowest set bit
    
    def _get_point_value(self, idx: int) -> float:
        """Get value at position idx by computing range sum."""
        if idx == 1:
            return self._prefix_sum(1)
        else:
            return self._prefix_sum(idx) - self._prefix_sum(idx - 1)
    
    def _prefix_sum(self, idx: int) -> float:
        """Get prefix sum from 1 to idx (inclusive)."""
        if idx <= 0:
            return 0.0
        
        result = 0.0
        while idx > 0:
            result += self._tree[idx]
            idx -= idx & (-idx)  # Remove lowest set bit
        return result
    
    def prefix_sum(self, index: int) -> float:
        """
        Get prefix sum from 1 to index (1-indexed, inclusive).
        
        For Fenwick Tree, index 1 is the first element.
        To query sum of first 3 elements, use prefix_sum(3).
        """
        if index < 1:
            return 0.0
        
        # Ensure index is within bounds
        if index >= len(self._tree):
            index = len(self._tree) - 1
        
        return self._prefix_sum(index)
    
    def range_sum(self, left: int, right: int) -> float:
        """
        Get sum of elements in range [left, right] (1-indexed, inclusive).
        
        For Fenwick Tree, indices start at 1 (standard for BIT).
        To query sum of elements 2-5, use range_sum(2, 5).
        """
        if left > right or left < 1:
            return 0.0
        
        return self._prefix_sum(right) - self._prefix_sum(left - 1)
    
    def point_update(self, index: int, new_value: float) -> None:
        """Update value at index (0-indexed)."""
        if index < 0 or index >= self._size:
            return
        
        tree_idx = index + 1  # Convert to 1-indexed
        old_value = self._get_point_value(tree_idx)
        delta = new_value - old_value
        self._update_point(tree_idx, delta)
    
    def point_add(self, index: int, delta: float) -> None:
        """Add delta to value at index (0-indexed)."""
        if index < 0 or index >= self._size:
            return
        
        tree_idx = index + 1  # Convert to 1-indexed
        self._update_point(tree_idx, delta)
    
    def total_sum(self) -> float:
        """Get sum of all elements."""
        return self._prefix_sum(self._size)
    
    def find_prefix_sum_index(self, target_sum: float) -> int:
        """Find smallest index where prefix sum >= target_sum."""
        # Binary search using Fenwick tree properties
        idx = 0
        current_sum = 0.0
        
        # Start from the highest power of 2 <= tree size
        bit_mask = 1
        while bit_mask <= len(self._tree):
            bit_mask <<= 1
        bit_mask >>= 1
        
        while bit_mask > 0:
            next_idx = idx + bit_mask
            if next_idx < len(self._tree) and current_sum + self._tree[next_idx] < target_sum:
                idx = next_idx
                current_sum += self._tree[idx]
            bit_mask >>= 1
        
        return idx  # Returns 1-indexed, caller should adjust if needed
    
    def get_range_statistics(self, left: int, right: int) -> Dict[str, float]:
        """Get statistics for a range."""
        if left > right or right < 0 or left >= self._size:
            return {'sum': 0.0, 'count': 0, 'average': 0.0}
        
        left = max(0, left)
        right = min(self._size - 1, right)
        
        range_sum = self.range_sum(left, right)
        count = right - left + 1
        average = range_sum / count if count > 0 else 0.0
        
        return {
            'sum': range_sum,
            'count': count,
            'average': average
        }
    
    def bulk_update(self, updates: List[tuple[int, float]]) -> None:
        """Perform multiple point updates efficiently."""
        for index, value in updates:
            if 0 <= index < self._size:
                self.point_update(index, value)
    
    # ============================================================================
    # PERFORMANCE CHARACTERISTICS
    # ============================================================================
    
    @property
    def backend_info(self) -> Dict[str, Any]:
        """Get backend implementation info."""
        return {
            'strategy': 'FENWICK_TREE',
            'backend': 'Binary Indexed Tree',
            'indexing': '1-based internal, 0-based external',
            'complexity': {
                'prefix_sum': 'O(log n)',
                'range_sum': 'O(log n)',
                'point_update': 'O(log n)',
                'point_add': 'O(log n)',
                'space': 'O(n)'
            }
        }
    
    @property
    def metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        tree_utilization = self._size / max(1, len(self._tree) - 1) * 100
        
        return {
            'size': self._size,
            'tree_capacity': len(self._tree) - 1,
            'tree_utilization': f"{tree_utilization:.1f}%",
            'total_sum': self.total_sum(),
            'memory_usage': f"{len(self._tree) * 8 + self._size * 24} bytes (estimated)",
            'next_index': self._next_index
        }
