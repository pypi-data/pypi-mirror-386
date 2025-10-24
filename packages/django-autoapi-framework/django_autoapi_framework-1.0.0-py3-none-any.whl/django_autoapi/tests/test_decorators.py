"""
Tests untuk endpoint decorators
"""

import pytest
from django.db import models
from rest_framework.response import Response

from django_autoapi.core import AutoAPI
from django_autoapi.decorators import (
    endpoint, 
    is_endpoint, 
    get_endpoint_config,
    get_endpoint,
    post_endpoint,
    detail_action,
    collection_action,
)
from django_autoapi.registry import AutoAPIRegistry


@pytest.fixture(autouse=True)
def clear_registry():
    """Clear registry"""
    AutoAPIRegistry.clear()
    yield
    AutoAPIRegistry.clear()


def test_endpoint_decorator_basic():
    """Test: Basic endpoint decorator"""
    
    @endpoint(methods=['POST'], detail=True)
    def my_action(self, request, instance):
        return Response({'status': 'ok'})
    
    # Check marked as endpoint
    assert is_endpoint(my_action)
    
    # Check config stored
    config = get_endpoint_config(my_action)
    assert config is not None
    assert config['methods'] == ['POST']
    assert config['detail'] is True


def test_endpoint_decorator_defaults():
    """Test: Endpoint decorator with defaults"""
    
    @endpoint()
    def my_action(self, request, instance):
        return Response({'status': 'ok'})
    
    config = get_endpoint_config(my_action)
    
    # Check defaults
    assert config['methods'] == ['GET']
    assert config['detail'] is True
    assert config['permissions'] == []
    assert config['serializer_class'] is None


def test_endpoint_decorator_all_options():
    """Test: Endpoint decorator with all options"""
    
    from rest_framework.permissions import IsAuthenticated
    from rest_framework import serializers
    
    class CustomSerializer(serializers.Serializer):
        pass
    
    @endpoint(
        methods=['POST', 'PUT'],
        detail=False,
        permissions=[IsAuthenticated],
        serializer_class=CustomSerializer,
        url_path='custom-path',
        url_name='custom-name'
    )
    def my_action(self, request, queryset):
        return Response({'status': 'ok'})
    
    config = get_endpoint_config(my_action)
    
    # Check all options
    assert config['methods'] == ['POST', 'PUT']
    assert config['detail'] is False
    assert IsAuthenticated in config['permissions']
    assert config['serializer_class'] == CustomSerializer
    assert config['url_path'] == 'custom-path'
    assert config['url_name'] == 'custom-name'


def test_endpoint_on_api_class(sample_model):
    """Test: Endpoint decorator pada API class"""
    
    class ProductAPI(AutoAPI):
        model = sample_model
        
        @endpoint(methods=['POST'], detail=True)
        def activate(self, request, instance):
            instance.is_active = True
            instance.save()
            return Response({'status': 'activated'})
    
    # Extract endpoints
    endpoints = ProductAPI._get_endpoints()
    
    # Should have 1 endpoint
    assert len(endpoints) == 1
    
    # Check endpoint details
    name, func, config = endpoints[0]
    assert name == 'activate'
    assert config['methods'] == ['POST']
    assert config['detail'] is True


def test_multiple_endpoints_on_api(sample_model):
    """Test: Multiple endpoints pada satu API class"""
    
    class ProductAPI(AutoAPI):
        model = sample_model
        
        @endpoint(methods=['POST'], detail=True)
        def activate(self, request, instance):
            return Response({'status': 'activated'})
        
        @endpoint(methods=['POST'], detail=True)
        def deactivate(self, request, instance):
            return Response({'status': 'deactivated'})
        
        @endpoint(methods=['GET'], detail=False)
        def statistics(self, request, queryset):
            return Response({'total': queryset.count()})
    
    # Extract endpoints
    endpoints = ProductAPI._get_endpoints()
    
    # Should have 3 endpoints
    assert len(endpoints) == 3
    
    # Check names
    names = [name for name, func, config in endpoints]
    assert 'activate' in names
    assert 'deactivate' in names
    assert 'statistics' in names


def test_get_endpoint_info(sample_model):
    """Test: get_endpoint_info method"""
    
    class ProductAPI(AutoAPI):
        model = sample_model
        
        @endpoint(methods=['POST'], detail=True)
        def activate(self, request, instance):
            return Response({'status': 'activated'})
        
        @endpoint(methods=['GET'], detail=False)
        def statistics(self, request, queryset):
            return Response({'total': queryset.count()})
    
    # Get info
    info = ProductAPI.get_endpoint_info()
    
    # Check structure
    assert 'count' in info
    assert 'endpoints' in info
    assert info['count'] == 2
    assert len(info['endpoints']) == 2
    
    # Check endpoint details
    activate_info = next(ep for ep in info['endpoints'] if ep['name'] == 'activate')
    assert activate_info['methods'] == ['POST']
    assert activate_info['type'] == 'detail'
    assert activate_info['url_path'] == 'activate'


def test_shorthand_decorators(sample_model):
    """Test: Shorthand decorator functions"""
    
    class ProductAPI(AutoAPI):
        model = sample_model
        
        @get_endpoint(detail=True)
        def status(self, request, instance):
            return Response({'status': instance.is_active})
        
        @post_endpoint(detail=True)
        def activate(self, request, instance):
            return Response({'status': 'activated'})
    
    endpoints = ProductAPI._get_endpoints()
    assert len(endpoints) == 2
    
    # Check GET endpoint
    get_ep = next(ep for name, func, ep in endpoints if name == 'status')
    assert get_ep['methods'] == ['GET']
    
    # Check POST endpoint
    post_ep = next(ep for name, func, ep in endpoints if name == 'activate')
    assert post_ep['methods'] == ['POST']


def test_detail_action_decorator(sample_model):
    """Test: detail_action decorator"""
    
    class ProductAPI(AutoAPI):
        model = sample_model
        
        @detail_action(methods=['POST'])
        def archive(self, request, instance):
            return Response({'status': 'archived'})
    
    endpoints = ProductAPI._get_endpoints()
    name, func, config = endpoints[0]
    
    assert config['detail'] is True
    assert config['methods'] == ['POST']


def test_collection_action_decorator(sample_model):
    """Test: collection_action decorator"""
    
    class ProductAPI(AutoAPI):
        model = sample_model
        
        @collection_action(methods=['GET'])
        def export(self, request, queryset):
            return Response({'count': queryset.count()})
    
    endpoints = ProductAPI._get_endpoints()
    name, func, config = endpoints[0]
    
    assert config['detail'] is False
    assert config['methods'] == ['GET']


def test_endpoint_not_on_regular_method(sample_model):
    """Test: Regular methods tidak dianggap endpoint"""
    
    class ProductAPI(AutoAPI):
        model = sample_model
        
        def regular_method(self):
            """Regular method tanpa decorator"""
            pass
        
        @endpoint(methods=['POST'], detail=True)
        def custom_action(self, request, instance):
            return Response({'status': 'ok'})
    
    endpoints = ProductAPI._get_endpoints()
    
    # Hanya custom_action yang ter-extract
    assert len(endpoints) == 1
    assert endpoints[0][0] == 'custom_action'


def test_is_endpoint_function():
    """Test: is_endpoint helper function"""
    
    @endpoint()
    def endpoint_func():
        pass
    
    def regular_func():
        pass
    
    assert is_endpoint(endpoint_func) is True
    assert is_endpoint(regular_func) is False


def test_get_endpoint_config_on_non_endpoint():
    """Test: get_endpoint_config on non-endpoint returns None"""
    
    def regular_func():
        pass
    
    config = get_endpoint_config(regular_func)
    assert config is None

    