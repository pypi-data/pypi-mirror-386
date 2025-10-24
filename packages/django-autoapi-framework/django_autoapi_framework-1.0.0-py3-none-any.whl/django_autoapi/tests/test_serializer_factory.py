"""
Tests untuk SerializerFactory
"""

import pytest
from django.db import models
from rest_framework import serializers as drf_serializers
from django_autoapi.core import AutoAPI
from django_autoapi.factories.serializer import SerializerFactory
from django_autoapi.registry import AutoAPIRegistry


@pytest.fixture(autouse=True)
def clear_registry():
    """Clear registry"""
    AutoAPIRegistry.clear()
    yield
    AutoAPIRegistry.clear()


def test_auto_generate_serializer(sample_model):
    """Test: Serializer otomatis di-generate dari model"""
    
    class ProductAPI(AutoAPI):
        model = sample_model
    
    # Generate serializer
    serializer_class = SerializerFactory.create_serializer(ProductAPI)
    
    # Assertions
    assert serializer_class is not None
    assert issubclass(serializer_class, drf_serializers.ModelSerializer)
    assert serializer_class.Meta.model == sample_model
    assert serializer_class.Meta.fields == '__all__'


def test_serializer_with_read_only_fields(sample_model):
    """Test: read_only_fields configuration"""
    
    class ProductAPI(AutoAPI):
        model = sample_model
        read_only_fields = ['created_at', 'updated_at']
    
    serializer_class = SerializerFactory.create_serializer(ProductAPI)
    
    # Check Meta
    assert hasattr(serializer_class.Meta, 'read_only_fields')
    assert 'created_at' in serializer_class.Meta.read_only_fields
    assert 'updated_at' in serializer_class.Meta.read_only_fields


def test_serializer_with_exclude_fields(sample_model):
    """Test: exclude_fields configuration"""
    
    class ProductAPI(AutoAPI):
        model = sample_model
        exclude_fields = ['description', 'stock']
    
    serializer_class = SerializerFactory.create_serializer(ProductAPI)
    
    # Check Meta
    assert hasattr(serializer_class.Meta, 'exclude')
    assert 'description' in serializer_class.Meta.exclude
    assert 'stock' in serializer_class.Meta.exclude
    # Should not have 'fields' key when 'exclude' is used
    assert not hasattr(serializer_class.Meta, 'fields')


def test_serializer_with_specific_fields(sample_model):
    """Test: Specific fields only"""
    
    class ProductAPI(AutoAPI):
        model = sample_model
        fields = ['id', 'name', 'price']
    
    serializer_class = SerializerFactory.create_serializer(ProductAPI)
    
    # Check Meta
    assert serializer_class.Meta.fields == ['id', 'name', 'price']


def test_custom_serializer_override(sample_model):
    """Test: Custom serializer override auto-generation"""
    
    # Define custom serializer
    class CustomProductSerializer(drf_serializers.ModelSerializer):
        custom_field = drf_serializers.CharField(read_only=True)
        
        class Meta:
            model = sample_model
            fields = ['id', 'name', 'custom_field']
    
    class ProductAPI(AutoAPI):
        model = sample_model
        serializer_class = CustomProductSerializer
    
    # Should use custom serializer
    serializer_class = SerializerFactory.create_serializer(ProductAPI)
    assert serializer_class == CustomProductSerializer


def test_serializer_instantiation(sample_model):
    """Test: Generated serializer dapat di-instantiate"""
    
    class ProductAPI(AutoAPI):
        model = sample_model
    
    serializer_class = SerializerFactory.create_serializer(ProductAPI)
    
    # Test instantiation
    data = {
        'name': 'Test Product',
        'price': '99.99',
        'stock': 10,
    }
    
    serializer = serializer_class(data=data)
    
    # Should be instantiable
    assert serializer is not None
    assert hasattr(serializer, 'is_valid')


def test_serializer_validation(sample_model):
    """Test: Generated serializer validation works"""
    
    class ProductAPI(AutoAPI):
        model = sample_model
    
    serializer_class = SerializerFactory.create_serializer(ProductAPI)
    
    # Valid data
    valid_data = {
        'name': 'Test Product',
        'price': '99.99',
        'stock': 10,
    }
    
    serializer = serializer_class(data=valid_data)
    assert serializer.is_valid()
    
    # Invalid data (missing required field 'name')
    invalid_data = {
        'price': '99.99',
    }
    
    serializer = serializer_class(data=invalid_data)
    assert not serializer.is_valid()
    assert 'name' in serializer.errors


def test_serializer_extra_kwargs(sample_model):
    """Test: extra_kwargs configuration"""
    
    class ProductAPI(AutoAPI):
        model = sample_model
        extra_kwargs = {
            'name': {'required': True, 'min_length': 3},
            'price': {'required': True},
        }
    
    serializer_class = SerializerFactory.create_serializer(ProductAPI)
    
    # Check extra_kwargs applied
    assert hasattr(serializer_class.Meta, 'extra_kwargs')
    assert 'name' in serializer_class.Meta.extra_kwargs
    assert serializer_class.Meta.extra_kwargs['name']['min_length'] == 3


def test_write_only_fields(sample_model):
    """Test: write_only_fields configuration"""
    
    # Add password field to model
    sample_model.add_to_class('password', models.CharField(max_length=128))
    
    class ProductAPI(AutoAPI):
        model = sample_model
        write_only_fields = ['password']
    
    serializer_class = SerializerFactory.create_serializer(ProductAPI)
    
    # Password field should exist and be write_only
    serializer = serializer_class()
    assert 'password' in serializer.fields
    assert serializer.fields['password'].write_only is True


def test_serializer_name_generation(sample_model):
    """Test: Generated serializer has correct name"""
    
    class ProductAPI(AutoAPI):
        model = sample_model
    
    serializer_class = SerializerFactory.create_serializer(ProductAPI)
    
    # Check name
    assert serializer_class.__name__ == 'ProductSerializer'


def test_multiple_api_classes_different_serializers(sample_model):
    """Test: Different API classes generate different serializers"""

    class ProductAPI1(AutoAPI):
        model = sample_model
        fields = ['id', 'name']

    class ProductAPI2(AutoAPI):
        model = sample_model
        fields = ['id', 'name', 'price']

    # Both are registered now (multiple APIs per model supported!)
    # Test serializer generation for each
    serializer1 = SerializerFactory.create_serializer(ProductAPI1)
    serializer2 = SerializerFactory.create_serializer(ProductAPI2)
    
    # Should generate different serializers
    assert serializer1.Meta.fields == ['id', 'name']
    assert serializer2.Meta.fields == ['id', 'name', 'price']

    