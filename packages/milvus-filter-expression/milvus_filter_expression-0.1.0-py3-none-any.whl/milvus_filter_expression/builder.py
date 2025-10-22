from typing import Any, Dict, List, Union


class FilterBuilder:
    """
    Fluent API for building Milvus Filter

    Examples:
        # Basic comparision
        >>> fb = FilterBuilder().eq("age", 25).gte("score", 80)

        # LIKE pattern
        >>> fb = FilterBuilder().like("name", "test%")

        # NULL check
        >>> fb = FilterBuilder().is_null("deleted_at")

        # OR condition
        >>> fb = FilterBuilder().or_([{"status": "active"}, {"status": "pending"}])
    """

    def __init__(self) -> None:
        self.filters: Dict[str, Any] = {}

    def eq(self, key: str, value: Any) -> 'FilterBuilder':
        """Equal (==)"""
        self.filters[key] = value
        return self
    
    def ne(self, key: str, value: Any) -> 'FilterBuilder':
        """Not equal (!=)"""
        self.filters[key] = {"$ne": value}
        return self

    def gt(self, key: str, value: Union[int, float]) -> 'FilterBuilder':
        """Greater than (>)"""
        if key in self.filters and isinstance(self.filters[key], dict):
            self.filters[key]['$gt'] = value
        else:
            self.filters[key] = {"$gt": value}
        return self

    def gte(self, key: str, value: Union[int, float]) -> 'FilterBuilder':
        """Greater than or equal (>=)"""
        if key in self.filters and isinstance(self.filters[key], dict):
            self.filters[key]["$gte"] = value
        else:
            self.filters[key] = {"$gte": value}
        return self
    
    def lt(self, key: str, value: Union[int, float]) -> 'FilterBuilder':
        """Less than (<)"""
        if key in self.filters and isinstance(self.filters[key], dict):
            self.filters[key]["$lt"] = value
        else:
            self.filters[key] = {"$lt": value}
        return self
    
    def lte(self, key: str, value: Union[int, float]) -> 'FilterBuilder':
        """Less than or equal (<=)"""
        if key in self.filters and isinstance(self.filters[key], dict):
            self.filters[key]["$lte"] = value
        else:
            self.filters[key] = {"$lte": value}
        return self
    
    def in_(self, key: str, values: List[Any]) -> 'FilterBuilder':
        """IN operator"""
        self.filters[key] = {"$in": values}
        return self
    
    def between(
        self, 
        key: str, 
        min_val: Union[int, float], 
        max_val: Union[int, float]
    ) -> 'FilterBuilder':
        """Range (inclusive)"""
        self.filters[key] = {"$gte": min_val, "$lte": max_val}
        return self
    
    def like(self, key: str, pattern: str) -> 'FilterBuilder':
        """LIKE pattern matching"""
        self.filters[key] = {"$like": pattern}
        return self
    
    def is_null(self, key: str) -> 'FilterBuilder':
        """IS NULL"""
        self.filters[key] = {"$is_null": True}
        return self
    
    def is_not_null(self, key: str) -> 'FilterBuilder':
        """IS NOT NULL"""
        self.filters[key] = {"$is_not_null": True}
        return self
    
    def or_(self, conditions: List[Dict[str, Any]]) -> 'FilterBuilder':
        """OR condition"""
        self.filters["$or"] = conditions
        return self
    
    def and_(self, conditions: List[Dict[str, Any]]) -> 'FilterBuilder':
        """AND condition (explicit)"""
        self.filters["$and"] = conditions
        return self
    
    def not_(self, condition: Dict[str, Any]) -> 'FilterBuilder':
        """NOT condition"""
        self.filters["$not"] = condition
        return self
    
    def build(self) -> Dict[str, Any]:
        """Build and return the filter dictionary"""
        return self.filters
    
    def clear(self) -> 'FilterBuilder':
        """Clear all filters"""
        self.filters = {}
        return self
    
    def __repr__(self) -> str:
        return f"FilterBuilder({self.filters})"

__all__ = ["FilterBuilder"]