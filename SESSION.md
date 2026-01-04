# Session state

## Branch
`refactor/clean-parser-engine` (pushed)

## What was done
1. Stripped all old code (~40k lines deleted)
2. Created clean parser engine:
   - `src/rac/ast.py` - Pydantic AST nodes
   - `src/rac/parser.py` - Lexer + recursive descent
   - `src/rac/compiler.py` - Temporal resolution, amendments, topo sort
   - `src/rac/executor.py` - Evaluate IR against relational data
   - `src/rac/schema.py` - Entity/FK/PK data model
   - `src/rac/codegen/rust.py` - Rust code generator

3. Removed: benchmarks, data, docs, paper, viz, old tests

## What's left
1. Fix syntax error in rust.py line 179 (already fixed, just run tests)
2. Run `pytest tests/ -v` to verify
3. Could add more codegen targets (JS, Python, SQL)

## Quick test
```python
from datetime import date
from rac import parse, compile, execute

module = parse('''
    variable gov/rate:
        from 2024-01-01: 0.25
''')
ir = compile([module], as_of=date(2024, 6, 1))
result = execute(ir, {})
print(result.scalars)  # {'gov/rate': 0.25}
```

## Key features
- Temporal values with date ranges
- Amendments can override/replace variables (like legislation)
- Repeals make variables undefined after a date
- Relational data with FK/PK lookups
- Rust codegen from IR
