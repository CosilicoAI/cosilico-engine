"""Executor: evaluates compiled IR against input data."""

from typing import Any

from pydantic import BaseModel

from . import ast
from .compiler import IR
from .schema import Data

# Try to import Rust backend
try:
    from .rac_rust import execute_fast
    RUST_AVAILABLE = True
except ImportError:
    RUST_AVAILABLE = False


class ExecutionError(Exception):
    pass


class Context(BaseModel):
    """Runtime context for evaluation."""

    data: Data
    computed: dict[str, Any] = {}  # path -> value
    current_row: dict | None = None  # when evaluating entity-scoped vars
    current_entity: str | None = None

    class Config:
        arbitrary_types_allowed = True

    def get(self, path: str) -> Any:
        """Get a value by path."""
        if path in self.computed:
            return self.computed[path]
        if self.current_row and path in self.current_row:
            return self.current_row[path]
        raise ExecutionError(f"undefined: {path}")

    def get_related(self, entity: str, fk_field: str) -> list[dict]:
        """Get related rows via reverse relation."""
        if self.current_row is None:
            raise ExecutionError("no current row for relation lookup")
        pk = self.current_row.get("id")
        return self.data.get_related(entity, fk_field, pk)

    def get_fk_target(self, fk_value: Any, target_entity: str) -> dict | None:
        """Get target row via foreign key."""
        return self.data.get_row(target_entity, fk_value)


BUILTINS = {
    "min": min,
    "max": max,
    "abs": abs,
    "round": round,
    "sum": sum,
    "len": len,
    "clip": lambda x, lo, hi: max(lo, min(hi, x)),
    "any": any,
    "all": all,
}


def evaluate(expr: ast.Expr, ctx: Context) -> Any:
    """Evaluate an expression in context."""
    match expr:
        case ast.Literal(value=v):
            return v

        case ast.Var(path=path):
            return ctx.get(path)

        case ast.BinOp(op=op, left=left, right=right):
            l = evaluate(left, ctx)
            r = evaluate(right, ctx)
            match op:
                case "+":
                    return l + r
                case "-":
                    return l - r
                case "*":
                    return l * r
                case "/":
                    return l / r if r != 0 else 0
                case "<":
                    return l < r
                case ">":
                    return l > r
                case "<=":
                    return l <= r
                case ">=":
                    return l >= r
                case "==":
                    return l == r
                case "!=":
                    return l != r
                case "and":
                    return l and r
                case "or":
                    return l or r
                case _:
                    raise ExecutionError(f"unknown op: {op}")

        case ast.UnaryOp(op=op, operand=operand):
            v = evaluate(operand, ctx)
            match op:
                case "-":
                    return -v
                case "not":
                    return not v
                case _:
                    raise ExecutionError(f"unknown unary op: {op}")

        case ast.Call(func=func, args=args):
            if func not in BUILTINS:
                raise ExecutionError(f"unknown function: {func}")
            arg_vals = [evaluate(a, ctx) for a in args]
            return BUILTINS[func](*arg_vals)

        case ast.FieldAccess(obj=obj, field=fld):
            o = evaluate(obj, ctx)
            if isinstance(o, dict):
                return o.get(fld)
            if isinstance(o, list):
                return [
                    item.get(fld) if isinstance(item, dict) else getattr(item, fld)
                    for item in o
                ]
            return getattr(o, fld)

        case ast.Match(subject=subject, cases=cases, default=default):
            val = evaluate(subject, ctx)
            for pattern, result in cases:
                pattern_val = evaluate(pattern, ctx)
                if val == pattern_val:
                    return evaluate(result, ctx)
            if default:
                return evaluate(default, ctx)
            raise ExecutionError(f"no match for: {val}")

        case ast.Cond(condition=cond, then_expr=then_e, else_expr=else_e):
            if evaluate(cond, ctx):
                return evaluate(then_e, ctx)
            return evaluate(else_e, ctx)

        case _:
            raise ExecutionError(f"unknown expr type: {type(expr)}")


class Result(BaseModel):
    """Execution result."""

    scalars: dict[str, Any]  # path -> computed value
    entities: dict[str, dict[str, list[Any]]]  # entity -> path -> values per row

    class Config:
        arbitrary_types_allowed = True


class Executor:
    """Executes compiled IR against data."""

    def __init__(self, ir: IR):
        self.ir = ir

    def execute(self, data: Data) -> Result:
        """Execute the IR against input data."""
        ctx = Context(data=data)
        entities: dict[str, dict[str, list[Any]]] = {}

        for path in self.ir.order:
            var = self.ir.variables[path]

            if var.entity is None:
                # Scalar variable
                ctx.computed[path] = evaluate(var.expr, ctx)
            else:
                # Entity-scoped variable
                entity_name = var.entity
                rows = data.get_rows(entity_name)

                if entity_name not in entities:
                    entities[entity_name] = {}
                entities[entity_name][path] = []

                for i, row in enumerate(rows):
                    # Build augmented row with previously computed entity vars
                    augmented = dict(row)
                    for prev_path, prev_vals in entities.get(entity_name, {}).items():
                        if len(prev_vals) > i:
                            augmented[prev_path] = prev_vals[i]
                    ctx.current_row = augmented
                    ctx.current_entity = entity_name
                    val = evaluate(var.expr, ctx)
                    entities[entity_name][path].append(val)
                    ctx.current_row = None
                    ctx.current_entity = None

        return Result(scalars=ctx.computed, entities=entities)


def _expr_to_dict(expr: ast.Expr) -> dict:
    """Convert AST expression to dict for Rust backend."""
    match expr:
        case ast.Literal(value=v):
            return {"type": "literal", "value": float(v) if isinstance(v, (int, float)) else 0.0}
        case ast.Var(path=path):
            return {"type": "var", "path": path}
        case ast.BinOp(op=op, left=left, right=right):
            return {"type": "binop", "op": op, "left": _expr_to_dict(left), "right": _expr_to_dict(right)}
        case ast.Call(func=func, args=args):
            return {"type": "call", "func": func, "args": [_expr_to_dict(a) for a in args]}
        case ast.Cond(condition=cond, then_expr=then_e, else_expr=else_e):
            return {"type": "cond", "cond": _expr_to_dict(cond), "then": _expr_to_dict(then_e), "else": _expr_to_dict(else_e)}
        case _:
            return {"type": "literal", "value": 0.0}


def run(ir: IR, data: Data | dict[str, list[dict]], use_rust: bool = True) -> Result:
    """Execute IR against data.

    Args:
        ir: Compiled IR
        data: Input data (dict of entity -> list of rows)
        use_rust: Use Rust backend if available (default True)
    """
    if isinstance(data, dict):
        data = Data(tables=data)

    # Use Rust backend for entity variables if available
    if use_rust and RUST_AVAILABLE and data.tables:
        return _run_rust(ir, data)

    return Executor(ir).execute(data)


def _run_rust(ir: IR, data: Data) -> Result:
    """Execute using Rust backend."""
    # Convert IR to format for Rust
    variables = []
    for path in ir.order:
        var = ir.variables[path]
        variables.append({
            "path": path,
            "entity": var.entity,
            "expr": _expr_to_dict(var.expr),
        })

    # Execute Python for scalars first
    executor = Executor(ir)
    ctx = Context(data=data)
    for path in ir.order:
        var = ir.variables[path]
        if var.entity is None:
            ctx.computed[path] = evaluate(var.expr, ctx)

    # Use Rust for each entity
    entities: dict[str, dict[str, list[Any]]] = {}

    for entity_name, rows in data.tables.items():
        if not rows:
            continue

        # Get entity variables
        entity_vars = [v for v in variables if v["entity"] == entity_name]
        if not entity_vars:
            continue

        # Add scalar values to each row
        rows_with_scalars = []
        for row in rows:
            augmented = dict(row)
            augmented.update(ctx.computed)
            rows_with_scalars.append(augmented)

        # Execute in Rust
        results = execute_fast(
            variables,
            ir.order,
            entity_name,
            rows_with_scalars,
        )

        # Extract entity variable results
        entities[entity_name] = {}
        for var in entity_vars:
            path = var["path"]
            entities[entity_name][path] = [r.get(path, 0.0) for r in results]

    return Result(scalars=ctx.computed, entities=entities)
