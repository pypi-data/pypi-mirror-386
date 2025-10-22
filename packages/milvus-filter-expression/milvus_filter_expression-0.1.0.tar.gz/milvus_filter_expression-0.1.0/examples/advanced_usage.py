"""Advanced filter examples with real-world scenarios"""

from milvus_filter_expression import FilterBuilder, to_expression, or_, and_, between

print("=" * 80)
print("Advanced Filter Examples")
print("=" * 80)

# Scenario 1: E-commerce Product Search
print("\n1. E-commerce Product Search")
print("-" * 40)
print("Find electronics under $1000, in stock, with 4+ stars")

filters = {
    "category": "electronics",
    "price": {"$lte": 1000},
    "in_stock": True,
    "rating": {"$gte": 4.0}
}

expr = to_expression(filters)
print(f"Expression:\n  {expr}\n")

# Scenario 2: User Activity Analysis
print("2. User Activity Analysis")
print("-" * 40)
print("Active premium users who logged in recently")

fb = (FilterBuilder()
    .eq("subscription", "premium")
    .eq("is_active", True)
    .gte("last_login_timestamp", 1700000000)
    .gt("total_purchases", 0)
)

expr = to_expression(fb.build())
print(f"Expression:\n  {expr}\n")

# Scenario 3: Content Moderation
print("3. Content Moderation")
print("-" * 40)
print("Flagged content that needs review")

filters = {
    "$or": [
        {"status": "flagged"},
        {"report_count": {"$gte": 3}}
    ],
    "reviewed_at": {"$is_null": True},
    "content_type": {"$in": ["post", "comment", "reply"]}
}

expr = to_expression(filters)
print(f"Expression:\n  {expr}\n")

# Scenario 4: Document Search with Relevance
print("4. Document Search with Relevance")
print("-" * 40)
print("Recent ML papers with high citation count")

fb = (FilterBuilder()
    .like("title", "%machine learning%")
    .gte("published_year", 2020)
    .gte("citation_count", 50)
    .in_("venue", ["NeurIPS", "ICML", "ICLR"])
    .is_not_null("abstract")
)

expr = to_expression(fb.build())
print(f"Expression:\n  {expr}\n")

# Scenario 5: Multi-tenant Data Filtering
print("5. Multi-tenant Data Filtering")
print("-" * 40)
print("Tenant-specific data with access control")

filters = {
    "tenant_id": "tenant_123",
    "$or": [
        {"visibility": "public"},
        {
            "$and": [
                {"visibility": "private"},
                {"owner_id": "user_456"}
            ]
        }
    ],
    "deleted_at": {"$is_null": True}
}

expr = to_expression(filters)
print(f"Expression:\n  {expr}\n")

# Scenario 6: Time-based Filtering
print("6. Time-based Filtering")
print("-" * 40)
print("Events in the last 24 hours, not processed")

current_time = 1700000000  # Example timestamp

filters = {
    "event_type": {"$in": ["error", "warning", "critical"]},
    "timestamp": {"$gte": current_time - 86400},  # 24 hours
    "processed": False,
    "severity": {"$gte": 3}
}

expr = to_expression(filters)
print(f"Expression:\n  {expr}\n")

# Scenario 7: Geospatial-like Filtering
print("7. Range-based Filtering (e.g., nearby items)")
print("-" * 40)
print("Items within price and rating range")

fb = (FilterBuilder()
    .between("price", 50, 200)
    .between("rating", 4.0, 5.0)
    .eq("available", True)
    .ne("condition", "damaged")
)

expr = to_expression(fb.build())
print(f"Expression:\n  {expr}\n")

# Scenario 8: Complex Nested Logic
print("8. Complex Nested Logic")
print("-" * 40)
print("Advanced user segmentation")

filters = {
    "$and": [
        {
            "$or": [
                {"user_type": "premium"},
                {"lifetime_value": {"$gte": 1000}}
            ]
        },
        {
            "$or": [
                {"engagement_score": {"$gte": 80}},
                {"active_days": {"$gte": 200}}
            ]
        },
        {"churn_risk": {"$lt": 0.3}}
    ]
}

expr = to_expression(filters)
print(f"Expression:\n  {expr}\n")

# Scenario 9: Data Quality Filtering
print("9. Data Quality Filtering")
print("-" * 40)
print("Valid, complete records only")

fb = (FilterBuilder()
    .is_not_null("email")
    .is_not_null("phone")
    .ne("email_verified", False)
    .ne("data_quality_score", {"$lt": 0.8})
    .gt("completeness_percentage", 90)
)

expr = to_expression(fb.build())
print(f"Expression:\n  {expr}\n")

# Scenario 10: Bulk Operations Filter
print("10. Bulk Operations Filter")
print("-" * 40)
print("Select items for batch processing")

filters = {
    "status": {"$in": ["pending", "queued", "retry"]},
    "retry_count": {"$lt": 3},
    "priority": {"$gte": 5},
    "$or": [
        {"scheduled_at": {"$lte": 1700000000}},
        {"scheduled_at": {"$is_null": True}}
    ]
}

expr = to_expression(filters)
print(f"Expression:\n  {expr}\n")

print("=" * 80)
print("✅ All advanced examples completed!")
print("\nThese filters can be used directly with Milvus search:")
print("  collection.search(")
print("      data=[query_vector],")
print("      anns_field='embedding',")
print("      expr=expr,  # ← Use the expression here")
print("      limit=10")
print("  )")
print("=" * 80)