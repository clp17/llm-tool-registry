# Python Tool Registry

## Overview

A lightweight **Tool Registry Pattern** for managing Python tools exposed to LLMs in the OpenAI-compatible tool format.

This project implements the **Registry design pattern**: a central `ToolRegistry` class acts as the single point of access to all tools, decoupling their definition from their use.

Each tool consists of two modules: one for its implementation and one for its metadata and Pydantic parameter schema. The registry automatically discovers tools, generates their JSON schemas, validates arguments, and executes the corresponding functions.

## Project Structure

```text
project/
├── main.py
└── tools/
    ├── implementations/
    │   ├── sum.py
    │   └── read_data.py
    └── schemas/
        ├── sum.py
        └── read_data.py
```

- **`implementations/`**: Contains the Python functions that execute the tools.
- **`schemas/`**: Defines tool names, descriptions, and Pydantic parameter models.
- **`main.py`**: Coordinates the application and LLM interactions.

## Creating a Tool

Each tool requires two files with the same name.

### 1. Define the schema

In `tools/schemas/sum.py`:

```python
from pydantic import BaseModel, Field

NAME = "sum"
DESCRIPTION = "Calculates the sum of two numbers."


class Parameters(BaseModel):
    a: float = Field(
        description="The first number to add."
    )
    b: float = Field(
        description="The second number to add."
    )
```

Each schema module must define:

- `NAME`: Unique tool identifier.
- `DESCRIPTION`: Explains the tool's purpose to the LLM.
- `Parameters`: Pydantic model defining the accepted arguments.

### 2. Implement the tool

In `tools/implementations/sum.py`:

```python
def sum(a: float, b: float) -> float:
    """Return the sum of two numbers."""
    return a + b
```

The function name must match the module filename.

## Using the Registry

```python
from tools.registry import tool_registry

# List available tools
print(tool_registry.names())

# Generate tool definitions in the OpenAI-compatible format
tools = tool_registry.to_openai_tools()

# Execute a tool with validated arguments
result = tool_registry.run(
    "sum",
    {"a": 38.47, "b": 48.22},
)
```

Pass the generated definitions to LiteLLM:

```python
response = litellm.completion(
    model=MODEL,
    messages=messages,
    tools=tool_registry.to_openai_tools(),
)
```

The application must handle the tool-calling loop and send execution results back to the LLM.

## Setup and Extensibility

Copy the `.env_example` file to `.env` and set the `API_KEY` value with your API key.

The registry is not tied to the OpenAI tool format: since it stores format-agnostic tool metadata (name, description, and Pydantic parameters model), other formats can be supported by simply adding a new method to the `ToolRegistry` class, for example `to_anthropic_tools()`, next to the existing `to_openai_tools()`.

## Key Features

- **Automatic discovery:** Finds matching schema and implementation modules at initialization.
- **Centralized management:** Provides a single interface to list and execute tools.
- **Pydantic validation:** Validates arguments before execution.
- **Extensibility:** New tools can be added without modifying the registry's core logic.

## Requirements

The code depends on litellm, pydantic, pyyaml, and python-dotenv.

Install dependencies from `requirements.txt`:

```bash
pip install -r requirements.txt
```

**Note:** Tool names must be unique, and each schema must have a matching implementation. Validation does not replace authorization checks or application-level error handling.
