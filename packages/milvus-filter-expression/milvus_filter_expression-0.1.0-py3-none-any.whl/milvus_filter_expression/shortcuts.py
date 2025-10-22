"""Convenience functions for quick filter creation"""

from typing import Dict, Any, List, Union

def eq(key: str, value: Any) -> Dict[str, Any]:
    """Quick equality filter"""
    return {key: value}

def ne(key: str, value: Any) -> Dict[str, Any]:
    """Quick not-equal filter"""
    return {key: {"$ne": value}}

def gt(key: str, value: Union[int, float]) -> Dict[str, Any]:
    """Quick greater-than filter"""
    return {key: {"$gt": value}}

def gte(key: str, value: Union[int, float]) -> Dict[str, Any]:
    """Quick greater-than-or-equal filter"""
    return {key: {"$gte": value}}

def lt(key: str, value: Union[int, float]) -> Dict[str, Any]:
    """Quick less-than filter"""
    return {key: {"$lt": value}}

def lte(key: str, value: Union[int, float]) -> Dict[str, Any]:
    """Quick less-than-or-equal filter"""
    return {key: {"$lte": value}}

def in_(key: str, values: List[Any]) -> Dict[str, Any]:
    """Quick IN filter"""
    return {key: {"$in": values}}

def like(key: str, pattern: str) -> Dict[str, Any]:
    """Quick LIKE pattern filter"""
    return {key: {"$like": pattern}}

def is_null(key: str) -> Dict[str, Any]:
    """Quick IS NULL filter"""
    return {key: {"$is_null": True}}

def is_not_null(key: str) -> Dict[str, Any]:
    """Quick IS NOT NULL filter"""
    return {key: {"$is_not_null": True}}

def or_(*conditions: Dict[str, Any]) -> Dict[str, Any]:
    """Quick OR filter"""
    return {"$or": list(conditions)}

def and_(*conditions: Dict[str, Any]) -> Dict[str, Any]:
    """Quick AND filter"""
    return {"$and": list(conditions)}

def not_(condition: Dict[str, Any]) -> Dict[str, Any]:
    """Quick NOT filter"""
    return {"$not": condition}

def between(key: str, min_val: Union[int, float], max_val: Union[int, float]) -> Dict[str, Any]:
    """Quick range filter"""
    return {key: {"$gte": min_val, "$lte": max_val}}

__all__ = [
    "eq", "ne", "gt", "gte", "lt", "lte", "in_",
    "like", "is_null", "is_not_null",
    "or_", "and_", "not_", "between"
]