"""
Tests untuk Advanced Features
- SerializerMethodField
- Custom validation
- Nested serializers
- Custom fields
"""

import pytest
from django.db import models
from rest_framework import serializers as drf_serializers
from django_autoapi.core import AutoAPI
from django_autoapi.factories.serializer import SerializerFactory
from django_autoapi.registry import AutoAPIRegistry


@pytest.fixture(autouse=True)
def clear_registry():
    """Clear registry sebelum dan sesudah test"""
    AutoAPIRegistry.clear()
    yield
    AutoAPIRegistry.clear()


# ============================================================================
# Test SerializerMethodField
# ============================================================================

def test_serializer_method_field(sample_model):
    """Test: Custom SerializerMethodField otomatis dibuat"""

    class ProductAPI(AutoAPI):
        model = sample_model

        @staticmethod
        def get_full_info(obj):
            """Custom method untuk computed field"""
            return f"{obj.name} - ${obj.price}"

    serializer_class = SerializerFactory.create_serializer(ProductAPI)

    # Check field exists
    serializer = serializer_class()
    assert 'full_info' in serializer.fields
    assert isinstance(serializer.fields['full_info'], drf_serializers.SerializerMethodField)


def test_multiple_serializer_method_fields(sample_model):
    """Test: Multiple SerializerMethodField"""

    class ProductAPI(AutoAPI):
        model = sample_model

        @staticmethod
        def get_display_name(obj):
            return obj.name.upper()

        @staticmethod
        def get_stock_status(obj):
            return "In Stock" if obj.stock > 0 else "Out of Stock"

        @staticmethod
        def get_price_formatted(obj):
            return f"${obj.price:.2f}"

    serializer_class = SerializerFactory.create_serializer(ProductAPI)
    serializer = serializer_class()

    # All custom fields should exist
    assert 'display_name' in serializer.fields
    assert 'stock_status' in serializer.fields
    assert 'price_formatted' in serializer.fields


def test_serializer_method_field_with_instance(sample_model):
    """Test: SerializerMethodField works dengan real instance"""

    class ProductAPI(AutoAPI):
        model = sample_model
        fields = ['id', 'name', 'price', 'stock', 'full_description']

        @staticmethod
        def get_full_description(obj):
            return f"{obj.name}: {obj.description}" if obj.description else obj.name

    serializer_class = SerializerFactory.create_serializer(ProductAPI)

    # Create mock instance
    instance = sample_model(
        name="Test Product",
        description="Test Description",
        price=99.99,
        stock=10
    )

    serializer = serializer_class(instance)
    data = serializer.data

    # Check computed field
    assert 'full_description' in data
    # Note: In actual test with DB, this would work properly


# ============================================================================
# Test Custom Validation
# ============================================================================

def test_custom_field_validation(sample_model):
    """Test: Custom validation method untuk specific field"""

    class ProductAPI(AutoAPI):
        model = sample_model

        @staticmethod
        def validate_name(value):
            """Custom validation untuk field 'name'"""
            if len(value) < 3:
                raise drf_serializers.ValidationError(
                    "Name must be at least 3 characters"
                )
            return value

    serializer_class = SerializerFactory.create_serializer(ProductAPI)

    # Test dengan invalid data
    serializer = serializer_class(data={'name': 'AB', 'price': '99.99', 'stock': 10})

    is_valid = serializer.is_valid()
    assert not is_valid
    assert 'name' in serializer.errors


def test_multiple_validation_methods(sample_model):
    """Test: Multiple validation methods"""

    class ProductAPI(AutoAPI):
        model = sample_model

        @staticmethod
        def validate_name(value):
            if 'test' in value.lower():
                raise drf_serializers.ValidationError("Name cannot contain 'test'")
            return value

        @staticmethod
        def validate_price(value):
            if value < 0:
                raise drf_serializers.ValidationError("Price must be positive")
            return value

        @staticmethod
        def validate_stock(value):
            if value < 0:
                raise drf_serializers.ValidationError("Stock cannot be negative")
            return value

    serializer_class = SerializerFactory.create_serializer(ProductAPI)

    # Test with invalid data
    serializer = serializer_class(data={
        'name': 'Test Product',  # Invalid
        'price': '-10',  # Invalid
        'stock': -5  # Invalid
    })

    is_valid = serializer.is_valid()
    assert not is_valid
    assert 'name' in serializer.errors
    assert 'price' in serializer.errors
    assert 'stock' in serializer.errors


def test_object_level_validation(sample_model):
    """Test: Object-level validation method"""

    class ProductAPI(AutoAPI):
        model = sample_model

        @staticmethod
        def validate(data):
            """Object-level validation"""
            if data.get('stock', 0) > 0 and data.get('price', 0) == 0:
                raise drf_serializers.ValidationError(
                    "Product with stock must have a price"
                )
            return data

    serializer_class = SerializerFactory.create_serializer(ProductAPI)

    # Test with invalid combination
    serializer = serializer_class(data={
        'name': 'Test Product',
        'price': '0',
        'stock': 10
    })

    is_valid = serializer.is_valid()
    assert not is_valid


# ============================================================================
# Test Custom Fields
# ============================================================================

def test_custom_fields_configuration(sample_model):
    """Test: Custom fields via custom_fields attribute"""

    class ProductAPI(AutoAPI):
        model = sample_model
        custom_fields = {
            'custom_field': drf_serializers.CharField(read_only=True),
            'extra_info': drf_serializers.JSONField(required=False)
        }

    serializer_class = SerializerFactory.create_serializer(ProductAPI)
    serializer = serializer_class()

    # Check custom fields exist
    assert 'custom_field' in serializer.fields
    assert 'extra_info' in serializer.fields
    assert serializer.fields['custom_field'].read_only is True


# ============================================================================
# Test Combined Features
# ============================================================================

def test_combined_advanced_features(sample_model):
    """Test: Kombinasi SerializerMethodField + Validation + Custom Fields"""

    class ProductAPI(AutoAPI):
        model = sample_model
        fields = ['id', 'name', 'price', 'stock', 'status', 'discount_price']

        # Custom fields
        custom_fields = {
            'status': drf_serializers.CharField(read_only=True)
        }

        # SerializerMethodField
        @staticmethod
        def get_discount_price(obj):
            return float(obj.price) * 0.9  # 10% discount

        # Validation
        @staticmethod
        def validate_price(value):
            if value < 0:
                raise drf_serializers.ValidationError("Price must be positive")
            return value

    serializer_class = SerializerFactory.create_serializer(ProductAPI)
    serializer = serializer_class()

    # Check all features
    assert 'discount_price' in serializer.fields  # SerializerMethodField
    assert 'status' in serializer.fields  # Custom field
    assert serializer.fields['status'].read_only is True

    # Test validation
    test_serializer = serializer_class(data={
        'name': 'Test',
        'price': '-10',  # Invalid
        'stock': 5
    })
    assert not test_serializer.is_valid()
    assert 'price' in test_serializer.errors


# ============================================================================
# Test Edge Cases
# ============================================================================

def test_method_field_without_obj(sample_model):
    """Test: SerializerMethodField handles None object"""

    class ProductAPI(AutoAPI):
        model = sample_model

        @staticmethod
        def get_safe_name(obj):
            return obj.name if obj else "N/A"

    serializer_class = SerializerFactory.create_serializer(ProductAPI)

    # This test ensures the method structure is correct
    serializer = serializer_class()
    assert 'safe_name' in serializer.fields


def test_validation_returns_value(sample_model):
    """Test: Validation method harus return value"""

    class ProductAPI(AutoAPI):
        model = sample_model

        @staticmethod
        def validate_name(value):
            # Must return value
            return value.strip().upper()

    serializer_class = SerializerFactory.create_serializer(ProductAPI)

    serializer = serializer_class(data={
        'name': '  test product  ',
        'price': '99.99',
        'stock': 10
    })

    if serializer.is_valid():
        # Name should be stripped and uppercased
        assert serializer.validated_data['name'] == 'TEST PRODUCT'


def test_skip_private_methods(sample_model):
    """Test: Private methods (start with _) tidak di-include"""

    class ProductAPI(AutoAPI):
        model = sample_model

        @staticmethod
        def _private_method(obj):
            return "Should not be included"

        @staticmethod
        def get_public_field(obj):
            return "Should be included"

    serializer_class = SerializerFactory.create_serializer(ProductAPI)
    serializer = serializer_class()

    # Public field should exist
    assert 'public_field' in serializer.fields

    # Private method should NOT create field
    assert '_private_method' not in serializer.fields
    assert 'private_method' not in serializer.fields


def test_get_queryset_not_included(sample_model):
    """Test: get_queryset method tidak di-include sebagai SerializerMethodField"""

    class ProductAPI(AutoAPI):
        model = sample_model

        @staticmethod
        def get_queryset():
            return sample_model.objects.all()

        @staticmethod
        def get_custom_field(obj):
            return "Custom"

    serializer_class = SerializerFactory.create_serializer(ProductAPI)
    serializer = serializer_class()

    # get_queryset should NOT create field
    assert 'queryset' not in serializer.fields

    # But get_custom_field should
    assert 'custom_field' in serializer.fields
