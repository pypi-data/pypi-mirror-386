"""Tests for static_refl.serde_common module."""
import pytest
from dataclasses import dataclass
from typing import Union, Literal, Any
from static_refl.serde_common import orthogonal_split, SplitFastTell, TagInfo, _get_tag_info
from static_refl.core import refl, TypeIdUnion, TypeIdDataClass


class TestOrthogonalSplit:
    """Test orthogonal_split function for union type splitting."""

    def test_split_literal_union(self):
        """Test splitting union of literals."""
        union_type = refl(Union[Literal["a"], Literal["b"], Literal["c"]])
        assert isinstance(union_type, TypeIdUnion)

        split = orthogonal_split(union_type)

        assert split.fast_tell == SplitFastTell.all_lit
        assert len(split.literals) == 3
        assert "a" in split.literals
        assert "b" in split.literals
        assert "c" in split.literals
        assert len(split.dataclasses) == 0
        assert len(split.typeddicts) == 0
        assert len(split.others) == 0
        assert split.has_any is False

    def test_split_dataclass_union(self):
        """Test splitting union of dataclasses."""
        @dataclass
        class Dog:
            kind: Literal["dog"]
            breed: str

        @dataclass
        class Cat:
            kind: Literal["cat"]
            indoor: bool

        union_type = refl(Union[Dog, Cat])
        assert isinstance(union_type, TypeIdUnion)

        split = orthogonal_split(union_type)

        assert split.fast_tell == SplitFastTell.all_dataclass
        assert len(split.dataclasses) == 2
        assert "dog" in split.dataclasses
        assert "cat" in split.dataclasses
        assert split.dataclass_tagname == "kind"
        assert len(split.literals) == 0
        assert len(split.typeddicts) == 0
        assert len(split.others) == 0

    def test_split_primitive_union(self):
        """Test splitting union of primitive types."""
        union_type = refl(Union[int, str, float])
        assert isinstance(union_type, TypeIdUnion)

        split = orthogonal_split(union_type)

        assert split.fast_tell == SplitFastTell.all_other
        assert len(split.others) == 3
        assert int in split.others
        assert str in split.others
        assert float in split.others
        assert len(split.literals) == 0
        assert len(split.dataclasses) == 0

    def test_split_mixed_union(self):
        """Test splitting mixed union."""
        @dataclass
        class Dog:
            kind: Literal["dog"]
            breed: str

        union_type = refl(Union[Dog, Literal["cat"], int])
        assert isinstance(union_type, TypeIdUnion)

        split = orthogonal_split(union_type)

        assert split.fast_tell == SplitFastTell.mixed
        assert len(split.dataclasses) == 1
        assert len(split.literals) == 1
        assert len(split.others) == 1

    def test_split_union_with_any(self):
        """Test splitting union containing Any."""
        union_type = refl(Union[int, str, Any])
        assert isinstance(union_type, TypeIdUnion)

        split = orthogonal_split(union_type)

        assert split.has_any is True
        # Fast tell should be mixed when Any is present
        assert split.fast_tell == SplitFastTell.mixed


class TestGetTagInfo:
    """Test _get_tag_info function for extracting tag information."""

    def test_get_tag_info_string_literal(self):
        """Test tag extraction with string literal."""
        @dataclass
        class Dog:
            kind: Literal["dog"]
            breed: str

        tid = refl(Dog)
        assert isinstance(tid, TypeIdDataClass)

        tag_info = _get_tag_info(tid)

        assert tag_info.name == "kind"
        assert tag_info.value == "dog"

    def test_get_tag_info_int_literal(self):
        """Test tag extraction with int literal."""
        @dataclass
        class Response:
            status: Literal[200]
            body: str

        tid = refl(Response)
        assert isinstance(tid, TypeIdDataClass)

        tag_info = _get_tag_info(tid)

        assert tag_info.name == "status"
        assert tag_info.value == 200

    def test_get_tag_info_empty_fields_error(self):
        """Test that empty dataclass raises error."""
        @dataclass
        class Empty:
            pass

        tid = refl(Empty)
        assert isinstance(tid, TypeIdDataClass)

        with pytest.raises(ValueError, match="empty fields cannot be used in union"):
            _get_tag_info(tid)

    def test_get_tag_info_non_literal_error(self):
        """Test that non-literal first field raises error."""
        @dataclass
        class Invalid:
            kind: str  # Not a literal
            value: int

        tid = refl(Invalid)
        assert isinstance(tid, TypeIdDataClass)

        with pytest.raises(ValueError, match="must have a first field with literal type"):
            _get_tag_info(tid)

    def test_get_tag_info_invalid_literal_type_error(self):
        """Test that literal with invalid type raises error."""
        # Note: Literal[True] is actually converted to Literal[1] in Python's type system
        # So we test with None literal instead (which is valid but will fail the int/str check)
        @dataclass
        class Invalid:
            kind: Literal[None]  # None literal not allowed for union tags
            value: int

        tid = refl(Invalid)
        assert isinstance(tid, TypeIdDataClass)

        with pytest.raises(ValueError, match="int or str literal type"):
            _get_tag_info(tid)


class TestUnionTagConsistency:
    """Test that union types enforce consistent tag field names."""

    def test_inconsistent_tag_names_error(self):
        """Test that dataclasses with different tag field names raise error."""
        @dataclass
        class Dog:
            kind: Literal["dog"]
            breed: str

        @dataclass
        class Cat:
            type: Literal["cat"]  # Different field name
            indoor: bool

        union_type = refl(Union[Dog, Cat])
        assert isinstance(union_type, TypeIdUnion)

        with pytest.raises(ValueError, match="same tag field name"):
            orthogonal_split(union_type)

    def test_consistent_tag_names_success(self):
        """Test that dataclasses with same tag field names work."""
        @dataclass
        class Dog:
            animal_type: Literal["dog"]
            breed: str

        @dataclass
        class Cat:
            animal_type: Literal["cat"]
            indoor: bool

        union_type = refl(Union[Dog, Cat])
        assert isinstance(union_type, TypeIdUnion)

        split = orthogonal_split(union_type)
        assert split.dataclass_tagname == "animal_type"
        assert len(split.dataclasses) == 2


class TestOrthogonalSplitCaching:
    """Test that orthogonal_split results are cached."""

    def test_split_caching(self):
        """Test that split results are cached."""
        union_type = refl(Union[Literal["a"], Literal["b"]])
        assert isinstance(union_type, TypeIdUnion)

        split1 = orthogonal_split(union_type)
        split2 = orthogonal_split(union_type)

        # Should be the same object due to caching
        assert split1 is split2


class TestSplitFastTell:
    """Test SplitFastTell enum values."""

    def test_split_fast_tell_values(self):
        """Test that SplitFastTell has expected values."""
        assert SplitFastTell.mixed.value == 1
        assert SplitFastTell.all_dataclass.value == 2
        assert SplitFastTell.all_lit.value == 3
        assert SplitFastTell.all_other.value == 4


class TestComplexUnionScenarios:
    """Test complex union scenarios."""

    def test_nested_union_dataclasses(self):
        """Test union with nested structures."""
        @dataclass
        class Success:
            status: Literal["success"]
            data: str

        @dataclass
        class Error:
            status: Literal["error"]
            message: str

        @dataclass
        class Pending:
            status: Literal["pending"]

        union_type = refl(Union[Success, Error, Pending])
        assert isinstance(union_type, TypeIdUnion)

        split = orthogonal_split(union_type)

        assert split.fast_tell == SplitFastTell.all_dataclass
        assert len(split.dataclasses) == 3
        assert "success" in split.dataclasses
        assert "error" in split.dataclasses
        assert "pending" in split.dataclasses
        assert split.dataclass_tagname == "status"

    def test_union_with_complex_literals(self):
        """Test union with multiple literal types."""
        union_type = refl(Union[Literal[1, 2, 3], Literal["a", "b", "c"]])
        assert isinstance(union_type, TypeIdUnion)

        split = orthogonal_split(union_type)

        assert split.fast_tell == SplitFastTell.all_lit
        # Should have all literal values
        assert 1 in split.literals
        assert 2 in split.literals
        assert 3 in split.literals
        assert "a" in split.literals
        assert "b" in split.literals
        assert "c" in split.literals
