"""
Tests untuk advanced endpoint features
"""

import pytest
from django.db import models
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from django_autoapi.core import AutoAPI
from django_autoapi.decorators import endpoint
from django_autoapi.utils import (
    EndpointResponse,
    EndpointValidation,
    handle_endpoint_errors
)
from django_autoapi.registry import AutoAPIRegistry


@pytest.fixture(autouse=True)
def clear_registry():
    """Clear registry"""
    AutoAPIRegistry.clear()
    yield
    AutoAPIRegistry.clear()


# Use sample_model from conftest.py instead of creating a new fixture
# to avoid model conflicts


def test_endpoint_response_success():
    """Test: EndpointResponse.success"""
    response = EndpointResponse.success(data={'key': 'value'})
    
    assert response.status_code == 200
    assert 'data' in response.data
    assert response.data['data'] == {'key': 'value'}


def test_endpoint_response_error():
    """Test: EndpointResponse.error"""
    response = EndpointResponse.error('Error message')
    
    assert response.status_code == 400
    assert 'error' in response.data
    assert response.data['error'] == 'Error message'


def test_endpoint_response_created():
    """Test: EndpointResponse.created"""
    response = EndpointResponse.created(data={'id': 123})
    
    assert response.status_code == 201
    assert response.data['data'] == {'id': 123}


def test_endpoint_validation_require_fields():
    """Test: Require fields validation"""
    data = {'field1': 'value1'}
    
    # Should raise error
    with pytest.raises(ValidationError):
        EndpointValidation.require_fields(data, ['field1', 'field2'])
    
    # Should pass
    EndpointValidation.require_fields(data, ['field1'])


def test_endpoint_validation_status(sample_model):
    """Test: Status validation"""
    instance = sample_model(name='Test', status='active')
    
    # Should pass
    EndpointValidation.validate_status(instance, 'active')
    
    # Should raise
    with pytest.raises(ValidationError):
        EndpointValidation.validate_status(instance, 'inactive')


def test_endpoint_validation_not_status(sample_model):
    """Test: Not status validation"""
    instance = sample_model(name='Test', status='active')
    
    # Should pass
    EndpointValidation.validate_not_status(instance, 'inactive')
    
    # Should raise
    with pytest.raises(ValidationError):
        EndpointValidation.validate_not_status(instance, 'active')


def test_endpoint_validation_condition():
    """Test: Condition validation"""
    # Should pass
    EndpointValidation.validate_condition(True, 'Error')
    
    # Should raise
    with pytest.raises(ValidationError):
        EndpointValidation.validate_condition(False, 'Error message')


def test_handle_endpoint_errors_decorator(sample_model):
    """Test: Error handling decorator"""

    class ProductAPI(AutoAPI):
        model = sample_model
        
        @endpoint(methods=['POST'], detail=True)
        @handle_endpoint_errors
        def error_action(self, request, instance):
            raise ValueError('Test error')
    
    # Create ViewSet
    from django_autoapi.factories.viewset import ViewSetFactory
    viewset_class = ViewSetFactory.create_viewset(ProductAPI)
    
    # Method should exist
    assert hasattr(viewset_class, 'error_action')


def test_endpoint_with_validation(sample_model):
    """Test: Endpoint with validation logic"""

    class ProductAPI(AutoAPI):
        model = sample_model
        
        @endpoint(methods=['POST'], detail=True)
        def activate(self, request, instance):
            # Validation
            EndpointValidation.validate_condition(
                instance.can_activate(),
                'Cannot activate: out of stock'
            )
            
            instance.is_active = True
            return EndpointResponse.success(message='Activated')
    
    endpoints = ProductAPI._get_endpoints()
    assert len(endpoints) == 1


def test_endpoint_with_custom_serializer(sample_model):
    """Test: Endpoint with custom serializer"""

    class CustomSerializer(serializers.Serializer):
        message = serializers.CharField()

    class ProductAPI(AutoAPI):
        model = sample_model
        
        @endpoint(
            methods=['POST'],
            detail=True,
            serializer_class=CustomSerializer
        )
        def custom_action(self, request, instance):
            serializer = CustomSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            return Response(serializer.data)
    
    endpoints = ProductAPI._get_endpoints()
    name, func, config = endpoints[0]
    
    assert config['serializer_class'] == CustomSerializer


def test_complex_endpoint_pattern(sample_model):
    """Test: Complex endpoint with all features"""

    class UpdateSerializer(serializers.Serializer):
        status = serializers.CharField()

    class ProductAPI(AutoAPI):
        model = sample_model
        
        @endpoint(
            methods=['POST'],
            detail=True,
            serializer_class=UpdateSerializer
        )
        @handle_endpoint_errors
        def update_status(self, request, instance):
            # Validate input
            serializer = UpdateSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Validate business rules
            EndpointValidation.validate_condition(
                instance.can_activate(),
                'Cannot update status'
            )
            
            # Execute
            instance.status = serializer.validated_data['status']
            
            # Return
            return EndpointResponse.success(
                data={'status': instance.status},
                message='Status updated'
            )
    
    endpoints = ProductAPI._get_endpoints()
    assert len(endpoints) == 1

    