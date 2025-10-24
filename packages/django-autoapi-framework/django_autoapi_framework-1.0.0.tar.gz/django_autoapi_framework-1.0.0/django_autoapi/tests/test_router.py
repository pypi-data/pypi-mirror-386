"""
Tests untuk AutoAPIRouter
"""

import pytest
from django.db import models
from django_autoapi.core import AutoAPI
from django_autoapi.routers import AutoAPIRouter
from django_autoapi.registry import AutoAPIRegistry


@pytest.fixture(autouse=True)
def clear_registry():
    """Clear registry"""
    AutoAPIRegistry.clear()
    yield
    AutoAPIRegistry.clear()


# Note: product_model and category_model fixtures removed
# Use sample_model and another_model from conftest.py instead


def test_router_creation():
    """Test: Router dapat dibuat"""
    router = AutoAPIRouter()
    assert router is not None


def test_register_api_class(sample_model):
    """Test: Register API class ke router"""

    class ProductAPI(AutoAPI):
        model = sample_model
    
    router = AutoAPIRouter()
    router.register(ProductAPI)
    
    # Check registered
    registered = router.get_registered_apis()
    assert 'test_app.product' in registered


def test_register_generates_urls(sample_model):
    """Test: Registration generates URLs"""

    class ProductAPI(AutoAPI):
        model = sample_model
    
    router = AutoAPIRouter()
    router.register(ProductAPI)
    
    # Check URLs generated
    urls = router.urls
    assert len(urls) > 0


def test_register_with_custom_prefix(sample_model):
    """Test: Register dengan custom prefix"""

    class ProductAPI(AutoAPI):
        model = sample_model
    
    router = AutoAPIRouter()
    router.register(ProductAPI, prefix='items')
    
    # Check custom prefix used
    registered = router.get_registered_apis()
    assert registered['test_app.product']['prefix'] == 'items'


def test_register_with_custom_basename(sample_model):
    """Test: Register dengan custom basename"""

    class ProductAPI(AutoAPI):
        model = sample_model
    
    router = AutoAPIRouter()
    router.register(ProductAPI, basename='item')
    
    # Check custom basename used
    registered = router.get_registered_apis()
    assert registered['test_app.product']['basename'] == 'item'


def test_autodiscover(sample_model, another_model):
    """Test: Autodiscover registers all APIs"""

    class ProductAPI(AutoAPI):
        model = sample_model

    class CategoryAPI(AutoAPI):
        model = another_model

    # Both should be in registry
    assert AutoAPIRegistry.is_registered(sample_model)
    assert AutoAPIRegistry.is_registered(another_model)
    
    # Autodiscover
    router = AutoAPIRouter()
    router.autodiscover()
    
    # Both should be registered in router
    registered = router.get_registered_apis()
    assert 'test_app.product' in registered
    assert 'test_app.category' in registered


def test_autodiscover_idempotent(sample_model):
    """Test: Autodiscover safe to call multiple times"""

    class ProductAPI(AutoAPI):
        model = sample_model
    
    router = AutoAPIRouter()
    
    # Call multiple times
    router.autodiscover()
    router.autodiscover()
    router.autodiscover()
    
    # Should only register once
    registered = router.get_registered_apis()
    assert len(registered) == 1


def test_unregister(sample_model):
    """Test: Unregister removes API"""

    class ProductAPI(AutoAPI):
        model = sample_model
    
    router = AutoAPIRouter()
    router.register(ProductAPI)
    
    # Check registered
    assert 'test_app.product' in router.get_registered_apis()
    
    # Unregister
    result = router.unregister(ProductAPI)
    assert result is True
    
    # Check not registered
    assert 'test_app.product' not in router.get_registered_apis()


def test_unregister_by_prefix(sample_model):
    """Test: Unregister by prefix"""

    class ProductAPI(AutoAPI):
        model = sample_model
    
    router = AutoAPIRouter()
    router.register(ProductAPI)
    
    # Unregister by prefix
    result = router.unregister('products')
    assert result is True


def test_get_api_info(sample_model):
    """Test: Get API info"""

    class ProductAPI(AutoAPI):
        model = sample_model
        filterable = ['name']
    
    router = AutoAPIRouter()
    router.register(ProductAPI)
    
    # Get info
    info = router.get_api_info(ProductAPI)
    assert info is not None
    assert info['api_class'] == ProductAPI
    assert info['prefix'] == 'products'
    assert info['basename'] == 'product'


def test_prefix_pluralization(sample_model):
    """Test: Prefix pluralization"""

    class ProductAPI(AutoAPI):
        model = sample_model
    
    router = AutoAPIRouter()
    router.register(ProductAPI)
    
    # Check pluralization
    info = router.get_api_info(ProductAPI)
    assert info['prefix'] == 'products'  # product -> products


def test_register_multiple_apis(sample_model, another_model):
    """Test: Register multiple APIs"""

    class ProductAPI(AutoAPI):
        model = sample_model

    class CategoryAPI(AutoAPI):
        model = another_model
    
    router = AutoAPIRouter()
    router.register(ProductAPI)
    router.register(CategoryAPI)
    
    # Both registered
    registered = router.get_registered_apis()
    assert len(registered) == 2
    assert 'test_app.product' in registered
    assert 'test_app.category' in registered


def test_get_urls_info(sample_model):
    """Test: Get URLs info"""

    class ProductAPI(AutoAPI):
        model = sample_model
    
    router = AutoAPIRouter()
    router.register(ProductAPI)
    
    # Get URLs info
    urls_info = router.get_urls_info()
    assert len(urls_info) > 0
    
    # Check some patterns exist
    patterns = [info['pattern'] for info in urls_info]
    # Should have list, detail, etc.
    assert any('products' in p for p in patterns)


def test_register_validation_error():
    """Test: Register dengan invalid API class raises error"""
    
    class InvalidAPI:
        pass  # Not inheriting from AutoAPI
    
    router = AutoAPIRouter()
    
    with pytest.raises(ValueError, match="must have 'model' attribute"):
        router.register(InvalidAPI)

        