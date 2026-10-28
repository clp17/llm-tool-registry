"""Centralized registry for the tools defined in `tools/schemas` and `tools/implementations`.

Expected structure:
tools/
    __init__.py
    registry.py
    schemas/
        __init__.py
        sum.py
    implementations/
        __init__.py
        sum.py

Each module in `schemas` must define:
- `NAME: str`
- `DESCRIPTION: str`
- `Parameters`: a Pydantic `BaseModel` class

Each module in `implementations` must expose a function with the same name as the file; for example, `sum.py` → `sum(...)`.
"""

from __future__ import annotations

import importlib
import json
import pkgutil
from pathlib import Path
from typing import Any

from pydantic import BaseModel

class ToolRegistry:
    """Discovers, describes, validates and runs the available tools."""

    def __init__(self, *, auto_discover: bool = True) -> None:
        self._tools: dict[str, dict[str, Any]] = {}

        if auto_discover:
            self.discover()

    def discover(self) -> None:
        """Loads the tools from the schemas/ and implementations/ folders."""
        if not __package__:
            raise RuntimeError(
                "Import the registry as a package, for example "
                "'from tools.registry import ToolRegistry', "
                "do not run registry.py directly."
            )

        root = Path(__file__).resolve().parent
        schemas_dir = root / "schemas"
        implementations_dir = root / "implementations"

        if not schemas_dir.is_dir():
            raise FileNotFoundError(f"Schemas folder not found: {schemas_dir}")
        if not implementations_dir.is_dir():
            raise FileNotFoundError(
                f"Implementations folder not found: {implementations_dir}"
            )

        schemas = self._module_names(schemas_dir)
        implementations = self._module_names(implementations_dir)

        missing_implementations = sorted(schemas - implementations)
        missing_schemas = sorted(implementations - schemas)

        if missing_implementations or missing_schemas:
            problems = []
            if missing_implementations:
                problems.append(
                    "missing implementation for: "
                    + ", ".join(missing_implementations)
                )
            if missing_schemas:
                problems.append(
                    "missing schema for: " + ", ".join(missing_schemas)
                )
            raise ValueError("Invalid tools configuration: " + "; ".join(problems))

        # Deterministic loading, also useful for testing and debugging.
        for module_name in sorted(schemas):
            schema_module = importlib.import_module(
                f"{__package__}.schemas.{module_name}"
            )
            implementation_module = importlib.import_module(
                f"{__package__}.implementations.{module_name}"
            )

            name = getattr(schema_module, "NAME", None)
            description = getattr(schema_module, "DESCRIPTION", None)
            parameters_model = getattr(schema_module, "Parameters", None)
            function = getattr(implementation_module, module_name, None)

            if not isinstance(name, str) or not name.strip():
                raise ValueError(
                    f"{module_name}: NAME must be a non-empty string."
                )
            if not isinstance(description, str) or not description.strip():
                raise ValueError(
                    f"{module_name}: DESCRIPTION must be a non-empty string."
                )
            if not isinstance(parameters_model, type) or not issubclass(
                parameters_model, BaseModel
            ):
                raise TypeError(
                    f"{module_name}: Parameters must be a Pydantic class "
                    "that inherits from BaseModel."
                )
            if not callable(function):
                raise TypeError(
                    f"{module_name}: a callable function named "
                    f"'{module_name}' is missing in implementations/{module_name}.py."
                )
            if name in self._tools:
                raise ValueError(f"Duplicate tool name: {name}")

            self._tools[name] = {
                "name": name,
                "description": description,
                "parameters_model": parameters_model,
                "function": function,
            }

    @staticmethod
    def _module_names(directory: Path) -> set[str]:
        """Returns the Python modules in the directory, ignoring __init__.py."""
        return {
            module.name
            for module in pkgutil.iter_modules([str(directory)])
            if not module.ispkg and not module.name.startswith("_")
        }

    def names(self) -> list[str]:
        """Returns the names of the registered tools."""
        return sorted(self._tools)

    def get(self, name: str) -> dict[str, Any]:
        """Returns the internal metadata of a tool."""
        try:
            return self._tools[name]
        except KeyError:
            raise KeyError(f"Tool not found: {name}") from None

    def to_openai_tools(self) -> list[dict[str, Any]]:
        """Generates the tools list in the OpenAI-compatible format used by LiteLLM."""
        result = []

        for name in self.names():
            tool = self._tools[name]
            result.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool["description"],
                        "parameters": tool["parameters_model"].model_json_schema(),
                    },
                }
            )

        return result

    def run(self, name: str, arguments: dict[str, Any] | str) -> Any:
        """Validates the arguments with Pydantic and runs the tool.

        `arguments` can be either a dictionary or the JSON string returned
        by the model during a tool call.
        """
        tool = self.get(name)

        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"The arguments of tool '{name}' are not valid JSON."
                ) from exc

        if not isinstance(arguments, dict):
            raise TypeError("Tool arguments must be a JSON object.")

        validated = tool["parameters_model"].model_validate(arguments)
        return tool["function"](**validated.model_dump())


# Shared instance: import this variable in the application code.
tool_registry = ToolRegistry()
