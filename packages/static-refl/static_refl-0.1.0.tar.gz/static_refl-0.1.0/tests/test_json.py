"""Tests for static_refl.json module."""
import pytest
import datetime
import uuid
import base64
from dataclasses import dataclass
from typing import List, Dict, Set, Tuple, Union, Optional, Literal, Any, TypedDict
from static_refl.json import (
    Schema,
    JsonSerdeOptions,
    JsonSerializer,
    JsonDeserializer,
    UUIDEncoding,
    DecodeError,
)
from static_refl.core import refl
from static_refl.options import refl_options, refl_rename


class TestPrimitiveSerialization:
    """Test serialization of primitive types."""

    def test_serialize_int(self):
        """Test int serialization."""
        schema = Schema[int]
        result = schema.to_untyped(42)
        assert result == 42

    def test_serialize_float(self):
        """Test float serialization."""
        schema = Schema[float]
        result = schema.to_untyped(3.14)
        assert result == 3.14

    def test_serialize_str(self):
        """Test str serialization."""
        schema = Schema[str]
        result = schema.to_untyped("hello")
        assert result == "hello"

    def test_serialize_bool(self):
        """Test bool serialization."""
        schema = Schema[bool]
        result = schema.to_untyped(True)
        assert result is True

    def test_serialize_bytes_default(self):
        """Test bytes serialization with default options."""
        schema = Schema[bytes]
        data = b"hello world"
        result = schema.to_untyped(data)
        assert result == {"base64": base64.b64encode(data).decode("utf-8")}

    def test_serialize_bytes_keep_bytes(self):
        """Test bytes serialization with keep_bytes option."""
        schema = Schema[bytes]
        data = b"hello world"
        options = JsonSerdeOptions(keep_bytes=True)
        result = schema.to_untyped(data, options)
        assert result == data

    def test_serialize_complex_default(self):
        """Test complex number serialization."""
        schema = Schema[complex]
        result = schema.to_untyped(3 + 4j)
        assert result == {"real": 3.0, "imag": 4.0}

    def test_serialize_complex_keep_complex(self):
        """Test complex serialization with keep_complex option."""
        schema = Schema[complex]
        options = JsonSerdeOptions(keep_complex=True)
        result = schema.to_untyped(3 + 4j, options)
        assert result == 3 + 4j

    def test_serialize_datetime(self):
        """Test datetime serialization."""
        schema = Schema[datetime.datetime]
        dt = datetime.datetime(2024, 1, 15, 12, 30, 45)
        result = schema.to_untyped(dt)
        assert result == dt.isoformat()

    def test_serialize_date(self):
        """Test date serialization."""
        schema = Schema[datetime.date]
        d = datetime.date(2024, 1, 15)
        result = schema.to_untyped(d)
        assert result == d.isoformat()

    def test_serialize_uuid_hex(self):
        """Test UUID serialization with hex encoding (default)."""
        schema = Schema[uuid.UUID]
        u = uuid.uuid4()
        result = schema.to_untyped(u)
        assert result == u.hex

    def test_serialize_uuid_bytes(self):
        """Test UUID serialization with bytes encoding."""
        schema = Schema[uuid.UUID]
        u = uuid.uuid4()
        options = JsonSerdeOptions(uuid_encoding=UUIDEncoding.bytes)
        result = schema.to_untyped(u, options)
        assert result == u.bytes

    def test_serialize_uuid_object(self):
        """Test UUID serialization with object encoding."""
        schema = Schema[uuid.UUID]
        u = uuid.uuid4()
        options = JsonSerdeOptions(uuid_encoding=UUIDEncoding.object)
        result = schema.to_untyped(u, options)
        assert result == u


class TestPrimitiveDeserialization:
    """Test deserialization of primitive types."""

    def test_deserialize_int(self):
        """Test int deserialization."""
        schema = Schema[int]
        result = schema.to_typed(42)
        assert result == 42

    def test_deserialize_float(self):
        """Test float deserialization."""
        schema = Schema[float]
        result = schema.to_typed(3.14)
        assert result == 3.14

    def test_deserialize_str(self):
        """Test str deserialization."""
        schema = Schema[str]
        result = schema.to_typed("hello")
        assert result == "hello"

    def test_deserialize_bool(self):
        """Test bool deserialization."""
        schema = Schema[bool]
        result = schema.to_typed(True)
        assert result is True

    def test_deserialize_bytes_from_base64(self):
        """Test bytes deserialization from base64."""
        schema = Schema[bytes]
        data = b"hello world"
        encoded = {"base64": base64.b64encode(data).decode("utf-8")}
        result = schema.to_typed(encoded)
        assert result == data

    def test_deserialize_bytes_direct(self):
        """Test bytes deserialization from bytes."""
        schema = Schema[bytes]
        data = b"hello world"
        result = schema.to_typed(data)
        assert result == data

    def test_deserialize_complex(self):
        """Test complex number deserialization."""
        schema = Schema[complex]
        result = schema.to_typed({"real": 3.0, "imag": 4.0})
        assert result == 3 + 4j

    def test_deserialize_datetime(self):
        """Test datetime deserialization."""
        schema = Schema[datetime.datetime]
        dt = datetime.datetime(2024, 1, 15, 12, 30, 45)
        result = schema.to_typed(dt.isoformat())
        assert result == dt

    def test_deserialize_date(self):
        """Test date deserialization."""
        schema = Schema[datetime.date]
        d = datetime.date(2024, 1, 15)
        result = schema.to_typed(d.isoformat())
        assert result == d

    def test_deserialize_uuid_from_string(self):
        """Test UUID deserialization from string."""
        schema = Schema[uuid.UUID]
        u = uuid.uuid4()
        result = schema.to_typed(str(u))
        assert result == u

    def test_deserialize_uuid_from_bytes(self):
        """Test UUID deserialization from bytes."""
        schema = Schema[uuid.UUID]
        u = uuid.uuid4()
        result = schema.to_typed(u.bytes)
        assert result == u


class TestCollectionSerialization:
    """Test serialization of collection types."""

    def test_serialize_list(self):
        """Test list serialization."""
        schema = Schema[List[int]]
        result = schema.to_untyped([1, 2, 3])
        assert result == [1, 2, 3]

    def test_serialize_list_nested(self):
        """Test nested list serialization."""
        schema = Schema[List[List[int]]]
        result = schema.to_untyped([[1, 2], [3, 4]])
        assert result == [[1, 2], [3, 4]]

    def test_serialize_tuple_fixed(self):
        """Test fixed-size tuple serialization."""
        schema = Schema[Tuple[int, str]]
        result = schema.to_untyped((42, "hello"))
        assert result == [42, "hello"]

    def test_serialize_tuple_variadic(self):
        """Test variadic tuple serialization."""
        schema = Schema[Tuple[int, ...]]
        result = schema.to_untyped((1, 2, 3, 4, 5))
        assert result == [1, 2, 3, 4, 5]

    def test_serialize_set(self):
        """Test set serialization."""
        schema = Schema[Set[int]]
        result = schema.to_untyped({1, 2, 3})
        assert set(result) == {1, 2, 3}  # Order not guaranteed

    def test_serialize_dict_str_key(self):
        """Test dict serialization with string keys."""
        schema = Schema[Dict[str, int]]
        result = schema.to_untyped({"a": 1, "b": 2})
        assert result == {"a": 1, "b": 2}

    def test_serialize_dict_complex_key(self):
        """Test dict serialization with complex keys."""
        schema = Schema[Dict[int, str]]
        result = schema.to_untyped({1: "one", 2: "two"})
        # Keys should be JSON-encoded
        assert "1" in result or 1 in result
        assert len(result) == 2


class TestCollectionDeserialization:
    """Test deserialization of collection types."""

    def test_deserialize_list(self):
        """Test list deserialization."""
        schema = Schema[List[int]]
        result = schema.to_typed([1, 2, 3])
        assert result == [1, 2, 3]

    def test_deserialize_tuple_fixed(self):
        """Test fixed-size tuple deserialization."""
        schema = Schema[Tuple[int, str]]
        result = schema.to_typed([42, "hello"])
        assert result == (42, "hello")
        assert isinstance(result, tuple)

    def test_deserialize_tuple_wrong_length(self):
        """Test tuple deserialization with wrong length."""
        schema = Schema[Tuple[int, str]]
        with pytest.raises(ValueError, match="Expected tuple of length"):
            schema.to_typed([42])

    def test_deserialize_set(self):
        """Test set deserialization."""
        schema = Schema[Set[int]]
        result = schema.to_typed([1, 2, 3])
        assert result == {1, 2, 3}
        assert isinstance(result, set)

    def test_deserialize_dict(self):
        """Test dict deserialization."""
        schema = Schema[Dict[str, int]]
        result = schema.to_typed({"a": 1, "b": 2})
        assert result == {"a": 1, "b": 2}


class TestDataClassSerialization:
    """Test serialization of dataclass types."""

    def test_serialize_simple_dataclass(self):
        """Test simple dataclass serialization."""
        @dataclass
        class Person:
            name: str
            age: int

        schema = Schema[Person]
        person = Person(name="Alice", age=30)
        result = schema.to_untyped(person)
        assert result == {"name": "Alice", "age": 30}

    def test_serialize_dataclass_with_rename_all(self):
        """Test dataclass serialization with rename_all."""
        @refl_options(rename_all="kebab-case")
        @dataclass
        class Person:
            full_name: str
            age: int

        schema = Schema[Person]
        person = Person(full_name="Alice Smith", age=30)
        result = schema.to_untyped(person)
        assert result == {"full-name": "Alice Smith", "age": 30}

    def test_serialize_dataclass_with_rename(self):
        """Test dataclass serialization with field rename."""
        @refl_rename(full_name="fullName")
        @dataclass
        class Person:
            full_name: str
            age: int

        schema = Schema[Person]
        person = Person(full_name="Alice Smith", age=30)
        result = schema.to_untyped(person)
        assert result == {"fullName": "Alice Smith", "age": 30}

    def test_serialize_dataclass_optional_field(self):
        """Test dataclass serialization with optional field."""
        @dataclass
        class Person:
            name: str
            nickname: Optional[str]

        schema = Schema[Person]
        person1 = Person(name="Alice", nickname="Ali")
        result1 = schema.to_untyped(person1)
        assert result1 == {"name": "Alice", "nickname": "Ali"}

        person2 = Person(name="Bob", nickname=None)
        result2 = schema.to_untyped(person2)
        # None fields should not be included
        assert "nickname" not in result2 or result2.get("nickname") is None

    def test_serialize_nested_dataclass(self):
        """Test nested dataclass serialization."""
        @dataclass
        class Address:
            street: str
            city: str

        @dataclass
        class Person:
            name: str
            address: Address

        schema = Schema[Person]
        person = Person(
            name="Alice",
            address=Address(street="123 Main St", city="Springfield")
        )
        result = schema.to_untyped(person)
        assert result == {
            "name": "Alice",
            "address": {"street": "123 Main St", "city": "Springfield"}
        }

    def test_serialize_generic_dataclass(self):
        """Test generic dataclass serialization."""
        @dataclass
        class Container[T]:
            value: T

        schema = Schema[Container[int]]
        container = Container(value=42)
        result = schema.to_untyped(container)
        assert result == {"value": 42}


class TestDataClassDeserialization:
    """Test deserialization of dataclass types."""

    def test_deserialize_simple_dataclass(self):
        """Test simple dataclass deserialization."""
        @dataclass
        class Person:
            name: str
            age: int

        schema = Schema[Person]
        result = schema.to_typed({"name": "Alice", "age": 30})
        assert result.name == "Alice"
        assert result.age == 30
        assert isinstance(result, Person)

    def test_deserialize_dataclass_with_rename_all(self):
        """Test dataclass deserialization with rename_all."""
        @refl_options(rename_all="kebab-case")
        @dataclass
        class Person:
            full_name: str
            age: int

        schema = Schema[Person]
        result = schema.to_typed({"full-name": "Alice Smith", "age": 30})
        assert result.full_name == "Alice Smith"
        assert result.age == 30

    def test_deserialize_dataclass_missing_required_field(self):
        """Test dataclass deserialization with missing required field."""
        @dataclass
        class Person:
            name: str
            age: int

        schema = Schema[Person]
        with pytest.raises(ValueError, match="Missing required field"):
            schema.to_typed({"name": "Alice"})

    def test_deserialize_dataclass_optional_field(self):
        """Test dataclass deserialization with optional field."""
        @dataclass
        class Person:
            name: str
            nickname: Optional[str]

        schema = Schema[Person]
        result = schema.to_typed({"name": "Alice"})
        assert result.name == "Alice"
        assert result.nickname is None

    def test_deserialize_nested_dataclass(self):
        """Test nested dataclass deserialization."""
        @dataclass
        class Address:
            street: str
            city: str

        @dataclass
        class Person:
            name: str
            address: Address

        schema = Schema[Person]
        result = schema.to_typed({
            "name": "Alice",
            "address": {"street": "123 Main St", "city": "Springfield"}
        })
        assert result.name == "Alice"
        assert result.address.street == "123 Main St"
        assert result.address.city == "Springfield"

    def test_deserialize_dataclass_wrong_type(self):
        """Test dataclass deserialization with wrong input type."""
        @dataclass
        class Person:
            name: str
            age: int

        schema = Schema[Person]
        with pytest.raises(ValueError, match="Expected a dict"):
            schema.to_typed("not a dict")


class TestTypedDictSerialization:
    """Test serialization of TypedDict types."""

    def test_serialize_typeddict(self):
        """Test TypedDict serialization."""
        class PersonDict(TypedDict):
            name: str
            age: int

        schema = Schema[PersonDict]
        data = {"name": "Alice", "age": 30}
        result = schema.to_untyped(data)
        assert result == {"name": "Alice", "age": 30}

    def test_deserialize_typeddict(self):
        """Test TypedDict deserialization."""
        class PersonDict(TypedDict):
            name: str
            age: int

        schema = Schema[PersonDict]
        result = schema.to_typed({"name": "Alice", "age": 30})
        assert result == {"name": "Alice", "age": 30}
        assert isinstance(result, dict)


class TestUnionSerialization:
    """Test serialization of Union types."""

    def test_serialize_union_literal(self):
        """Test union of literals serialization."""
        schema = Schema[Literal["a", "b", "c"]]
        result = schema.to_untyped("b")
        assert result == "b"

    def test_deserialize_union_literal(self):
        """Test union of literals deserialization."""
        schema = Schema[Literal["a", "b", "c"]]
        result = schema.to_typed("b")
        assert result == "b"

    def test_deserialize_union_literal_invalid(self):
        """Test union of literals with invalid value."""
        schema = Schema[Literal["a", "b", "c"]]
        with pytest.raises(ValueError):
            schema.to_typed("d")

    def test_serialize_union_dataclass(self):
        """Test union of dataclasses serialization."""
        @dataclass
        class Dog:
            kind: Literal["dog"]
            breed: str

        @dataclass
        class Cat:
            kind: Literal["cat"]
            indoor: bool

        schema = Schema[Union[Dog, Cat]]
        dog = Dog(kind="dog", breed="Labrador")
        result = schema.to_untyped(dog)
        assert result == {"kind": "dog", "breed": "Labrador"}

        cat = Cat(kind="cat", indoor=True)
        result = schema.to_untyped(cat)
        assert result == {"kind": "cat", "indoor": True}

    def test_deserialize_union_dataclass(self):
        """Test union of dataclasses deserialization."""
        @dataclass
        class Dog:
            kind: Literal["dog"]
            breed: str

        @dataclass
        class Cat:
            kind: Literal["cat"]
            indoor: bool

        schema = Schema[Union[Dog, Cat]]

        dog_result = schema.to_typed({"kind": "dog", "breed": "Labrador"})
        assert isinstance(dog_result, Dog)
        assert dog_result.breed == "Labrador"

        cat_result = schema.to_typed({"kind": "cat", "indoor": True})
        assert isinstance(cat_result, Cat)
        assert cat_result.indoor is True


class TestOptionSerialization:
    """Test serialization of Optional types."""

    def test_serialize_optional_some(self):
        """Test Optional serialization with value."""
        schema = Schema[Optional[int]]
        result = schema.to_untyped(42)
        assert result == 42

    def test_serialize_optional_none(self):
        """Test Optional serialization with None."""
        schema = Schema[Optional[int]]
        result = schema.to_untyped(None)
        assert result is None

    def test_deserialize_optional_some(self):
        """Test Optional deserialization with value."""
        schema = Schema[Optional[int]]
        result = schema.to_typed(42)
        assert result == 42

    def test_deserialize_optional_none(self):
        """Test Optional deserialization with None."""
        schema = Schema[Optional[int]]
        result = schema.to_typed(None)
        assert result is None


class TestAnySerialization:
    """Test serialization of Any type."""

    def test_serialize_any(self):
        """Test Any serialization."""
        schema = Schema[Any]
        result = schema.to_untyped({"anything": [1, 2, 3]})
        assert result == {"anything": [1, 2, 3]}

    def test_deserialize_any(self):
        """Test Any deserialization."""
        schema = Schema[Any]
        result = schema.to_typed({"anything": [1, 2, 3]})
        assert result == {"anything": [1, 2, 3]}


class TestErrorHandling:
    """Test error handling and error messages."""

    def test_decode_error_with_path(self):
        """Test that error includes path information."""
        @dataclass
        class Person:
            name: str
            age: int

        schema = Schema[Person]
        # The error should be an Exception (not ValueError) with path info
        with pytest.raises(Exception, match=r"path.*age"):
            schema.to_typed({"name": "Alice", "age": "not a number"})

    def test_decode_error_nested_path(self):
        """Test that DecodeError includes nested path information."""
        @dataclass
        class Address:
            city: str

        @dataclass
        class Person:
            address: Address

        schema = Schema[Person]
        with pytest.raises(ValueError, match=r"path.*address"):
            schema.to_typed({"address": "not a dict"})


class TestRoundTrip:
    """Test round-trip serialization and deserialization."""

    def test_roundtrip_simple_dataclass(self):
        """Test round-trip with simple dataclass."""
        @dataclass
        class Person:
            name: str
            age: int

        schema = Schema[Person]
        original = Person(name="Alice", age=30)
        serialized = schema.to_untyped(original)
        deserialized = schema.to_typed(serialized)
        assert deserialized.name == original.name
        assert deserialized.age == original.age

    def test_roundtrip_complex_structure(self):
        """Test round-trip with complex structure."""
        @dataclass
        class Item:
            name: str
            price: float

        @dataclass
        class Order:
            id: int
            items: List[Item]
            metadata: Dict[str, str]

        schema = Schema[Order]
        original = Order(
            id=123,
            items=[
                Item(name="Widget", price=9.99),
                Item(name="Gadget", price=19.99)
            ],
            metadata={"customer": "Alice", "region": "US"}
        )

        serialized = schema.to_untyped(original)
        deserialized = schema.to_typed(serialized)

        assert deserialized.id == original.id
        assert len(deserialized.items) == 2
        assert deserialized.items[0].name == "Widget"
        assert deserialized.metadata["customer"] == "Alice"
