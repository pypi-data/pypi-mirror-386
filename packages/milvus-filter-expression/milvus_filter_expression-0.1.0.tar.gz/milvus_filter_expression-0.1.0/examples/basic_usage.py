"""Basic usage examples for milvus-filter-expression"""

from milvus_filter_expression import FilterBuilder, to_expression

print("=" * 80)
print("Basic Usage Examples")
print("=" * 80)

# Example 1: Simple equality
print("\n1. Simple Equality Filter")
print("-" * 40)
filters = {"age": 25}
expr = to_expression(filters)
print(f"Filters: {filters}")
print(f"Expression: {expr}")
# Output: age == 25

# Example 2: Comparison operators
print("\n2. Comparison Operators")
print("-" * 40)
filters = {"age": {"$gte": 18, "$lte": 65}}
expr = to_expression(filters)
print(f"Filters: {filters}")
print(f"Expression: {expr}")
# Output: (age >= 18) AND (age <= 65)

# Example 3: Using FilterBuilder
print("\n3. FilterBuilder (Method Chaining)")
print("-" * 40)
fb = FilterBuilder().eq("status", "active").gte("score", 80)
filters = fb.build()
expr = to_expression(filters)
print(f"Builder: FilterBuilder().eq('status', 'active').gte('score', 80)")
print(f"Filters: {filters}")
print(f"Expression: {expr}")
# Output: (status == "active") AND (score >= 80)

# Example 4: OR conditions
print("\n4. OR Conditions")
print("-" * 40)
filters = {
    "$or": [
        {"status": "active"},
        {"status": "pending"}
    ]
}
expr = to_expression(filters)
print(f"Filters: {filters}")
print(f"Expression: {expr}")
# Output: (status == "active") OR (status == "pending")

# Example 5: IN operator
print("\n5. IN Operator")
print("-" * 40)
filters = {"category": {"$in": ["tech", "science", "ai"]}}
expr = to_expression(filters)
print(f"Filters: {filters}")
print(f"Expression: {expr}")
# Output: category IN ["tech", "science", "ai"]

# Example 6: LIKE pattern matching
print("\n6. LIKE Pattern Matching")
print("-" * 40)
filters = {"email": {"$like": "%@gmail.com"}}
expr = to_expression(filters)
print(f"Filters: {filters}")
print(f"Expression: {expr}")
# Output: email LIKE "%@gmail.com"

# Example 7: NULL checks
print("\n7. NULL Checks")
print("-" * 40)
filters = {
    "deleted_at": {"$is_null": True},
    "updated_at": {"$is_not_null": True}
}
expr = to_expression(filters)
print(f"Filters: {filters}")
print(f"Expression: {expr}")
# Output: (deleted_at IS NULL) AND (updated_at IS NOT NULL)

# Example 8: Complex combined filters
print("\n8. Complex Combined Filters")
print("-" * 40)
fb = (FilterBuilder()
    .or_([
        {"category": "ml"},
        {"category": "nlp"}
    ])
    .between("score", 80, 100)
    .is_not_null("author")
)
filters = fb.build()
expr = to_expression(filters)
print(f"Filters: {filters}")
print(f"Expression: {expr}")

# Example 9: Using field prefix
print("\n9. Field Prefix (for metadata)")
print("-" * 40)
filters = {"age": 25, "country": "US"}
expr = to_expression(filters, field_prefix="metadata.")
print(f"Filters: {filters}")
print(f"Prefix: 'metadata.'")
print(f"Expression: {expr}")
# Output: (metadata.age == 25) AND (metadata.country == "US")

print("\n" + "=" * 80)
print("✅ All basic examples completed!")
print("\nNext: Try advanced_filters.py for more complex scenarios")
print("=" * 80)