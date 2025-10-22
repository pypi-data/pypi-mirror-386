"""Integration tests - End-to-end scenarios"""

import pytest
from milvus_filter_expression import (
    FilterBuilder,
    to_expression,
    eq, ne, gt, gte, lt, lte, in_,
    like, is_null, is_not_null,
    or_, and_, not_, between
)

class TestFilterBuilder:
    """Test FilterBuilder integration"""
    
    def test_simple_chain(self):
        """Test simple method chaining"""
        fb = FilterBuilder().eq("age", 25).eq("status", "active")
        filters = fb.build()
        expr = to_expression(filters)
        
        assert "age == 25" in expr
        assert 'status == "active"' in expr
        assert " AND " in expr
    
    def test_complex_chain(self):
        """Test complex filter building"""
        fb = (FilterBuilder()
            .or_([{"category": "ml"}, {"category": "nlp"}])
            .between("score", 80, 100)
            .like("title", "%deep learning%")
            .is_not_null("author")
        )
        
        filters = fb.build()
        expr = to_expression(filters)
        
        assert " OR " in expr
        assert " AND " in expr
        assert "score >=" in expr
        assert "LIKE" in expr
        assert "IS NOT NULL" in expr
    
    def test_builder_clear(self):
        """Test clearing filters"""
        fb = FilterBuilder().eq("age", 25).eq("name", "test")
        fb.clear()
        
        assert fb.build() == {}
    
    def test_builder_reuse(self):
        """Test reusing FilterBuilder"""
        fb = FilterBuilder()
        
        # First use
        fb.eq("age", 25)
        filters1 = fb.build()
        
        # Clear and reuse
        fb.clear().eq("name", "test")
        filters2 = fb.build()
        
        assert filters1 == {"age": 25}
        assert filters2 == {"name": "test"}


class TestShortcuts:
    """Test shortcut functions"""
    
    def test_eq_shortcut(self):
        """Test eq shortcut"""
        filters = eq("age", 25)
        expr = to_expression(filters)
        assert expr == "age == 25"
    
    def test_between_shortcut(self):
        """Test between shortcut"""
        filters = between("age", 18, 65)
        expr = to_expression(filters)
        assert "age >=" in expr
        assert "age <=" in expr
    
    def test_or_shortcut(self):
        """Test or_ shortcut"""
        filters = or_({"status": "active"}, {"status": "pending"})
        expr = to_expression(filters)
        assert " OR " in expr
    
    def test_like_shortcut(self):
        """Test like shortcut"""
        filters = like("email", "%@gmail.com")
        expr = to_expression(filters)
        assert 'LIKE "%@gmail.com"' in expr
    
    def test_is_null_shortcut(self):
        """Test is_null shortcut"""
        filters = is_null("deleted_at")
        expr = to_expression(filters)
        assert "IS NULL" in expr


class TestRealWorldScenarios:
    """Test real-world use cases"""
    
    def test_user_search(self):
        """Search for active users with high scores"""
        filters = {
            "status": "active",
            "score": {"$gte": 80},
            "$or": [
                {"role": "admin"},
                {"role": "moderator"}
            ]
        }
        
        expr = to_expression(filters)
        
        assert 'status == "active"' in expr
        assert "score >= 80" in expr
        assert " OR " in expr
        assert " AND " in expr
    
    def test_document_search(self):
        """Search documents with complex filters"""
        fb = (FilterBuilder()
            .like("title", "%machine learning%")
            .between("page_count", 10, 500)
            .in_("category", ["tech", "science", "ai"])
            .is_not_null("author")
            .gte("published_year", 2020)
        )
        
        expr = to_expression(fb.build())
        
        assert "LIKE" in expr
        assert "IN" in expr
        assert "IS NOT NULL" in expr
        assert "published_year >=" in expr
    
    def test_ecommerce_product_filter(self):
        """E-commerce product filtering"""
        filters = {
            "$and": [
                {"price": {"$gte": 10, "$lte": 100}},
                {
                    "$or": [
                        {"category": "electronics"},
                        {"category": "books"}
                    ]
                },
                {"in_stock": True},
                {"rating": {"$gte": 4.0}}
            ]
        }
        
        expr = to_expression(filters)
        
        assert "price >=" in expr
        assert "price <=" in expr
        assert " OR " in expr
        assert " AND " in expr
        assert "in_stock == true" in expr
        assert "rating >=" in expr
    
    def test_log_filtering(self):
        """Filter system logs"""
        filters = {
            "level": {"$in": ["error", "critical"]},
            "timestamp": {"$gte": 1640000000},
            "$not": {"source": "test"}
        }
        
        expr = to_expression(filters)
        
        assert "IN" in expr
        assert "timestamp >=" in expr
        assert "NOT" in expr
    
    def test_content_moderation(self):
        """Content moderation filters"""
        fb = (FilterBuilder()
            .or_([
                {"status": "pending"},
                {"status": "flagged"}
            ])
            .is_null("reviewed_at")
            .gte("report_count", 3)
            .ne("auto_approved", True)
        )
        
        expr = to_expression(fb.build())
        
        assert " OR " in expr
        assert "IS NULL" in expr
        assert "report_count >=" in expr
        assert "auto_approved !=" in expr


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_empty_filters(self):
        """Test empty filter dict"""
        result = to_expression({})
        assert result is None
    
    def test_none_filters(self):
        """Test None filters"""
        result = to_expression(None)
        assert result is None
    
    def test_single_filter(self):
        """Test single filter (no AND needed)"""
        filters = {"age": 25}
        expr = to_expression(filters)
        assert expr == "age == 25"
        assert " AND " not in expr
    
    def test_empty_or(self):
        """Test empty OR list"""
        filters = {"$or": []}
        result = to_expression(filters)
        # Empty OR returns None (no valid expressions)
        assert result is None  # ✅ 수정
    
    def test_empty_in(self):
        """Test empty IN list"""
        filters = {"status": {"$in": []}}
        expr = to_expression(filters)
        assert "false" in expr
    
    def test_null_value(self):
        """Test None value in filter"""
        filters = {"deleted_at": None}
        expr = to_expression(filters)
        assert "IS NULL" in expr
    
    def test_boolean_values(self):
        """Test boolean true/false"""
        filters = {
            "is_active": True,
            "is_deleted": False
        }
        expr = to_expression(filters)
        assert "is_active == true" in expr
        assert "is_deleted == false" in expr
    
    def test_unsupported_operator(self):
        """Test unsupported operator raises error"""
        filters = {"age": {"$invalid": 25}}
        
        with pytest.raises(ValueError, match="Unsupported operator"):
            to_expression(filters)


class TestFieldPrefix:
    """Test field prefix functionality"""
    
    def test_simple_prefix(self):
        """Test simple field prefix"""
        filters = {"age": 25}
        expr = to_expression(filters, field_prefix="metadata.")
        assert expr == "metadata.age == 25"
    
    def test_prefix_with_complex_filters(self):
        """Test prefix with complex filters"""
        filters = {
            "age": {"$gte": 18},
            "status": "active"
        }
        expr = to_expression(filters, field_prefix="user.")
        
        assert "user.age >=" in expr
        assert 'user.status == "active"' in expr
    
    def test_prefix_with_or(self):
        """Test prefix with OR conditions"""
        filters = {
            "$or": [{"type": "a"}, {"type": "b"}]
        }
        expr = to_expression(filters, field_prefix="doc.")
        
        assert "doc.type" in expr


if __name__ == "__main__":
    pytest.main([__file__, "-v"])