"""
Tests untuk AutoAPI metaclass
"""

import pytest
from django.db import models
from django_autoapi.core import AutoAPI
from django_autoapi.registry import AutoAPIRegistry


@pytest.fixture(autouse=True)
def clear_registry():
    """Clear registry sebelum dan sesudah test"""
    AutoAPIRegistry.clear()
    yield
    AutoAPIRegistry.clear()


def test_metaclass_triggers_registration(sample_model):
    """Test: Metaclass automatically triggers registration"""
    
    # Create class
    class ProductAPI(AutoAPI):
        model = sample_model
    
    # Should be registered automatically
    assert AutoAPIRegistry.is_registered(sample_model)


def test_metaclass_skips_base_autoapi():
    """Test: Metaclass tidak register base AutoAPI class"""
    
    # AutoAPI itself should not be registered
    # (it has model=None)
    assert len(AutoAPIRegistry.get_all()) == 0


def test_metaclass_skips_class_without_model():
    """Test: Metaclass skip class tanpa model"""
    
    # This should raise ValueError from __init_subclass__
    # but NOT from metaclass registration
    with pytest.raises(ValueError, match='harus mendefinisikan'):
        class InvalidAPI(AutoAPI):
            pass


def test_metaclass_handles_duplicate_class_name_error(sample_model):
    """Test: Metaclass propagate registration errors for duplicate class names"""

    # First registration
    class ProductAPI(AutoAPI):
        model = sample_model

    # Same class name should error
    with pytest.raises(ValueError, match='Failed to register'):
        class ProductAPI(AutoAPI):  # Same name!
            model = sample_model


def test_metaclass_allows_multiple_registrations(sample_model):
    """Test: Metaclass allows multiple API classes for same model"""

    # First registration
    class ProductListAPI(AutoAPI):
        model = sample_model

    # Second registration with different name - should work
    class ProductDetailAPI(AutoAPI):
        model = sample_model

    # Both should be registered
    assert AutoAPIRegistry.is_registered(sample_model)
    api_classes = AutoAPIRegistry.get_api_classes(sample_model)
    assert len(api_classes) == 2

            