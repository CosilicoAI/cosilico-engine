"""Parameter loader for YAML files."""

import os
from datetime import date
from pathlib import Path
from typing import Any, Optional

import yaml

from .schema import ParameterDefinition, ParameterStore, ParameterValue


class ParameterLoader:
    """Loads parameters from YAML files organized by statute structure."""

    def __init__(self, rules_dir: Optional[str] = None):
        """Initialize loader.

        Args:
            rules_dir: Root directory for parameter YAML files.
                       Defaults to 'rules/' relative to project root.
        """
        if rules_dir is None:
            # Find project root (look for .git or pyproject.toml)
            current = Path(__file__).parent
            while current != current.parent:
                if (current / ".git").exists() or (current / "pyproject.toml").exists():
                    rules_dir = str(current / "rules")
                    break
                current = current.parent
            else:
                rules_dir = "rules"

        self.rules_dir = Path(rules_dir)
        self.store = ParameterStore()

    def load_all(self) -> ParameterStore:
        """Load all parameter files from rules directory."""
        if not self.rules_dir.exists():
            return self.store

        for yaml_file in self.rules_dir.rglob("*.yaml"):
            self._load_file(yaml_file)

        for yml_file in self.rules_dir.rglob("*.yml"):
            self._load_file(yml_file)

        return self.store

    def load_file(self, filepath: str) -> ParameterStore:
        """Load a specific parameter file."""
        self._load_file(Path(filepath))
        return self.store

    def _load_file(self, filepath: Path):
        """Load parameters from a YAML file."""
        try:
            with open(filepath, "r") as f:
                data = yaml.safe_load(f)

            if not data:
                return

            # Each top-level key is a parameter path
            for path, definition in data.items():
                if path.startswith("_"):  # Skip metadata keys
                    continue

                param = self._parse_definition(path, definition)
                if param:
                    self.store.add(param)

        except Exception as e:
            print(f"Warning: Failed to load {filepath}: {e}")

    def _parse_definition(
        self, path: str, definition: dict
    ) -> Optional[ParameterDefinition]:
        """Parse a parameter definition from YAML."""
        if not isinstance(definition, dict):
            return None

        # Extract metadata
        description = definition.get("description", "")
        unit = definition.get("unit", "")
        reference = definition.get("reference", "")
        indexed_by = definition.get("indexed_by", [])

        if isinstance(indexed_by, str):
            indexed_by = [indexed_by]

        # Parse values
        values = []
        raw_values = definition.get("values", [])

        if isinstance(raw_values, list):
            for v in raw_values:
                pv = self._parse_value(v, indexed_by)
                if pv:
                    values.append(pv)
        elif isinstance(raw_values, dict):
            # Single value without date range
            pv = ParameterValue(
                value=raw_values,
                effective_from=date(1900, 1, 1),  # Always effective
            )
            values.append(pv)

        # Handle simple scalar values
        if not values and "value" in definition:
            values.append(ParameterValue(
                value=definition["value"],
                effective_from=date(1900, 1, 1),
            ))

        return ParameterDefinition(
            path=path,
            description=description,
            unit=unit,
            reference=reference,
            indexed_by=indexed_by,
            values=values,
        )

    def _parse_value(
        self, value_def: dict, indexed_by: list[str]
    ) -> Optional[ParameterValue]:
        """Parse a single parameter value entry."""
        if not isinstance(value_def, dict):
            return None

        effective_from = value_def.get("effective_from")
        if isinstance(effective_from, str):
            effective_from = date.fromisoformat(effective_from)
        elif effective_from is None:
            effective_from = date(1900, 1, 1)

        effective_to = value_def.get("effective_to")
        if isinstance(effective_to, str):
            effective_to = date.fromisoformat(effective_to)

        # Extract the actual value
        # Could be under "value" key or indexed keys like "by_n_children"
        value = value_def.get("value")

        if value is None:
            # Check for indexed values
            for idx in indexed_by:
                key = f"by_{idx}"
                if key in value_def:
                    value = value_def[key]
                    break

        if value is None:
            # Use all non-metadata keys as the value dict
            metadata_keys = {"effective_from", "effective_to", "source", "notes"}
            value = {k: v for k, v in value_def.items() if k not in metadata_keys}
            if not value:
                return None

        return ParameterValue(
            value=value,
            effective_from=effective_from,
            effective_to=effective_to,
            source=value_def.get("source"),
            notes=value_def.get("notes"),
        )


def load_parameters(rules_dir: Optional[str] = None) -> ParameterStore:
    """Convenience function to load all parameters."""
    loader = ParameterLoader(rules_dir)
    return loader.load_all()
