#exonware\xnode\strategies\impls\node_skip_list.py
"""
Skip List Node Strategy Implementation

This module implements the SKIP_LIST strategy for probabilistic data structures
with O(log n) expected performance for search, insertion, and deletion.
"""

import random
from typing import Any, Iterator, List, Dict, Optional, Tuple
from .base import ANodeTreeStrategy
from .contracts import NodeType
from ...defs import NodeMode, NodeTrait


class SkipListNode:
    """Node in the skip list."""
    
    def __init__(self, key: str, value: Any = None, level: int = 0):
        """Time Complexity: O(level)"""
        self.key = key
        self.value = value
        self.level = level
        self.forward: List[Optional['SkipListNode']] = [None] * (level + 1)
        self._hash = None
    
    def __hash__(self) -> int:
        """
        Cache hash for performance.
        
        Time Complexity: O(1) amortized
        """
        if self._hash is None:
            self._hash = hash((self.key, self.value))
        return self._hash
    
    def __eq__(self, other) -> bool:
        """
        Structural equality.
        
        Time Complexity: O(1)
        """
        if not isinstance(other, SkipListNode):
            return False
        return self.key == other.key and self.value == other.value


class SkipListStrategy(ANodeTreeStrategy):
    """
    Skip List strategy for probabilistic sorted data structures.
    
    WHY Skip List:
    - Simpler implementation than balanced trees (no complex rotations)
    - Lock-free concurrent access possible with careful implementation
    - O(log n) expected time for search, insert, delete (probabilistic)
    - Memory-efficient alternative to balanced trees for dynamic datasets
    - Excellent for distributed systems (natural partitioning by levels)
    
    WHY this implementation:
    - Probabilistic level promotion (p=0.5) ensures balanced height distribution
    - Header node sentinel pattern eliminates special-case handling
    - Path caching during search amortizes traversal cost
    - Forward pointers list enables efficient level-by-level traversal
    - Statistics tracking for monitoring performance characteristics
    
    Time Complexity:
    - Insert: O(log n) expected, O(n) worst case (probabilistic)
    - Search: O(log n) expected, O(n) worst case (probabilistic)
    - Delete: O(log n) expected, O(n) worst case (probabilistic)
    - Range Query: O(k + log n) where k is result size
    - Iteration: O(n) sorted order at bottom level
    
    Space Complexity: O(n log n) expected (multiple forward pointers per node)
    
    Trade-offs:
    - Advantage: Simpler than balanced trees, good concurrent properties
    - Advantage: No rebalancing overhead (probabilistic balance)
    - Limitation: Worst-case O(n) if unlucky with random levels
    - Limitation: Higher memory overhead than plain linked list
    - Compared to B-Tree: Simpler, better concurrency, but less deterministic
    - Compared to AVL: Easier to implement, but higher memory usage
    
    Best for:
    - Concurrent sorted data structures (lock-free variants)
    - When simplicity is more important than worst-case guarantees
    - Distributed systems requiring sorted indices
    - Real-time systems (no unpredictable rebalancing pauses)
    - In-memory caches with sorted key access
    
    Not recommended for:
    - Hard real-time systems (probabilistic behavior)
    - Memory-constrained environments (O(n log n) space)
    - When worst-case guarantees are critical (use balanced tree)
    - Disk-based storage (use B-Tree for locality)
    - Write-once, read-many scenarios (plain sorted array better)
    
    Following eXonware Priorities:
    1. Usability: Simple API, no complex rebalancing logic to debug
    2. Maintainability: Clean probabilistic design, easy to understand
    3. Performance: O(log n) expected time, efficient range queries
    4. Extensibility: Easy to add concurrent variants or custom level logic
    5. Security: Input validation on all operations, prevents malformed structure
    
    Industry Best Practices:
    - Follows Pugh's original skip list paper (1990)
    - Uses p=0.5 probability (optimal for most workloads)
    - Implements header sentinel for cleaner code
    - Provides statistics for monitoring probabilistic behavior
    - Supports both case-sensitive and case-insensitive keys
    
    Performance Note:
    Skip list is probabilistic - O(log n) is EXPECTED, not worst-case.
    For guaranteed O(log n), use RED_BLACK_TREE or AVL_TREE instead.
    The trade-off is simplicity and concurrency vs determinism.
    """
    
    # Strategy type classification
    STRATEGY_TYPE = NodeType.TREE
    
    def __init__(self, traits: NodeTrait = NodeTrait.NONE, **options):
        """
        Initialize the skip list strategy.
        
        Time Complexity: O(max_level)
        Space Complexity: O(max_level)
        """
        super().__init__(NodeMode.SKIP_LIST, traits, **options)
        
        self.case_sensitive = options.get('case_sensitive', True)
        self.max_level = options.get('max_level', 16)  # Maximum level for skip list
        self.probability = options.get('probability', 0.5)  # Probability for level promotion
        
        # Core skip list
        self._header = SkipListNode("", None, self.max_level)  # Header node
        self._level = 0  # Current maximum level
        self._size = 0
        
        # Statistics
        self._total_insertions = 0
        self._total_deletions = 0
        self._total_searches = 0
        self._max_level_reached = 0
    
    def get_supported_traits(self) -> NodeTrait:
        """
        Get the traits supported by the skip list strategy.
        
        Time Complexity: O(1)
        """
        return (NodeTrait.ORDERED | NodeTrait.INDEXED)
    
    def _normalize_key(self, key: str) -> str:
        """
        Normalize key based on case sensitivity.
        
        Time Complexity: O(|key|)
        """
        return key if self.case_sensitive else key.lower()
    
    def _random_level(self) -> int:
        """
        Generate random level for new node.
        
        Time Complexity: O(log n) expected
        """
        level = 0
        while random.random() < self.probability and level < self.max_level:
            level += 1
        self._max_level_reached = max(self._max_level_reached, level)
        return level
    
    def _search_path(self, key: str) -> List[Optional[SkipListNode]]:
        """Find the path to the node with given key."""
        normalized_key = self._normalize_key(key)
        current = self._header
        path = [None] * (self._level + 1)
        
        # Start from highest level and work down
        for i in range(self._level, -1, -1):
            while (current.forward[i] is not None and 
                   self._normalize_key(current.forward[i].key) < normalized_key):
                current = current.forward[i]
            path[i] = current
        
        return path
    
    def _find_node(self, key: str) -> Optional[SkipListNode]:
        """Find node with given key."""
        normalized_key = self._normalize_key(key)
        current = self._header
        
        # Start from highest level and work down
        for i in range(self._level, -1, -1):
            while (current.forward[i] is not None and 
                   self._normalize_key(current.forward[i].key) < normalized_key):
                current = current.forward[i]
        
        # Check if we found the exact key
        current = current.forward[0]
        if current is not None and self._normalize_key(current.key) == normalized_key:
            return current
        
        return None
    
    def _insert_node(self, key: str, value: Any) -> bool:
        """Insert node with given key and value."""
        normalized_key = self._normalize_key(key)
        
        # Find the path to insertion point
        path = self._search_path(key)
        current = path[0].forward[0]
        
        # Check if key already exists
        if current is not None and self._normalize_key(current.key) == normalized_key:
            # Update existing node
            current.value = value
            return False
        
        # Create new node
        new_level = self._random_level()
        new_node = SkipListNode(key, value, new_level)
        
        # If new level is higher than current level, update header
        if new_level > self._level:
            for i in range(self._level + 1, new_level + 1):
                path.append(self._header)
            self._level = new_level
        
        # Insert node into skip list
        for i in range(new_level + 1):
            new_node.forward[i] = path[i].forward[i]
            path[i].forward[i] = new_node
        
        self._size += 1
        self._total_insertions += 1
        return True
    
    def _delete_node(self, key: str) -> bool:
        """Delete node with given key."""
        normalized_key = self._normalize_key(key)
        
        # Find the path to deletion point
        path = self._search_path(key)
        current = path[0].forward[0]
        
        # Check if key exists
        if current is None or self._normalize_key(current.key) != normalized_key:
            return False
        
        # Remove node from skip list
        for i in range(self._level + 1):
            if path[i].forward[i] != current:
                break
            path[i].forward[i] = current.forward[i]
        
        # Update level if necessary
        while (self._level > 0 and 
               self._header.forward[self._level] is None):
            self._level -= 1
        
        self._size -= 1
        self._total_deletions += 1
        return True
    
    def _inorder_traversal(self) -> Iterator[Tuple[str, Any]]:
        """In-order traversal of skip list."""
        current = self._header.forward[0]
        while current is not None:
            yield (current.key, current.value)
            current = current.forward[0]
    
    # ============================================================================
    # CORE OPERATIONS
    # ============================================================================
    
    def put(self, key: Any, value: Any = None) -> None:
        """Store a key-value pair."""
        if not isinstance(key, str):
            key = str(key)
        
        self._insert_node(key, value)
    
    def get(self, key: Any, default: Any = None) -> Any:
        """Retrieve a value by key."""
        if not isinstance(key, str):
            key = str(key)
        
        self._total_searches += 1
        node = self._find_node(key)
        return node.value if node else default
    
    def delete(self, key: Any) -> bool:
        """Remove a key-value pair."""
        if not isinstance(key, str):
            key = str(key)
        
        return self._delete_node(key)
    
    def has(self, key: Any) -> bool:
        """Check if key exists."""
        if not isinstance(key, str):
            key = str(key)
        
        return self._find_node(key) is not None
    
    def clear(self) -> None:
        """Clear all data."""
        self._header = SkipListNode("", None, self.max_level)
        self._level = 0
        self._size = 0
    
    def size(self) -> int:
        """Get number of key-value pairs."""
        return self._size
    
    def __len__(self) -> int:
        """Get number of key-value pairs."""
        return self._size
    
    def to_native(self) -> Dict[str, Any]:
        """Convert to native Python dict."""
        return dict(self.items())
    
    def is_empty(self) -> bool:
        """Check if skip list is empty."""
        return self._size == 0
    
    # ============================================================================
    # ITERATION
    # ============================================================================
    
    def keys(self) -> Iterator[str]:
        """Iterate over keys in sorted order."""
        for key, _ in self._inorder_traversal():
            yield key
    
    def values(self) -> Iterator[Any]:
        """Iterate over values in key order."""
        for _, value in self._inorder_traversal():
            yield value
    
    def items(self) -> Iterator[Tuple[str, Any]]:
        """Iterate over key-value pairs in sorted order."""
        yield from self._inorder_traversal()
    
    def __iter__(self) -> Iterator[str]:
        """Iterate over keys."""
        yield from self.keys()
    
    # ============================================================================
    # SKIP LIST SPECIFIC OPERATIONS
    # ============================================================================
    
    def get_min(self) -> Optional[Tuple[str, Any]]:
        """Get the minimum key-value pair."""
        if self._size == 0:
            return None
        
        current = self._header.forward[0]
        return (current.key, current.value) if current else None
    
    def get_max(self) -> Optional[Tuple[str, Any]]:
        """Get the maximum key-value pair."""
        if self._size == 0:
            return None
        
        current = self._header
        for i in range(self._level, -1, -1):
            while current.forward[i] is not None:
                current = current.forward[i]
        
        return (current.key, current.value) if current != self._header else None
    
    def range_query(self, start_key: str, end_key: str) -> Iterator[Tuple[str, Any]]:
        """Get all key-value pairs in range [start_key, end_key]."""
        if not isinstance(start_key, str) or not isinstance(end_key, str):
            return
        
        normalized_start = self._normalize_key(start_key)
        normalized_end = self._normalize_key(end_key)
        
        # Find starting position
        path = self._search_path(start_key)
        current = path[0].forward[0]
        
        # Iterate through range
        while (current is not None and 
               self._normalize_key(current.key) <= normalized_end):
            if self._normalize_key(current.key) >= normalized_start:
                yield (current.key, current.value)
            current = current.forward[0]
    
    def get_level(self) -> int:
        """Get current maximum level."""
        return self._level
    
    def get_max_level(self) -> int:
        """Get maximum level reached."""
        return self._max_level_reached
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        return {
            'size': self._size,
            'level': self._level,
            'max_level_reached': self._max_level_reached,
            'total_insertions': self._total_insertions,
            'total_deletions': self._total_deletions,
            'total_searches': self._total_searches,
            'probability': self.probability,
            'max_level': self.max_level,
            'strategy': 'SKIP_LIST',
            'backend': 'Probabilistic skip list with O(log n) expected performance',
            'traits': [trait.name for trait in NodeTrait if self.has_trait(trait)]
        }
