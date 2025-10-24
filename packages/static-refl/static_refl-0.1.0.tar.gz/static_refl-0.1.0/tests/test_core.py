"""Tests for static_refl.core module."""
import pytest
import datetime
import uuid
from dataclasses import dataclass
from typing import List, Dict, Set, Tuple, Union, Optional, Literal, Any
from static_refl.core import (
    refl,
    TypeIdPrim,
    TypeIdArray,
    TypeIdMap,
    TypeIdSet,
    TypeIdTuple,
    TypeIdDataClass,
    TypeIdOption,
    TypeIdUnion,
    TypeIdLit,
    TypeIdAny,
    PrimTag,
    NONE_TYPE_ID,
    ANY_TYPE_ID,
)


class TestPrimitiveTypes:
    """Test reflection of primitive types."""

    def test_refl_int(self):
        """Test int type reflection."""
        tid = refl(int)
        assert isinstance(tid, TypeIdPrim)
        assert tid.tag == PrimTag.int
        assert tid.pytype is int
        assert tid.is_primitive is True

    def test_refl_float(self):
        """Test float type reflection."""
        tid = refl(float)
        assert isinstance(tid, TypeIdPrim)
        assert tid.tag == PrimTag.float
        assert tid.pytype is float

    def test_refl_str(self):
        """Test str type reflection."""
        tid = refl(str)
        assert isinstance(tid, TypeIdPrim)
        assert tid.tag == PrimTag.str
        assert tid.pytype is str

    def test_refl_bool(self):
        """Test bool type reflection."""
        tid = refl(bool)
        assert isinstance(tid, TypeIdPrim)
        assert tid.tag == PrimTag.bool
        assert tid.pytype is bool

    def test_refl_bytes(self):
        """Test bytes type reflection."""
        tid = refl(bytes)
        assert isinstance(tid, TypeIdPrim)
        assert tid.tag == PrimTag.bytes
        assert tid.pytype is bytes

    def test_refl_complex(self):
        """Test complex type reflection."""
        tid = refl(complex)
        assert isinstance(tid, TypeIdPrim)
        assert tid.tag == PrimTag.complex
        assert tid.pytype is complex

    def test_refl_datetime(self):
        """Test datetime type reflection."""
        tid = refl(datetime.datetime)
        assert isinstance(tid, TypeIdPrim)
        assert tid.tag == PrimTag.datetime
        assert tid.pytype is datetime.datetime

    def test_refl_date(self):
        """Test date type reflection."""
        tid = refl(datetime.date)
        assert isinstance(tid, TypeIdPrim)
        assert tid.tag == PrimTag.date
        assert tid.pytype is datetime.date

    def test_refl_uuid(self):
        """Test UUID type reflection."""
        tid = refl(uuid.UUID)
        assert isinstance(tid, TypeIdPrim)
        assert tid.tag == PrimTag.uuid
        assert tid.pytype is uuid.UUID


class TestCollectionTypes:
    """Test reflection of collection types."""

    def test_refl_list_int(self):
        """Test List[int] reflection."""
        tid = refl(List[int])
        assert isinstance(tid, TypeIdArray)
        assert isinstance(tid.element, TypeIdPrim)
        assert tid.element.tag == PrimTag.int
        assert tid.pytype is list

    def test_refl_list_no_args(self):
        """Test list without type arguments - should raise error."""
        with pytest.raises(ValueError, match="Unsupported built-in type"):
            refl(list)

    def test_refl_dict_str_int(self):
        """Test Dict[str, int] reflection."""
        tid = refl(Dict[str, int])
        assert isinstance(tid, TypeIdMap)
        assert isinstance(tid.key, TypeIdPrim)
        assert tid.key.tag == PrimTag.str
        assert isinstance(tid.value, TypeIdPrim)
        assert tid.value.tag == PrimTag.int
        assert tid.pytype is dict

    def test_refl_set_str(self):
        """Test Set[str] reflection."""
        tid = refl(Set[str])
        assert isinstance(tid, TypeIdSet)
        assert isinstance(tid.element, TypeIdPrim)
        assert tid.element.tag == PrimTag.str
        assert tid.pytype is set

    def test_refl_tuple_fixed(self):
        """Test Tuple[int, str] reflection."""
        tid = refl(Tuple[int, str])
        assert isinstance(tid, TypeIdTuple)
        assert len(tid.elements) == 2
        assert isinstance(tid.elements[0], TypeIdPrim)
        assert tid.elements[0].tag == PrimTag.int
        assert isinstance(tid.elements[1], TypeIdPrim)
        assert tid.elements[1].tag == PrimTag.str
        assert tid.variadic_tail is None
        assert tid.pytype is tuple

    def test_refl_tuple_variadic(self):
        """Test Tuple[int, ...] reflection."""
        tid = refl(Tuple[int, ...])
        assert isinstance(tid, TypeIdTuple)
        assert len(tid.elements) == 0
        assert tid.variadic_tail is not None
        assert isinstance(tid.variadic_tail, TypeIdPrim)
        assert tid.variadic_tail.tag == PrimTag.int

    def test_refl_tuple_empty(self):
        """Test empty Tuple reflection."""
        tid = refl(Tuple[()])
        assert isinstance(tid, TypeIdTuple)
        assert len(tid.elements) == 0
        assert tid.variadic_tail is None


class TestUnionAndOptionTypes:
    """Test reflection of Union and Optional types."""

    def test_refl_optional_int(self):
        """Test Optional[int] reflection."""
        tid = refl(Optional[int])
        assert isinstance(tid, TypeIdOption)
        assert isinstance(tid.element, TypeIdPrim)
        assert tid.element.tag == PrimTag.int

    def test_refl_union_int_str(self):
        """Test Union[int, str] reflection."""
        tid = refl(Union[int, str])
        assert isinstance(tid, TypeIdUnion)
        assert len(tid.choices) == 2
        # Check that both types are in choices
        types = {choice.tag for choice in tid.choices if isinstance(choice, TypeIdPrim)}
        assert PrimTag.int in types
        assert PrimTag.str in types

    def test_refl_union_with_none(self):
        """Test Union[int, None] reflection (equivalent to Optional)."""
        tid = refl(Union[int, None])
        assert isinstance(tid, TypeIdOption)
        assert isinstance(tid.element, TypeIdPrim)
        assert tid.element.tag == PrimTag.int

    def test_refl_none_type(self):
        """Test None type reflection."""
        tid = refl(type(None))
        assert tid is NONE_TYPE_ID
        assert isinstance(tid, TypeIdLit)
        assert tid.literal is None
        assert tid.is_none_type is True


class TestLiteralTypes:
    """Test reflection of Literal types."""

    def test_refl_literal_str(self):
        """Test Literal['hello'] reflection."""
        tid = refl(Literal["hello"])
        assert isinstance(tid, TypeIdLit)
        assert tid.literal == "hello"
        assert tid.is_primitive is True

    def test_refl_literal_int(self):
        """Test Literal[42] reflection."""
        tid = refl(Literal[42])
        assert isinstance(tid, TypeIdLit)
        assert tid.literal == 42

    def test_refl_literal_multiple(self):
        """Test Literal with multiple values."""
        tid = refl(Literal["a", "b", "c"])
        # Should create a union of literals
        assert isinstance(tid, TypeIdUnion)

    def test_refl_literal_none(self):
        """Test Literal[None] reflection."""
        tid = refl(Literal[None])
        # Literal[None] becomes NONE_TYPE_ID which is a TypeIdLit
        assert isinstance(tid, TypeIdLit)
        assert tid.literal is None


class TestDataClassReflection:
    """Test reflection of dataclass types."""

    def test_refl_simple_dataclass(self):
        """Test simple dataclass reflection."""
        @dataclass
        class Person:
            name: str
            age: int

        tid = refl(Person)
        assert isinstance(tid, TypeIdDataClass)
        assert tid.class_obj is Person
        assert tid.pytype is Person
        assert len(tid.type_params) == 0

        # Check structure
        struct = tid.structure
        assert len(struct.fields) == 2
        assert struct.fields[0].name == "name"
        assert struct.fields[0].serde_name == "name"
        assert isinstance(struct.fields[0].type, TypeIdPrim)
        assert struct.fields[0].type.tag == PrimTag.str
        assert struct.fields[1].name == "age"
        assert isinstance(struct.fields[1].type, TypeIdPrim)
        assert struct.fields[1].type.tag == PrimTag.int

    def test_refl_generic_dataclass(self):
        """Test generic dataclass reflection."""
        @dataclass
        class Container[T]:
            value: T

        tid = refl(Container[int])
        assert isinstance(tid, TypeIdDataClass)
        assert len(tid.type_params) == 1
        assert isinstance(tid.type_params[0], TypeIdPrim)
        assert tid.type_params[0].tag == PrimTag.int

        # Check field type is substituted
        struct = tid.structure
        assert len(struct.fields) == 1
        assert isinstance(struct.fields[0].type, TypeIdPrim)
        assert struct.fields[0].type.tag == PrimTag.int

    def test_refl_nested_dataclass(self):
        """Test nested dataclass reflection."""
        @dataclass
        class Address:
            street: str
            city: str

        @dataclass
        class Person:
            name: str
            address: Address

        tid = refl(Person)
        assert isinstance(tid, TypeIdDataClass)
        struct = tid.structure
        assert len(struct.fields) == 2
        # Second field should be a dataclass type
        assert isinstance(struct.fields[1].type, TypeIdDataClass)
        assert struct.fields[1].type.class_obj is Address

    def test_refl_optional_field(self):
        """Test dataclass with optional field."""
        @dataclass
        class Person:
            name: str
            nickname: Optional[str]

        tid = refl(Person)
        struct = tid.structure
        assert len(struct.fields) == 2
        assert struct.fields[1].nullable is True
        assert isinstance(struct.fields[1].type, TypeIdOption)


class TestAnyType:
    """Test Any type reflection."""

    def test_refl_any(self):
        """Test Any type reflection."""
        tid = refl(Any)
        assert tid is ANY_TYPE_ID
        assert isinstance(tid, TypeIdAny)

    def test_any_has_no_pytype(self):
        """Test that Any type has no specific Python type."""
        with pytest.raises(Exception, match="Any has no specific Python type"):
            ANY_TYPE_ID.pytype


class TestTypeIdCaching:
    """Test that type IDs are cached properly."""

    def test_primitive_caching(self):
        """Test that primitive types are cached."""
        tid1 = refl(int)
        tid2 = refl(int)
        assert tid1 is tid2

    def test_dataclass_caching(self):
        """Test that dataclass types are cached."""
        @dataclass
        class TestClass:
            value: int

        tid1 = refl(TestClass)
        tid2 = refl(TestClass)
        assert tid1 is tid2

    def test_generic_caching(self):
        """Test that generic types with same args are cached."""
        tid1 = refl(List[int])
        tid2 = refl(List[int])
        assert tid1 is tid2


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_unsupported_builtin_type(self):
        """Test that unsupported builtin types raise error."""
        with pytest.raises(ValueError, match="Unsupported built-in type"):
            refl(object)

    def test_repr_methods(self):
        """Test __repr__ methods of TypeId classes."""
        assert repr(refl(int)) == "!int"
        assert repr(refl(List[int])) == "array[!int]"
        assert "map[" in repr(refl(Dict[str, int]))
        assert "set[" in repr(refl(Set[int]))
        assert "any" == repr(ANY_TYPE_ID)
        assert "lit[None]" == repr(NONE_TYPE_ID)

    def test_is_primitive_property(self):
        """Test is_primitive property."""
        assert refl(int).is_primitive is True
        assert refl(str).is_primitive is True
        assert refl(List[int]).is_primitive is False
        assert refl(Dict[str, int]).is_primitive is False
        assert NONE_TYPE_ID.is_primitive is True
