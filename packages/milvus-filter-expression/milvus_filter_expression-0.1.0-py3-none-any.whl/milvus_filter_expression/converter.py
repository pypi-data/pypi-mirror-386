from math import exp
from typing import Any, Dict, List, Union


class MilvusFilterConverter:
    
    @staticmethod
    def convert(
        filters: Dict[str, Any],
        field_prefix: str = ""
    ) -> str:
        """
        Convert filter dictionary to Milvus expression
        
        Args:
            filters: MongoDB-style filter dictionary
            field_prefix: Field prefix (e.g., "metadata.")
        
        Returns:
            Milvus expression string

        Examples:
            >>> convert({"age": 25})
            'age == 25'

            >>> convert({"age": {"$gte": 18, "$lte": 65}})
            '(age >= 18) AND (age <= 65)'

            >>> convert({"$or": [{"status": "active"}, {"status": "pending"}]})
            '(status == "active") OR (status == "pending")

            >>> convert({"name": {"$like": "test%"}})
            'name LIKE "test%"'
            
            >>> convert({"score": {"$is_null": True}})
            'score IS NULL'
        """
        if not filters:
            return None

        expressions = []
        
        for key, value in filters.items():
            if key == "$or":
                expr = MilvusFilterConverter._build_or(value, field_prefix)
                if expr:
                    expressions.append(expr)
                
            elif key == "$and":
                expr = MilvusFilterConverter._build_and(value, field_prefix)
                if expr:
                    expressions.append(expr)

            elif key == "$not":
                inner = MilvusFilterConverter.convert(value, field_prefix)
                if inner:
                    expressions.append(f"NOT ({inner})")

            else:
                field_name = f"{field_prefix}{key}" if field_prefix else key

                if isinstance(value, dict):
                    expr = MilvusFilterConverter._build_operator(field_name, value)
                elif isinstance(value, list):
                    expr = MilvusFilterConverter._build_in(field_name, value)
                else:
                    expr = MilvusFilterConverter._build_equality(field_name, value)

                expressions.append(expr)

        if len(expressions) == 0:
            return None
        elif len(expressions) == 1:
            return expressions[0]
        else:
            return " AND ".join(f"({expr})" for expr in expressions)

        
    @staticmethod
    def _build_or(conditions: List[Dict[str, Any]], field_prefix: str) -> str:
        """Build OR expression"""
        if not conditions:
            return None
        
        sub_exprs = []
        for condition in conditions:
            expr = MilvusFilterConverter.convert(condition, field_prefix)
            if expr:
                sub_exprs.append(expr)

        if not sub_exprs:
            return None
        elif len(sub_exprs) == 1:
            return sub_exprs[0]
        else:
            return " OR ".join(f"({e})" for e in sub_exprs)

        
    @staticmethod
    def _build_and(conditions: List[Dict[str, Any]], field_prefix: str) -> str:
        """Build AND expression"""
        if not conditions:
            return None
        
        sub_exprs = []
        for condition in conditions:
            expr = MilvusFilterConverter.convert(condition, field_prefix)
            if expr:
                sub_exprs.append(expr)
        
        if not sub_exprs:
            return None
        elif len(sub_exprs) == 1:
            return sub_exprs[0]
        else:
            return " AND ".join(f"({e})" for e in sub_exprs)

    @staticmethod
    def _build_equality(field_name: str, value: Any) -> str:
        """Build equality comparision"""
        if isinstance(value, str):
            # Strings
            return f'{field_name} == "{value}"'
        elif isinstance(value, bool):
            # Boolean
            return f'{field_name} == {str(value).lower()}'
        elif value is None:
            # None
            return f'{field_name} IS NULL'
        else:
            # Number
            return f'{field_name} == {value}'

        
    @staticmethod
    def _build_operator(field_name: str, value_dict: Dict[str, Any]) -> str:
        """Build operator expression"""
        operator_map = {
            "$eq": "==",
            "$ne": "!=",
            "$gt": ">",
            "$gte": ">=",
            "$lt": "<",
            "$lte": "<=",
            "$in": "IN",
            "$like": "LIKE",
            "$is_null": "IS NULL",
            "$is_not_null": "IS NOT NULL",
        }

        expressions = []
        for op, val in value_dict.items():
            if op not in operator_map:
                raise ValueError(f"Unsupported operator: {op}")
            
            milvus_op = operator_map[op]

            if op == "$in":
                expr = MilvusFilterConverter._build_in(field_name, val)

            elif op == "$like":
                expr = f'{field_name} LIKE "{val}"'

            elif op == "$is_null":
                if val:
                    expr = f'{field_name} IS NULL'
                else:
                    expr = f'{field_name} IS NOT NULL'

            elif op == "$is_not_null":
                if val:
                    expr = f'{field_name} IS NOT NULL'
                else:
                    expr = f'{field_name} IS NULL'

            else:
                if isinstance(val, str):
                    expr = f'{field_name} {milvus_op} "{val}"'
                elif val is None:
                    if milvus_op == "==":
                        expr = f'{field_name} IS NULL'
                    elif milvus_op == "!=":
                        expr = f'{field_name} IS NOT NULL'
                    else:
                        expr = f'{field_name} {milvus_op} NULL'
                else:
                    expr = f'{field_name} {milvus_op} {val}'

            expressions.append(expr)
        
        if len(expressions) == 1:
            return expressions[0]
        else:
            return " AND ".join(f"({e})" for e in expressions)

    
    @staticmethod
    def _build_in(field_name: str, values: List[Any]) -> str:
        """Build IN expression"""
        if not values:
            return "false"

        formatted = []
        for val in values:
            if isinstance(val, str):
                formatted.append(f'"{val}"')
            elif val is None:
                formatted.append("NULL")
            else:
                formatted.append(str(val))
        
        values_str = "[" + ", ".join(formatted) + "]"
        return f'{field_name} IN {values_str}'

    @staticmethod
    def _build_arithmetic(
        field_name: str,
        operator: str,
        value: Union[int, float],
        comparision_op: str = "==",
        comparision_value: Union[int, float] = None
    ) -> str:
        """
        Build arithmetic expression
        
        Examples:
            >>> build_arithmetic("price", "*", 0.9, ">", 100)
            'price * 0.9 > 100'
            
            >>> build_arithmetic("age", "+", 5, "<=", 30)
            'age + 5 <= 30'
        """
        left = f"{field_name} {operator} {value}"

        if comparision_value is not None:
            return f"{left} {comparision_op} {comparision_value}" 
        else:
            return left

__all__ = ["MilvusFilterConverter"]