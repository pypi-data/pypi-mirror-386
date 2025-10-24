"""
Tests untuk AutoAPI core class
"""

import pytest
from django.db import models
from django_autoapi.core import AutoAPI


def test_autoapi_requires_model():
    """Test: AutoAPI harus punya model"""
    with pytest.raises(ValueError, match='harus mendefinisikan attribute "model"'):
        class InvalidAPI(AutoAPI):
            pass


def test_autoapi_model_must_be_django_model():
    """Test: model harus Django model"""
    with pytest.raises(ValueError, match='harus berupa Django model class'):
        class InvalidAPI(AutoAPI):
            model = str  # str bukan Django model


def test_autoapi_valid_definition(sample_model):
    """Test: AutoAPI dengan definisi yang valid"""
    class ProductAPI(AutoAPI):
        model = sample_model
        filterable = ['name', 'price']
        searchable = ['name']
        orderable = ['price']
    
    # Assertions
    assert ProductAPI.model == sample_model
    assert ProductAPI.filterable == ['name', 'price']
    assert ProductAPI.searchable == ['name']
    assert ProductAPI.orderable == ['price']


def test_autoapi_default_values(sample_model):
    """Test: AutoAPI dengan nilai default"""
    class ProductAPI(AutoAPI):
        model = sample_model

    # Check defaults
    assert ProductAPI.filterable == []
    assert ProductAPI.searchable == []
    assert ProductAPI.orderable == []
    assert ProductAPI.pagination == 'cursor'  # Default adalah 'cursor'
    assert ProductAPI.page_size == 50


def test_autoapi_filterable_must_be_list(sample_model):
    """Test: filterable harus list atau tuple"""
    with pytest.raises(TypeError, match='harus berupa list atau tuple'):
        class InvalidAPI(AutoAPI):
            model = sample_model
            filterable = 'name'  # String, bukan list


def test_autoapi_get_model_name(sample_model):
    """Test: get_model_name method"""
    class ProductAPI(AutoAPI):
        model = sample_model
    
    assert ProductAPI.get_model_name() == 'product'


def test_autoapi_get_app_label(sample_model):
    """Test: get_app_label method"""
    class ProductAPI(AutoAPI):
        model = sample_model
    
    assert ProductAPI.get_app_label() == 'test_app'


def test_autoapi_repr(sample_model):
    """Test: __repr__ method"""
    class ProductAPI(AutoAPI):
        model = sample_model
    
    assert 'ProductAPI' in repr(ProductAPI())
    assert 'Product' in repr(ProductAPI())

    