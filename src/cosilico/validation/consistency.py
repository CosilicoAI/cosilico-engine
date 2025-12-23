"""Cross-compilation consistency validation.

Ensures all compilation targets produce identical results for the same inputs.
"""

import json
import subprocess
from dataclasses import dataclass, field
from typing import Any, Callable

from ..dsl_parser import Module, parse_dsl
from ..js_generator import generate_js


@dataclass
class CompilationResult:
    """Result from executing compiled code."""

    target: str  # "js", "python", "wasm", etc.
    value: float
    error: str | None = None

    @property
    def success(self) -> bool:
        return self.error is None


@dataclass
class ConsistencyReport:
    """Report comparing results across compilation targets."""

    variable: str
    inputs: dict[str, Any]
    results: list[CompilationResult]
    tolerance: float = 1e-9

    @property
    def consistent(self) -> bool:
        """All targets produced the same result."""
        successful = [r for r in self.results if r.success]
        if len(successful) < 2:
            return False
        reference = successful[0].value
        return all(abs(r.value - reference) <= self.tolerance for r in successful)

    @property
    def max_deviation(self) -> float:
        """Maximum deviation between any two results."""
        successful = [r for r in self.results if r.success]
        if len(successful) < 2:
            return 0.0
        values = [r.value for r in successful]
        return max(values) - min(values)


class CrossCompilationValidator:
    """Validates that all compilation targets produce identical results."""

    def __init__(self, tolerance: float = 1e-9):
        self.tolerance = tolerance
        self._executors: dict[str, Callable] = {
            "js": self._execute_js,
        }

    def add_executor(self, target: str, executor: Callable):
        """Register an executor for a compilation target."""
        self._executors[target] = executor

    def validate(
        self,
        dsl_code: str,
        variable: str,
        inputs: dict[str, Any],
        targets: list[str] | None = None,
    ) -> ConsistencyReport:
        """Validate a single input case across compilation targets.

        Args:
            dsl_code: DSL source code
            variable: Name of the variable to evaluate
            inputs: Input values
            targets: List of targets to check (default: all registered)

        Returns:
            ConsistencyReport with results from each target
        """
        targets = targets or list(self._executors.keys())
        module = parse_dsl(dsl_code)

        results = []
        for target in targets:
            if target not in self._executors:
                results.append(CompilationResult(
                    target=target,
                    value=0.0,
                    error=f"No executor registered for target: {target}",
                ))
                continue

            try:
                value = self._executors[target](module, variable, inputs)
                results.append(CompilationResult(target=target, value=value))
            except Exception as e:
                results.append(CompilationResult(
                    target=target,
                    value=0.0,
                    error=str(e),
                ))

        return ConsistencyReport(
            variable=variable,
            inputs=inputs,
            results=results,
            tolerance=self.tolerance,
        )

    def validate_batch(
        self,
        dsl_code: str,
        variable: str,
        test_cases: list[dict[str, Any]],
        targets: list[str] | None = None,
    ) -> list[ConsistencyReport]:
        """Validate multiple test cases."""
        return [
            self.validate(dsl_code, variable, inputs, targets)
            for inputs in test_cases
        ]

    def _execute_js(
        self,
        module: Module,
        variable: str,
        inputs: dict[str, Any],
    ) -> float:
        """Execute compiled JavaScript and return result."""
        js_code = generate_js(module)

        wrapper = f"""
const inputs = {json.dumps(inputs)};
const params = {{}};

{js_code}

console.log({variable}(inputs, params));
"""
        result = subprocess.run(
            ["node", "-e", wrapper],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode != 0:
            raise RuntimeError(f"JS execution failed: {result.stderr}")

        output = result.stdout.strip()
        if output.lower() == "true":
            return 1.0
        if output.lower() == "false":
            return 0.0
        return float(output)


def check_consistency(
    dsl_code: str,
    variable: str,
    test_cases: list[dict[str, Any]],
    tolerance: float = 1e-9,
) -> bool:
    """Convenience function to check if all test cases are consistent.

    Returns True if all cases pass, raises AssertionError otherwise.
    """
    validator = CrossCompilationValidator(tolerance=tolerance)
    reports = validator.validate_batch(dsl_code, variable, test_cases)

    failures = [r for r in reports if not r.consistent]
    if failures:
        msgs = []
        for report in failures:
            msgs.append(
                f"  {report.variable} with {report.inputs}: "
                f"deviation={report.max_deviation}"
            )
        raise AssertionError(
            f"Cross-compilation inconsistency detected:\n" + "\n".join(msgs)
        )

    return True
