"""Milvus filter operators"""

from enum import Enum

class ComparisonOperator(str, Enum):
    """Comparison operators"""
    EQ = "$eq"          # ==
    NE = "$ne"          # !=
    GT = "$gt"          # >
    GTE = "$gte"        # >=
    LT = "$lt"          # <
    LTE = "$lte"        # <=
    IN = "$in"          # IN
    LIKE = "$like"      # LIKE

class LogicalOperator(str, Enum):
    """Logical operators"""
    AND = "$and"        
    OR = "$or"          
    NOT = "$not"    

class NullOperator(str, Enum):
    """NULL operators"""
    IS_NULL = "$is_null"            # IS NULL
    IS_NOT_NULL = "$is_not_null"    # IS NOT NULL

class ArithmeticOperator(str, Enum):
    """Arithmetic operators"""
    ADD = "+"       # Addition
    SUB = "-"       # Subtraction
    MUL = "*"       # Multiplication
    DIV = "/"       # Division
    MOD = "%"       # Modulo
    POW = "**"      # Power

__all__ = [
    "ComparisonOperator",
    "LogicalOperator", 
    "NullOperator",
    "ArithmeticOperator"
]