"""Tests for static_refl.utils module."""
import pytest
from static_refl.utils import transform_case


class TestTransformCase:
    """Test case transformation utility."""

    def test_transform_case_kebab(self):
        """Test kebab-case transformation."""
        assert transform_case("full_name", "kebab-case") == "full-name"
        assert transform_case("firstName", "kebab-case") == "first-name"
        assert transform_case("FULL_NAME", "kebab-case") == "full-name"

    def test_transform_case_snake(self):
        """Test snake_case transformation."""
        assert transform_case("fullName", "snake_case") == "full_name"
        assert transform_case("full-name", "snake_case") == "full_name"
        assert transform_case("FULLNAME", "snake_case") == "fullname"

    def test_transform_case_lowercase(self):
        """Test lowercase transformation."""
        assert transform_case("FullName", "lowercase") == "fullname"
        assert transform_case("FULL_NAME", "lowercase") == "full_name"  # Preserves underscores
        assert transform_case("full_name", "lowercase") == "full_name"

    def test_transform_case_uppercase(self):
        """Test UPPERCASE transformation."""
        assert transform_case("fullName", "UPPERCASE") == "FULLNAME"
        assert transform_case("full_name", "UPPERCASE") == "FULL_NAME"  # Preserves underscores
        assert transform_case("full-name", "UPPERCASE") == "FULL-NAME"  # Preserves hyphens

    def test_transform_case_camel(self):
        """Test camelCase transformation."""
        assert transform_case("full_name", "camelCase") == "fullName"
        assert transform_case("full-name", "camelCase") == "fullName"
        assert transform_case("FULL_NAME", "camelCase") == "fullName"

    def test_transform_case_none(self):
        """Test None case (no transformation)."""
        assert transform_case("full_name", None) == "full_name"
        assert transform_case("fullName", None) == "fullName"
        assert transform_case("full-name", None) == "full-name"

    def test_transform_case_invalid(self):
        """Test invalid case transformation."""
        with pytest.raises(ValueError, match="Unknown case"):
            transform_case("test", "invalid-case")  # type: ignore

    def test_transform_case_caching(self):
        """Test that transform_case caches results."""
        # Call twice with same arguments
        result1 = transform_case("test_value", "kebab-case")
        result2 = transform_case("test_value", "kebab-case")
        # Results should be identical (same object due to caching)
        assert result1 is result2
