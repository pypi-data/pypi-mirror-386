# static-refl

A Python library for static type reflection with full type safety.

## Overview

`static-refl` provides compile-time type introspection and runtime serialization capabilities for Python 3.12+. It analyzes type annotations to generate efficient serializers and deserializers without requiring manual schema definitions.

## Features

- **Type Reflection**: Extract structured type information from Python type hints
- **JSON Serialization**: Type-safe conversion between Python objects and JSON-compatible dictionaries
- **Generic Type Support**: Full support for generic dataclasses and TypedDicts with type parameters
- **Field Renaming**: Automatic case conversion (camelCase, kebab-case, snake_case, etc.)
- **Complex Types**: Support for datetime, UUID, bytes, complex numbers, and nested structures
- **Union Types**: Handle discriminated unions and optional fields
- **Zero Runtime Overhead**: Reflection happens at the type level with cached results

## Installation

```bash
pip install static-refl
```

## Quick Start

```python
from dataclasses import dataclass
import static_refl as sr

@dataclass
class User:
    id: int
    name: str
    email: str | None = None

# Serialize to dict
user = User(id=1, name="Alice", email="alice@example.com")

# to avoid reflection overhead, cache the schema first with:
#   user_schema = sr.json.Schema[User]
#   user_schema.to_untyped(user)
data = sr.json.Schema[User].to_untyped(user)
# {'id': 1, 'name': 'Alice', 'email': 'alice@example.com'}
# Deserialize from dict
user_copy = sr.json.Schema[User].to_typed(data)
assert user == user_copy
```

## Advanced Usage

### Field Renaming

Use `@refl_options` to automatically convert field names:

```python
from dataclasses import dataclass
import static_refl as sr

@sr.refl_options(rename_all="kebab-case")
@dataclass
class Config:
    api_key: str
    max_retries: int

config = Config(api_key="secret", max_retries=3)
data = sr.json.Schema[Config].to_untyped(config)
# {'api-key': 'secret', 'max-retries': 3}
```

Supported case conversions:
- `kebab-case`
- `snake_case`
- `camelCase`
- `lowercase`
- `UPPERCASE`

### Custom Field Names

Use `@refl_rename` for specific field mappings:

```python
@sr.refl_rename(user_id="userId", created_at="createdAt")
@dataclass
class Document:
    user_id: int
    created_at: str
```

### Generic Types

Full support for generic dataclasses:

```python
from dataclasses import dataclass
from typing import Generic, TypeVar
import static_refl as sr

T = TypeVar('T')

@dataclass
class Container[T]:
    value: T
    items: list[T]

# Works with concrete type parameters
int_container = Container(value=42, items=[1, 2, 3])
data = sr.json.Schema[Container[int]].to_untyped(int_container)
result = sr.json.Schema[Container[int]].to_typed(data)
```

### Complex Nested Structures

```python
from dataclasses import dataclass
import datetime
import static_refl as sr

@dataclass
class Address:
    street: str
    city: str

@dataclass
class Person:
    name: str
    born: datetime.date
    addresses: dict[str, Address]

person = Person(
    name="Bob",
    born=datetime.date(1990, 1, 1),
    addresses={
        "home": Address(street="123 Main St", city="Springfield"),
        "work": Address(street="456 Office Rd", city="Shelbyville")
    }
)

data = sr.json.Schema[Person].to_untyped(person)
person_copy = sr.json.Schema[Person].to_typed(data)
```

### JSON Serialization Options

Customize serialization behavior with `JsonSerdeOptions`:

```python
from static_refl.json import JsonSerdeOptions, UUIDEncoding
import uuid

options = JsonSerdeOptions(
    keep_bytes=True,        # Don't base64-encode bytes
    keep_complex=True,      # Keep complex numbers as-is
    uuid_encoding=UUIDEncoding.hex  # Encode UUIDs as hex strings
)

data = sr.json.Schema[MyClass].to_untyped(obj, options=options)
```

UUID encoding options:
- `UUIDEncoding.hex` - Encode as hex string (default)
- `UUIDEncoding.bytes` - Encode as bytes
- `UUIDEncoding.object` - Keep as UUID object

## Supported Types

### Primitive Types
- `int`, `float`, `str`, `bool`
- `bytes`, `complex`
- `datetime.datetime`, `datetime.date`
- `uuid.UUID`

### Collection Types
- `list[T]`, `tuple[T, ...]`, `set[T]`
- `dict[K, V]`
- Fixed-length tuples: `tuple[int, str, bool]`
- Variadic tuples: `tuple[int, str, ...]`

### Structured Types
- `dataclass` (with `@dataclass` decorator)
- `TypedDict` (with required/optional fields)

### Special Types
- `T | None` (Optional types)
- `Union[A, B, C]` (Discriminated unions)
- `Literal[1, 2, 3]` (Literal types)
- `Any` (Untyped values)
- Generic type parameters

## API Reference

### Core Functions

#### `refl(tp: type) -> TypeId`
Reflect on a type and return its type descriptor.

```python
from static_refl import refl

type_id = refl(list[int])
print(type_id)  # array[!int]
```

### Decorators

#### `@refl_options(rename_all=None)`
Configure serialization options for a class.

#### `@refl_rename(**kwargs)`
Map specific field names to serialization keys.

### JSON Schema

#### `Schema[T].to_untyped(obj: T, options=None) -> dict | list`
Serialize a typed object to JSON-compatible structure.

#### `Schema[T].to_typed(data: dict | list, options=None) -> T`
Deserialize JSON-compatible structure to typed object.

## Type Reflection

The core `refl()` function returns a `TypeId` object representing the structure:

```python
from static_refl import refl
from dataclasses import dataclass

@dataclass
class Point:
    x: float
    y: float

type_id = refl(Point)
print(type_id)  # Point
print(type_id.structure.fields)
# (FieldDef(name='x', serde_name='x', type=!float, nullable=False),
#  FieldDef(name='y', serde_name='y', type=!float, nullable=False))
```

## Requirements

- Python >= 3.12.5
- casefy >= 1.1.0

## Development

### Running Tests

```bash
pytest
```

## License

See LICENSE file for details.

## Author

thautwarm (twshere@outlook.com)
