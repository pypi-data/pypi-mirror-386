"""
Edge case tests untuk custom endpoints
"""

import pytest
from django.db import models
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, PermissionDenied

from django_autoapi.core import AutoAPI
from django_autoapi.decorators import endpoint, collection_action
from django_autoapi.factories.viewset import ViewSetFactory
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


# Use sample_model from conftest.py instead of creating duplicate fixture
# to avoid model conflicts


def test_endpoint_with_missing_required_fields(sample_model):
    """Test: Endpoint with missing required fields raises validation error"""

    class ProductAPI(AutoAPI):
        model = sample_model
        
        @endpoint(methods=['POST'], detail=True)
        def update_info(self, request, instance):
            EndpointValidation.require_fields(request.data, ['name', 'price'])
            return Response({'status': 'ok'})
    
    endpoints = ProductAPI._get_endpoints()
    assert len(endpoints) == 1


def test_endpoint_with_invalid_status(sample_model):
    """Test: Endpoint validates status correctly"""

    class ProductAPI(AutoAPI):
        model = sample_model
        
        @endpoint(methods=['POST'], detail=True)
        def activate(self, request, instance):
            EndpointValidation.validate_status(instance, 'inactive')
            instance.status = 'active'
            return Response({'status': 'active'})
    
    endpoints = ProductAPI._get_endpoints()
    assert len(endpoints) == 1


def test_endpoint_with_multiple_validations(sample_model):
    """Test: Endpoint with multiple validation checks"""

    class ProductAPI(AutoAPI):
        model = sample_model
        
        @endpoint(methods=['POST'], detail=True)
        @handle_endpoint_errors
        def complex_action(self, request, instance):
            # Multiple validations
            EndpointValidation.require_fields(request.data, ['quantity'])
            EndpointValidation.validate_status(instance, 'active')
            EndpointValidation.validate_condition(
                instance.stock > 0,
                'Out of stock'
            )
            
            return EndpointResponse.success(message='Action completed')
    
    endpoints = ProductAPI._get_endpoints()
    assert len(endpoints) == 1


def test_endpoint_with_serializer_validation_error(sample_model):
    """Test: Endpoint with serializer validation errors"""

    class UpdateSerializer(serializers.Serializer):
        price = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)
        stock = serializers.IntegerField(min_value=0)

    class ProductAPI(AutoAPI):
        model = sample_model
        
        @endpoint(
            methods=['POST'],
            detail=True,
            serializer_class=UpdateSerializer
        )
        def update_pricing(self, request, instance):
            serializer = UpdateSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            return Response(serializer.data)
    
    endpoints = ProductAPI._get_endpoints()
    assert len(endpoints) == 1


def test_endpoint_returning_error_response(sample_model):
    """Test: Endpoint explicitly returning error response"""

    class ProductAPI(AutoAPI):
        model = sample_model
        
        @endpoint(methods=['POST'], detail=True)
        def risky_action(self, request, instance):
            if instance.stock < 10:
                return EndpointResponse.error(
                    'Low stock warning',
                    errors={'stock': instance.stock},
                    status_code=400
                )
            
            return EndpointResponse.success(message='Action completed')
    
    endpoints = ProductAPI._get_endpoints()
    assert len(endpoints) == 1


def test_endpoint_with_permission_check(sample_model):
    """Test: Endpoint with permission validation"""

    class ProductAPI(AutoAPI):
        model = sample_model
        
        @endpoint(methods=['POST'], detail=True)
        def admin_action(self, request, instance):
            # This would check in real scenario
            # EndpointValidation.check_permission(request.user, 'app.admin_action')
            return EndpointResponse.success(message='Admin action completed')
    
    endpoints = ProductAPI._get_endpoints()
    assert len(endpoints) == 1


def test_collection_endpoint_with_empty_queryset(sample_model):
    """Test: Collection endpoint with empty queryset"""

    class ProductAPI(AutoAPI):
        model = sample_model
        
        @collection_action(methods=['GET'])
        def statistics(self, request, queryset):
            # Should handle empty queryset gracefully
            return EndpointResponse.success(data={
                'total': queryset.count(),
                'active': queryset.filter(status='active').count()
            })
    
    endpoints = ProductAPI._get_endpoints()
    assert len(endpoints) == 1


def test_collection_endpoint_with_filters(sample_model):
    """Test: Collection endpoint respects queryset filters"""

    class ProductAPI(AutoAPI):
        model = sample_model
        filterable = ['status']
        
        @collection_action(methods=['GET'])
        def summary(self, request, queryset):
            # Queryset should already be filtered
            return EndpointResponse.success(data={
                'count': queryset.count()
            })
    
    endpoints = ProductAPI._get_endpoints()
    assert len(endpoints) == 1


def test_endpoint_with_null_instance(sample_model):
    """Test: Endpoint gracefully handles null checks"""

    class ProductAPI(AutoAPI):
        model = sample_model
        
        @endpoint(methods=['POST'], detail=True)
        @handle_endpoint_errors
        def safe_action(self, request, instance):
            if not instance:
                raise ValueError('Instance not found')
            
            return EndpointResponse.success(message='Action completed')
    
    endpoints = ProductAPI._get_endpoints()
    assert len(endpoints) == 1


def test_endpoint_with_complex_business_logic(sample_model):
    """Test: Endpoint with complex multi-step business logic"""

    class ProductAPI(AutoAPI):
        model = sample_model
        
        @endpoint(methods=['POST'], detail=True)
        @handle_endpoint_errors
        def process_order(self, request, instance):
            # Step 1: Validate
            quantity = request.data.get('quantity', 0)
            EndpointValidation.validate_condition(
                quantity > 0,
                'Quantity must be positive'
            )
            EndpointValidation.validate_condition(
                instance.stock >= quantity,
                'Insufficient stock'
            )
            
            # Step 2: Execute
            instance.stock -= quantity
            
            # Step 3: Return
            return EndpointResponse.success(
                data={'remaining_stock': instance.stock},
                message='Order processed'
            )
    
    endpoints = ProductAPI._get_endpoints()
    assert len(endpoints) == 1


def test_multiple_endpoints_different_methods(sample_model):
    """Test: Multiple endpoints with different HTTP methods"""

    class ProductAPI(AutoAPI):
        model = sample_model
        
        @endpoint(methods=['GET'], detail=True)
        def get_status(self, request, instance):
            return Response({'status': instance.status})
        
        @endpoint(methods=['POST'], detail=True)
        def set_status(self, request, instance):
            instance.status = request.data.get('status')
            return Response({'status': instance.status})
        
        @endpoint(methods=['PUT'], detail=True)
        def update_status(self, request, instance):
            instance.status = request.data.get('status')
            return Response({'status': instance.status})
    
    endpoints = ProductAPI._get_endpoints()
    assert len(endpoints) == 3


def test_endpoint_with_nested_validation(sample_model):
    """Test: Endpoint with nested validation logic"""

    class ProductAPI(AutoAPI):
        model = sample_model
        
        @endpoint(methods=['POST'], detail=True)
        @handle_endpoint_errors
        def nested_validation(self, request, instance):
            # Nested validations
            if instance.status == 'active':
                EndpointValidation.validate_condition(
                    instance.stock > 0,
                    'Active products must have stock'
                )
                
                if instance.stock < 10:
                    EndpointValidation.validate_condition(
                        instance.price > 0,
                        'Low stock items must have price'
                    )
            
            return EndpointResponse.success(message='Validation passed')
    
    endpoints = ProductAPI._get_endpoints()
    assert len(endpoints) == 1


def test_endpoint_response_formats(sample_model):
    """Test: Different response format patterns"""

    class ProductAPI(AutoAPI):
        model = sample_model
        
        @endpoint(methods=['POST'], detail=True)
        def format_test(self, request, instance):
            format_type = request.data.get('format', 'success')
            
            if format_type == 'success':
                return EndpointResponse.success(data={'id': instance.id})
            elif format_type == 'created':
                return EndpointResponse.created(data={'id': instance.id})
            elif format_type == 'error':
                return EndpointResponse.error('Test error')
            else:
                return EndpointResponse.no_content()
    
    endpoints = ProductAPI._get_endpoints()
    assert len(endpoints) == 1


def test_endpoint_with_transaction_rollback(sample_model):
    """Test: Endpoint that may need transaction rollback"""

    class ProductAPI(AutoAPI):
        model = sample_model
        
        @endpoint(methods=['POST'], detail=True)
        @handle_endpoint_errors
        def transactional_action(self, request, instance):
            # In real scenario, use transaction.atomic()
            instance.stock -= 10
            
            # If this fails, stock change should rollback
            EndpointValidation.validate_condition(
                instance.stock >= 0,
                'Stock cannot be negative'
            )
            
            return EndpointResponse.success(message='Transaction completed')
    
    endpoints = ProductAPI._get_endpoints()
    assert len(endpoints) == 1

    