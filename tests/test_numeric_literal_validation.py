"""Tests for numeric literal validation in DSL formulas.

Per DSL_SPEC.md: Only 0, 1, -1 are allowed as numeric literals in formulas.
All other values must come from parameters.
"""

import pytest
from src.cosilico.dsl_parser import parse_dsl
from src.cosilico.validation.literals import validate_numeric_literals, NumericLiteralError


class TestNumericLiteralValidation:
    """Test that formulas only contain allowed numeric literals (0, 1, -1)."""

    def test_allowed_zero(self):
        """Zero is allowed in formulas."""
        source = """
entity: Person
period: Year
dtype: Money

formula:
  return max(0, income - threshold)
"""
        ast = parse_dsl(source)
        # Should not raise
        validate_numeric_literals(ast)

    def test_allowed_one(self):
        """One is allowed in formulas."""
        source = """
entity: Person
period: Year
dtype: Money

formula:
  return income * (1 - rate)
"""
        ast = parse_dsl(source)
        validate_numeric_literals(ast)

    def test_allowed_negative_one(self):
        """Negative one is allowed in formulas."""
        source = """
entity: Person
period: Year
dtype: Money

formula:
  return income * -1
"""
        ast = parse_dsl(source)
        validate_numeric_literals(ast)

    def test_disallowed_integer(self):
        """Other integers are not allowed."""
        source = """
entity: Person
period: Year
dtype: Money

formula:
  return income * 12
"""
        ast = parse_dsl(source)
        with pytest.raises(NumericLiteralError) as exc_info:
            validate_numeric_literals(ast)
        assert "12" in str(exc_info.value)
        assert "must come from parameters" in str(exc_info.value).lower()

    def test_disallowed_float(self):
        """Floats are not allowed."""
        source = """
entity: Person
period: Year
dtype: Money

formula:
  return income * 0.34
"""
        ast = parse_dsl(source)
        with pytest.raises(NumericLiteralError) as exc_info:
            validate_numeric_literals(ast)
        assert "0.34" in str(exc_info.value)

    def test_disallowed_large_number(self):
        """Large numbers like thresholds are not allowed."""
        source = """
entity: Person
period: Year
dtype: Money

formula:
  if income > 200000:
    return 0
  else:
    return credit
"""
        ast = parse_dsl(source)
        with pytest.raises(NumericLiteralError) as exc_info:
            validate_numeric_literals(ast)
        assert "200000" in str(exc_info.value)

    def test_disallowed_in_nested_expression(self):
        """Disallowed numbers in nested expressions are caught."""
        source = """
entity: Person
period: Year
dtype: Money

formula:
  result = max(0, min(income, 50000))
  return result
"""
        ast = parse_dsl(source)
        with pytest.raises(NumericLiteralError) as exc_info:
            validate_numeric_literals(ast)
        assert "50000" in str(exc_info.value)

    def test_allowed_in_default(self):
        """Numbers in default values are allowed (they're metadata, not formula)."""
        source = """
entity: Person
period: Year
dtype: Money

default: 1000

formula:
  return income
"""
        ast = parse_dsl(source)
        # Should not raise - default is metadata
        validate_numeric_literals(ast)

    def test_multiple_violations_reported(self):
        """All violations in a formula are reported."""
        source = """
entity: Person
period: Year
dtype: Money

formula:
  rate = 0.34
  threshold = 50000
  return income * rate
"""
        ast = parse_dsl(source)
        with pytest.raises(NumericLiteralError) as exc_info:
            validate_numeric_literals(ast)
        error_msg = str(exc_info.value)
        assert "0.34" in error_msg
        assert "50000" in error_msg

    def test_error_includes_line_number(self):
        """Error message includes line number for debugging."""
        source = """
entity: Person
period: Year
dtype: Money

formula:
  return income * 27.4
"""
        ast = parse_dsl(source)
        with pytest.raises(NumericLiteralError) as exc_info:
            validate_numeric_literals(ast)
        # Should mention line number
        assert "line" in str(exc_info.value).lower()

    def test_allowed_zero_point_zero(self):
        """0.0 is equivalent to 0 and should be allowed."""
        source = """
entity: Person
period: Year
dtype: Money

formula:
  return max(0.0, income)
"""
        ast = parse_dsl(source)
        validate_numeric_literals(ast)

    def test_allowed_one_point_zero(self):
        """1.0 is equivalent to 1 and should be allowed."""
        source = """
entity: Person
period: Year
dtype: Money

formula:
  return income * 1.0
"""
        ast = parse_dsl(source)
        validate_numeric_literals(ast)
