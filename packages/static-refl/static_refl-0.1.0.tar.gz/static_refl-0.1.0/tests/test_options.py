"""Tests for static_refl.options module."""
import pytest
from dataclasses import dataclass
from static_refl.options import refl_options, refl_rename, get_refl_options


class TestReflOptions:
    """Test refl_options decorator."""

    def test_refl_options_rename_all_kebab(self):
        """Test rename_all with kebab-case."""
        @refl_options(rename_all="kebab-case")
        @dataclass
        class TestClass:
            full_name: str

        opts = get_refl_options(TestClass)
        assert opts["rename_all"] == "kebab-case"
        assert opts["rename_map"] == {}

    def test_refl_options_rename_all_snake(self):
        """Test rename_all with snake_case."""
        @refl_options(rename_all="snake_case")
        @dataclass
        class TestClass:
            fullName: str

        opts = get_refl_options(TestClass)
        assert opts["rename_all"] == "snake_case"

    def test_refl_options_rename_all_camel(self):
        """Test rename_all with camelCase."""
        @refl_options(rename_all="camelCase")
        @dataclass
        class TestClass:
            full_name: str

        opts = get_refl_options(TestClass)
        assert opts["rename_all"] == "camelCase"

    def test_refl_options_default(self):
        """Test default options without decorator."""
        @dataclass
        class TestClass:
            name: str

        opts = get_refl_options(TestClass)
        assert opts["rename_all"] is None
        assert opts["rename_map"] == {}


class TestReflRename:
    """Test refl_rename decorator."""

    def test_refl_rename_single_field(self):
        """Test renaming a single field."""
        @refl_rename(full_name="fullName")
        @dataclass
        class TestClass:
            full_name: str

        opts = get_refl_options(TestClass)
        assert opts["rename_map"] == {"full_name": "fullName"}
        assert opts["rename_all"] is None

    def test_refl_rename_multiple_fields(self):
        """Test renaming multiple fields."""
        @refl_rename(first_name="firstName", last_name="lastName")
        @dataclass
        class TestClass:
            first_name: str
            last_name: str

        opts = get_refl_options(TestClass)
        assert opts["rename_map"] == {
            "first_name": "firstName",
            "last_name": "lastName"
        }

    def test_refl_rename_combined_with_options(self):
        """Test combining refl_rename with refl_options."""
        @refl_options(rename_all="kebab-case")
        @refl_rename(special_field="customName")
        @dataclass
        class TestClass:
            special_field: str
            other_field: str

        opts = get_refl_options(TestClass)
        assert opts["rename_all"] == "kebab-case"
        assert opts["rename_map"] == {"special_field": "customName"}

    def test_refl_rename_empty(self):
        """Test refl_rename with no arguments."""
        @refl_rename()
        @dataclass
        class TestClass:
            name: str

        opts = get_refl_options(TestClass)
        assert opts["rename_map"] == {}


class TestGetReflOptions:
    """Test get_refl_options function."""

    def test_get_refl_options_marks_as_done(self):
        """Test that get_refl_options marks class as finalized."""
        @dataclass
        class TestClass:
            name: str

        # First call should mark as done
        get_refl_options(TestClass)
        assert hasattr(TestClass, "__srefl_class_done__")

    def test_cannot_apply_options_after_finalized(self):
        """Test that decorators cannot be applied after finalization."""
        @dataclass
        class TestClass:
            name: str

        # Finalize the class
        get_refl_options(TestClass)

        # Try to apply decorator - should fail
        with pytest.raises(RuntimeError, match="Cannot apply refl_options"):
            refl_options(rename_all="kebab-case")(TestClass)

    def test_cannot_apply_rename_after_finalized(self):
        """Test that refl_rename cannot be applied after finalization."""
        @dataclass
        class TestClass:
            name: str

        # Finalize the class
        get_refl_options(TestClass)

        # Try to apply decorator - should fail
        with pytest.raises(RuntimeError, match="Cannot apply refl_rename"):
            refl_rename(name="customName")(TestClass)
