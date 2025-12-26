"""Numeric literal validation for Cosilico DSL.

Per DSL_SPEC.md: Only 0, 1, -1 are allowed as numeric literals in formulas.
All other values must come from parameters.
"""

from dataclasses import dataclass
from typing import List, Set

from ..dsl_parser import (
    Module,
    VariableDef,
    FormulaBlock,
    LetBinding,
    Literal,
    BinaryOp,
    UnaryOp,
    IfExpr,
    FunctionCall,
    IndexExpr,
    Identifier,
    MatchExpr,
)


# Allowed numeric literals in formulas
ALLOWED_LITERALS: Set[float] = {0, 0.0, 1, 1.0, -1, -1.0}


class NumericLiteralError(Exception):
    """Raised when a formula contains disallowed numeric literals."""

    def __init__(self, violations: List["LiteralViolation"]):
        self.violations = violations
        messages = []
        for v in violations:
            messages.append(
                f"Disallowed numeric literal {v.value} at line {v.line} in variable '{v.variable_name}'. "
                f"Values other than 0, 1, -1 must come from parameters."
            )
        super().__init__("\n".join(messages))


@dataclass
class LiteralViolation:
    """A single violation of the numeric literal rule."""

    value: float
    line: int
    variable_name: str


def validate_numeric_literals(ast: Module) -> None:
    """Validate that all numeric literals in formulas are 0, 1, or -1.

    Args:
        ast: Parsed DSL module

    Raises:
        NumericLiteralError: If any formula contains disallowed literals
    """
    violations: List[LiteralViolation] = []

    for var in ast.variables:
        if var.formula:
            var_violations = _check_expression(var.formula, var.name)
            violations.extend(var_violations)

    if violations:
        raise NumericLiteralError(violations)


def _check_expression(expr, variable_name: str, line: int = 0) -> List[LiteralViolation]:
    """Recursively check an expression for disallowed literals."""
    violations = []

    if expr is None:
        return violations

    # Handle FormulaBlock - the top-level formula structure
    if isinstance(expr, FormulaBlock):
        # Check all let bindings
        for binding in expr.bindings:
            violations.extend(_check_expression(binding, variable_name, line))
        # Check all guards (if conditions)
        for guard in expr.guards:
            # guards are tuples of (condition, return_value)
            condition, return_value = guard
            violations.extend(_check_expression(condition, variable_name, line))
            violations.extend(_check_expression(return_value, variable_name, line))
        # Check return expression
        violations.extend(_check_expression(expr.return_expr, variable_name, line))
        return violations

    # Handle LetBinding
    if isinstance(expr, LetBinding):
        violations.extend(_check_expression(expr.value, variable_name, line))
        return violations

    if isinstance(expr, Literal):
        if expr.dtype == "number":
            value = expr.value
            # Check if it's an allowed value
            if value not in ALLOWED_LITERALS:
                # Also check for negative one represented differently
                if not (value == -1 or value == -1.0):
                    violations.append(
                        LiteralViolation(
                            value=value,
                            line=line,
                            variable_name=variable_name,
                        )
                    )

    elif isinstance(expr, BinaryOp):
        violations.extend(_check_expression(expr.left, variable_name, line))
        violations.extend(_check_expression(expr.right, variable_name, line))

    elif isinstance(expr, UnaryOp):
        # Handle -1 case: UnaryOp('-', Literal(1))
        if expr.op == "-" and isinstance(expr.operand, Literal):
            if expr.operand.dtype == "number" and expr.operand.value == 1:
                # This is -1, which is allowed
                return violations
        violations.extend(_check_expression(expr.operand, variable_name, line))

    elif isinstance(expr, IfExpr):
        violations.extend(_check_expression(expr.condition, variable_name, line))
        violations.extend(_check_expression(expr.then_branch, variable_name, line))
        if expr.else_branch:
            violations.extend(_check_expression(expr.else_branch, variable_name, line))

    elif isinstance(expr, FunctionCall):
        for arg in expr.args:
            violations.extend(_check_expression(arg, variable_name, line))

    elif isinstance(expr, IndexExpr):
        violations.extend(_check_expression(expr.obj, variable_name, line))
        violations.extend(_check_expression(expr.index, variable_name, line))

    elif isinstance(expr, MatchExpr):
        violations.extend(_check_expression(expr.subject, variable_name, line))
        for case in expr.cases:
            violations.extend(_check_expression(case.pattern, variable_name, line))
            violations.extend(_check_expression(case.value, variable_name, line))

    elif isinstance(expr, list):
        for item in expr:
            violations.extend(_check_expression(item, variable_name, line))

    # Identifier and other types don't contain literals

    return violations
