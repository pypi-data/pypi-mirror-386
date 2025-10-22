"""Converter tests (Milvus official syntax)"""

import pytest
from milvus_filter_expression import to_expression

def test_simple_equality():
    """Test simple equality comparisons"""
    assert to_expression({"age": 25}) == 'age == 25'
    assert to_expression({"name": "test"}) == 'name == "test"'

def test_comparison():
    """Test comparison operators"""
    assert to_expression({"age": {"$gte": 18}}) == 'age >= 18'
    assert to_expression({"score": {"$gt": 80, "$lte": 100}}) == \
        '(score > 80) AND (score <= 100)'

def test_or_operator():
    """Test OR operator"""
    filters = {"$or": [{"status": "active"}, {"status": "pending"}]}
    expr = to_expression(filters)
    assert 'status == "active"' in expr
    assert 'status == "pending"' in expr
    assert " OR " in expr

def test_like_operator():
    """Test LIKE pattern matching"""
    # Starts with
    filters = {"name": {"$like": "test%"}}
    assert to_expression(filters) == 'name LIKE "test%"'
    
    # Ends with
    filters = {"name": {"$like": "%test"}}
    assert to_expression(filters) == 'name LIKE "%test"'
    
    # Contains
    filters = {"name": {"$like": "%test%"}}
    assert to_expression(filters) == 'name LIKE "%test%"'

def test_null_operators():
    """Test NULL operators"""
    # IS NULL
    filters = {"deleted_at": {"$is_null": True}}
    assert to_expression(filters) == 'deleted_at IS NULL'
    
    # IS NOT NULL
    filters = {"created_at": {"$is_not_null": True}}
    assert to_expression(filters) == 'created_at IS NOT NULL'
    
    # None value
    filters = {"field": None}
    assert to_expression(filters) == 'field IS NULL'

def test_in_operator():
    """Test IN operator"""
    filters = {"status": {"$in": ["active", "pending", "review"]}}
    expr = to_expression(filters)
    assert "IN" in expr
    assert '"active"' in expr

def test_mixed_filters():
    """Test mixed filter conditions"""
    filters = {
        "$or": [{"category": "ml"}, {"category": "nlp"}],
        "score": {"$gte": 80},
        "status": "active"
    }
    expr = to_expression(filters)
    
    assert " OR " in expr
    assert " AND " in expr
    assert 'category == "ml"' in expr or 'category == "nlp"' in expr
    assert "score >=" in expr
    assert 'status == "active"' in expr

def test_nested_logic():
    """Test nested logical operators"""
    filters = {
        "$and": [
            {"$or": [{"status": "active"}, {"status": "pending"}]},
            {"score": {"$gte": 80}}
        ]
    }
    expr = to_expression(filters)
    assert " AND " in expr
    assert " OR " in expr

def test_not_operator():
    """Test NOT operator"""
    filters = {"$not": {"status": "deleted"}}
    expr = to_expression(filters)
    assert "NOT" in expr

def test_field_prefix():
    """Test field prefix support"""
    filters = {"age": 25}
    expr = to_expression(filters, field_prefix="metadata.")
    assert expr == 'metadata.age == 25'