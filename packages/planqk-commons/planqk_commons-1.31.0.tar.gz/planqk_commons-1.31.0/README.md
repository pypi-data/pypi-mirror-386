# planqk-commons

Set of common utilities and classes to boost development of quantum computing applications using PLANQK.

## Overview

`planqk-commons` is a Python library that simplifies the development of quantum computing services on the PLANQK platform. 
It provides a runtime system that automatically handles input/output processing, parameter binding, and OpenAPI specification generation from your Python functions.

### Key Features

- **Zero-Configuration Runtime**: Automatically discovers and executes your entrypoint functions
- **Automatic Parameter Binding**: Maps input files to function parameters using type hints
- **Secret Management**: Secure handling of sensitive values with automatic environment variable injection
- **DataPool Integration**: Direct access to mounted data pools for large file processing
- **OpenAPI Generation**: Automatically generates API specifications from function signatures
- **Type Safety**: Full support for Pydantic models and Python type hints

## Usage Guide

### 1. Basic Service Function

The simplest way to use planqk-commons is to define a function with type hints:

```python
from pydantic import BaseModel


class InputData(BaseModel):
    values: list[float]


def run(data: InputData) -> float:
    return sum(data.values)
```

The runtime will:

- Read input files from the configured directory
- Parse them according to your type hints
- Call your function with the correct parameters
- Write the result to the output directory

### 2. Working with Secrets

For sensitive values like API tokens, use the `SecretValue` type:

```python
from planqk.commons.secret import SecretValue


def run(api_token: SecretValue, data: InputData) -> dict:
    # Access the actual value
    token = api_token.unwrap()

    # Secrets are automatically redacted in logs
    print(api_token)  # Output: [redacted]

    return {"status": "processed"}
```

Secrets are automatically loaded from environment variables following the pattern:

- Parameter `api_token` → Environment variable `SECRET_API_TOKEN`
- Parameter `ibmToken` → Environment variable `SECRET_IBM_TOKEN`

### 3. DataPool Integration

For processing large files from mounted data pools:

```python
from planqk.commons.datapool import DataPool


def run(data: InputData, training_data: DataPool) -> dict:
    # List available files
    files = training_data.list_files()

    # Open and read files
    with training_data.open("model.pkl", "rb") as f:
        model = pickle.load(f)

    return {"files_processed": len(files)}
```

DataPools are automatically mounted from `/var/runtime/datapool/{parameter_name}` when you declare a parameter with type `DataPool`.

### 4. Runtime Execution

Run your service using the main runtime:

```python
from planqk.commons.runtime.main import main

if __name__ == "__main__":
    exit(main())
```

Configure via environment variables:

- `ENTRYPOINT`: Function to execute (default: `user_code.src.program:run`)
- `INPUT_DIRECTORY`: Input files location (default: `/var/runtime/input`)
- `OUTPUT_DIRECTORY`: Output files location (default: `/var/runtime/output`)

### 5. OpenAPI Specification Generation

Generate OpenAPI specs automatically from your function signatures:

```python
from planqk.commons.openapi.generator import generate_openapi

generate_openapi(
    entrypoint="my_module:my_function",
    title="My Quantum Service",
    version="1.0"
)
```

Or use the Docker command:

```bash
docker run -v "$(pwd)/user_code:/workspace" planqk-commons openapi
```

The generator will:

- Extract parameter schemas from type hints
- Handle Pydantic models, primitives, and complex types
- Generate request/response schemas
- Include secret parameter handling in the specification

### 6. Advanced Type Support

The parameter binding system supports rich type annotations:

```python
from typing import Optional, Dict, List
from datetime import datetime
from uuid import UUID


def run(
        data: InputData,
        config: Optional[Dict[str, Any]] = None,
        timestamps: List[datetime] = [],
        job_id: UUID = None
) -> dict:
    # All parameters are automatically parsed and validated
    return {"processed": True}
```

Supported types:

- **Primitives**: `str`, `int`, `float`, `bool`
- **Collections**: `List[T]`, `Dict[K, V]`, `Set[T]`, `Tuple[T, ...]`
- **Optional**: `Optional[T]`, `Union[X, Y]`
- **Pydantic Models**: Full support for `BaseModel` with validation
- **Special Types**: `datetime`, `date`, `time`, `UUID`, `Decimal`, `Path`, `Enum`
- **Platform Types**: `DataPool`, `SecretValue`

### 7. Function Resolution

The entrypoint system uses string-based function references:

```python
from planqk.commons.entrypoint import run_entrypoint
from planqk.commons.reflection import resolve_signature, resolve_function

# Get function signature
signature = resolve_signature("my_module.submodule:my_function")

# Execute with parameters
result = run_entrypoint(
    "my_module.submodule:my_function",
    {"param1": value1, "param2": value2}
)
```

## Examples

### Complete Service Example

```python
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from planqk.commons.secret import SecretValue
from planqk.commons.datapool import DataPool


class CircuitParams(BaseModel):
    num_qubits: int = Field(ge=1, le=100)
    depth: int = Field(ge=1)
    shots: int = Field(default=1024)


def run(
        circuit: CircuitParams,
        backend_token: SecretValue,
        training_data: Optional[DataPool] = None
) -> Dict[str, Any]:
    """
    Execute quantum circuit with optional training data.

    Input files:
    - circuit.json: Circuit parameters

    Environment variables:
    - SECRET_BACKEND_TOKEN: API token for quantum backend

    Data pools (optional):
    - training_data: Mounted at /var/runtime/datapool/training_data
    """
    # Use the token securely
    token = backend_token.unwrap()

    # Process training data if available
    files_used = []
    if training_data:
        files_used = list(training_data.list_files().keys())

    # Execute circuit (implementation omitted)
    result = execute_circuit(circuit, token)

    return {
        "result": result,
        "training_files": files_used,
        "shots": circuit.shots
    }
```

## Development

### Setup

```bash
uv venv
source .venv/bin/activate

uv lock
uv sync
```

Update dependencies and lock files:

```bash
uv sync -U
```

### Run tests

```bash
pytest
```

### Export dependencies to requirements files

> This is useful to keep the project independent of the `uv` tool.
> Developers can install the dependencies using `pip install -r requirements.txt` and `pip install -r requirements-dev.txt`.
> Further, they may use a different tool to manage virtual environments.

```bash
uv export --format requirements-txt --no-dev --no-emit-project > requirements.txt
uv export --format requirements-txt --only-dev --no-emit-project > requirements-dev.txt
```

### Docker

Build the image:

```bash
docker build -t planqk-commons .
```

Run interactive shell:

```bash
docker run -it -v "$(pwd)/user_code:/workspace" planqk-commons
```

Generate OpenAPI description:

```bash
docker run -v "$(pwd)/user_code:/workspace" planqk-commons openapi
```

You can also use the pre-built image:

```bash
docker run -it -v "$(pwd)/user_code:/workspace" registry.gitlab.com/planqk-foss/planqk-commons:latest
```

## License

Apache-2.0 | Copyright 2024-present Kipu Quantum GmbH
