"""FilterBuilder tests"""

import pytest
from milvus_filter_expression import FilterBuilder

def test_simple_build():
    """Test simple filter building"""
    fb = FilterBuilder().eq("page", 5)
    assert fb.build() == {"page": 5}

def test_chaining():
    """Test method chaining"""
    fb = FilterBuilder().eq("page", 5).gte("score", 0.8)
    result = fb.build()
    assert result["page"] == 5
    assert result["score"] == {"$gte": 0.8}

def test_range():
    """Test range filter"""
    fb = FilterBuilder().between("page", 10, 20)
    result = fb.build()
    assert result["page"]["$gte"] == 10
    assert result["page"]["$lte"] == 20

def test_or():
    """Test OR condition"""
    fb = FilterBuilder().or_([{"page": 5}, {"page": 10}])
    result = fb.build()
    assert "$or" in result
    assert len(result["$or"]) == 2

def test_like():
    """Test LIKE pattern"""
    fb = FilterBuilder().like("name", "test%")
    result = fb.build()
    assert result["name"]["$like"] == "test%"

def test_null_operators():
    """Test NULL operators"""
    fb = FilterBuilder().is_null("deleted_at").is_not_null("created_at")
    result = fb.build()
    assert result["deleted_at"]["$is_null"] == True
    assert result["created_at"]["$is_not_null"] == True