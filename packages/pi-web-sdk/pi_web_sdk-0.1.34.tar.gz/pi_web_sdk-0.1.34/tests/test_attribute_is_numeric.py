"""Tests for Attribute.is_numeric() and AttributeTemplate.is_numeric() methods."""

import pytest
from pi_web_sdk.models.attribute import Attribute, AttributeTemplate, AttributeType


def test_is_numeric_with_double():
    """Test that Double type is recognized as numeric."""
    attr = Attribute(type=AttributeType.DOUBLE.value)
    assert attr.is_numeric() is True


def test_is_numeric_with_int32():
    """Test that Int32 type is recognized as numeric."""
    attr = Attribute(type=AttributeType.INT32.value)
    assert attr.is_numeric() is True


def test_is_numeric_with_int16():
    """Test that Int16 type is recognized as numeric."""
    attr = Attribute(type=AttributeType.INT16.value)
    assert attr.is_numeric() is True


def test_is_numeric_with_int64():
    """Test that Int64 type is recognized as numeric."""
    attr = Attribute(type=AttributeType.INT64.value)
    assert attr.is_numeric() is True


def test_is_numeric_with_single():
    """Test that Single type is recognized as numeric."""
    attr = Attribute(type=AttributeType.SINGLE.value)
    assert attr.is_numeric() is True


def test_is_numeric_with_byte():
    """Test that Byte type is recognized as numeric."""
    attr = Attribute(type=AttributeType.BYTE.value)
    assert attr.is_numeric() is True


def test_is_numeric_with_string():
    """Test that String type is not recognized as numeric."""
    attr = Attribute(type=AttributeType.STRING.value)
    assert attr.is_numeric() is False


def test_is_numeric_with_boolean():
    """Test that Boolean type is not recognized as numeric."""
    attr = Attribute(type=AttributeType.BOOLEAN.value)
    assert attr.is_numeric() is False


def test_is_numeric_with_datetime():
    """Test that DateTime type is not recognized as numeric."""
    attr = Attribute(type=AttributeType.DATETIME.value)
    assert attr.is_numeric() is False


def test_is_numeric_with_blob():
    """Test that Blob type is not recognized as numeric."""
    attr = Attribute(type=AttributeType.BLOB.value)
    assert attr.is_numeric() is False


def test_is_numeric_with_guid():
    """Test that Guid type is not recognized as numeric."""
    attr = Attribute(type=AttributeType.GUID.value)
    assert attr.is_numeric() is False


def test_is_numeric_with_none_type():
    """Test that None type returns False."""
    attr = Attribute(type=None)
    assert attr.is_numeric() is False


def test_is_numeric_with_no_type():
    """Test that attribute without type returns False."""
    attr = Attribute()
    assert attr.is_numeric() is False


def test_is_numeric_case_sensitive():
    """Test that type comparison is case-sensitive."""
    # Using lowercase should not match
    attr = Attribute(type="double")
    assert attr.is_numeric() is False

    # Using correct case should match
    attr = Attribute(type="Double")
    assert attr.is_numeric() is True


def test_is_numeric_with_all_numeric_types():
    """Test all numeric types at once."""
    numeric_types = [
        AttributeType.BYTE,
        AttributeType.INT16,
        AttributeType.INT32,
        AttributeType.INT64,
        AttributeType.DOUBLE,
        AttributeType.SINGLE,
    ]

    for attr_type in numeric_types:
        attr = Attribute(type=attr_type.value)
        assert attr.is_numeric() is True, f"{attr_type.value} should be numeric"


def test_is_numeric_with_all_non_numeric_types():
    """Test all non-numeric types at once."""
    non_numeric_types = [
        AttributeType.STRING,
        AttributeType.BOOLEAN,
        AttributeType.DATETIME,
        AttributeType.BLOB,
        AttributeType.GUID,
    ]

    for attr_type in non_numeric_types:
        attr = Attribute(type=attr_type.value)
        assert attr.is_numeric() is False, f"{attr_type.value} should not be numeric"


# Tests for AttributeTemplate.is_numeric()

def test_template_is_numeric_with_double():
    """Test that Double type is recognized as numeric for AttributeTemplate."""
    template = AttributeTemplate(type=AttributeType.DOUBLE.value)
    assert template.is_numeric() is True


def test_template_is_numeric_with_int32():
    """Test that Int32 type is recognized as numeric for AttributeTemplate."""
    template = AttributeTemplate(type=AttributeType.INT32.value)
    assert template.is_numeric() is True


def test_template_is_numeric_with_string():
    """Test that String type is not recognized as numeric for AttributeTemplate."""
    template = AttributeTemplate(type=AttributeType.STRING.value)
    assert template.is_numeric() is False


def test_template_is_numeric_with_none():
    """Test that None type returns False for AttributeTemplate."""
    template = AttributeTemplate(type=None)
    assert template.is_numeric() is False


def test_template_is_numeric_with_all_numeric_types():
    """Test all numeric types at once for AttributeTemplate."""
    numeric_types = [
        AttributeType.BYTE,
        AttributeType.INT16,
        AttributeType.INT32,
        AttributeType.INT64,
        AttributeType.DOUBLE,
        AttributeType.SINGLE,
    ]

    for attr_type in numeric_types:
        template = AttributeTemplate(type=attr_type.value)
        assert template.is_numeric() is True, f"{attr_type.value} should be numeric"


def test_template_is_numeric_with_all_non_numeric_types():
    """Test all non-numeric types at once for AttributeTemplate."""
    non_numeric_types = [
        AttributeType.STRING,
        AttributeType.BOOLEAN,
        AttributeType.DATETIME,
        AttributeType.BLOB,
        AttributeType.GUID,
    ]

    for attr_type in non_numeric_types:
        template = AttributeTemplate(type=attr_type.value)
        assert template.is_numeric() is False, f"{attr_type.value} should not be numeric"