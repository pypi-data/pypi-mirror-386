"""
Enhanced Strategy System for XWNode

This package implements the enhanced strategy system with xwsystem-inspired optimizations:
- 28 Node Modes (comprehensive data structure coverage)
- 16 Edge Modes (complete graph support)
- 12 Traits (cross-cutting capabilities)
- Flyweight pattern for memory optimization
- Intelligent pattern detection for AUTO mode selection
- Performance monitoring and optimization recommendations
- Comprehensive metrics and statistics tracking
- Lazy materialization and strategy management
- 100% backward compatibility with existing XWNode

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1.26
Generation Date: 07-Sep-2025
"""

from ..defs import (
    NodeMode, EdgeMode, QueryMode, NodeTrait, EdgeTrait, QueryTrait,
    AUTO, LEGACY, HASH_MAP, ORDERED_MAP, ORDERED_MAP_BALANCED,
    ARRAY_LIST, LINKED_LIST, TRIE, RADIX_TRIE, PATRICIA,
    HEAP, SET_HASH, SET_TREE, BLOOM_FILTER, CUCKOO_HASH,
    BITMAP, BITSET_DYNAMIC, ROARING_BITMAP, B_TREE, B_PLUS_TREE,
    LSM_TREE, PERSISTENT_TREE, COW_TREE, UNION_FIND, SEGMENT_TREE, FENWICK_TREE,
    SUFFIX_ARRAY, AHO_CORASICK, COUNT_MIN_SKETCH, HYPERLOGLOG,
    ADJ_LIST, DYNAMIC_ADJ_LIST, ADJ_MATRIX, BLOCK_ADJ_MATRIX,
    CSR, CSC, COO, BIDIR_WRAPPER, TEMPORAL_EDGESET,
    HYPEREDGE_SET, EDGE_PROPERTY_STORE, R_TREE, QUADTREE, OCTREE,
    SQL, HIVEQL, PIG, CQL, N1QL, EQL, KQL, FLUX, DATALOG,
    GRAPHQL, SPARQL, GREMLIN, CYPHER,
    LINQ, JSONIQ, JMESPATH, XQUERY, XPATH,
    XML_QUERY, JSON_QUERY
)

# Node strategies
from .nodes.base import ANodeStrategy, ANodeLinearStrategy, ANodeTreeStrategy, ANodeGraphStrategy, ANodeMatrixStrategy
from .nodes.array_list import ArrayListStrategy
from .nodes.linked_list import LinkedListStrategy
from .nodes.stack import StackStrategy
from .nodes.queue import QueueStrategy
from .nodes.priority_queue import PriorityQueueStrategy
from .nodes.deque import DequeStrategy
from .nodes.trie import TrieStrategy
from .nodes.heap import HeapStrategy
from .nodes.aho_corasick import AhoCorasickStrategy
from .nodes.hash_map import HashMapStrategy
from .nodes.union_find import UnionFindStrategy
from .nodes.adjacency_list import AdjacencyListStrategy
from .nodes.sparse_matrix import SparseMatrixStrategy

# Edge strategies  
from .edges.base import AEdgeStrategy, ALinearEdgeStrategy, ATreeEdgeStrategy, AGraphEdgeStrategy
from .edges.adj_list import AdjListStrategy
from .edges.adj_matrix import AdjMatrixStrategy

from ..common.patterns.registry import StrategyRegistry, get_registry, register_node_strategy, register_edge_strategy
from ..common.patterns.advisor import StrategyAdvisor, get_advisor
from ..common.management.manager import StrategyManager

# Enhanced components
from ..common.patterns.flyweight import StrategyFlyweight, get_flyweight, get_flyweight_stats, clear_flyweight_cache
from ..common.monitoring.pattern_detector import DataPatternDetector, get_detector, analyze_data_patterns, recommend_strategy
from ..common.monitoring.performance_monitor import StrategyPerformanceMonitor, get_monitor, record_operation, get_performance_summary
from ..common.monitoring.metrics import StrategyMetricsCollector, get_metrics_collector, collect_comprehensive_metrics, get_metrics_summary

__all__ = [
    # Types and enums
    'NodeMode', 'EdgeMode', 'QueryMode', 'NodeTrait', 'EdgeTrait', 'QueryTrait',
    'AUTO', 'LEGACY', 'HASH_MAP', 'ORDERED_MAP', 'ORDERED_MAP_BALANCED',
    'ARRAY_LIST', 'LINKED_LIST', 'TRIE', 'RADIX_TRIE', 'PATRICIA',
    'HEAP', 'SET_HASH', 'SET_TREE', 'BLOOM_FILTER', 'CUCKOO_HASH',
    'BITMAP', 'BITSET_DYNAMIC', 'ROARING_BITMAP', 'B_TREE', 'B_PLUS_TREE',
    'LSM_TREE', 'PERSISTENT_TREE', 'COW_TREE', 'UNION_FIND', 'SEGMENT_TREE', 'FENWICK_TREE',
    'SUFFIX_ARRAY', 'AHO_CORASICK', 'COUNT_MIN_SKETCH', 'HYPERLOGLOG',
    'ADJ_LIST', 'DYNAMIC_ADJ_LIST', 'ADJ_MATRIX', 'BLOCK_ADJ_MATRIX',
    'CSR', 'CSC', 'COO', 'BIDIR_WRAPPER', 'TEMPORAL_EDGESET',
    'HYPEREDGE_SET', 'EDGE_PROPERTY_STORE', 'R_TREE', 'QUADTREE', 'OCTREE',
    'SQL', 'HIVEQL', 'PIG', 'CQL', 'N1QL', 'EQL', 'KQL', 'FLUX', 'DATALOG',
    'GRAPHQL', 'SPARQL', 'GREMLIN', 'CYPHER',
    'LINQ', 'JSONIQ', 'JMESPATH', 'XQUERY', 'XPATH',
    'XML_QUERY', 'JSON_QUERY',
    
    # Node strategy base classes
    'ANodeStrategy', 'ANodeLinearStrategy', 'ANodeTreeStrategy', 'ANodeGraphStrategy', 'ANodeMatrixStrategy',
    
    # Node strategy implementations
    'ArrayListStrategy', 'LinkedListStrategy', 'StackStrategy', 'QueueStrategy',
    'PriorityQueueStrategy', 'DequeStrategy', 'TrieStrategy', 'HeapStrategy',
    'AhoCorasickStrategy', 'HashMapStrategy', 'UnionFindStrategy',
    'AdjacencyListStrategy', 'SparseMatrixStrategy',
    
    # Edge strategy base classes
    'AEdgeStrategy', 'ALinearEdgeStrategy', 'ATreeEdgeStrategy', 'AGraphEdgeStrategy',
    
    # Edge strategy implementations
    'AdjListStrategy', 'AdjMatrixStrategy',
    
    # Strategy management
    'StrategyRegistry', 'get_registry', 'register_node_strategy', 'register_edge_strategy',
    'StrategyAdvisor', 'get_advisor',
    'StrategyManager',
    
    # Enhanced components
    'StrategyFlyweight', 'get_flyweight', 'get_flyweight_stats', 'clear_flyweight_cache',
    'DataPatternDetector', 'get_detector', 'analyze_data_patterns', 'recommend_strategy',
    'StrategyPerformanceMonitor', 'get_monitor', 'record_operation', 'get_performance_summary',
    'StrategyMetricsCollector', 'get_metrics_collector', 'collect_comprehensive_metrics', 'get_metrics_summary'
]
