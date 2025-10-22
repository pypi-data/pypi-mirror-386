"""
Milvus Filter - Type-safe, MongoDB-style filter builder for Milvus

Examples:
    # Dictionary style (most flexible)
    >>> filters = {"page": 5, "$or": [{"category": "ml"}, {"category": "nlp"}]}
    
    # Builder style (type-safe)
    >>> from milvus_filter import FilterBuilder
    >>> fb = FilterBuilder().eq("page", 5).or_([{"category": "ml"}, {"category": "nlp"}])
    >>> filters = fb.build()
    
    # Shortcut style (quick)
    >>> from milvus_filter import eq, or_
    >>> filters = {**eq("page", 5), **or_({"category": "ml"}, {"category": "nlp"})}
    
    # Convert to Milvus expression
    >>> from milvus_filter import to_expression
    >>> expr = to_expression(filters)
    >>> # 'page == 5 AND ...'
"""

from .builder import FilterBuilder
from .converter import MilvusFilterConverter
from .operators import (
    ComparisonOperator,
    LogicalOperator,
    NullOperator,
    ArithmeticOperator
)
from .shortcuts import (
    eq, ne, gt, gte, lt, lte, in_,
    like, is_null, is_not_null,
    or_, and_, not_, between
)

__version__ = "0.1.0"

__all__ = [
    # Main classes
    "FilterBuilder",
    "MilvusFilterConverter",
    
    # Enums
    "ComparisonOperator",
    "LogicalOperator",
    "NullOperator",
    "ArithmeticOperator",
    
    # Shortcuts
    "eq", "ne", "gt", "gte", "lt", "lte", "in_",
    "like", "is_null", "is_not_null",
    "or_", "and_", "not_", "between",
    
    # Main function
    "to_expression",
]

def to_expression(filters: dict, field_prefix: str = "") -> str:
    """
    Convert filter dictionary to Milvus expression string
    
    Args:
        filters: MongoDB-style filter dictionary
        field_prefix: Optional field prefix (e.g., "metadata.")
        
    Returns:
        Milvus expression string
        
    Examples:
        >>> to_expression({"age": 25})
        'age == 25'
        
        >>> to_expression({"$or": [{"age": 18}, {"age": 21}]})
        '(age == 18) OR (age == 21)'
        
        >>> to_expression({"name": {"$like": "test%"}})
        'name LIKE "test%"'
    """
    return MilvusFilterConverter.convert(filters, field_prefix)