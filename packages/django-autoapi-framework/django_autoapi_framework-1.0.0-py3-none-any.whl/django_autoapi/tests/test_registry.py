"""
Tests untuk AutoAPI registry system
"""

import pytest
from django.db import models
from django_autoapi.core import AutoAPI
from django_autoapi.registry import AutoAPIRegistry


@pytest.fixture(autouse=True)
def clear_registry():
    """Clear registry sebelum dan sesudah setiap test"""
    AutoAPIRegistry.clear()
    yield
    AutoAPIRegistry.clear()


# Note: another_model fixture moved to conftest.py
# It's now shared across all test files


def test_auto_registration(sample_model):
    """Test: Class otomatis ter-register via metaclass"""
    
    class ProductAPI(AutoAPI):
        model = sample_model
    
    # Check registered
    assert AutoAPIRegistry.is_registered(sample_model)
    
    # Check dapat di-retrieve
    api_class = AutoAPIRegistry.get_api_class(sample_model)
    assert api_class == ProductAPI


def test_registration_with_multiple_classes(sample_model, another_model):
    """Test: Multiple classes bisa registered"""
    
    class ProductAPI(AutoAPI):
        model = sample_model
    
    class CategoryAPI(AutoAPI):
        model = another_model
    
    # Both registered
    assert AutoAPIRegistry.is_registered(sample_model)
    assert AutoAPIRegistry.is_registered(another_model)
    
    # Can retrieve both
    assert AutoAPIRegistry.get_api_class(sample_model) == ProductAPI
    assert AutoAPIRegistry.get_api_class(another_model) == CategoryAPI


def test_duplicate_registration_allows_different_names(sample_model):
    """Test: Multiple API classes dengan nama berbeda diperbolehkan"""

    class ProductAPI1(AutoAPI):
        model = sample_model

    # Different name, same model - should work!
    class ProductAPI2(AutoAPI):
        model = sample_model

    # Both should be registered
    api_classes = AutoAPIRegistry.get_api_classes(sample_model)
    assert len(api_classes) == 2
    assert ProductAPI1 in api_classes
    assert ProductAPI2 in api_classes


def test_duplicate_class_name_raises_error(sample_model):
    """Test: Duplicate API class name harus error"""

    class ProductAPI(AutoAPI):
        model = sample_model

    # Same class name - should error
    with pytest.raises(ValueError, match='already registered'):
        class ProductAPI(AutoAPI):  # Same name!
            model = sample_model


def test_get_all_registered(sample_model, another_model):
    """Test: get_all() returns semua registered classes"""
    
    class ProductAPI(AutoAPI):
        model = sample_model
    
    class CategoryAPI(AutoAPI):
        model = another_model
    
    all_apis = AutoAPIRegistry.get_all()
    
    assert len(all_apis) == 2
    assert ProductAPI in all_apis
    assert CategoryAPI in all_apis


def test_unregister(sample_model):
    """Test: unregister menghapus dari registry"""
    
    class ProductAPI(AutoAPI):
        model = sample_model
    
    # Registered
    assert AutoAPIRegistry.is_registered(sample_model)
    
    # Unregister
    result = AutoAPIRegistry.unregister(ProductAPI)
    assert result is True
    
    # Not registered anymore
    assert not AutoAPIRegistry.is_registered(sample_model)


def test_get_registry_info(sample_model, another_model):
    """Test: get_registry_info returns correct info"""

    class ProductAPI(AutoAPI):
        model = sample_model

    class CategoryAPI(AutoAPI):
        model = another_model

    info = AutoAPIRegistry.get_registry_info()

    assert info['total_registered'] == 2
    assert info['total_models'] == 2
    assert 'test_app.product' in info['models']
    assert 'test_app.category' in info['models']
    assert 'ProductAPI' in info['api_classes']
    assert 'CategoryAPI' in info['api_classes']


def test_get_api_classes_returns_all(sample_model):
    """Test: get_api_classes returns all API classes for a model"""

    class ProductListAPI(AutoAPI):
        model = sample_model

    class ProductDetailAPI(AutoAPI):
        model = sample_model

    class ProductSummaryAPI(AutoAPI):
        model = sample_model

    # Get all API classes for this model
    api_classes = AutoAPIRegistry.get_api_classes(sample_model)

    assert len(api_classes) == 3
    assert ProductListAPI in api_classes
    assert ProductDetailAPI in api_classes
    assert ProductSummaryAPI in api_classes


def test_is_registered_returns_false_for_unregistered(sample_model):
    """Test: is_registered returns False untuk model yang belum registered"""
    assert not AutoAPIRegistry.is_registered(sample_model)


def test_get_api_class_returns_none_for_unregistered(sample_model):
    """Test: get_api_class returns None untuk model yang belum registered"""
    assert AutoAPIRegistry.get_api_class(sample_model) is None


def test_clear_registry(sample_model):
    """Test: clear() menghapus semua registration"""
    
    class ProductAPI(AutoAPI):
        model = sample_model
    
    # Registered
    assert AutoAPIRegistry.is_registered(sample_model)
    
    # Clear
    AutoAPIRegistry.clear()
    
    # Empty
    assert not AutoAPIRegistry.is_registered(sample_model)
    assert len(AutoAPIRegistry.get_all()) == 0


def test_get_model_key(sample_model):
    """Test: get_model_key returns correct key"""
    
    class ProductAPI(AutoAPI):
        model = sample_model
    
    assert ProductAPI.get_model_key() == 'test_app.product'

    